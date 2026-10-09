#!/bin/bash
source .env.local

# Latest Claude models as of 2024-2025
MODELS=(
  "anthropic.claude-3-5-sonnet-20241022-v2:0"
  "anthropic.claude-3-5-sonnet-20240620-v1:0"
  "anthropic.claude-3-opus-20240229-v1:0"
  "anthropic.claude-3-sonnet-20240229-v1:0"
  "anthropic.claude-3-haiku-20240307-v1:0"
)

echo "Checking with verbose error messages..."
for MODEL in "${MODELS[@]}"; do
  echo ""
  echo "=== Testing: $MODEL ==="
  ENDPOINT="https://bedrock-runtime.${AWS_REGION}.amazonaws.com/model/${MODEL}/converse"
  
  curl -s -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $AWS_BEARER_TOKEN_BEDROCK" \
    -d '{"messages":[{"role":"user","content":[{"text":"test"}]}],"inferenceConfig":{"maxTokens":10}}' \
    | python3 -m json.tool 2>/dev/null || echo "(Response not JSON)"
done
