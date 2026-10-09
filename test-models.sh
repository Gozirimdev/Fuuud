#!/bin/bash
source .env.local

MODELS=(
  "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
  "anthropic.claude-3-5-sonnet-20240620-v1:0"
  "us.anthropic.claude-3-5-sonnet-20240620-v1:0"
  "anthropic.claude-3-sonnet-20240229-v1:0"
)

for MODEL in "${MODELS[@]}"; do
  echo "Testing: $MODEL"
  ENDPOINT="https://bedrock-runtime.${AWS_REGION}.amazonaws.com/model/${MODEL}/converse"
  
  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $AWS_BEARER_TOKEN_BEDROCK" \
    -d '{"messages":[{"role":"user","content":[{"text":"Hi"}]}],"inferenceConfig":{"maxTokens":50}}')
  
  STATUS=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | head -n -1)
  
  if [ "$STATUS" = "200" ]; then
    echo "✓ SUCCESS - This model works!"
    echo "Response: $BODY" | head -c 200
    echo ""
    break
  else
    echo "✗ Status $STATUS: $(echo "$BODY" | head -c 100)"
  fi
  echo ""
done
