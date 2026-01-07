# ============================================================
# CORE CONFIGURATION (YOU MUST SET THESE)
# ============================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Environment name (dev, test, prod, etc.)"
  type        = string
  default     = "dev"
}

variable "github_repo" {
  description = "Your GitHub repository URL (for documentation)"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name (unique across all of AWS!)"
  type        = string
}

# ============================================================
# ECS TASK CONFIGURATION
# ============================================================

variable "desired_count" {
  description = "Number of tasks to run (0 = stopped, 1 = running)"
  type        = number
  default     = 1

  validation {
    condition     = var.desired_count >= 0
    error_message = "desired_count must be 0 or greater"
  }
}

variable "cpu" {
  description = "Task CPU units (256 = 0.25 vCPU, 512 = 0.5 vCPU, 1024 = 1 vCPU)"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Task memory in MB (512 = 0.5 GB, 1024 = 1 GB, 2048 = 2 GB)"
  type        = number
  default     = 512
}

variable "image_tag" {
  description = "Docker image tag from ECR (e.g., 'latest', 'build-123')"
  type        = string
  default     = "latest"
}

# ============================================================
# ACCESS CONTROL
# ============================================================

variable "allowed_ip_ranges" {
  description = "Who can access API (must specify CIDR blocks, e.g., 203.0.113.0/24)"
  type        = list(string)

  validation {
    condition     = length(var.allowed_ip_ranges) > 0
    error_message = "allowed_ip_ranges must contain at least one CIDR block"
  }

  validation {
    condition     = alltrue([for cidr in var.allowed_ip_ranges : can(cidrhost(cidr, 0))])
    error_message = "allowed_ip_ranges must contain valid CIDR blocks"
  }
}

# ============================================================
# RESOURCE REUSE OPTIONS (MAKE IT TRIVIAL!)
# ============================================================

variable "reuse_existing_resources" {
  description = "Set to true to reuse existing resources, false to create new (default)"
  type        = bool
  default     = false
}

variable "existing_s3_bucket_name" {
  description = "Existing S3 bucket name (if reuse_existing_resources = true)"
  type        = string
  default     = ""
}

variable "existing_vpc_id" {
  description = "Existing VPC ID (if reuse_existing_resources = true)"
  type        = string
  default     = ""
}

variable "existing_subnet_ids" {
  description = "Existing subnet IDs (if reuse_existing_resources = true)"
  type        = list(string)
  default     = []
}

variable "existing_ecs_cluster_name" {
  description = "Existing ECS cluster name (if reuse_existing_resources = true)"
  type        = string
  default     = ""
}
