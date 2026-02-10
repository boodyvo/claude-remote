#!/bin/bash

# Coolify One-Command Deployment Script
# Usage: ./deploy.sh

set -e

# Configuration - EDIT THESE VALUES
COOLIFY_WEBHOOK_URL="https://coolify.yourdomain.com/api/v1/deploy/your-uuid-here"
COOLIFY_API_TOKEN="coolify_token_your-token-here"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting deployment to Coolify...${NC}"

# Trigger deployment
response=$(curl -s -w "\n%{http_code}" --request GET "$COOLIFY_WEBHOOK_URL" \
  --header "Authorization: Bearer $COOLIFY_API_TOKEN")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
  echo -e "${GREEN}✅ Deployment triggered successfully!${NC}"
  echo -e "${BLUE}📊 Monitor progress in Coolify dashboard${NC}"
  exit 0
else
  echo -e "${RED}❌ Deployment failed with status code: $http_code${NC}"
  echo "$body"
  exit 1
fi
