# Compute Module Outputs

output "lambda_function_names" {
  description = "Names of Lambda functions"
  value = {
    rss_monitor         = aws_lambda_function.rss_monitor.function_name
    stream_status_checker = aws_lambda_function.stream_status_checker.function_name
    ecs_task_launcher   = aws_lambda_function.ecs_task_launcher.function_name
    api_handler         = aws_lambda_function.api_handler.function_name
  }
}

output "lambda_function_arns" {
  description = "ARNs of Lambda functions"
  value = {
    rss_monitor         = aws_lambda_function.rss_monitor.arn
    stream_status_checker = aws_lambda_function.stream_status_checker.arn
    ecs_task_launcher   = aws_lambda_function.ecs_task_launcher.arn
    api_handler         = aws_lambda_function.api_handler.arn
  }
}

output "ecs_cluster_name" {
  description = "Name of ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "ecr_repository_url" {
  description = "URL of ECR repository"
  value       = aws_ecr_repository.comment_collector.repository_url
}

output "api_handler_lambda" {
  description = "API Handler Lambda function details"
  value = {
    function_name = aws_lambda_function.api_handler.function_name
    arn          = aws_lambda_function.api_handler.arn
    invoke_arn   = aws_lambda_function.api_handler.invoke_arn
  }
}
