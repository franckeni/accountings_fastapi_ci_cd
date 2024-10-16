variable "aws_access_key" {
  type = string
  default = ""
}

variable "aws_secret_key" {
  type = string
  default = ""
}

variable "region" {
  type = string
  default = "eu-west-3"
}

variable "environment" {
  type = string
  default = "main"
}

variable "instance_type" {
  type = string
  default = "t2.nano"
}