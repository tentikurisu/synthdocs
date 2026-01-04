# SynthDocs Synthetic Factory

Generate synthetic PDF/JPG documents with ground truth JSON for testing OCR and data extraction systems.

## Features

- Generate bank statements and letters with realistic data
- Apply realistic noise to simulate scanned documents
- Support for local Ollama or AWS Bedrock LLMs
- Store outputs locally or upload to S3
- HTTP API for programmatic access
- Docker support for local and cloud deployment
- GitHub Actions CI/CD for AWS deployment

## Requirements

- Python 3.11+
- Docker (optional, for containerized deployment)
- AWS account (for cloud deployment)

## Quick Start

### Local Development

```bash
# Clone and enter directory
cd synthdocs_synthetic_factory

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate documents using the script
./scripts/generate_data.sh --count 10 --prompt "Bank statements"

# Or run the API locally
./scripts/run_api.sh
```

### Docker

```bash
# Build and run API
docker-compose up --build

# API available at http://localhost:8080
curl http://localhost:8080/health
```

### Generate Documents via API

```bash
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "count": 10,
    "prompt": "Bank statements",
    "mix": {"statement": 0.5, "letter": 0.5}
  }'
```

## Configuration

### Config Files

| File | Use Case |
|------|----------|
| `config.yaml` | Original config (backward compatible) |
| `config_dev.yaml` | Local development with Ollama |
| `config_aws.yaml` | AWS deployment with Bedrock |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONFIG_PATH` | Path to config file | `config.yaml` |
| `OUTPUT_MODE` | "local" or "s3" | "local" |
| `LOCAL_DESTINATION` | Local output folder | "./artifacts" |
| `S3_BUCKET` | S3 bucket name | "" |
| `LLM_PROVIDER` | "ollama" or "bedrock" | "ollama" |
| `OLLAMA_BASE_URL` | Ollama endpoint | "http://localhost:11434" |
| `BEDROCK_MODEL_ID` | Bedrock model ID | "anthropic.claude-3-sonnet-20240307" |
| `AWS_REGION` | AWS region | "us-east-1" |
| `API_HOST` | API listen host | "0.0.0.0" |
| `API_PORT` | API listen port | "8080" |

### LLM Configuration

#### Local Ollama

1. Install [Ollama](https://ollama.com/)
2. Pull a model:
   ```bash
   ollama pull qwen2.5:1.5b-instruct
   ```
3. Start Ollama:
   ```bash
   ollama serve
   ```
4. Configure in `config_dev.yaml`:
   ```yaml
   llm:
     provider: "ollama"
     ollama:
       base_url: "http://localhost:11434"
       model: "qwen2.5:1.5b-instruct"
   ```

#### AWS Bedrock

1. Enable Bedrock in your AWS account
2. Configure IAM permissions
3. Update `config_aws.yaml`:
   ```yaml
   llm:
     provider: "bedrock"
     bedrock:
       region: "us-east-1"
       model_id: "anthropic.claude-3-sonnet-20240307"
       temperature: 0.7
   ```

## API Reference

### Endpoints

#### GET /

API information.

**Response:**
```json
{
  "name": "SynthDocs Synthetic Factory",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "generate": "/generate"
  }
}
```

#### GET /health

Health check.

**Response:**
```json
{
  "status": "healthy"
}
```

#### POST /generate

Generate documents.

**Request Body:**
```json
{
  "count": 40,
  "prompt": "A construction company...",
  "mix": {
    "statement": 0.4,
    "letter": 0.6
  },
  "llm_provider": "ollama",
  "output_mode": "local",
  "local_destination": "./output",
  "s3_bucket": "my-bucket"
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "documents": [
    {
      "doc_id": "doc_00001",
      "filename": "doc_00001.pdf",
      "local_path": "./output/doc_00001/doc_00001.pdf"
    }
  ]
}
```

## Output Structure

```
artifacts/<doc_id>/
  <doc_id>.pdf
  pages/
    <doc_id>_p1.jpg ...
    <doc_id>.jpg   (letters)
  <doc_id>.json    (ground truth + per-field visibility flags)
```

### Ground Truth JSON

```json
{
  "doc_type": "statement",
  "doc_id": "doc_00001_1234",
  "fields": {
    "industry": {"value": "banking", "visible": true},
    "company_name": {"value": "Harbourlight Ltd (Synthetic)", "visible": true},
    "owner_full_name": {"value": "John Smith", "visible": true},
    "owner_address_lines": {"value": "123 Main St", "visible": true},
    "account_number": {"value": "12345678", "visible": true}
  },
  "meta": {
    "prompt": "Bank statements",
    "pdf": "doc_00001_1234.pdf",
    "jpg_pages": ["doc_00001_1234_p1.jpg"],
    "theme": {
      "accent_rgb": [255, 0, 0],
      "logo_style": "nb_bars"
    }
  }
}
```

## AWS Deployment

### Prerequisites

- AWS CLI configured
- SAM CLI installed
- Docker running

### First Deployment

```bash
# Configure AWS credentials
aws configure

# Build and deploy
sam build
sam deploy --guided
```

### Required Secrets (GitHub Actions)

Add these to your GitHub repository secrets:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user programmatic access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `S3_BUCKET_NAME` | S3 bucket for documents |

### Deployment Process

1. Push to `main` branch
2. GitHub Actions builds Docker image
3. Pushes image to Amazon ECR
4. SAM deploys to ECS Fargate

## Project Structure

```
synthdocs_synthetic_factory/
├── api.py                    # FastAPI HTTP server
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Local Docker orchestration
├── config.yaml               # Original config (backward compatible)
├── config_dev.yaml           # Local development config
├── config_aws.yaml           # AWS deployment config
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
├── .dockerignore            # Docker ignore rules
├── .github/
│   └── workflows/
│       └── deploy.yml       # GitHub Actions CI/CD
├── aws/
│   └── template.yaml        # AWS SAM template
├── scripts/
│   ├── generate_data.sh     # CLI document generation
│   └── run_api.sh          # Start API server
├── synthfactory/            # Main package
│   ├── config.py           # Configuration models
│   ├── pipeline.py         # Document generation pipeline
│   ├── llm_client.py       # LLM interface
│   ├── llm_factory.py      # LLM client factory
│   ├── ollama_client.py    # Ollama implementation
│   ├── bedrock_client.py   # AWS Bedrock implementation
│   ├── storage_client.py   # Local/S3 storage
│   ├── scenario_factory.py # Document scenario generation
│   ├── template_designer.py # Template selection
│   ├── faker_gen.py        # Content generation
│   ├── branding.py         # Visual theming
│   ├── render_pdf.py       # PDF rendering
│   ├── render_jpg.py       # JPG rendering
│   ├── noise.py            # Image degradation
│   └── models.py           # Data models
└── artifacts/               # Generated documents
```

## License

MIT
