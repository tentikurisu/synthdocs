# Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker (optional)
- Ollama (optional, for local LLM)
- AWS account (for cloud deployment)

## Installation

```bash
cd synthdocs_synthetic_factory

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Generate Documents (CLI)

```bash
# Generate 10 bank statement documents
python -m synthfactory.generate --count 10 --prompt "Bank statements"

# Generate random documents
python -m synthfactory.generate

# Generate letters with specific theme
python -m synthfactory.generate --count 5 --prompt "Healthcare appointment letters"
```

Output location: `./artifacts/<doc_id>/`

### 2. Run HTTP API

```bash
# Start the API server
./scripts/run_api.sh

# API available at http://localhost:8080

# Generate documents via API
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"count": 10, "prompt": "Bank statements"}'
```

### 3. Docker

```bash
# Build and run
docker-compose up --build

# API at http://localhost:8080
```

## Configuration

### Local Development (Ollama)

Edit `config_dev.yaml`:
```yaml
llm:
  provider: "ollama"
  ollama:
    base_url: "http://localhost:11434"
    model: "qwen2.5:1.5b-instruct"

output:
  mode: "local"
  local:
    destination: "./artifacts"
```

### AWS Deployment (Bedrock)

Edit `config_aws.yaml`:
```yaml
llm:
  provider: "bedrock"
  bedrock:
    region: "us-east-1"
    model_id: "anthropic.claude-3-sonnet-20240307"

output:
  mode: "s3"
  s3:
    bucket: "your-s3-bucket-name"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | "ollama" or "bedrock" | "ollama" |
| `OLLAMA_BASE_URL` | Ollama server URL | "http://localhost:11434" |
| `OUTPUT_MODE` | "local" or "s3" | "local" |
| `LOCAL_DESTINATION` | Local output folder | "./artifacts" |
| `S3_BUCKET` | S3 bucket name | "" |

## Ollama Setup

```bash
# Install Ollama from https://ollama.com

# Pull a model
ollama pull qwen2.5:1.5b-instruct

# Start Ollama server
ollama serve
```

## AWS Deployment

```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Configure AWS credentials
aws configure

# Build and deploy
sam build
sam deploy --guided
```

## Project Structure

```
synthdocs_synthetic_factory/
├── api.py                    # FastAPI HTTP server
├── config.yaml               # Main config
├── config_dev.yaml           # Local dev config
├── config_aws.yaml           # AWS config
├── Dockerfile                # Docker image
├── docker-compose.yml        # Docker Compose
├── requirements.txt          # Dependencies
├── scripts/
│   ├── generate_data.sh      # CLI script
│   └── run_api.sh           # API script
├── synthfactory/
│   ├── pipeline.py          # Document generation
│   ├── llm_client.py        # LLM interface
│   ├── bedrock_client.py    # AWS Bedrock
│   ├── ollama_client.py     # Ollama
│   ├── storage_client.py    # Local/S3 storage
│   └── ...
└── artifacts/               # Generated output
```

## Output Format

Each document generates:

```
artifacts/<doc_id>/
├── <doc_id>.pdf             # PDF document
├── <doc_id>.json            # Ground truth
└── pages/
    └── <doc_id>_p1.jpg      # Scanned image
```

## Troubleshooting

**Ollama not connecting:**
- Ensure Ollama is running: `ollama serve`
- Check base_url in config
- Verify firewall settings

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**AWS errors:**
- Verify AWS credentials: `aws configure list`
- Check IAM permissions for Bedrock and S3

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/generate` | Generate documents |

### POST /generate Request

```json
{
  "count": 40,
  "prompt": "Bank statements",
  "mix": {"statement": 0.5, "letter": 0.5},
  "llm_provider": "ollama",
  "output_mode": "local"
}
```

### POST /generate Response

```json
{
  "job_id": "abc123",
  "status": "completed",
  "documents": [
    {
      "doc_id": "doc_00001",
      "filename": "doc_00001.pdf",
      "local_path": "./artifacts/doc_00001/doc_00001.pdf"
    }
  ]
}
```
