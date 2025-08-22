# Frontend Module Outputs

output "bucket_name" {
  description = "S3 bucket name for frontend hosting"
  value       = aws_s3_bucket.frontend.id
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.frontend.arn
}

output "website_endpoint" {
  description = "S3 website endpoint URL"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "website_url" {
  description = "Complete S3 website URL"
  value       = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}

output "bucket_domain_name" {
  description = "S3 bucket domain name (for CloudFront origin)"
  value       = aws_s3_bucket.frontend.bucket_domain_name
}

output "deployment_command" {
  description = "AWS CLI command to deploy React.js build files"
  value       = "aws s3 sync build/ s3://${aws_s3_bucket.frontend.id}/ --delete"
}
