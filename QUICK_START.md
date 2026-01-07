# 🚀 QUICK START GUIDE - ECS Fargate Deployment

## ✅ What Changed?

- ✅ **Moved from `terraform/` to `infra/`** (Bamboo standard)
- ✅ **Converted from EC2 to ECS Fargate** (serverless containers)
- ✅ **Added ECR repository** (for Bamboo to push Docker images)
- ✅ **Added Bamboo integration guide** (bamboo-instructions.md)
- ✅ **Simplified on/off control** (`desired_count` instead of `instance_state`)

**Backup:** Old EC2 Terraform is in `terraform-ec2-backup/`

---

## 📋 Your 5-Minute Deployment

### Step 1: Configure AWS CLI

```bash
# Install AWS CLI if not already installed
# Download from: https://aws.amazon.com/cli/

# Configure credentials
aws configure
# Enter: Access Key, Secret Key, Region: eu-west-1, Format: json
```

### Step 2: Configure Terraform

```bash
cd infra

# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with YOUR values
nano terraform.tfvars  # or use any text editor
```

**YOU MUST CHANGE THESE 3 VALUES:**
```hcl
github_repo = "https://github.com/YOUR_USERNAME/YOUR_REPO.git"
s3_bucket_name = "synthdocs-YOURNAME-documents"  # Make unique!
environment = "dev"
```

**Optional but recommended:**
```hcl
allowed_ip_ranges = ["YOUR_OFFICE_IP/24"]  # More secure than 0.0.0.0/0
```

### Step 3: Deploy Infrastructure

```bash
cd infra

# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Apply (create resources)
terraform apply
```

**Expected output:**
```
Plan: 8 to add, 0 to change, 0 to destroy.
Apply complete! Resources: 8 added, 0 changed, 0 destroyed.
```

### Step 4: Build & Push Docker Image (One-time)

```bash
# Build Docker image
cd ..
docker build -t synthdocs:latest .

# Login to ECR (replace ACCOUNT_ID with your AWS account ID)
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com

# Tag image for ECR
docker tag synthdocs:latest YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/synthdocs-dev:latest

# Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.eu-west-1.amazonaws.com/synthdocs-dev:latest
```

### Step 5: Deploy to ECS

```bash
cd infra

# Deploy with latest image
terraform apply -var="image_tag=latest"
```

### Step 6: Get API Endpoint

```bash
# Get ECR repository URL
terraform output ecr_repository_url

# Get ECS cluster name
terraform output ecs_cluster_name

# Get S3 bucket name
terraform output s3_bucket_used
```

**To get public IP:**
1. Go to **AWS Console** → **ECS**
2. Click **Clusters** → **synthdocs-dev**
3. Click **Tasks** tab
4. Find **Public IP** column
5. Access: `http://PUBLIC_IP:8080`

### Step 7: Test Your API

```bash
# Test health endpoint (replace PUBLIC_IP with actual IP)
curl http://PUBLIC_IP:8080/health

# Generate test documents
curl -X POST http://PUBLIC_IP:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 5,
    "prompt": "Bank statements for testing"
  }'
```

---

## 💰 Save Money - Stop When Not in Use

```bash
cd infra
terraform apply -var='desired_count=0'
```

To start again:
```bash
terraform apply -var='desired_count=1'
```

---

## 🤝 Next: Configure Bamboo

**Follow `bamboo-instructions.md` for complete Bamboo pipeline setup.**

### Quick Summary:

**Bamboo Environment Variables Needed:**
```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=eu-west-1
AWS_ACCOUNT_ID=123456789012
```

**Bamboo Stages:**
1. **Build:** `docker build -t synthdocs:build-${bamboo.buildNumber} .`
2. **Push:** `docker push ecr-repo:build-${bamboo.buildNumber}`
3. **Deploy:** `terraform apply -var="image_tag=build-${bamboo.buildNumber}"`

---

## 📊 Cost Summary

| Resource | Monthly Cost |
|----------|-------------|
| ECS Fargate (0.25 vCPU, 0.5 GB) | ~$14/month |
| ECR Storage (10GB) | ~$0.10/month |
| CloudWatch Logs | ~$0.50/month |
| S3 Storage (10GB) | ~$0.23/month |
| **Total** | **~$15/month** |

**Stop to save money:** `terraform apply -var='desired_count=0'`

---

## 🔍 Troubleshooting

### Issue: terraform apply fails with "InvalidBucketName"

**Cause:** Bucket name is already taken by someone else in AWS.

**Solution:** Choose a more unique name:
```hcl
s3_bucket_name = "synthdocs-YOURNAME-COMPANY-20250107"
```

### Issue: "Error: Unable to locate credentials"

**Cause:** AWS CLI not configured properly.

**Solution:**
```bash
aws configure
# Enter your credentials again
aws sts get-caller-identity  # Test connection
```

### Issue: ECS tasks not starting

**Cause:** Docker image not pushed to ECR or incorrect tag.

**Solution:**
```bash
# Check ECR repository has images
aws ecr describe-images --repository-name synthdocs-dev --region eu-west-1

# If empty, rebuild and push
# Follow Step 4 above
```

### Issue: API not accessible

**Cause:** Takes 1-2 minutes to start up, or security group blocking.

**Solution:**
```bash
# Wait a few minutes
sleep 120

# Check ECS tasks are running
aws ecs list-tasks --cluster synthdocs-dev --service-name synthdocs

# Check security group allows port 8080
aws ec2 describe-security-groups --group-ids $(aws ecs describe-services --cluster synthdocs-dev --services synthdocs --query 'services[0].networkConfiguration.securityGroups[0]' --output text)
```

---

## ✅ Deployment Checklist

Before deploying, make sure you:

- [ ] Have AWS Access Key ID and Secret Access Key
- [ ] Have configured AWS CLI with `aws configure`
- [ ] Have Terraform installed
- [ ] Have edited `infra/terraform.tfvars` with your values
- [ ] Have run `terraform init`
- [ ] Have reviewed `terraform plan` and it looks good
- [ ] Have Docker installed locally
- [ ] Have built and pushed Docker image to ECR

---

## 📚 Documentation

- **`infra/README.md`** - Complete ECS deployment guide
- **`infra/bamboo-instructions.md`** - Bamboo pipeline setup guide
- **`infra/terraform.tfvars.example`** - Example configuration

---

## 🎯 Key Files

| File | Purpose |
|------|---------|
| `infra/provider.tf` | AWS provider configuration |
| `infra/variables.tf` | All variables (12 total) |
| `infra/main.tf` | ECS resources (355 lines) |
| `infra/outputs.tf` | Deployment outputs |
| `infra/terraform.tfvars` | Your personal config (DON'T COMMIT) |
| `infra/.gitignore` | Ignore sensitive files |
| `infra/README.md` | ECS guide (439 lines) |
| `infra/bamboo-instructions.md` | Bamboo integration (569 lines) |

**Total: 1,577 lines of Terraform + documentation**

---

## 🎉 You're Ready!

**Manual Deployment:**
```bash
cd infra
terraform init
terraform apply
```

**Bamboo Deployment:**
Follow `bamboo-instructions.md` to set up your pipeline.

**Stop to Save Money:**
```bash
terraform apply -var='desired_count=0'
```

**Happy deploying! 🚀**
