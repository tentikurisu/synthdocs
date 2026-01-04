#!/bin/bash
# Quick local document generation
# Usage: ./scripts/generate_data.sh --count 10 --prompt "Bank statements"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

COUNT="${COUNT:-40}"
PROMPT="${PROMPT:-A construction company sending customer account letters.}"
OUTPUT_MODE="${OUTPUT_MODE:-local}"
LOCAL_DESTINATION="${LOCAL_DESTINATION:-./artifacts}"
LLM_PROVIDER="${LLM_PROVIDER:-ollama}"
OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://localhost:11434}"

echo "=============================================="
echo "SynthDocs - Local Document Generation"
echo "=============================================="
echo "Count: ${COUNT}"
echo "Prompt: ${PROMPT}"
echo "Output Mode: ${OUTPUT_MODE}"
echo "Output Directory: ${LOCAL_DESTINATION}"
echo "LLM Provider: ${LLM_PROVIDER}"
echo "Ollama URL: ${OLLAMA_BASE_URL}"
echo "=============================================="

if [ -d ".venv" ]; then
    source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate 2>/dev/null || true
fi

export OUTPUT_MODE
export LOCAL_DESTINATION
export LLM_PROVIDER
export OLLAMA_BASE_URL

python -m synthfactory.generate --config config_dev.yaml --count "${COUNT}" --prompt "${PROMPT}"

echo ""
echo "Done! Documents saved to ${LOCAL_DESTINATION}"
