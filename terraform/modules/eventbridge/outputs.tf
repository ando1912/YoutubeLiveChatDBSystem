# EventBridge Module Outputs

output "eventbridge_rules" {
  description = "EventBridge rule information"
  value = {
    rss_monitor_schedule = {
      name = aws_cloudwatch_event_rule.rss_monitor_schedule.name
      arn  = aws_cloudwatch_event_rule.rss_monitor_schedule.arn
    }
    stream_status_checker_schedule = {
      name = aws_cloudwatch_event_rule.stream_status_checker_schedule.name
      arn  = aws_cloudwatch_event_rule.stream_status_checker_schedule.arn
    }
    ecs_task_launcher_manual = {
      name = aws_cloudwatch_event_rule.ecs_task_launcher_manual.name
      arn  = aws_cloudwatch_event_rule.ecs_task_launcher_manual.arn
    }
  }
}

output "custom_event_bus" {
  description = "Custom EventBridge bus information"
  value = {
    name = aws_cloudwatch_event_bus.youtube_comment_collector.name
    arn  = aws_cloudwatch_event_bus.youtube_comment_collector.arn
  }
}

output "dead_letter_queue" {
  description = "Dead Letter Queue information"
  value = {
    name = aws_sqs_queue.eventbridge_dlq.name
    arn  = aws_sqs_queue.eventbridge_dlq.arn
    url  = aws_sqs_queue.eventbridge_dlq.url
  }
}

output "cloudwatch_alarms" {
  description = "CloudWatch alarm information"
  value = {
    rss_monitor_errors = {
      name = aws_cloudwatch_metric_alarm.rss_monitor_errors.alarm_name
      arn  = aws_cloudwatch_metric_alarm.rss_monitor_errors.arn
    }
    stream_status_checker_errors = {
      name = aws_cloudwatch_metric_alarm.stream_status_checker_errors.alarm_name
      arn  = aws_cloudwatch_metric_alarm.stream_status_checker_errors.arn
    }
  }
}

output "log_group" {
  description = "CloudWatch log group information"
  value = {
    name = aws_cloudwatch_log_group.eventbridge_logs.name
    arn  = aws_cloudwatch_log_group.eventbridge_logs.arn
  }
}
