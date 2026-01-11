#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Price Monitor${NC}"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS CLI not found. Installing...${NC}"
    pip install awscli
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS SAM CLI not found. Installing...${NC}"
    pip install aws-sam-cli
fi

# Set AWS region
AWS_REGION=${AWS_REGION:-us-east-1}
STACK_NAME="club-med-price-monitor"

echo -e "${GREEN}Step 1: Building SAM application${NC}"
sam build --use-container

echo ""
echo -e "${GREEN}Step 2: Deploying infrastructure${NC}"
sam deploy \
    --guided \
    --stack-name $STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --region $AWS_REGION

echo ""
echo -e "${GREEN}Step 3: Getting stack outputs${NC}"
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' \
    --output text \
    --region $AWS_REGION)

DATA_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`PriceHistoryBucketName`].OutputValue' \
    --output text \
    --region $AWS_REGION)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
    --output text \
    --region $AWS_REGION)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
    --output text \
    --region $AWS_REGION)

echo -e "${BLUE}📦 Frontend Bucket: ${FRONTEND_BUCKET}${NC}"
echo -e "${BLUE}📊 Data Bucket: ${DATA_BUCKET}${NC}"
echo -e "${BLUE}🌐 CloudFront URL: ${CLOUDFRONT_URL}${NC}"

echo ""
echo -e "${GREEN}Step 4: Updating frontend configuration${NC}"
# Update the CSV URL in app.js
sed -i.bak "s|csvUrl: '.*'|csvUrl: 'https://${DATA_BUCKET}.s3.amazonaws.com/price_history.csv'|g" \
    PriceMonitorFrontend/app.js
rm -f PriceMonitorFrontend/app.js.bak

echo ""
echo -e "${GREEN}Step 5: Uploading initial CSV${NC}"
if [ -f "PriceParser/price_history.csv" ]; then
    aws s3 cp PriceParser/price_history.csv \
        s3://${DATA_BUCKET}/price_history.csv \
        --content-type text/csv \
        --cache-control no-cache \
        --region $AWS_REGION
    echo -e "${BLUE}✓ Uploaded price_history.csv${NC}"
fi

echo ""
echo -e "${GREEN}Step 6: Deploying frontend${NC}"
# Upload assets with long cache
aws s3 sync PriceMonitorFrontend/ \
    s3://${FRONTEND_BUCKET}/ \
    --delete \
    --cache-control max-age=31536000 \
    --exclude "*.html" \
    --region $AWS_REGION

# Upload HTML with no cache
aws s3 sync PriceMonitorFrontend/ \
    s3://${FRONTEND_BUCKET}/ \
    --exclude "*" \
    --include "*.html" \
    --cache-control no-cache,no-store,must-revalidate \
    --region $AWS_REGION

echo ""
echo -e "${GREEN}Step 7: Invalidating CloudFront cache${NC}"
aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --region $AWS_REGION

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}🌐 Your website is live at:${NC}"
echo -e "${YELLOW}   ${CLOUDFRONT_URL}${NC}"
echo ""
echo -e "${BLUE}📊 S3 Buckets:${NC}"
echo -e "   Frontend: ${FRONTEND_BUCKET}"
echo -e "   Data: ${DATA_BUCKET}"
echo ""
echo -e "${BLUE}⏰ Price Scraper:${NC}"
echo -e "   Runs daily at 12:00 AM EST"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo -e "   1. Visit your website to see the price chart"
echo -e "   2. (Optional) Set up a custom domain in Route 53"
echo -e "   3. Monitor Lambda logs in CloudWatch"
echo ""
