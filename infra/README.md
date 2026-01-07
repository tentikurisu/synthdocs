# 🚀 SynthDocs AWS Deployment - ECS Fargate

Deploy your SynthDocs API to AWS ECS using **Fargate (serverless)** with Terraform.

**Perfect for Bamboo pipelines!**

---

## ✨ Key Features

- ✅ **ECS Fargate** - No EC2 instances to manage
- ✅ **Bamboo-ready** - Builds Docker image, pushes to ECR, deploys with Terraform
- ✅ **Simple on/off control** - Set `desired_count = 0` to stop (save money)
- ✅ **Hybrid flexibility** - Create new OR reuse existing VPC/subnets/cluster
- ✅ **Auto-healing** - ECS automatically restarts failed tasks
- ✅ **Cost-effective** - ~$15/month when running 8hrs/day

---

## 📋 Quick Start (5 Minutes!)

### Step 1: Install Tools

```bash
# Install Terraform
# Download from: https://developer.hashicorp.com/terraform/downloads

# Install AWS CLI
# Download from: https://aws.amazon.com/cli/

# Configure AWS credentials
aws configure
# Enter your AWS Access Key and Secret Key
```

### Step 2: Initialize Terraform

```bash
cd infra
terraform init
```

### Step 3: Configure & Deploy

```bash
# Copy example config
cp terraform.tfvars.example terraform.tfvars

# Edit it (change these 3 required values):
# - github_repo: Your GitHub repository URL
# - s3_bucket_name: Unique bucket name
# - environment: "dev", "test", "prod", etc.
nano terraform.tfvars

# Deploy infrastructure
terraform apply
```

Wait 2-3 minutes. Your ECS infrastructure will be ready!

---

## 🎯 Deployment Options

### Option 1: Create Everything New (Default)

**Best for:** Beginners, testing, isolated deployments

```hcl
# In terraform.tfvars
reuse_existing_resources = false
```

**What happens:**
- Creates new S3 bucket
- Uses default AWS VPC
- Creates new ECS cluster
- Creates new ECR repository
- Complete control and isolation

### Option 2: Reuse Existing Resources

**Best for:** Production, team compliance, cost optimization

```hcl
# In terraform.tfvars
reuse_existing_resources = true

# Then provide existing resource IDs:
existing_s3_bucket_name    = "company-shared-bucket"
existing_vpc_id           = "vpc-0123456789abcdef0"
existing_subnet_ids        = ["subnet-0123456789abcdef0", "subnet-0987654321fedcba0"]
existing_ecs_cluster_name   = "company-ecs-cluster"
```

**What happens:**
- Reuses existing S3 bucket
- Reuses existing VPC
- Reuses existing ECS cluster
- Follows company standards

**Leave empty:** If you don't provide a resource ID, Terraform will create a new one instead. It won't break!

---

## 💰 Cost Control

### Stop Service (Save Money!)

```bash
terraform apply -var='desired_count=0'
```

**Cost savings:** Service goes from ~$15/month to $0 (S3/ECR costs remain)

### Start Service (When Needed)

```bash
terraform apply -var='desired_count=1'
```

**Startup time:** 1-2 minutes (ECS starts new task)

### Task Sizing Options

| CPU | Memory | Monthly Cost (8hrs/day) | Equivalent |
|-----|---------|-------------------------|-------------|
| 256 | 512 | ~$14 | t3.nano (default) |
| 256 | 1024 | ~$18 | t3.micro |
| 512 | 1024 | ~$28 | t3.small |
| 1024 | 2048 | ~$56 | t3.medium |

**Change size:**
```hcl
cpu = 256
memory = 512
```

---

## 🎓 How to Use API

### Get Your API Endpoint

```bash
terraform output api_endpoint
```

**Note:** With ECS Fargate and direct public IP access, you need to get the public IP from AWS Console:
1. Go to **ECS Console** → **Clusters** → **synthdocs-dev**
2. Click **Tasks** tab
3. Find **Public IP** column
4. Access: `http://PUBLIC_IP:8080`

### Generate Documents

```bash
curl -X POST http://PUBLIC_IP:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 5,
    "prompt": "Bank statements for testing"
  }'
```

### View API Documentation

Open in browser:
```
http://PUBLIC_IP:8080/docs
```

---

## 🤝 Bamboo Pipeline Integration

**See `bamboo-instructions.md` for complete Bamboo setup guide.**

### Quick Summary

**Bamboo Stages:**
1. **Build** Docker image from your code
2. **Push** to ECR (Elastic Container Registry)
3. **Deploy** with Terraform (updates ECS task definition)

**Example Bamboo Command:**
```bash
cd infra
terraform apply -var="image_tag=${bamboo.buildNumber}"
```

---

## 🔄 Common Tasks

### Deploy New Version (via Bamboo)

Bamboo will:
1. Build Docker image
2. Tag with build number: `:build-123`
3. Push to ECR
4. Update ECS task definition
5. ECS automatically rolls out new tasks

**Deployment time:** ~30-60 seconds (no downtime!)

### Deploy New Version (manual)

```bash
# Step 1: Build and push Docker image
docker build -t synthdocs:latest .
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com
docker tag synthdocs:latest ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/synthdocs-dev:latest
docker push ACCOUNT.dkr.ecr.eu-west-1.amazonaws.com/synthdocs-dev:latest

# Step 2: Update Terraform
cd infra
terraform apply -var="image_tag=latest"
```

### View Logs

```bash
# Option 1: AWS Console
# Go to CloudWatch → Log Groups → /ecs/synthdocs-dev

# Option 2: AWS CLI
aws logs tail /ecs/synthdocs-dev/synthdocs --follow
```

### Change Task Size

Edit `terraform.tfvars`:
```hcl
cpu = 256
memory = 1024  # More memory
```

Apply:
```bash
terraform apply
```

### Restrict Access to Office IPs

Edit `terraform.tfvars`:
```hcl
allowed_ip_ranges = ["203.0.113.0/24"]  # Your office IP range
```

Apply:
```bash
terraform apply
```

---

## 🗑️ Cleanup

### Stop Service (Keep Resources)

```bash
terraform apply -var='desired_count=0'
```

### Delete Everything

```bash
terraform destroy
```

⚠️ **Warning:** This deletes all resources including ECR repository and S3 bucket!

To keep S3 data:
```bash
aws s3 rm s3://$(terraform output -raw s3_bucket_used) --recursive
terraform destroy
```

---

## 🔍 Troubleshooting

### Issue: ECS task not starting

```bash
# Check ECS service status
aws ecs describe-services \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --services synthdocs

# Check CloudWatch logs
aws logs tail /ecs/synthdocs-dev/synthdocs --follow

# Check security group
aws ec2 describe-security-groups \
  --group-ids $(aws ecs describe-services \
    --cluster $(terraform output -raw ecs_cluster_name) \
    --services synthdocs \
    --query 'services[0].networkConfiguration.securityGroups[0]' \
    --output text)
```

### Issue: "Unable to locate credentials"

```bash
# Configure AWS credentials
aws configure

# Verify connection
aws sts get-caller-identity
```

### Issue: Bedrock Access Denied

```bash
# Go to AWS Console → Bedrock
# Request access to Claude models
# Wait for approval (usually instant)

# No need to restart - new tasks will pick up permission
terraform apply -var='desired_count=0'
terraform apply -var='desired_count=1'
```

### Issue: Docker image not found

```bash
# Check if image exists in ECR
aws ecr describe-images \
  --repository-name synthdocs-dev \
  --region eu-west-1

# If empty, need to push image first
# See bamboo-instructions.md for build/push commands
```

### Issue: Public IP not accessible

```bash
# Check task is running
aws ecs list-tasks \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --service-name synthdocs

# Check security group allows HTTP
aws ec2 describe-security-group-rules \
  --group-id YOUR_SECURITY_GROUP_ID

# Check task has public IP assigned
aws ecs describe-tasks \
  --cluster $(terraform output -raw ecs_cluster_name) \
  --tasks YOUR_TASK_ID \
  --query 'tasks[0].attachments[0].details'
```

---

## 📊 Resource Mode Check

See what resources are being used:

```bash
terraform output resource_mode
```

Output:
- `create_new` = Terraform created everything
- `reuse_existing` = Terraform reused existing resources

---

## 📚 Architecture Overview

```
Bamboo Pipeline
    ↓ (Build Docker image)
    ↓ (Push to ECR)
    ↓
ECS Service (Fargate)
    ↓ (Task Definition)
    ↓ (ECS Task with Public IP)
    ↓
SynthDocs API Container
    ↓ (port 8080)
    ↓
AWS Bedrock + S3 Bucket
```

**Key Components:**
- **ECS Cluster** - Logical grouping for tasks
- **ECS Service** - Manages running tasks (desired_count)
- **ECS Task Definition** - Defines container configuration
- **ECR Repository** - Stores Docker images
- **Security Group** - Controls access to port 8080
- **CloudWatch Logs** - Stores application logs

---

## 💡 Tips

1. **Use build numbers as image tags** for easy rollbacks
2. **Stop service when not in use** to save money
3. **Use specific IP ranges** instead of 0.0.0.0/0 when possible
4. **Commit terraform.tfvars.example** but NOT terraform.tfvars
5. **Check CloudWatch logs** for troubleshooting
6. **Monitor costs** in AWS Cost Explorer

---

## 📁 File Structure

```
infra/
├── provider.tf                  # AWS provider configuration
├── variables.tf                 # All variables with simple reuse options
├── main.tf                      # ECS resources (ECR, cluster, tasks, service)
├── outputs.tf                   # Helpful outputs
├── terraform.tfvars            # Your personal config (DON'T COMMIT)
├── terraform.tfvars.example    # Template for team members
├── .gitignore                  # Ignore sensitive files
├── README.md                   # This file
└── bamboo-instructions.md       # Bamboo pipeline integration guide
```

---

## 🎉 You're Ready!

**Manual Deployment:**
```bash
terraform init
terraform apply
```

**Bamboo Deployment:**
See `bamboo-instructions.md` for complete setup guide.

**Happy deploying! 🚀**
