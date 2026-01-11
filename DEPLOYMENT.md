# 🚀 Club Med Price Monitor - Deployment Guide

A beautiful, serverless price monitoring dashboard that tracks Club Med Quebec Charlevoix prices daily.

## 📸 What You'll Get

- ✨ **Beautiful Dashboard**: Modern, responsive price chart with historical data
- 📊 **Automatic Updates**: Prices scraped daily and saved to S3
- 💰 **Low Cost**: ~$1-2/month on AWS
- 🌐 **Custom Domain**: Optional custom domain support
- ⚡ **Fast**: CloudFront CDN for global performance

## 🏗️ Architecture

```
┌─────────────────┐
│  EventBridge    │ (Daily Trigger)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Lambda         │ (Python + Playwright)
│  Price Scraper  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  S3 Bucket      │ (CSV Storage)
│  price_history  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CloudFront +   │ (Static Website)
│  S3 Bucket      │
└─────────────────┘
```

## 📋 Prerequisites

### Required
- AWS Account ([Create one](https://aws.amazon.com/free/))
- AWS CLI installed ([Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- Python 3.13+ ([Download](https://www.python.org/downloads/))
- AWS SAM CLI ([Install Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))

### Optional (for CI/CD)
- GitHub account
- Git installed

## 🎯 Deployment Options

### Option 1: Quick Deploy (Easiest) ⭐

1. **Configure AWS CLI**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

2. **Run the deployment script**
```bash
cd /path/to/ResortPriceMonitor
./deploy.sh
```

3. **Follow the prompts**
   - Review the changes
   - Confirm deployment
   - Wait 5-10 minutes

4. **Done!** 🎉
   - Your website URL will be displayed
   - Visit it to see your price chart

### Option 2: Manual SAM Deploy

```bash
# 1. Build the application
sam build --use-container

# 2. Deploy (first time)
sam deploy --guided

# 3. Deploy (subsequent times)
sam deploy
```

### Option 3: GitHub Actions CI/CD (Automatic)

1. **Fork/Push this repo to GitHub**

2. **Add AWS credentials to GitHub Secrets**
   
   Go to: Settings → Secrets and variables → Actions
   
   **Option A: Using OIDC (Recommended)**
   - Add secret: `AWS_ROLE_ARN` = `arn:aws:iam::ACCOUNT_ID:role/GitHubActionsRole`
   - [Setup Guide](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
   
   **Option B: Using Access Keys**
   - Add secret: `AWS_ACCESS_KEY_ID`
   - Add secret: `AWS_SECRET_ACCESS_KEY`

3. **Push to main branch**
```bash
git push origin main
```

4. **GitHub Actions will automatically:**
   - Build the Lambda function
   - Deploy infrastructure
   - Upload frontend to S3
   - Configure CloudFront

## 🔧 What Gets Created

### AWS Resources

| Resource | Purpose | Cost |
|----------|---------|------|
| Lambda Function | Scrapes prices daily | FREE (Free tier) |
| EventBridge Rule | Triggers Lambda at midnight | FREE |
| S3 Bucket (Data) | Stores price_history.csv | $0.01/month |
| S3 Bucket (Frontend) | Hosts website files | $0.50/month |
| CloudFront Distribution | CDN for fast delivery | $1/month |
| CloudWatch Logs | Lambda execution logs | FREE |

**Total: ~$1-2/month** 💰

## 🌐 Custom Domain Setup (Optional)

### Using Route 53

1. **Buy domain in Route 53** (or use existing)

2. **Request SSL Certificate**
```bash
aws acm request-certificate \
    --domain-name yourdomain.com \
    --validation-method DNS \
    --region us-east-1
```

3. **Update CloudFront**
   - Add domain as CNAME
   - Attach SSL certificate

4. **Update Route 53**
   - Create A record
   - Point to CloudFront distribution

### Using Cloudflare (Cheaper)

1. **Buy domain on Cloudflare** (~$10/year)

2. **Add CNAME record**
   - Name: `@` or subdomain
   - Target: Your CloudFront domain

3. **Enable SSL** (Flexible or Full)

## 📊 Monitoring

### View Lambda Logs
```bash
sam logs --stack-name club-med-price-monitor --tail
```

### Check S3 Data
```bash
# List files
aws s3 ls s3://club-med-price-history-ACCOUNT_ID/

# Download CSV
aws s3 cp s3://club-med-price-history-ACCOUNT_ID/price_history.csv ./
```

### Manually Trigger Lambda
```bash
aws lambda invoke \
    --function-name ClubMedPriceScraper-prod \
    --payload '{"start_date":"2026-12-13","end_date":"2026-12-19"}' \
    response.json
```

## 🔄 Updating

### Update Lambda Code
```bash
# Make changes to site_price_parser.py
sam build --use-container
sam deploy
```

### Update Frontend
```bash
# Make changes to PriceMonitorFrontend/
aws s3 sync PriceMonitorFrontend/ s3://YOUR-FRONTEND-BUCKET/
aws cloudfront create-invalidation --distribution-id YOUR-DIST-ID --paths "/*"
```

### Or use the deploy script
```bash
./deploy.sh
```

## 🐛 Troubleshooting

### Lambda Timeout
- Increase timeout in `template.yaml` (currently 60s)
- Or split into smaller functions

### Prices Not Showing
1. Check Lambda logs: `sam logs --tail`
2. Check S3 for CSV: `aws s3 ls s3://YOUR-BUCKET/`
3. Check CloudFront cache: Clear cache in AWS Console

### CORS Errors
- Ensure S3 bucket has CORS policy
- Check CloudFront behavior settings

### SSL Certificate Issues (Local Testing)
- SSL bypass is enabled for local testing
- Comment out these lines for production:
```python
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

## 💡 Tips

### Reduce Costs Further
1. Use S3 Intelligent-Tiering for old data
2. Set CloudWatch Logs retention to 7 days
3. Use CloudFront PriceClass_100 (North America + Europe only)

### Improve Performance
1. Enable CloudFront compression
2. Use WebP images for logo
3. Minify JavaScript/CSS

### Add Features
1. Email alerts when price drops
2. Multiple resorts monitoring
3. Historical price comparison
4. Mobile app (React Native)

## 🔐 Security

- Lambda has minimal IAM permissions (S3 read/write only)
- S3 buckets are private (accessed through CloudFront)
- No API keys stored in code
- All traffic over HTTPS

## 🗑️ Cleanup

To delete everything:

```bash
# Delete CloudFormation stack
aws cloudformation delete-stack --stack-name club-med-price-monitor

# Empty S3 buckets first
aws s3 rm s3://YOUR-FRONTEND-BUCKET/ --recursive
aws s3 rm s3://YOUR-DATA-BUCKET/ --recursive

# Delete buckets
aws s3 rb s3://YOUR-FRONTEND-BUCKET
aws s3 rb s3://YOUR-DATA-BUCKET
```

Or use the SAM CLI:
```bash
sam delete --stack-name club-med-price-monitor
```

## 📞 Support

- AWS SAM Issues: [GitHub](https://github.com/aws/aws-sam-cli/issues)
- Playwright Issues: [Docs](https://playwright.dev/python/docs/intro)
- This Project: Open an issue in this repo

## 📄 License

MIT License - Feel free to modify and use!

---

Built with ❤️ using AWS SAM, Python, Chart.js, and Playwright
# Vercel deployment triggered Sat Jan 10 20:01:18 EST 2026
