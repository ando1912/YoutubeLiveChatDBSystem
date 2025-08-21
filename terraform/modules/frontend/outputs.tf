# Frontend Module Outputs

output "bucket_name" {
  description = "Name of frontend S3 bucket"
  value       = aws_s3_bucket.frontend.id
}

output "bucket_arn" {
  description = "ARN of frontend S3 bucket"
  value       = aws_s3_bucket.frontend.arn
}

output "website_url" {
  description = "URL of frontend application"
  value       = "http://${aws_s3_bucket_website_configuration.frontend.website_endpoint}"
}

output "website_domain" {
  description = "Website endpoint domain"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}
