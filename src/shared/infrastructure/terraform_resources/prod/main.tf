provider "aws" {
  region = var.region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
}

terraform {
/*  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
*/
  backend "s3" {
    bucket = "terraform-backend-accountings"
    key = "accountings-dev.tfstate"
    region = "eu-west-3"
  }
}

module "security_group" {
  source = "../modules/security_group"
}

module "ec2" {
  source = "../modules/ec2"
  environment = var.environment
  instance_type = var.instance_type
  security_group_name = module.security_group.output_sg_name
}

