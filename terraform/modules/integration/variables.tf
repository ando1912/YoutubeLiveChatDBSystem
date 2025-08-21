# Integration Module Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_function_names" {
  description = "Names of Lambda functions"
  type        = object({
    rss_monitor         = string
    stream_status_checker = string
    ecs_task_launcher   = string
    api_handler         = string
  })
}

variable "lambda_function_arns" {
  description = "ARNs of Lambda functions"
  type        = object({
    rss_monitor         = string
    stream_status_checker = string
    ecs_task_launcher   = string
    api_handler         = string
  })
}

variable "eventbridge_rule_names" {
  description = "Names of EventBridge rules"
  type        = object({
    rss_monitor_schedule    = string
    stream_status_schedule  = string
  })
}

variable "eventbridge_rule_arns" {
  description = "ARNs of EventBridge rules"
  type        = object({
    rss_monitor_schedule    = string
    stream_status_schedule  = string
  })
}

variable "sqs_queue_arn" {
  description = "ARN of SQS task control queue"
  type        = string
}
