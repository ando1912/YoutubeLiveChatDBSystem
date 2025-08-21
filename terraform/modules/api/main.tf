# API Gateway Module - REST API

# API Gateway REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.environment}-youtube-chat-collector-api"
  description = "YouTube Live Chat Collector REST API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.environment}-youtube-chat-collector-api"
  }
}

# API Gateway Resources
resource "aws_api_gateway_resource" "channels" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "channels"
}

resource "aws_api_gateway_resource" "streams" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "streams"
}

resource "aws_api_gateway_resource" "stream_id" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.streams.id
  path_part   = "{video_id}"
}

resource "aws_api_gateway_resource" "comments" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.stream_id.id
  path_part   = "comments"
}

# CORS Options Method for all resources
resource "aws_api_gateway_method" "channels_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.channels.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "streams_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.streams.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "comments_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.comments.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# API Methods
resource "aws_api_gateway_method" "channels_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.channels.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_method" "channels_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.channels.id
  http_method   = "POST"
  authorization = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_method" "streams_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.streams.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = true
}

resource "aws_api_gateway_method" "comments_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.comments.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = true
}

# Lambda Integrations
resource "aws_api_gateway_integration" "channels_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.channels.id
  http_method = aws_api_gateway_method.channels_get.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.api_handler_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "channels_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.channels.id
  http_method = aws_api_gateway_method.channels_post.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.api_handler_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "streams_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.streams.id
  http_method = aws_api_gateway_method.streams_get.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.api_handler_lambda.invoke_arn
}

resource "aws_api_gateway_integration" "comments_get" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.comments.id
  http_method = aws_api_gateway_method.comments_get.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.api_handler_lambda.invoke_arn
}

# CORS Integration
resource "aws_api_gateway_integration" "channels_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.channels.id
  http_method = aws_api_gateway_method.channels_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_integration" "streams_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.streams.id
  http_method = aws_api_gateway_method.streams_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_integration" "comments_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.comments.id
  http_method = aws_api_gateway_method.comments_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

# Method Responses for CORS
resource "aws_api_gateway_method_response" "channels_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.channels.id
  http_method = aws_api_gateway_method.channels_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_method_response" "streams_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.streams.id
  http_method = aws_api_gateway_method.streams_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_method_response" "comments_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.comments.id
  http_method = aws_api_gateway_method.comments_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

# Integration Responses for CORS
resource "aws_api_gateway_integration_response" "channels_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.channels.id
  http_method = aws_api_gateway_method.channels_options.http_method
  status_code = aws_api_gateway_method_response.channels_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

resource "aws_api_gateway_integration_response" "streams_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.streams.id
  http_method = aws_api_gateway_method.streams_options.http_method
  status_code = aws_api_gateway_method_response.streams_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

resource "aws_api_gateway_integration_response" "comments_options" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.comments.id
  http_method = aws_api_gateway_method.comments_options.http_method
  status_code = aws_api_gateway_method_response.comments_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Lambda Permission
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.api_handler_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# API Key
resource "aws_api_gateway_api_key" "main" {
  name = "${var.environment}-youtube-chat-collector-key"

  tags = {
    Name = "${var.environment}-youtube-chat-collector-key"
  }
}

# Usage Plan
resource "aws_api_gateway_usage_plan" "main" {
  name = "${var.environment}-youtube-chat-collector-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_deployment.main.stage_name
  }

  quota_settings {
    limit  = 10000
    period = "DAY"
  }

  throttle_settings {
    rate_limit  = 100
    burst_limit = 200
  }

  tags = {
    Name = "${var.environment}-youtube-chat-collector-plan"
  }
}

# Usage Plan Key
resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.main.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main.id
}

# API Deployment
resource "aws_api_gateway_deployment" "main" {
  depends_on = [
    aws_api_gateway_integration.channels_get,
    aws_api_gateway_integration.channels_post,
    aws_api_gateway_integration.streams_get,
    aws_api_gateway_integration.comments_get,
    aws_api_gateway_integration.channels_options,
    aws_api_gateway_integration.streams_options,
    aws_api_gateway_integration.comments_options,
  ]

  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = var.environment

  lifecycle {
    create_before_destroy = true
  }
}
