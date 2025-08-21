# YouTube Live Chat Collector - Development Environment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
  
  # S3バックエンド設定（構文チェック時はコメントアウト）
  # backend "s3" {
  #   bucket = "youtube-chat-collector-terraform-state"
  #   key    = "dev/terraform.tfstate"
  #   region = "ap-northeast-1"
  # }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = merge(var.common_tags, {
      Environment = var.environment
      ManagedBy   = "terraform"
      CreatedAt   = "2025-08-21"
    })
  }
}

provider "random" {}

# ネットワーキング
module "networking" {
  source = "../../modules/networking"
  
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
  
  public_subnet_cidrs = var.public_subnet_cidrs
  availability_zones  = var.availability_zones
}

# ストレージ
module "storage" {
  source = "../../modules/storage"
  
  environment     = var.environment
  youtube_api_key = var.youtube_api_key
}

# メッセージング (先に作成)
module "messaging" {
  source = "../../modules/messaging"
  
  environment = var.environment
}

# コンピューティング
module "compute" {
  source = "../../modules/compute"
  
  environment = var.environment
  
  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  security_group_ids = module.networking.security_group_ids
  
  dynamodb_table_names           = module.storage.dynamodb_table_names
  dynamodb_table_arns            = module.storage.dynamodb_table_arns
  youtube_api_key_parameter_arn  = module.storage.youtube_api_key_parameter_arn
  sqs_queue_url                  = module.messaging.sqs_queue_url
  sqs_queue_arn                  = module.messaging.sqs_queue_arn
}

# API
module "api" {
  source = "../../modules/api"
  
  environment        = var.environment
  api_handler_lambda = module.compute.api_handler_lambda
}

# フロントエンド
module "frontend" {
  source = "../../modules/frontend"
  
  environment     = var.environment
  api_gateway_url = module.api.api_gateway_url
}

# 統合 (EventBridge、Lambda接続)
module "integration" {
  source = "../../modules/integration"
  
  environment = var.environment
  
  lambda_function_names = module.compute.lambda_function_names
  lambda_function_arns  = module.compute.lambda_function_arns
  
  eventbridge_rule_names = module.messaging.eventbridge_rule_names
  eventbridge_rule_arns  = module.messaging.eventbridge_rule_arns
  
  sqs_queue_arn = module.messaging.sqs_queue_arn
}
