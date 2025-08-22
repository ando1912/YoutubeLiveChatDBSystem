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

# EventBridge Outputs
output "eventbridge_rules" {
  description = "EventBridge rule information"
  value       = module.eventbridge.eventbridge_rules
}

output "eventbridge_custom_bus" {
  description = "Custom EventBridge bus information"
  value       = module.eventbridge.custom_event_bus
}

output "eventbridge_monitoring" {
  description = "EventBridge monitoring information"
  value = {
    dead_letter_queue = module.eventbridge.dead_letter_queue
    cloudwatch_alarms = module.eventbridge.cloudwatch_alarms
    log_group        = module.eventbridge.log_group
  }
}

output "frontend_bucket_name" {
  description = "Name of frontend S3 bucket"
  value       = module.frontend.bucket_name
}

output "frontend_url" {
  description = "URL of frontend application"
  value       = module.frontend.website_url
}

output "api_key" {
  description = "API Gateway API Key for frontend"
  value       = module.api.api_key_value
  sensitive   = true
}

output "frontend_deployment_command" {
  description = "AWS CLI command to deploy React.js build files"
  value       = module.frontend.deployment_command
}
