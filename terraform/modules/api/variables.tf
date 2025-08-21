# API Gateway Module Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "api_handler_lambda" {
  description = "API Handler Lambda function details"
  type        = object({
    function_name = string
    arn          = string
    invoke_arn   = string
  })
}
