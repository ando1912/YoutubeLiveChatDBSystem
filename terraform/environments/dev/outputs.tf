# YouTube Live Chat Collector - Development Environment Outputs

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.networking.public_subnet_ids
}

output "dynamodb_table_names" {
  description = "Names of DynamoDB tables"
  value       = module.storage.dynamodb_table_names
}

output "lambda_function_names" {
  description = "Names of Lambda functions"
  value       = module.compute.lambda_function_names
}

output "ecs_cluster_name" {
  description = "Name of ECS cluster"
  value       = module.compute.ecs_cluster_name
}

output "api_gateway_url" {
  description = "URL of API Gateway"
  value       = module.api.api_gateway_url
}

output "frontend_bucket_name" {
  description = "Name of frontend S3 bucket"
  value       = module.frontend.bucket_name
}

output "frontend_url" {
  description = "URL of frontend application"
  value       = module.frontend.website_url
}
