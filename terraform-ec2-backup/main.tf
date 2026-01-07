# ============================================================
# DATA SOURCES (GET UBUNTU AMI)
# ============================================================

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ============================================================
# S3 BUCKET (CREATE NEW OR REUSE EXISTING)
# ============================================================

# Option 1: Create new bucket (default)
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

# Option 2: Reuse existing bucket (if reuse_existing_resources = true AND bucket name is provided)
data "aws_s3_bucket" "existing_documents" {
  count = (var.reuse_existing_resources && var.existing_s3_bucket_name != "") ? 1 : 0
  bucket = var.existing_s3_bucket_name
}

# Local to determine which bucket to use
locals {
  s3_bucket_id = (
    var.reuse_existing_resources && var.existing_s3_bucket_name != ""
    ? data.aws_s3_bucket.existing_documents[0].id
    : aws_s3_bucket.documents[0].id
  )
}

# ============================================================
# VPC (USE DEFAULT OR REUSE EXISTING)
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

# ============================================================
# SUBNETS (USE DEFAULT OR REUSE EXISTING)
# ============================================================

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
# SECURITY GROUP (CREATE NEW OR REUSE EXISTING)
# ============================================================

# Option 1: Create new security group (default)
resource "aws_security_group" "synthdocs" {
  count = (var.reuse_existing_resources && var.existing_security_group_id != "") ? 0 : 1

  name        = "synthdocs-${var.environment}-sg"
  description = "Security group for SynthDocs API"
  vpc_id      = local.vpc_id

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_vpc_security_group_ingress_rule" "http" {
  count              = (var.reuse_existing_resources && var.existing_security_group_id != "") ? 0 : 1
  security_group_id  = aws_security_group.synthdocs[0].id
  cidr_ipv4         = var.allowed_ip_ranges[0]
  from_port         = 8080
  ip_protocol       = "tcp"
  to_port           = 8080
}

resource "aws_vpc_security_group_egress_rule" "allow_all_outbound" {
  count              = (var.reuse_existing_resources && var.existing_security_group_id != "") ? 0 : 1
  security_group_id  = aws_security_group.synthdocs[0].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 0
  ip_protocol       = "-1"
  to_port           = 0
}

# Local to determine which security group to use
locals {
  security_group_ids = (
    var.reuse_existing_resources && var.existing_security_group_id != ""
    ? [var.existing_security_group_id]
    : [aws_security_group.synthdocs[0].id]
  )
}

# ============================================================
# IAM ROLE & POLICIES (ALWAYS CREATE NEW)
# ============================================================

resource "aws_iam_role" "ec2_instance" {
  name = "synthdocs-ec2-instance-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_ssm_core" {
  role       = aws_iam_role.ec2_instance.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "s3_bedrock_access" {
  name = "synthdocs-s3-bedrock-policy"
  role = aws_iam_role.ec2_instance.id

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

resource "aws_iam_instance_profile" "ec2_instance" {
  name = "synthdocs-instance-profile-${var.environment}"
  role = aws_iam_role.ec2_instance.name
}

# ============================================================
# EC2 INSTANCE (ALWAYS CREATE NEW)
# ============================================================

resource "aws_instance" "synthdocs" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.ec2_instance.name
  subnet_id              = local.subnet_ids[0]
  vpc_security_group_ids = local.security_group_ids

  user_data = templatefile("${path.module}/user-data.sh", {
    github_repo   = var.github_repo
    s3_bucket     = local.s3_bucket_id
    aws_region    = var.aws_region
    bedrock_model = "anthropic.claude-3-sonnet-20240307"
  })

  tags = {
    Name        = "synthdocs-${var.environment}"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [user_data, ami]
  }
}

# ============================================================
# INSTANCE STATE CONTROL (START/STOP)
# ============================================================

resource "null_resource" "instance_state" {
  triggers = {
    instance_state = var.instance_state
  }

  provisioner "local-exec" {
    command = var.instance_state == "stopped"
      ? "aws ec2 stop-instances --instance-ids ${aws_instance.synthdocs.id} --region ${var.aws_region}"
      : "aws ec2 start-instances --instance-ids ${aws_instance.synthdocs.id} --region ${var.aws_region}"
  }

  depends_on = [aws_instance.synthdocs]
}
