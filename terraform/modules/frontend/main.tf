# Frontend Module - S3 Static Website

# S3 Bucket for Frontend
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.environment}-youtube-chat-collector-frontend-${random_string.bucket_suffix.result}"

  tags = {
    Name = "${var.environment}-youtube-chat-collector-frontend"
  }
}

# Random string for bucket name uniqueness
resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Bucket Website Configuration
resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# S3 Bucket Policy for Public Read
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  depends_on = [aws_s3_bucket_public_access_block.frontend]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })
}

# S3 Bucket CORS Configuration
resource "aws_s3_bucket_cors_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# S3 Object for config.js (API Gateway URL injection)
resource "aws_s3_object" "config" {
  bucket       = aws_s3_bucket.frontend.id
  key          = "config.js"
  content_type = "application/javascript"
  
  content = templatefile("${path.module}/config.js.tpl", {
    api_gateway_url = var.api_gateway_url
    environment     = var.environment
  })

  tags = {
    Name = "${var.environment}-frontend-config"
  }
}

# Placeholder index.html
resource "aws_s3_object" "index" {
  bucket       = aws_s3_bucket.frontend.id
  key          = "index.html"
  content_type = "text/html"
  
  content = templatefile("${path.module}/index.html.tpl", {
    environment = var.environment
  })

  tags = {
    Name = "${var.environment}-frontend-index"
  }
}
