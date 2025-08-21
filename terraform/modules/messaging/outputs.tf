# Messaging Module Outputs

output "sqs_queue_url" {
  description = "URL of SQS task control queue"
  value       = aws_sqs_queue.task_control.url
}

output "sqs_queue_arn" {
  description = "ARN of SQS task control queue"
  value       = aws_sqs_queue.task_control.arn
}

output "sqs_dlq_url" {
  description = "URL of SQS dead letter queue"
  value       = aws_sqs_queue.task_control_dlq.url
}

output "sqs_dlq_arn" {
  description = "ARN of SQS dead letter queue"
  value       = aws_sqs_queue.task_control_dlq.arn
}

output "eventbridge_rule_arns" {
  description = "ARNs of EventBridge rules"
  value = {
    rss_monitor_schedule    = aws_cloudwatch_event_rule.rss_monitor_schedule.arn
    stream_status_schedule  = aws_cloudwatch_event_rule.stream_status_schedule.arn
  }
}

output "eventbridge_rule_names" {
  description = "Names of EventBridge rules"
  value = {
    rss_monitor_schedule    = aws_cloudwatch_event_rule.rss_monitor_schedule.name
    stream_status_schedule  = aws_cloudwatch_event_rule.stream_status_schedule.name
  }
}
