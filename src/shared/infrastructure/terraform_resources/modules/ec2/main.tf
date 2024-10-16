resource "aws_instance" "accountings_ec2" {
    ami                    = "ami-07db896e164bc4476"
    instance_type          = var.instance_type
    key_name               = var.key_name
    availability_zone = var.zones
    security_groups = ["${var.security_group_name}"]
    tags = {
        name = "${var.maintainer}-ec2"
    }

    root_block_device {
      delete_on_termination = true
    }

}

resource "aws_eip" "accountings_eip" {
    domain = "vpc"
    instance = aws_instance.accountings_ec2.id

    provisioner "local-exec" {
        command = <<EOT
            rm /var/jenkins_home/workspace/${var.project_name}/${var.environment}/public_ip.txt
            echo IP: ${self.public_ip} > /var/jenkins_home/workspace/${var.project_name}/${var.environment}/public_ip.txt
            EOT
    }
}