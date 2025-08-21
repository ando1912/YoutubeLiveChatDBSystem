# YouTube Live Chat Collector - Development Environment Variables

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["ap-northeast-1a", "ap-northeast-1c"]
}

variable "youtube_api_key" {
  description = "YouTube Data API key"
  type        = string
  sensitive   = true
}

variable "allowed_ip_addresses" {
  description = "IP addresses allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # 本番環境では制限する
}

# 共通タグ設定
variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    User    = "ryoga.ando@asia-quest.jp"
    Project = "Learning"
    SysName = "youtube-live-chat-collector"
  }
}
