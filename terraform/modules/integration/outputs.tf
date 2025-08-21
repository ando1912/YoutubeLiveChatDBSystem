# Integration Module Outputs

output "cloudwatch_log_groups" {
  description = "CloudWatch Log Group names"
  value = {
    lambda_logs = { for k, v in aws_cloudwatch_log_group.lambda_logs : k => v.name }
    ecs_logs    = aws_cloudwatch_log_group.ecs_logs.name
  }
}

output "event_source_mappings" {
  description = "Lambda Event Source Mapping UUIDs"
  value = {
    ecs_task_launcher_sqs = aws_lambda_event_source_mapping.ecs_task_launcher_sqs.uuid
  }
}
