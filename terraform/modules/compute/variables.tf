# Compute Module Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs"
  type        = object({
    ecs_tasks = string
    lambda    = string
  })
}

variable "dynamodb_table_names" {
  description = "DynamoDB table names"
  type        = object({
    channels    = string
    livestreams = string
    comments    = string
    taskstatus  = string
  })
}

variable "dynamodb_table_arns" {
  description = "DynamoDB table ARNs"
  type        = object({
    channels    = string
    livestreams = string
    comments    = string
    taskstatus  = string
  })
}

variable "youtube_api_key_parameter_arn" {
  description = "Parameter Store ARN for YouTube API Key"
  type        = string
}

variable "sqs_queue_url" {
  description = "SQS Queue URL"
  type        = string
}

variable "sqs_queue_arn" {
  description = "SQS Queue ARN"
  type        = string
}
