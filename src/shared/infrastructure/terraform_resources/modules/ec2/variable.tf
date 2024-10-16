variable "aws_key_pair" {
  default = "~/aws/aws_keys/default-ec2.pem"
}

variable "maintainer" {
    type = string
    default = "ec2_local_user"
}

variable "project_name" {
    type = string
    default = "accountings-pipeline"
}

variable "server_name" {
    type = string
    default = "NULL"
}

variable "security_group_name" {
    type = string
    default = "NULL"
}

variable "public_ip" {
    type = string
    default = "NULL"
}

variable "environment" {
    type = string
    default = "develop"
}

variable "instance_type" {
    type = string
    default = "t2.micro"
}

variable "key_name" {
    type = string
    default = "accountings"
}

variable "user" {
    type = string
    default = "ec2-user"
}

variable "zones" {
    type = string
    default = "eu-west-3a"
}
