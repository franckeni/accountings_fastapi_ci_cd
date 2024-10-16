import os
import uuid

import pytest
from moto import mock_aws

from accounts_type.domains.schemas.base_accounts_type import BaseAccountsType
from accounts_type.presentation.view_models.accounts_type import (
    CreateAccountsType,
    UpdateAccountsType,
)
from shared.infrastructure.adapters.dynamodb_table_adapter import DynamodbTableAdapter
from shared.infrastructure.repositories.dynamodb_repository import DynamodbRepository
from shared.utils.dynamodb_data_transformer import DynamodbDataTransformer
from shared.utils.dynamodb_utils import DynamodbUtils


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(scope="function")
def config_infos():
    """Mocked global configuration for moto."""
    os.environ["TABLE_NAME"] = "accountings-erp-api"
    os.environ["DYNAMODB_URL"] = ""


@pytest.fixture(scope="function")
def dynamodb_table_adapter():
    """
    Return a mocked dynamodb client
    """
    return DynamodbTableAdapter(table_name=os.getenv("TABLE_NAME", "test-dynamodb"))


@pytest.fixture(scope="function")
def dynamodb_table(dynamodb_table_adapter, aws_credentials, config_infos):
    with mock_aws():
        dynamodb = dynamodb_table_adapter.get_dynamodb()
        table_name = os.getenv("TABLE_NAME", "test-dynamodb")

        table = dynamodb.create_table(
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
                {"AttributeName": "gsi1_pk", "AttributeType": "S"},
                {"AttributeName": "gsi1_sk", "AttributeType": "S"},
                {"AttributeName": "gsi2_pk", "AttributeType": "S"},
                {"AttributeName": "gsi2_sk", "AttributeType": "S"},
            ],
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi1",
                    "KeySchema": [
                        {"AttributeName": "gsi1_pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi1_sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                },
                {
                    "IndexName": "gsi2",
                    "KeySchema": [
                        {"AttributeName": "gsi2_pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi2_sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "ALL",
                    },
                },
            ],
        )

        yield table


# Test without Repository class
def test_create_accounts_type_retrieved_by_id(dynamodb_table_adapter, dynamodb_table):
    dynamodb = dynamodb_table_adapter.get_dynamodb()
    table_name = os.getenv("TABLE_NAME", "test-dynamodb")
    table = dynamodb.Table(table_name)

    datas = {
        "id": f"{""}{uuid.uuid4().hex}",
        "title": "Test 8",
        "class_number": 8,
        "parent_id": None,
    }
    accounts_type = CreateAccountsType(**datas)

    dynamodb_item = DynamodbDataTransformer.transform(
        datas=accounts_type, entity_prefix=CreateAccountsType.ID_PREFIX
    )

    table.put_item(Item=dynamodb_item)

    created_accounts_type = table.get_item(
        Key=DynamodbUtils.format_key(CreateAccountsType.ID_PREFIX, accounts_type.id)
    ).get("Item")

    assert created_accounts_type.get("class_number") == accounts_type.class_number


@pytest.fixture()
def accounts_type_repository(dynamodb_table_adapter):
    return DynamodbRepository(
        table_adapter=dynamodb_table_adapter, model=BaseAccountsType
    )


@pytest.fixture()
def instanciate_accounts_type_create():
    datas = {
        "id": f"{""}{uuid.uuid4().hex}",
        "title": "Test 8",
        "class_number": 8,
        "parent_id": None,
    }

    return CreateAccountsType(**datas)


# Test with Repository class
def test_repository_create_accounts_type_and_retrieve_it_by_id(
    accounts_type_repository, instanciate_accounts_type_create, dynamodb_table
):

    created_accounts_type = accounts_type_repository._create(
        instanciate_accounts_type_create
    )
    retrieved_accounts_type = accounts_type_repository._find_one(
        instanciate_accounts_type_create.id
    )

    assert created_accounts_type.get("id") == retrieved_accounts_type.get("id")
    assert created_accounts_type.get("class_number") == retrieved_accounts_type.get(
        "class_number"
    )
    assert created_accounts_type.get("title") == retrieved_accounts_type.get("title")


# Test with Repository class
def test_repository_find_all(
    accounts_type_repository, instanciate_accounts_type_create, dynamodb_table
):

    created_accounts_type = accounts_type_repository._create(
        instanciate_accounts_type_create
    )
    list_accounts_type = accounts_type_repository._find_all({"parent_only": True})

    find_accounts_type = [
        item
        for item in list_accounts_type
        if item.get("class_number") == instanciate_accounts_type_create.class_number
    ]

    find_accounts_type = find_accounts_type[0] if len(find_accounts_type) > 0 else None

    assert created_accounts_type.get("id") == find_accounts_type.get("id")
    assert created_accounts_type.get("class_number") == find_accounts_type.get(
        "class_number"
    )
    assert created_accounts_type.get("title") == find_accounts_type.get("title")


# Test with Repository class
def test_repository_update_accounts_type_and_retrieve_it_by_id(
    accounts_type_repository, instanciate_accounts_type_create, dynamodb_table
):

    created_accounts_type = accounts_type_repository._create(
        instanciate_accounts_type_create
    )

    instanciate_accounts_type_create = instanciate_accounts_type_create.model_dump()
    instanciate_accounts_type_create["title"] = "New Title"

    datas = UpdateAccountsType(**instanciate_accounts_type_create)

    updated_accounts_type = accounts_type_repository._update(datas.id, datas)
    retrieved_accounts_type = accounts_type_repository._find_one(datas.id)

    assert updated_accounts_type.get("id") == retrieved_accounts_type.get("id")
    assert updated_accounts_type.get("class_number") == retrieved_accounts_type.get(
        "class_number"
    )
    assert updated_accounts_type.get("title") == "New Title"
    assert created_accounts_type.get("title") != retrieved_accounts_type.get("title")


# Test with Repository class
def test_repository_delete_accounts_type_retrieved_by_id(
    accounts_type_repository, instanciate_accounts_type_create, dynamodb_table
):

    created_accounts_type = accounts_type_repository._create(
        instanciate_accounts_type_create
    )

    response = accounts_type_repository._delete(created_accounts_type.get("id"))

    assert response is True
