# Messaging Module - SQS and EventBridge

# SQS Queue for Task Control
resource "aws_sqs_queue" "task_control" {
  name                      = "${var.environment}-task-control-queue"
  delay_seconds             = 0
  max_message_size          = 2048
  message_retention_seconds = 1209600  # 14 days
  visibility_timeout_seconds = 30

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.task_control_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "${var.environment}-task-control-queue"
  }
}

# Dead Letter Queue
resource "aws_sqs_queue" "task_control_dlq" {
  name                      = "${var.environment}-task-control-dlq"
  message_retention_seconds = 1209600  # 14 days

  tags = {
    Name = "${var.environment}-task-control-dlq"
  }
}

# EventBridge Rule for RSS Monitor (5 minutes)
resource "aws_cloudwatch_event_rule" "rss_monitor_schedule" {
  name                = "${var.environment}-rss-monitor-schedule"
  description         = "Trigger RSS monitor every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = {
    Name = "${var.environment}-rss-monitor-schedule"
  }
}

# EventBridge Rule for Stream Status Checker (1 minute)
resource "aws_cloudwatch_event_rule" "stream_status_schedule" {
  name                = "${var.environment}-stream-status-schedule"
  description         = "Trigger stream status checker every 1 minute"
  schedule_expression = "rate(1 minute)"

  tags = {
    Name = "${var.environment}-stream-status-schedule"
  }
}
