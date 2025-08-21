# Storage Module - DynamoDB Tables and Parameter Store

# YouTube API Key in Parameter Store
resource "aws_ssm_parameter" "youtube_api_key" {
  name  = "/${var.environment}/youtube-chat-collector/youtube-api-key"
  type  = "SecureString"
  value = var.youtube_api_key
  
  description = "YouTube Data API v3 Key for Live Chat Collector"
  
  tags = {
    Name = "${var.environment}-youtube-api-key"
  }
}

# Channels Table
resource "aws_dynamodb_table" "channels" {
  name           = "${var.environment}-Channels"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "channel_id"

  attribute {
    name = "channel_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.environment}-Channels"
  }
}

# LiveStreams Table
resource "aws_dynamodb_table" "livestreams" {
  name           = "${var.environment}-LiveStreams"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "video_id"

  attribute {
    name = "video_id"
    type = "S"
  }

  attribute {
    name = "channel_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name               = "channel_id-index"
    hash_key           = "channel_id"
    range_key          = "created_at"
    projection_type    = "ALL"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.environment}-LiveStreams"
  }
}

# Comments Table
resource "aws_dynamodb_table" "comments" {
  name           = "${var.environment}-Comments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "comment_id"
  range_key      = "video_id"

  attribute {
    name = "comment_id"
    type = "S"
  }

  attribute {
    name = "video_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name               = "video_id-timestamp-index"
    hash_key           = "video_id"
    range_key          = "timestamp"
    projection_type    = "ALL"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.environment}-Comments"
  }
}

# TaskStatus Table
resource "aws_dynamodb_table" "taskstatus" {
  name           = "${var.environment}-TaskStatus"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "video_id"

  attribute {
    name = "video_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.environment}-TaskStatus"
  }
}
