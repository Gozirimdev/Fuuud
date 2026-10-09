#!/bin/bash
source .env.local

MODELS=(
  "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
  "anthropic.claude-3-5-sonnet-v2:0"
  "claude-3-5-sonnet-20241022-v2:0"
  "us.anthropic.claude-3-5-sonnet-v2:0"
  "anthropic.claude-3-haiku-20240307-v1:0"
  "us.anthropic.claude-3-haiku-20240307-v1:0"
)

echo "Trying different model ID formats..."
echo ""

for MODEL in "${MODELS[@]}"; do
  echo "Model: $MODEL"
  ENDPOINT="https://bedrock-runtime.${AWS_REGION}.amazonaws.com/model/${MODEL}/converse"
  
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $AWS_BEARER_TOKEN_BEDROCK" \
    -d '{"messages":[{"role":"user","content":[{"text":"test"}]}],"inferenceConfig":{"maxTokens":10}}' \
    --max-time 10)
  
  echo "  Status: $RESPONSE"
  
  if [ "$RESPONSE" = "200" ]; then
    echo "  ✓ WORKS!"
    echo ""
    echo "UPDATE YOUR .env.local TO USE:"
    echo "BEDROCK_MODEL_ID=$MODEL"
    exit 0
  fi
done

echo ""
echo "All models failed. Your Bearer token might need model access enabled in AWS Bedrock console."
