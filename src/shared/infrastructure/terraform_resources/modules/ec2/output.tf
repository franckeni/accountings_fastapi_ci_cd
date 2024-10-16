output "output_ec2_id" {
  value = aws_instance.accountings_ec2.id
}

output "output_ec2_zones" {
  value = aws_instance.accountings_ec2.availability_zone
}