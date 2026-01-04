#!/bin/bash
# Start the HTTP API locally
# Usage: ./scripts/run_api.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

OUTPUT_MODE="${OUTPUT_MODE:-local}"
LOCAL_DESTINATION="${LOCAL_DESTINATION:-./artifacts}"
LLM_PROVIDER="${LLM_PROVIDER:-ollama}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"
AWS_REGION="${AWS_REGION:-eu-west-1}"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8080}"

echo "=============================================="
echo "SynthDocs API - Local Development Server"
echo "=============================================="
echo "Output Mode: ${OUTPUT_MODE}"
echo "LLM Provider: ${LLM_PROVIDER}"
echo "API Host: ${API_HOST}"
echo "API Port: ${API_PORT}"
echo "=============================================="

export OUTPUT_MODE
export LOCAL_DESTINATION
export LLM_PROVIDER
export OLLAMA_BASE_URL
export AWS_REGION

echo "Starting SynthDocs API..."
echo "API available at http://${API_HOST}:${API_PORT}"
echo ""
echo "Endpoints:"
echo "  - GET  /health         - Health check"
echo "  - POST /generate       - Generate documents"
echo "  - GET  /               - API info"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn api:app --host "${API_HOST}" --port "${API_PORT}" --reload
