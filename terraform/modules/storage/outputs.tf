# Storage Module Outputs

output "dynamodb_table_names" {
  description = "Names of DynamoDB tables"
  value = {
    channels    = aws_dynamodb_table.channels.name
    livestreams = aws_dynamodb_table.livestreams.name
    comments    = aws_dynamodb_table.comments.name
    taskstatus  = aws_dynamodb_table.taskstatus.name
  }
}

output "dynamodb_table_arns" {
  description = "ARNs of DynamoDB tables"
  value = {
    channels    = aws_dynamodb_table.channels.arn
    livestreams = aws_dynamodb_table.livestreams.arn
    comments    = aws_dynamodb_table.comments.arn
    taskstatus  = aws_dynamodb_table.taskstatus.arn
  }
}

output "youtube_api_key_parameter_name" {
  description = "Parameter Store name for YouTube API Key"
  value       = aws_ssm_parameter.youtube_api_key.name
}

output "youtube_api_key_parameter_arn" {
  description = "Parameter Store ARN for YouTube API Key"
  value       = aws_ssm_parameter.youtube_api_key.arn
}
