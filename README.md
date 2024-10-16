# Implementation of scalable FastAPI application on AWS EC2 with:
##### Clean architecture / Hexagonal Architecture and Clean Code with SONARQUBE
##### IOC with dependency-injector (base on containers providers)
##### Jenkins CI / CD
##### Ansible
##### Docker
##### Vagrant for test and development environment
##### Terraform for AWS EC2 deploy

## App main file
src/shared/infrastructure/fastapi/main.py

## IOC Dependency-injector containers
src/shared/infrastructure/containers
src/accounts_type/infrastructure/containers

## Terraform resources
src/shared/infrastructure/terraform_resources


terraform init / -migrate-state / reconfigure
terraform plan
terraform destroy --auto-approve

## Ansible resources
src/shared/infrastructure/ansible_resources

## Docker resources
src/shared/infrastructure/docker

## Install envsubst
apt-get install -y gettext-base

## Run a test
poetry run pytest -v

## Run API
poetry run uvicorn shared.infrastructure.fastapi.main:api --port 8080 --reload

## SONARQUBE
poetry run pytest -v --cov=./ --cov-report=xml
poetry run pytest test/e2e/test.py test/unit/test.py test/integration/test.py --cov=./ --cov-report=xml
pysonar-scanner -Dsonar.token=<your_generated_token>
