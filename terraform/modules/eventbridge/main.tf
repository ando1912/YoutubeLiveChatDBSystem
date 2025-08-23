# EventBridge Module for YouTube Live Chat Collector
# 定期実行によるLambda関数の自動化

# RSS Monitor - 5分間隔実行
resource "aws_cloudwatch_event_rule" "rss_monitor_schedule" {
  name                = "${var.environment}-rss-monitor-schedule"
  description         = "Trigger RSS Monitor Lambda every 5 minutes"
  schedule_expression = "rate(5 minutes)"
  
  tags = {
    Name        = "${var.environment}-rss-monitor-schedule"
    Environment = var.environment
    Component   = "EventBridge"
  }
}

# RSS Monitor target and permission are managed in integration module

# Stream Status Checker - 5分間隔実行（API クォータ削減のため）
resource "aws_cloudwatch_event_rule" "stream_status_checker_schedule" {
  name                = "${var.environment}-stream-status-checker-schedule"
  description         = "Trigger Stream Status Checker Lambda every 5 minutes (reduced from 1 minute to save API quota)"
  schedule_expression = "rate(5 minutes)"
  
  tags = {
    Name        = "${var.environment}-stream-status-checker-schedule"
    Environment = var.environment
    Component   = "EventBridge"
  }
}

resource "aws_cloudwatch_event_target" "stream_status_checker_target" {
  rule      = aws_cloudwatch_event_rule.stream_status_checker_schedule.name
  target_id = "StreamStatusCheckerLambdaTarget"
  arn       = var.lambda_function_arns.stream_status_checker
}

resource "aws_lambda_permission" "allow_eventbridge_stream_status_checker" {
  statement_id  = "AllowExecutionFromEventBridge-StreamStatusChecker"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_names.stream_status_checker
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stream_status_checker_schedule.arn
}

# ECS Task Launcher - オンデマンド実行（手動トリガー用）
resource "aws_cloudwatch_event_rule" "ecs_task_launcher_manual" {
  name        = "${var.environment}-ecs-task-launcher-manual"
  description = "Manual trigger for ECS Task Launcher Lambda"
  state       = "ENABLED"
  
  # 手動実行用のイベントパターン
  event_pattern = jsonencode({
    source      = ["youtube.live.chat.collector"]
    detail-type = ["Manual ECS Task Launch"]
  })
  
  tags = {
    Name        = "${var.environment}-ecs-task-launcher-manual"
    Environment = var.environment
    Component   = "EventBridge"
  }
}

resource "aws_cloudwatch_event_target" "ecs_task_launcher_target" {
  rule      = aws_cloudwatch_event_rule.ecs_task_launcher_manual.name
  target_id = "ECSTaskLauncherLambdaTarget"
  arn       = var.lambda_function_arns.ecs_task_launcher
}

resource "aws_lambda_permission" "allow_eventbridge_ecs_task_launcher" {
  statement_id  = "AllowExecutionFromEventBridge-ECSTaskLauncher"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_names.ecs_task_launcher
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ecs_task_launcher_manual.arn
}

# CloudWatch Logs for EventBridge
resource "aws_cloudwatch_log_group" "eventbridge_logs" {
  name              = "/aws/events/${var.environment}-youtube-comment-collector"
  retention_in_days = 7
  
  tags = {
    Name        = "${var.environment}-eventbridge-logs"
    Environment = var.environment
    Component   = "EventBridge"
  }
}

# EventBridge Custom Bus (オプション)
resource "aws_cloudwatch_event_bus" "youtube_comment_collector" {
  name = "${var.environment}-youtube-comment-collector-bus"
  
  tags = {
    Name        = "${var.environment}-youtube-comment-collector-bus"
    Environment = var.environment
    Component   = "EventBridge"
  }
}

# Dead Letter Queue for failed events
resource "aws_sqs_queue" "eventbridge_dlq" {
  name                      = "${var.environment}-eventbridge-dlq"
  message_retention_seconds = 1209600 # 14 days
  
  tags = {
    Name        = "${var.environment}-eventbridge-dlq"
    Environment = var.environment
    Component   = "EventBridge"
  }
}

# CloudWatch Alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "rss_monitor_errors" {
  alarm_name          = "${var.environment}-rss-monitor-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors RSS Monitor Lambda errors"
  alarm_actions       = []

  dimensions = {
    FunctionName = var.lambda_function_names.rss_monitor
  }

  tags = {
    Name        = "${var.environment}-rss-monitor-errors"
    Environment = var.environment
    Component   = "EventBridge"
  }
}

resource "aws_cloudwatch_metric_alarm" "stream_status_checker_errors" {
  alarm_name          = "${var.environment}-stream-status-checker-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors Stream Status Checker Lambda errors (5 minute intervals)"
  alarm_actions       = []

  dimensions = {
    FunctionName = var.lambda_function_names.stream_status_checker
  }

  tags = {
    Name        = "${var.environment}-stream-status-checker-errors"
    Environment = var.environment
    Component   = "EventBridge"
  }
}
