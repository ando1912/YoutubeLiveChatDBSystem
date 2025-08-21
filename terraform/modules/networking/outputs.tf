# Networking Module Outputs

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "security_group_ids" {
  description = "Security group IDs"
  value = {
    ecs_tasks = aws_security_group.ecs_tasks.id
    lambda    = aws_security_group.lambda.id
  }
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}
