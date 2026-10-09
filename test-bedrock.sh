#!/bin/bash
# Test Bedrock API directly

# Load env vars
source .env.local 2>/dev/null || true

if [ -z "$AWS_BEARER_TOKEN_BEDROCK" ]; then
  echo "❌ AWS_BEARER_TOKEN_BEDROCK not set"
  exit 1
fi

if [ -z "$AWS_REGION" ]; then
  echo "❌ AWS_REGION not set"
  exit 1
fi

if [ -z "$BEDROCK_MODEL_ID" ]; then
  echo "❌ BEDROCK_MODEL_ID not set"
  exit 1
fi

echo "✓ Token: SET (length: ${#AWS_BEARER_TOKEN_BEDROCK})"
echo "✓ Region: $AWS_REGION"
echo "✓ Model: $BEDROCK_MODEL_ID"
echo ""
echo "Testing Bedrock endpoint..."
echo ""

ENDPOINT="https://bedrock-runtime.${AWS_REGION}.amazonaws.com/model/${BEDROCK_MODEL_ID}/converse"

curl -v -X POST "$ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AWS_BEARER_TOKEN_BEDROCK" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": [{"text": "Hello"}]
      }
    ],
    "inferenceConfig": {
      "maxTokens": 100,
      "temperature": 0.7
    }
  }'
