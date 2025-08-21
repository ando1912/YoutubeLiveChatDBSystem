# Integration Module - EventBridge and Lambda Connections

# EventBridge Target for RSS Monitor
resource "aws_cloudwatch_event_target" "rss_monitor_target" {
  rule      = var.eventbridge_rule_names.rss_monitor_schedule
  target_id = "RSSMonitorLambdaTarget"
  arn       = var.lambda_function_arns.rss_monitor
}

# Lambda Permission for EventBridge (RSS Monitor)
resource "aws_lambda_permission" "allow_eventbridge_rss_monitor" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_names.rss_monitor
  principal     = "events.amazonaws.com"
  source_arn    = var.eventbridge_rule_arns.rss_monitor_schedule
}

# EventBridge Target for Stream Status Checker
resource "aws_cloudwatch_event_target" "stream_status_target" {
  rule      = var.eventbridge_rule_names.stream_status_schedule
  target_id = "StreamStatusCheckerLambdaTarget"
  arn       = var.lambda_function_arns.stream_status_checker
}

# Lambda Permission for EventBridge (Stream Status Checker)
resource "aws_lambda_permission" "allow_eventbridge_stream_status" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_names.stream_status_checker
  principal     = "events.amazonaws.com"
  source_arn    = var.eventbridge_rule_arns.stream_status_schedule
}

# SQS Event Source Mapping for ECS Task Launcher
resource "aws_lambda_event_source_mapping" "ecs_task_launcher_sqs" {
  event_source_arn = var.sqs_queue_arn
  function_name    = var.lambda_function_arns.ecs_task_launcher
  batch_size       = 1
  enabled          = true
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = var.lambda_function_names

  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7

  tags = {
    Name = "${var.environment}-${each.key}-logs"
  }
}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/${var.environment}-comment-collector"
  retention_in_days = 7

  tags = {
    Name = "${var.environment}-comment-collector-logs"
  }
}
