# Frontend Module Variables

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "api_gateway_url" {
  description = "API Gateway URL for React.js application"
  type        = string
}

variable "api_key" {
  description = "API Gateway API Key for React.js application"
  type        = string
  sensitive   = true
}

variable "app_version" {
  description = "Application version for deployment tracking"
  type        = string
  default     = "1.0.0"
}

variable "allowed_origins" {
  description = "Allowed origins for CORS configuration"
  type        = list(string)
  default     = ["*"]
}

variable "enable_versioning" {
  description = "Enable S3 bucket versioning for rollback capability"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
