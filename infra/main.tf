# ============================================================
# VPC AND NETWORK (USE DEFAULT OR REUSE EXISTING)
# ============================================================

data "aws_vpc" "default" {
  count = (var.reuse_existing_resources && var.existing_vpc_id != "") ? 0 : 1
  default = true
}

data "aws_vpc" "existing" {
  count = (var.reuse_existing_resources && var.existing_vpc_id != "") ? 1 : 0
  id = var.existing_vpc_id
}

locals {
  vpc_id = (
    var.reuse_existing_resources && var.existing_vpc_id != ""
    ? data.aws_vpc.existing[0].id
    : data.aws_vpc.default[0].id
  )
}

data "aws_subnets" "default" {
  count = (var.reuse_existing_resources && length(var.existing_subnet_ids) > 0) ? 0 : 1
  filter {
    name   = "vpc-id"
    values = [local.vpc_id]
  }
}

locals {
  subnet_ids = (
    var.reuse_existing_resources && length(var.existing_subnet_ids) > 0
    ? var.existing_subnet_ids
    : data.aws_subnets.default[0].ids
  )
}

# ============================================================
# S3 BUCKET (CREATE NEW OR REUSE EXISTING)
# ============================================================

resource "aws_s3_bucket" "documents" {
  count = var.reuse_existing_resources ? 0 : 1

  bucket = var.s3_bucket_name

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  count  = var.reuse_existing_resources ? 0 : 1
  bucket = aws_s3_bucket.documents[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  count  = var.reuse_existing_resources ? 0 : 1
  bucket = aws_s3_bucket.documents[0].id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents" {
  count  = var.reuse_existing_resources ? 0 : 1
  bucket = aws_s3_bucket.documents[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_s3_bucket" "existing_documents" {
  count = (var.reuse_existing_resources && var.existing_s3_bucket_name != "") ? 1 : 0
  bucket = var.existing_s3_bucket_name
}

locals {
  s3_bucket_id = (
    var.reuse_existing_resources && var.existing_s3_bucket_name != ""
    ? data.aws_s3_bucket.existing_documents[0].id
    : aws_s3_bucket.documents[0].id
  )
}

# ============================================================
# ECR REPOSITORY (ALWAYS CREATE NEW)
# ============================================================

resource "aws_ecr_repository" "synthdocs" {
  name = "synthdocs-${var.environment}"

  image_scanning_configuration {
    scan_on_push = true
  }

  force_delete = true

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }
}

# ============================================================
# ECS CLUSTER (CREATE NEW OR REUSE EXISTING)
# ============================================================

resource "aws_ecs_cluster" "main" {
  count = (var.reuse_existing_resources && var.existing_ecs_cluster_name != "") ? 0 : 1

  name = "synthdocs-${var.environment}"

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }
}

data "aws_ecs_cluster" "existing" {
  count = (var.reuse_existing_resources && var.existing_ecs_cluster_name != "") ? 1 : 0
  cluster_name = var.existing_ecs_cluster_name
}

locals {
  ecs_cluster_id = (
    var.reuse_existing_resources && var.existing_ecs_cluster_name != ""
    ? data.aws_ecs_cluster.existing[0].id
    : aws_ecs_cluster.main[0].id
  )
}

# ============================================================
# IAM ROLES (ALWAYS CREATE NEW)
# ============================================================

resource "aws_iam_role" "ecs_task_execution" {
  name = "synthdocs-ecs-execution-role-${var.environment}"

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

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name = "synthdocs-ecs-task-role-${var.environment}"

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

resource "aws_iam_role_policy" "ecs_task_s3_bedrock" {
  name = "s3-bedrock-access"
  role = aws_iam_role.ecs_task.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Resource = [
          "${local.s3_bucket_id}",
          "${local.s3_bucket_id}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================================
# SECURITY GROUP (ALWAYS CREATE NEW)
# ============================================================

resource "aws_security_group" "synthdocs" {
  name        = "synthdocs-${var.environment}-sg"
  description = "Security group for SynthDocs ECS tasks"
  vpc_id      = local.vpc_id

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  security_group_id = aws_security_group.synthdocs.id
  cidr_ipv4         = var.allowed_ip_ranges[0]
  from_port         = 8080
  ip_protocol       = "tcp"
  to_port           = 8080
}

resource "aws_vpc_security_group_egress_rule" "allow_all_outbound" {
  security_group_id = aws_security_group.synthdocs.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 0
  ip_protocol       = "-1"
  to_port           = 0
}

# ============================================================
# CLOUDWATCH LOG GROUP (ALWAYS CREATE NEW)
# ============================================================

resource "aws_cloudwatch_log_group" "synthdocs" {
  name              = "/ecs/synthdocs-${var.environment}"
  retention_in_days = 7

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }
}

# ============================================================
# ECS TASK DEFINITION (ALWAYS CREATE NEW)
# ============================================================

resource "aws_ecs_task_definition" "synthdocs" {
  family                   = "synthdocs"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn           = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "synthdocs"
      image     = "${aws_ecr_repository.synthdocs.repository_url}:${var.image_tag}"
      cpu       = var.cpu
      memory    = var.memory
      essential = true
      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "CONFIG_PATH"
          value = "config_aws.yaml"
        },
        {
          name  = "OUTPUT_MODE"
          value = "s3"
        },
        {
          name  = "S3_BUCKET"
          value = local.s3_bucket_id
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "LLM_PROVIDER"
          value = "bedrock"
        },
        {
          name  = "BEDROCK_MODEL_ID"
          value = "anthropic.claude-3-sonnet-20240307"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.synthdocs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "synthdocs"
          "awslogs-create-group"  = "true"
        }
      }
    }
  ])

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }
}

# ============================================================
# ECS SERVICE (ALWAYS CREATE NEW)
# ============================================================

resource "aws_ecs_service" "synthdocs" {
  name            = "synthdocs"
  cluster         = local.ecs_cluster_id
  task_definition = aws_ecs_task_definition.synthdocs.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.subnet_ids
    security_groups  = [aws_security_group.synthdocs.id]
    assign_public_ip = true
  }

  enable_execute_command = true

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }
}
