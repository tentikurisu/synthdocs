#!/bin/bash
set -e

echo "🚀 SynthDocs Deployment Starting..."

# Update system
apt-get update -y

# Install Docker
echo "📦 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
echo "📦 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install git
echo "📦 Installing Git..."
apt-get install -y git

# Clone repository
echo "📥 Cloning repository: ${github_repo}"
cd /opt
git clone ${github_repo} synthdocs
cd synthdocs

# Create .env file
echo "⚙️  Creating environment configuration..."
cat > .env << EOF
OUTPUT_MODE=s3
S3_BUCKET=${s3_bucket}
AWS_REGION=${aws_region}
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=${bedrock_model}
CONFIG_PATH=config_aws.yaml
EOF

# Build and start
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting application..."
docker-compose up -d

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ API is ready!"
    break
  fi
  echo "Attempt $i/30: Not ready yet..."
  sleep 5
done

# Enable Docker on boot
echo "🔄 Enabling Docker on boot..."
systemctl enable docker

echo "✅ Deployment complete!"
echo "📊 API URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
