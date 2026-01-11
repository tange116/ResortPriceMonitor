# 🎯 Quick Setup Guide

## What You Need to Deploy

### AWS Credentials
You need ONE of these options:

#### Option 1: AWS Access Keys (Easiest for first time)
1. Go to AWS Console → IAM → Users → Your User → Security Credentials
2. Create Access Key
3. Run: `aws configure`
4. Enter:
   - Access Key ID
   - Secret Access Key
   - Region: `us-east-1`
   - Output: `json`

#### Option 2: AWS CLI Profile
```bash
aws configure --profile clubmed
export AWS_PROFILE=clubmed
```

#### Option 3: IAM Role (For GitHub Actions)
See [DEPLOYMENT.md](DEPLOYMENT.md) for OIDC setup

---

## 🚀 Deploy in 3 Steps

### Step 1: Install Prerequisites
```bash
# Install AWS CLI
pip install awscli

# Install SAM CLI  
pip install aws-sam-cli

# Verify installations
aws --version
sam --version
```

### Step 2: Configure AWS
```bash
aws configure
# Enter your credentials when prompted
```

### Step 3: Deploy!
```bash
cd /path/to/DestinationPriceMonitor
./deploy.sh
```

That's it! 🎉

---

## 📝 What to Expect

### During Deployment (5-10 minutes)
```
✓ Building SAM application
✓ Deploying infrastructure
  - Creating S3 buckets
  - Creating Lambda function
  - Creating CloudFront distribution
  - Setting up EventBridge schedule
✓ Uploading frontend files
✓ Uploading price history CSV
✓ Invalidating CloudFront cache
```

### After Deployment
You'll see:
```
========================================
✅ Deployment Complete!
========================================

🌐 Your website is live at:
   https://d1234567890abc.cloudfront.net

📊 S3 Buckets:
   Frontend: club-med-frontend-123456789
   Data: club-med-price-history-123456789

⏰ Price Scraper:
   Runs daily at 12:00 AM EST
```

---

## 🔍 Verify It Works

### 1. Check Lambda Function
```bash
# View recent logs
sam logs --stack-name club-med-price-monitor --tail

# Manually trigger to test
aws lambda invoke \
    --function-name ClubMedPriceScraper-prod \
    --payload '{"start_date":"2026-12-13","end_date":"2026-12-19"}' \
    response.json

cat response.json
```

### 2. Check S3 Data
```bash
# List buckets
aws s3 ls | grep club-med

# Check CSV file
aws s3 ls s3://club-med-price-history-ACCOUNT_ID/

# Download and view
aws s3 cp s3://club-med-price-history-ACCOUNT_ID/price_history.csv ./
cat price_history.csv
```

### 3. Visit Your Website
Open the CloudFront URL in your browser. You should see:
- Beautiful dashboard with price chart
- Price history table
- Statistics cards

---

## 🐛 Common Issues

### "Command not found: sam"
```bash
pip install aws-sam-cli
```

### "Unable to locate credentials"
```bash
aws configure
# Enter your AWS credentials
```

### "Stack already exists"
```bash
# Update existing stack
sam deploy
```

### Lambda timeout
```bash
# Edit template.yaml
# Change: Timeout: 60 → Timeout: 120
sam deploy
```

### Website shows "Failed to Load Data"
1. Check if CSV exists in S3
2. Update csvUrl in `PriceMonitorFrontend/app.js`
3. Redeploy frontend:
```bash
aws s3 sync PriceMonitorFrontend/ s3://YOUR-FRONTEND-BUCKET/
```

---

## 💡 Next Steps

### 1. Set Up Auto-Deploy (Optional)
Push to GitHub and enable Actions:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR-REPO-URL
git push -u origin main
```

### 2. Add Custom Domain (Optional)
See [DEPLOYMENT.md](DEPLOYMENT.md) section "Custom Domain Setup"

### 3. Monitor Usage
- CloudWatch → Logs → `/aws/lambda/ClubMedPriceScraper-prod`
- S3 → Metrics (to track costs)
- CloudFront → Monitoring

---

## 💰 Cost Breakdown

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 30 invocations/month | $0 (free tier) |
| S3 Storage | ~1 MB | $0.01/month |
| S3 Requests | ~1,000/month | $0.01/month |
| CloudFront | ~1 GB/month | $0.50/month |
| EventBridge | 30 events/month | $0 (free) |
| CloudWatch Logs | 50 MB/month | $0 (free tier) |
| **TOTAL** | | **~$1-2/month** |

---

## 🎨 Customize

### Change Schedule
Edit `template.yaml`:
```yaml
Schedule: cron(0 5 * * ? *)  # Midnight EST
# Change to: cron(0 17 * * ? *)  # Noon EST
```

### Change Destination/Dates
Edit `site_price_parser.py`:
```python
query_parts = [
    'adults=2',
    'children=2',
    # Update these:
    'start_date=2026-12-13',
    'end_date=2026-12-19'
]
```

### Change Colors/Design
Edit `PriceMonitorFrontend/styles.css`:
```css
:root {
    --primary: #4F46E5;  /* Change to your color */
}
```

---

## 🆘 Need Help?

1. Read [DEPLOYMENT.md](DEPLOYMENT.md) for detailed docs
2. Check AWS CloudWatch Logs
3. Open an issue on GitHub
4. Check AWS SAM [documentation](https://docs.aws.amazon.com/serverless-application-model/)

---

**Happy Deploying! 🚀**
