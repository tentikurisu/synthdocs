# 🚀 SynthDocs AWS Deployment - Terraform Made Simple

Deploy your SynthDocs API to AWS in **3 minutes** using Terraform.

**Simple by default, flexible when needed.**

---

## ✨ Key Features

- ✅ **One-command deployment** - Just 3 steps to get running
- ✅ **Simple on/off control** - Stop instance to save money
- ✅ **Hybrid flexibility** - Create new OR reuse existing resources
- ✅ **Team-friendly** - Easy to share and modify
- ✅ **Cost-effective** - ~$12-25/month when running 8hrs/day

---

## 📋 Quick Start (3 Minutes!)

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
cd terraform
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

# Deploy!
terraform apply
```

That's it! Your API will be ready in 2-3 minutes.

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
- Creates new security group
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
existing_security_group_id = "sg-0123456789abcdef0"
```

**What happens:**
- Reuses existing S3 bucket
- Reuses existing VPC
- Reuses existing security group
- Follows company standards

**Leave empty:** If you don't provide a resource ID (e.g., `existing_vpc_id = ""`), Terraform will create a new one instead. It won't break!

---

## 💰 Cost Control

### Stop Instance (Save Money!)

```bash
terraform apply -var='instance_state=stopped'
```

**Cost savings:** Instance goes from ~$12/month to $0

### Start Instance (When Needed)

```bash
terraform apply -var='instance_state=running'
```

**Startup time:** 2-3 minutes

---

## 🎓 How to Use API

### Get Your API URL

```bash
terraform output api_endpoint
```

You'll see something like:
```
http://54.123.45.67:8080
```

### Generate Documents

```bash
curl -X POST http://YOUR_IP:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 5,
    "prompt": "Bank statements for testing"
  }'
```

### View API Documentation

Open in browser:
```
http://YOUR_IP:8080/docs
```

---

## 🤝 Sharing with Your Team

### Option 1: Share terraform Directory

1. Add `terraform/` to your GitHub repo (except `terraform.tfvars`)
2. Team member clones repo
3. Creates their own `terraform.tfvars`
4. Runs `terraform apply`

### Option 2: Share Only API URL

```bash
terraform output api_endpoint
```

Team can access: `http://YOUR_IP:8080`

### Show Team Member Different Approaches

```bash
# Show default (create new)
cat terraform.tfvars.example
terraform plan

# Show reuse option (edit file first)
nano terraform.tfvars  # Change reuse_existing_resources = true
terraform plan
```

---

## 🔄 Common Tasks

### Update Your Application

```bash
# Option 1: Restart instance (re-runs startup script)
terraform apply -var='instance_state=stopped'
terraform apply -var='instance_state=running'

# Option 2: Manually update via SSM
aws ssm start-session --target $(terraform output -raw instance_id)
cd /opt/synthdocs
git pull
docker-compose up -d --build
```

### Change Instance Size

Edit `terraform.tfvars`:
```hcl
instance_type = "t3.micro"  # More power
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

### Stop Instance (Keep Resources)

```bash
terraform apply -var='instance_state=stopped'
```

### Delete Everything

```bash
terraform destroy
```

⚠️ **Warning:** This deletes all resources including S3 bucket and documents!

To keep S3 data:
```bash
aws s3 rm s3://$(terraform output -raw s3_bucket_used) --recursive
terraform destroy
```

---

## 🔍 Troubleshooting

### Issue: terraform init fails

```bash
# Check Terraform is installed
terraform --version

# Check internet connection
ping hashicorp.com
```

### Issue: Instance starts but API not accessible

```bash
# Wait 2-3 minutes for startup
sleep 120

# Test health endpoint
curl http://$(terraform output -raw api_endpoint | cut -d: -f1,2):8080/health

# Check instance status
aws ec2 describe-instances --instance-ids $(terraform output -raw instance_id)
```

### Issue: Bedrock Access Denied

```bash
# Go to AWS Console → Bedrock
# Request access to Claude models
# Wait for approval (usually instant)
# Restart instance:
terraform apply -var='instance_state=stopped'
terraform apply -var='instance_state=running'
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

## 💡 Tips

1. **Test with default settings first** (reuse_existing_resources = false)
2. **Stop instance when not in use** to save money
3. **Use specific IP ranges** instead of 0.0.0.0/0 when possible
4. **Commit terraform.tfvars.example** but NOT terraform.tfvars
5. **Check costs** in AWS Cost Explorer

---

## 📊 File Structure

```
terraform/
├── provider.tf                  # AWS provider configuration
├── variables.tf                 # All variables with simple reuse options
├── main.tf                      # Resources with conditional logic
├── outputs.tf                   # Helpful outputs
├── user-data.sh                # EC2 startup script
├── terraform.tfvars            # Your personal config (DON'T COMMIT)
├── terraform.tfvars.example    # Template for team members
├── .gitignore                  # Ignore sensitive files
└── README.md                   # This file
```

---

## 🎉 You're Ready!

Deploy in 3 steps:
1. `terraform init`
2. Edit `terraform.tfvars` (3 required values)
3. `terraform apply`

**Happy deploying! 🚀**
