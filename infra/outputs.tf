output "api_endpoint" {
  description = "🚀 Your API URL - share this with your team! (Note: Public IP changes on redeploy)"
  value       = "Check ECS Console → Cluster → Tasks → Public IP"
}

output "ecs_cluster_name" {
  description = "📦 ECS cluster name"
  value       = local.ecs_cluster_id
}

output "ecs_service_name" {
  description = "🔧 ECS service name"
  value       = aws_ecs_service.synthdocs.name
}

output "ecr_repository_url" {
  description = "📦 ECR repository URL (for Bamboo pipeline)"
  value       = aws_ecr_repository.synthdocs.repository_url
}

output "s3_bucket_used" {
  description = "📦 S3 bucket being used (new or existing)"
  value       = local.s3_bucket_id
}

output "resource_mode" {
  description = "🔧 Resource mode: 'create_new' or 'reuse_existing'"
  value       = var.reuse_existing_resources ? "reuse_existing" : "create_new"
}

output "money_tip" {
  description = "💰 Save money by stopping service"
  value       = "terraform apply -var='desired_count=0'"
}

output "task_definition_arn" {
  description = "📋 Task definition ARN"
  value       = aws_ecs_task_definition.synthdocs.arn
}
