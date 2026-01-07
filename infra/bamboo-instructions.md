# 🎋 Bamboo Pipeline Integration Guide

This guide shows you how to configure Bamboo to deploy the SynthDocs API to AWS ECS Fargate.

---

## 📋 Overview

**Bamboo Pipeline Stages:**

```
┌─────────────────────────────────────────────────┐
│  Stage 1: Build Docker Image                │
│  - Clone repository                           │
│  - Build Docker image                        │
└──────────────┬────────────────────────────────┘
               │
┌──────────────▼────────────────────────────────┐
│  Stage 2: Push to ECR                     │
│  - Login to ECR                             │
│  - Tag image with build number                │
│  - Push image to ECR                        │
└──────────────┬────────────────────────────────┘
               │
┌──────────────▼────────────────────────────────┐
│  Stage 3: Deploy with Terraform          │
│  - Update image tag                        │
│  - Apply Terraform                        │
│  - ECS automatically rolls out new tasks   │
└───────────────────────────────────────────────┘
```

---

## 🎯 Prerequisites

### 1. Bamboo Environment Variables

Configure these in Bamboo (Bamboo Admin → Variables):

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | IAM user access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION` | AWS region | `eu-west-1` |
| `AWS_ACCOUNT_ID` | Your AWS account ID (12-digit number) | `123456789012` |

**How to get credentials:**
1. Go to AWS Console → IAM → Users
2. Create user with "Programmatic access"
3. Attach policy: `AdministratorAccess` (or custom policy for ECS/ECR/Bedrock/S3)
4. Copy Access Key ID, Secret Access Key, and Account ID

### 2. IAM Permissions Needed

Your Bamboo IAM user needs permissions to:
- **ECS:** Create/update/delete clusters, services, tasks
- **ECR:** Push/pull images
- **S3:** Create buckets, put/get objects
- **Bedrock:** Invoke models
- **VPC:** Describe network resources
- **IAM:** Create roles/policies

**Simplest approach:** Attach `AdministratorAccess` (for development)
**Production:** Create custom IAM policy with least privilege

---

## 🚀 Bamboo Pipeline Configuration

### Option A: Using Bamboo UI (Recommended)

#### Step 1: Create Project

1. Go to **Bamboo** → **Create** → **New Project**
2. Name: `SynthDocs`
3. Create plan from linked repository or add repository manually

#### Step 2: Configure Stages and Jobs

**Stage 1: Build Docker Image**

- Job name: `Build`
- Add task: **Script**
- Working directory: (root of repo)

**Script Content:**
```bash
# Set image tag
IMAGE_TAG="build-${bamboo.buildNumber}"
echo "Building Docker image: synthdocs:${IMAGE_TAG}"

# Build Docker image
docker build -t synthdocs:${IMAGE_TAG} .
```

**Optional: Add tests**
```bash
# Run tests (if you have them)
docker run --rm synthdocs:${IMAGE_TAG} python -m pytest tests/
```

---

**Stage 2: Push to ECR**

- Job name: `Push`
- Add task: **Script**
- Configure final task to run only if **Stage 1: Build** was successful

**Script Content:**
```bash
# Set variables
IMAGE_TAG="build-${bamboo.buildNumber}"
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/synthdocs-dev"
IMAGE_NAME="${ECR_REPO}:${IMAGE_TAG}"

echo "Pushing image: ${IMAGE_NAME}"

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Tag image
docker tag synthdocs:${IMAGE_TAG} ${IMAGE_NAME}

# Push to ECR
docker push ${IMAGE_NAME}

echo "✅ Image pushed to ECR: ${IMAGE_NAME}"
```

---

**Stage 3: Deploy with Terraform**

- Job name: `Deploy`
- Add task: **Script**
- Working directory: `infra`
- Configure final task to run only if **Stage 2: Push** was successful

**Script Content:**
```bash
# Set variables
IMAGE_TAG="build-${bamboo.buildNumber}"

echo "Deploying with Terraform..."
echo "Image tag: ${IMAGE_TAG}"

# Initialize Terraform (only needs to run once per Bamboo agent)
terraform init

# Apply Terraform with image tag
terraform apply \
  -var="image_tag=${IMAGE_TAG}" \
  -auto-approve

echo "✅ Deployment complete!"

# Show outputs
terraform output api_endpoint
terraform output ecr_repository_url
terraform output ecs_cluster_name
```

**Stage Dependencies:**
- Stage 2 depends on Stage 1
- Stage 3 depends on Stage 2

---

### Option B: Using bamboo-specs.yaml (Declarative)

Create `bamboo-specs.yaml` at root of your project:

```yaml
version: 2

plan:
  project-key: SYN
  name: SynthDocs Deployment
  stages:
    - Build Docker Image
    - Push to ECR
    - Deploy to ECS

Build Docker Image:
  jobs:
    - name: Build
      tasks:
        - type: script
          script: |
            #!/bin/bash
            set -e

            IMAGE_TAG="build-${bamboo.buildNumber}"
            echo "Building Docker image: synthdocs:${IMAGE_TAG}"

            docker build -t synthdocs:${IMAGE_TAG} .

Push to ECR:
  depends_on: Build Docker Image
  jobs:
    - name: Push
      tasks:
        - type: script
          script: |
            #!/bin/bash
            set -e

            IMAGE_TAG="build-${bamboo.buildNumber}"
            ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/synthdocs-dev"
            IMAGE_NAME="${ECR_REPO}:${IMAGE_TAG}"

            echo "Pushing image: ${IMAGE_NAME}"

            aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
            docker tag synthdocs:${IMAGE_TAG} ${IMAGE_NAME}
            docker push ${IMAGE_NAME}

            echo "✅ Image pushed to ECR: ${IMAGE_NAME}"

Deploy to ECS:
  depends_on: Push to ECR
  jobs:
    - name: Deploy
      working-directory: infra
      tasks:
        - type: script
          script: |
            #!/bin/bash
            set -e

            IMAGE_TAG="build-${bamboo.buildNumber}"
            echo "Deploying with Terraform..."
            echo "Image tag: ${IMAGE_TAG}"

            terraform init
            terraform apply \
              -var="image_tag=${IMAGE_TAG}" \
              -auto-approve

            echo "✅ Deployment complete!"
            terraform output api_endpoint
```

**Enable Bamboo Specs:**
1. Go to **Bamboo Admin** → **Settings**
2. Enable **Bamboo Specs**
3. Configure repository detection
4. Bamboo will automatically read `bamboo-specs.yaml`

---

## 🔄 How Deployment Works

### What Bamboo Does

1. **Build Stage:**
   - Clones your repository
   - Builds Docker image from `Dockerfile`
   - Tags image with build number: `synthdocs:build-123`

2. **Push Stage:**
   - Logs in to ECR
   - Tags image for ECR: `123456789012.dkr.ecr.eu-west-1.amazonaws.com/synthdocs-dev:build-123`
   - Pushes image to ECR repository

3. **Deploy Stage:**
   - Runs `terraform apply` with `image_tag=build-123`
   - Terraform updates ECS task definition with new image
   - ECS automatically creates new tasks with new image
   - Old tasks are gracefully stopped (no downtime)

### Deployment Flow Diagram

```
Bamboo Trigger (push to main)
    ↓
┌───────────────────────────────────┐
│  Stage 1: Build Docker Image    │
│  docker build -t :build-123   │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│  Stage 2: Push to ECR          │
│  docker push ecr-repo:build-123 │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│  Stage 3: Deploy with Terraform │
│  terraform apply                │
│  -var=image_tag=build-123       │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│  ECS Updates Task Definition     │
│  Creates new tasks              │
│  Stops old tasks                │
└───────────────────────────────────┘
```

---

## 🎯 Initial Setup (First Deployment)

### Step 1: Deploy Infrastructure Once

Before configuring Bamboo, deploy infrastructure manually:

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
nano terraform.tfvars

terraform init
terraform plan
terraform apply
```

This creates:
- ECS cluster
- ECR repository
- IAM roles
- Security groups
- S3 bucket
- CloudWatch log groups

### Step 2: Configure Bamboo

Follow the steps above (Option A or Option B) to set up Bamboo pipeline.

### Step 3: Test First Bamboo Deployment

1. Push to your repository (triggers Bamboo)
2. Monitor Bamboo build:
   - Stage 1: Build (1-2 minutes)
   - Stage 2: Push (1-2 minutes)
   - Stage 3: Deploy (1-2 minutes)
3. Check ECS Console for new tasks
4. Get public IP from ECS Console
5. Test API endpoint

---

## 💰 Cost Optimization

### Option 1: Stop When Not in Use

Add a Bamboo job to stop the service:

**New Job: Stop Service**
```bash
cd infra
terraform apply -var='desired_count=0' -auto-approve
echo "✅ Service stopped (saving money!)"
```

**New Job: Start Service**
```bash
cd infra
terraform apply -var='desired_count=1' -auto-approve
echo "✅ Service started!"
```

### Option 2: Use Bamboo Triggers

Configure Bamboo to:
- Trigger deployment on push to `main` branch
- Stop service after 8 hours of inactivity (custom script)
- Start service when next build triggers

---

## 🔍 Troubleshooting

### Issue: Bamboo can't connect to AWS

**Error:** `Unable to locate credentials`

**Solution:**
```bash
# Verify Bamboo variables are set
# Bamboo Admin → Variables → Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

# Test connection in Bamboo job
aws sts get-caller-identity
```

### Issue: Docker build fails

**Error:** `Build failed`

**Solution:**
- Check `Dockerfile` exists in repository
- Check Bamboo agent has Docker installed
- Add debug task to Bamboo job:
  ```bash
  docker --version
  ls -la
  pwd
  cat Dockerfile
  ```

### Issue: ECR login fails

**Error:** `Error logging in to your Amazon ECR registry`

**Solution:**
```bash
# Check AWS_ACCOUNT_ID variable in Bamboo
# Should be 12-digit number (no hyphens)

# Test ECR login in Bamboo job
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

### Issue: Terraform apply fails

**Error:** `Error: Failed to initialize Terraform`

**Solution:**
```bash
# Add terraform init to every Deploy job
# Or ensure working directory is correct

# Test in Bamboo job:
cd infra
terraform --version
terraform init
terraform plan
```

### Issue: ECS task not starting

**Error:** Service running but tasks unhealthy

**Solution:**
```bash
# Check CloudWatch logs
aws logs tail /ecs/synthdocs-dev/synthdocs --follow

# Check ECS task status
aws ecs describe-tasks --cluster synthdocs-dev --tasks TASK_ID

# Stop and start service
terraform apply -var='desired_count=0'
terraform apply -var='desired_count=1'
```

### Issue: Image tag not found

**Error:** `image not found in ECR`

**Solution:**
```bash
# Check image exists in ECR
aws ecr describe-images --repository-name synthdocs-dev

# If image list is empty, check Push stage succeeded
# Verify AWS_ACCOUNT_ID is correct in Bamboo variables
```

---

## 📊 Bamboo Job Artifacts (Optional)

### Save Build Information

Add artifact collection to Stage 1 (Build):

```bash
# Save build info
echo "Build Number: ${bamboo.buildNumber}" > build-info.txt
echo "Image Tag: build-${bamboo.buildNumber}" >> build-info.txt
echo "Timestamp: $(date)" >> build-info.txt
```

**Bamboo Artifact Configuration:**
- Artifact name: `build-info`
- Copy pattern: `build-info.txt`

This lets you download build information from Bamboo UI.

---

## 🚀 Advanced Bamboo Features

### 1. Manual Deployment Trigger

Add a Bamboo job that triggers only manually:

**Job: Deploy with Custom Tag**
```bash
# Get custom tag from Bamboo variable
IMAGE_TAG="${bamboo.CUSTOM_IMAGE_TAG:-latest}"

cd infra
terraform apply -var="image_tag=${IMAGE_TAG}" -auto-approve
```

**Configure Bamboo:**
- Add job to existing Deploy stage
- Set as **manual trigger**
- Add variable `CUSTOM_IMAGE_TAG` (optional)

### 2. Rollback to Previous Version

**Job: Rollback**
```bash
# Rollback to build-120
cd infra
terraform apply -var="image_tag=build-120" -auto-approve
```

### 3. Multiple Environments

Create separate Bamboo plans:
- `SynthDocs - Dev`
- `SynthDocs - Test`
- `SynthDocs - Prod`

Each plan uses different `environment` variable in `terraform.tfvars`:
- Dev: `environment = "dev"`
- Test: `environment = "test"`
- Prod: `environment = "prod"`

### 4. Deploy Notifications

Configure Bamboo notifications:
- **Email:** Send on deployment success/failure
- **Slack:** Send to #deployments channel
- **Teams:** Send to deployment group

---

## ✅ Checklist

Before first Bamboo deployment:

- [ ] AWS credentials configured in Bamboo variables
- [ ] ECR repository created (via Terraform)
- [ ] ECS infrastructure deployed (via Terraform)
- [ ] Bedrock access enabled in AWS account
- [ ] Bamboo agents have Docker installed
- [ ] Bamboo agents have Terraform installed
- [ ] Bamboo agents have AWS CLI installed
- [ ] `terraform.tfvars` configured with correct values
- [ ] Repository cloned in Bamboo

---

## 📚 Additional Resources

- **Bamboo Documentation:** https://docs.atlassian.com/bamboo
- **ECS Documentation:** https://docs.aws.amazon.com/ecs/
- **Terraform AWS Provider:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs

---

## 🎉 Success!

Your Bamboo pipeline is now configured to:
1. Build Docker images automatically
2. Push to ECR with version tags
3. Deploy to ECS Fargate with Terraform
4. Roll out updates with zero downtime

**Happy deploying! 🚀**
