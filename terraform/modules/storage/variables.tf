# Storage Module Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "youtube_api_key" {
  description = "YouTube Data API v3 Key"
  type        = string
  sensitive   = true
}
