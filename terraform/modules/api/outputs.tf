# API Gateway Module Outputs

output "api_gateway_url" {
  description = "URL of API Gateway"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}"
}

output "api_gateway_id" {
  description = "ID of API Gateway"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_key_id" {
  description = "ID of API Key"
  value       = aws_api_gateway_api_key.main.id
}

output "api_key_value" {
  description = "Value of API Key"
  value       = aws_api_gateway_api_key.main.value
  sensitive   = true
}

# Data source for current region
data "aws_region" "current" {}
