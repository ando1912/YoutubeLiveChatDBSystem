# EventBridge Module Variables

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "lambda_function_arns" {
  description = "ARNs of Lambda functions to be triggered by EventBridge"
  type = object({
    rss_monitor           = string
    stream_status_checker = string
    ecs_task_launcher     = string
    api_handler          = string
  })
}

variable "lambda_function_names" {
  description = "Names of Lambda functions to be triggered by EventBridge"
  type = object({
    rss_monitor           = string
    stream_status_checker = string
    ecs_task_launcher     = string
    api_handler          = string
  })
}

variable "rss_monitor_schedule" {
  description = "Schedule expression for RSS Monitor (default: every 5 minutes)"
  type        = string
  default     = "rate(5 minutes)"
}

variable "stream_status_checker_schedule" {
  description = "Schedule expression for Stream Status Checker (default: every 1 minute)"
  type        = string
  default     = "rate(1 minute)"
}

variable "enable_custom_bus" {
  description = "Whether to create a custom EventBridge bus"
  type        = bool
  default     = true
}

variable "enable_monitoring" {
  description = "Whether to create CloudWatch alarms for monitoring"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch logs retention period in days"
  type        = number
  default     = 7
}
