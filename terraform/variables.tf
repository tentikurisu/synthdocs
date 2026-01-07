# ============================================================
# CORE CONFIGURATION (YOU MUST SET THESE)
# ============================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-1"
}

variable "github_repo" {
  description = "Your GitHub repository URL"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name (unique across all of AWS!)"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, test, prod, etc.)"
  type        = string
  default     = "dev"
}

# ============================================================
# INSTANCE SETTINGS
# ============================================================

variable "instance_state" {
  description = "Instance state: 'running' to start, 'stopped' to stop (save money)"
  type        = string
  default     = "running"

  validation {
    condition     = contains(["running", "stopped"], var.instance_state)
    error_message = "Must be 'running' or 'stopped'"
  }
}

variable "instance_type" {
  description = "EC2 instance type: t3.nano (cheapest), t3.micro, t3.small"
  type        = string
  default     = "t3.nano"
}

variable "allowed_ip_ranges" {
  description = "Who can access API (0.0.0.0/0 = anyone, or office IP like 203.0.113.0/24)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# ============================================================
# RESOURCE REUSE OPTIONS (MAKE IT TRIVIAL!)
# ============================================================

variable "reuse_existing_resources" {
  description = "Set to true to reuse existing resources, false to create new (default)"
  type        = bool
  default     = false
}

# Only needed if reuse_existing_resources = true
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

variable "existing_security_group_id" {
  description = "Existing security group ID (if reuse_existing_resources = true)"
  type        = string
  default     = ""
}
