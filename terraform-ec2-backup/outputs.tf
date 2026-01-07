output "api_endpoint" {
  description = "🚀 Your API URL - share this with your team!"
  value       = "http://${aws_instance.synthdocs.public_ip}:8080"
}

output "s3_bucket_used" {
  description = "📦 S3 bucket being used (new or existing)"
  value       = local.s3_bucket_id
}

output "resource_mode" {
  description = "🔧 Resource mode: 'create_new' or 'reuse_existing'"
  value       = var.reuse_existing_resources ? "reuse_existing" : "create_new"
}

output "instance_id" {
  description = "🖥️  EC2 instance ID"
  value       = aws_instance.synthdocs.id
}

output "money_tip" {
  description = "💰 Save money by stopping instance"
  value       = "terraform apply -var='instance_state=stopped'"
}
