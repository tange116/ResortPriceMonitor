# 📦 Complete Solution Package

## ✅ What Has Been Created

### 🎨 Frontend (PriceMonitorFrontend/)
- **index.html** - Beautiful responsive dashboard with Chart.js
- **styles.css** - Modern CSS with animations and responsive design
- **app.js** - Fetches CSV from S3 and renders interactive charts
- **test-local.html** - For local testing without S3

**Features:**
- 📊 Interactive price chart with zoom/pan
- 📈 Price statistics and trends
- 📋 Detailed data table with filtering
- 💾 CSV export functionality
- 📱 Fully responsive (mobile/tablet/desktop)
- ⚡ Fast loading with caching

### 🔧 Backend (PriceParser/)
- **site_price_parser.py** - AWS Lambda function with Playwright
- **requirements.txt** - Python dependencies
- **price_history.csv** - Historical price data (23 records)

**Features:**
- 🌐 Web scraping with Playwright (no Selenium)
- 💾 Saves to S3 automatically
- 📅 Deduplicates by date
- 🕐 Eastern timezone support
- ✅ Works in AWS Lambda
- 🔄 Fallback to local file storage

### ☁️ Infrastructure (AWS SAM)
- **template.yaml** - Complete infrastructure as code
- **samconfig.toml** - SAM CLI configuration
- **deploy.sh** - One-command deployment script

**Resources Created:**
- Lambda Function (price scraper)
- EventBridge Rule (daily trigger at midnight EST)
- S3 Bucket (CSV storage)
- S3 Bucket (frontend hosting)
- CloudFront Distribution (CDN)
- IAM Roles & Policies
- CloudWatch Log Groups

### 🚀 CI/CD (.github/workflows/)
- **deploy.yml** - GitHub Actions workflow
  - Builds Lambda
  - Deploys infrastructure
  - Uploads frontend
  - Invalidates CloudFront cache

### 📚 Documentation
- **README.md** - Project overview
- **DEPLOYMENT.md** - Complete deployment guide
- **SETUP.md** - Quick setup guide
- **PriceParser/README.md** - Scraper documentation
- **.gitignore** - Git ignore rules

---

## 🎯 AWS Credentials Needed

You need ONE of these:

### Option 1: Access Keys (Simplest)
```bash
aws configure
# Enter when prompted:
AWS Access Key ID: AKIA...
AWS Secret Access Key: ...
Default region: us-east-1
Default output: json
```

**How to get:**
1. AWS Console → IAM → Users → Your User
2. Security Credentials tab
3. Create Access Key → CLI

### Option 2: IAM Role (GitHub Actions)
```bash
# Add to GitHub Secrets:
AWS_ROLE_ARN=arn:aws:iam::123456789:role/GitHubActionsRole
```

**How to set up:**
1. Create IAM Role with trust policy for GitHub
2. Attach permissions: CloudFormation, S3, Lambda, CloudFront
3. Add ARN to GitHub Secrets

---

## 🚀 How to Deploy

### Quick Deploy (Recommended)
```bash
cd DestinationPriceMonitor
./deploy.sh
```

### Manual Deploy
```bash
sam build --use-container
sam deploy --guided
```

### Auto Deploy (GitHub Actions)
```bash
git push origin main
# GitHub Actions will automatically deploy
```

---

## 💰 Cost Breakdown

| Service | Monthly Cost |
|---------|--------------|
| Lambda (30 runs) | $0 (free tier) |
| S3 Storage (~1 MB) | $0.01 |
| S3 Requests | $0.01 |
| CloudFront (1 GB) | $0.50 |
| EventBridge | $0 (free) |
| CloudWatch Logs | $0 (free tier) |
| **TOTAL** | **~$1-2/month** |

---

## 📋 Deployment Checklist

### Before Deploying
- [ ] AWS CLI installed: `aws --version`
- [ ] SAM CLI installed: `sam --version`
- [ ] Python 3.13+ installed: `python --version`
- [ ] AWS credentials configured: `aws sts get-caller-identity`
- [ ] Region set to us-east-1: `aws configure get region`

### After Deploying
- [ ] Visit CloudFront URL
- [ ] Check price chart loads
- [ ] Verify CSV data shows in table
- [ ] Check Lambda logs: `sam logs --tail`
- [ ] Verify S3 buckets created
- [ ] Test manual Lambda trigger

### Optional Setup
- [ ] Set up custom domain (Route 53 or Cloudflare)
- [ ] Enable GitHub Actions
- [ ] Set up cost alerts in AWS
- [ ] Add CloudWatch dashboard

---

## 🔍 Testing Locally

### Test Frontend Locally
```bash
cd PriceMonitorFrontend
python -m http.server 8000
# Open: http://localhost:8000/test-local.html
```

### Test Lambda Locally
```bash
cd PriceParser
python site_price_parser.py
```

### Test with SAM Local
```bash
sam local invoke PriceScraperFunction \
    --event test-event.json
```

---

## 🎨 Customization Guide

### Change Colors
Edit `PriceMonitorFrontend/styles.css`:
```css
:root {
    --primary: #4F46E5;  /* Your brand color */
}
```

### Change Schedule
Edit `template.yaml`:
```yaml
Schedule: cron(0 5 * * ? *)  # Current: Midnight EST
# Examples:
# cron(0 17 * * ? *)  # Noon EST
# cron(0 9 * * ? *)   # 4 AM EST
```

### Change Destination/Dates
Edit `site_price_parser.py`:
```python
query_parts = [
    'start_date=2026-12-13',  # Your dates
    'end_date=2026-12-19',
]
```

### Add More Destinations
1. Duplicate Lambda function in `template.yaml`
2. Change environment variables
3. Create separate CSV files
4. Update frontend to show multiple Destinations

---

## 🐛 Troubleshooting

### "Access Denied" errors
```bash
# Check your AWS credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

### Lambda timeout
```bash
# Edit template.yaml
Timeout: 60 → Timeout: 120

# Redeploy
sam deploy
```

### Website not loading
```bash
# Check CloudFront distribution
aws cloudfront list-distributions

# Check S3 bucket
aws s3 ls s3://YOUR-FRONTEND-BUCKET/

# Invalidate cache
aws cloudfront create-invalidation \
    --distribution-id YOUR-DIST-ID \
    --paths "/*"
```

### Prices not updating
```bash
# Check Lambda logs
sam logs --stack-name club-med-price-monitor --tail

# Manually trigger Lambda
aws lambda invoke \
    --function-name ClubMedPriceScraper-prod \
    --payload '{"start_date":"2026-12-13","end_date":"2026-12-19"}' \
    response.json
```

---

## 📊 What You'll See

### Dashboard
![Dashboard Preview](https://via.placeholder.com/800x500/FFFFFF/4F46E5?text=Beautiful+Price+Dashboard)

**Features:**
- Current price with change indicator
- Lowest price recorded
- 30-day trend analysis
- Last update timestamp
- Interactive line chart
- Detailed price table
- Export to CSV button

### Data Format
```csv
price_check_date,initial_price,best_price,start_date,end_date,number_of_adults,number_of_kids
2026-01-09,14682,7443,2026-12-13,2026-12-19,2,2
```

---

## 🔄 Update Workflow

### Update Lambda Code
1. Edit `site_price_parser.py`
2. Run `sam build --use-container`
3. Run `sam deploy`

### Update Frontend
1. Edit files in `PriceMonitorFrontend/`
2. Run `./deploy.sh` or:
```bash
aws s3 sync PriceMonitorFrontend/ s3://YOUR-BUCKET/
aws cloudfront create-invalidation --distribution-id ID --paths "/*"
```

### Update Infrastructure
1. Edit `template.yaml`
2. Run `sam deploy`

---

## 🎓 Learning Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [Playwright Python Docs](https://playwright.dev/python/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

---

## 📞 Support

- GitHub Issues: Open an issue for bugs/features
- AWS Support: For AWS-specific issues
- Stack Overflow: Tag with `aws-sam`, `aws-lambda`

---

## ✨ Next Steps

1. **Deploy Now**: Run `./deploy.sh`
2. **Test Website**: Visit your CloudFront URL
3. **Set Up Domain**: Add custom domain (optional)
4. **Enable CI/CD**: Push to GitHub for auto-deploy
5. **Monitor**: Check CloudWatch logs and metrics
6. **Customize**: Change colors, add features, modify schedule

---

**🎉 You're all set! Happy price monitoring!**
