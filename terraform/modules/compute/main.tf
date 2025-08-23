# Compute Module - Lambda Functions and ECS

# IAM Role for Lambda Functions
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.environment}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda Functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.environment}-lambda-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          for table_arn in values(var.dynamodb_table_arns) : table_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query"
        ]
        Resource = [
          for table_arn in values(var.dynamodb_table_arns) : "${table_arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = var.youtube_api_key_parameter_arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.sqs_queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "ecs:StopTask",
          "ecs:DescribeTasks",
          "ecs:TagResource",
          "ecs:ListTasks",
          "ecs:DescribeTaskDefinition"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          aws_iam_role.ecs_task_execution_role.arn,
          aws_iam_role.ecs_task_role.arn
        ]
      }
    ]
  })
}

# RSS Monitor Lambda Function
resource "aws_lambda_function" "rss_monitor" {
  filename         = "${path.module}/lambda_placeholder.zip"
  function_name    = "${var.environment}-rss-monitor-lambda"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "main.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      ENVIRONMENT = var.environment
      DYNAMODB_TABLE_CHANNELS = var.dynamodb_table_names.channels
      DYNAMODB_TABLE_LIVESTREAMS = var.dynamodb_table_names.livestreams
      SQS_QUEUE_URL = var.sqs_queue_url
    }
  }

  tags = {
    Name = "${var.environment}-rss-monitor-lambda"
  }
}

# Stream Status Checker Lambda Function
resource "aws_lambda_function" "stream_status_checker" {
  filename         = "${path.module}/lambda_placeholder.zip"
  function_name    = "${var.environment}-stream-status-checker-lambda"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "main.lambda_handler"
  runtime         = "python3.9"
  timeout         = 60

  environment {
    variables = {
      ENVIRONMENT = var.environment
      DYNAMODB_TABLE_CHANNELS = var.dynamodb_table_names.channels
      DYNAMODB_TABLE_LIVESTREAMS = var.dynamodb_table_names.livestreams
      DYNAMODB_TABLE_TASK_STATUS = var.dynamodb_table_names.taskstatus
      SQS_QUEUE_URL = var.sqs_queue_url
      ECS_CLUSTER_NAME = var.ecs_cluster_name
    }
  }

  tags = {
    Name = "${var.environment}-stream-status-checker-lambda"
  }
}

# ECS Task Launcher Lambda Function
resource "aws_lambda_function" "ecs_task_launcher" {
  filename         = "${path.module}/lambda_placeholder.zip"
  function_name    = "${var.environment}-ecs-task-launcher-lambda"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "main.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      ENVIRONMENT = var.environment
      DYNAMODB_TABLE_TASKSTATUS = var.dynamodb_table_names.taskstatus
      ECS_CLUSTER_NAME = aws_ecs_cluster.main.name
      ECS_TASK_DEFINITION = aws_ecs_task_definition.comment_collector.family
      ECS_SUBNETS = join(",", var.public_subnet_ids)
      ECS_SECURITY_GROUPS = var.security_group_ids.ecs_tasks
    }
  }

  tags = {
    Name = "${var.environment}-ecs-task-launcher-lambda"
  }
}

# API Handler Lambda Function
resource "aws_lambda_function" "api_handler" {
  filename         = "${path.module}/lambda_placeholder.zip"
  function_name    = "${var.environment}-api-handler-lambda"
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "main.lambda_handler"
  runtime         = "python3.9"
  timeout         = 30

  environment {
    variables = {
      ENVIRONMENT = var.environment
      DYNAMODB_TABLE_CHANNELS = var.dynamodb_table_names.channels
      DYNAMODB_TABLE_LIVESTREAMS = var.dynamodb_table_names.livestreams
      DYNAMODB_TABLE_COMMENTS = var.dynamodb_table_names.comments
      TASKSTATUS_TABLE = var.dynamodb_table_names.taskstatus
    }
  }

  tags = {
    Name = "${var.environment}-api-handler-lambda"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-youtube-comment-collector"

  setting {
    name  = "containerInsights"
    value = "disabled"  # コスト削減のため無効
  }

  tags = {
    Name = "${var.environment}-youtube-comment-collector"
  }
}

# ECR Repository
resource "aws_ecr_repository" "comment_collector" {
  name                 = "${var.environment}-comment-collector"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = false  # コスト削減のため無効
  }

  tags = {
    Name = "${var.environment}-comment-collector"
  }
}

# ECR Lifecycle Policy
resource "aws_ecr_lifecycle_policy" "comment_collector" {
  repository = aws_ecr_repository.comment_collector.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus = "any"
          countType = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# CodeBuild Service Role
resource "aws_iam_role" "codebuild_service_role" {
  name = "${var.environment}-codebuild-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.environment}-codebuild-service-role"
  }
}

# CodeBuild Service Role Policy
resource "aws_iam_role_policy" "codebuild_service_policy" {
  name = "${var.environment}-codebuild-service-policy"
  role = aws_iam_role.codebuild_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:GetAuthorizationToken",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = "*"
      }
    ]
  })
}

# CodeBuild Project
resource "aws_codebuild_project" "comment_collector" {
  name         = "${var.environment}-comment-collector-build"
  description  = "Build and push comment collector container to ECR"
  service_role = aws_iam_role.codebuild_service_role.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/amazonlinux2-x86_64-standard:3.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    privileged_mode            = true  # Docker操作に必要

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }

    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = aws_ecr_repository.comment_collector.name
    }

    environment_variable {
      name  = "IMAGE_TAG"
      value = "latest"
    }
  }

  source {
    type            = "GITHUB"
    location        = var.github_repository_url
    git_clone_depth = 1
    buildspec       = "ci-cd/buildspec.yml"

    git_submodules_config {
      fetch_submodules = false
    }
  }

  source_version = "main"

  tags = {
    Name = "${var.environment}-comment-collector-build"
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# ECS Task Execution Role
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.environment}-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# ECS Task Execution Policy
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# ECS Task Policy
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.environment}-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          var.dynamodb_table_arns.comments,
          var.dynamodb_table_arns.taskstatus
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# ECS Task Definition
resource "aws_ecs_task_definition" "comment_collector" {
  family                   = "${var.environment}-comment-collector"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "comment-collector"
      image = "${aws_ecr_repository.comment_collector.repository_url}:latest"
      
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "DYNAMODB_TABLE_COMMENTS"
          value = var.dynamodb_table_names.comments
        },
        {
          name  = "DYNAMODB_TABLE_TASKSTATUS"
          value = var.dynamodb_table_names.taskstatus
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.environment}-comment-collector"
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = "ecs"
          "awslogs-create-group"  = "true"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name = "${var.environment}-comment-collector"
  }
}

# Data source for current region
data "aws_region" "current" {}

# Placeholder Lambda deployment package
data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/lambda_placeholder.zip"
  source {
    content  = "def lambda_handler(event, context): return {'statusCode': 200}"
    filename = "main.py"
  }
}
