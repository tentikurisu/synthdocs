# 🚀 DEPLOYMENT INSTRUCTIONS

## ✅ Files Created Successfully!

All Terraform files are ready in the `terraform/` directory:

```
terraform/
├── provider.tf                  ✅ AWS provider configuration
├── variables.tf                 ✅ All variables (simple & flexible)
├── main.tf                      ✅ AWS resources with hybrid logic
├── outputs.tf                   ✅ Deployment outputs
├── user-data.sh                ✅ EC2 startup script
├── terraform.tfvars.example    ✅ Configuration template
├── .gitignore                  ✅ Ignore sensitive files
└── README.md                   ✅ Complete guide
```

---

## 📋 Your Next Steps (Follow These Exactly)

### Step 1: Configure AWS CLI (One-Time Setup)

```bash
# Install AWS CLI if not already installed
# Download from: https://aws.amazon.com/cli/

# Configure your AWS credentials
aws configure
```

You'll need:
- AWS Access Key ID
- Secret Access Key
- Default region: `eu-west-1`
- Default output format: `json`

**How to get credentials:**
1. Go to AWS Console → IAM → Users
2. Create user with "Programmatic access"
3. Attach policy: `AdministratorAccess` (or ask cloud team)
4. Copy Access Key ID and Secret Access Key

### Step 2: Configure Your Deployment

```bash
cd terraform

# Copy the example configuration
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

### Step 3: Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

### Step 4: Review Your Plan

```bash
terraform plan
```

This shows what Terraform will create without actually creating it.
Look for:
```
Plan: 6 to add, 0 to change, 0 to destroy.
```

### Step 5: Deploy!

```bash
terraform apply
```

When prompted, type: `yes`

Wait 2-3 minutes. You'll see:
```
Apply complete! Resources: 6 added, 0 changed, 0 destroyed.
```

### Step 6: Get Your API URL

```bash
terraform output api_endpoint
```

You'll see something like:
```
http://54.123.45.67:8080
```

Open this in your browser to test!

### Step 7: Test Your API

```bash
# Test health endpoint
curl http://YOUR_IP:8080/health

# Generate test documents
curl -X POST http://YOUR_IP:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 5,
    "prompt": "Bank statements for testing"
  }'
```

---

## 💰 Save Money - Stop When Not in Use

```bash
terraform apply -var='instance_state=stopped'
```

To start again:
```bash
terraform apply -var='instance_state=running'
```

---

## 🤝 Show to Team Member

### Option 1: Share Everything (Best for First Time)

1. Commit and push your code (including `terraform/` directory)
2. Team member clones repo
3. Runs the same steps above
4. Creates their own `terraform.tfvars`

### Option 2: Show Reuse Option (Best for Production)

Edit `terraform.tfvars`:
```hcl
reuse_existing_resources = true
existing_s3_bucket_name = "company-bucket"
existing_vpc_id = "vpc-123456"
existing_subnet_ids = ["subnet-123", "subnet-456"]
existing_security_group_id = "sg-123456"
```

Then run:
```bash
terraform plan
```

This shows your team member how easy it is to reuse existing resources!

---

## 📊 Cost Summary

| Resource | When Running (8hrs/day) | When Stopped |
|----------|-------------------------|--------------|
| EC2 t3.nano | ~$12/month | $0 |
| S3 Storage (10GB) | ~$0.23/month | $0.23/month |
| Bedrock | Variable | $0 |
| **Total** | **~$12-25/month** | **~$0.23/month** |

---

## 🔍 Troubleshooting

### Issue: "Error: InvalidBucketName"

**Cause:** Bucket name is already taken by someone else in AWS.

**Solution:** Choose a more unique name:
```hcl
s3_bucket_name = "synthdocs-YOURNAME-COMPANY-$(date +%Y%m%d)"
```

### Issue: "Error: Provider not installed"

**Cause:** Terraform needs AWS provider plugin.

**Solution:**
```bash
terraform init
```

### Issue: "Error: NoCredentialProviders"

**Cause:** AWS CLI not configured properly.

**Solution:**
```bash
aws configure
# Enter your credentials again
aws sts get-caller-identity  # Test connection
```

### Issue: Instance starts but API not accessible

**Cause:** Takes 2-3 minutes to start up.

**Solution:**
```bash
# Wait a few minutes
sleep 180

# Test again
curl http://$(terraform output -raw api_endpoint)/health
```

---

## 📚 What Each File Does

| File | Purpose |
|------|---------|
| `provider.tf` | Connects Terraform to AWS |
| `variables.tf` | All configuration options you can change |
| `main.tf` | Creates EC2, S3, IAM, security groups, etc. |
| `outputs.tf` | Shows you the API URL and other useful info |
| `user-data.sh` | Script that runs when EC2 instance starts |
| `terraform.tfvars` | YOUR personal configuration (don't commit this!) |
| `terraform.tfvars.example` | Template to show team members |
| `.gitignore` | Keeps sensitive data out of git |

---

## ✅ Deployment Checklist

Before deploying, make sure you:

- [ ] Have AWS Access Key ID and Secret Access Key
- [ ] Have GitHub repository URL ready
- [ ] Have chosen a unique S3 bucket name
- [ ] Have installed Terraform and AWS CLI
- [ ] Have configured AWS CLI with `aws configure`
- [ ] Have edited `terraform.tfvars` with your values
- [ ] Have run `terraform init`
- [ ] Have reviewed `terraform plan` and it looks good

---

## 🎉 You're All Set!

Deploy now in 3 commands:

```bash
terraform init
terraform apply
terraform output api_endpoint
```

**Happy deploying! 🚀**
