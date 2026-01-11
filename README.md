# Price Monitor

A beautiful, serverless price monitoring dashboard that automatically tracks Price Monitor Destination Pricing Monitoring prices daily and displays them in an interactive chart.

![Price Monitor Dashboard](https://via.placeholder.com/800x400/4F46E5/FFFFFF?text=Club+Med+Price+Monitor)

## ✨ Features

- 📊 **Interactive Price Charts** - View historical price trends with Chart.js
- 🤖 **Automatic Daily Updates** - Scrapes prices at midnight EST automatically
- 💰 **Cost Tracking** - See savings, discounts, and price trends over time
- 📱 **Responsive Design** - Beautiful UI that works on all devices
- ⚡ **Fast & Reliable** - Powered by AWS CloudFront CDN
- 💵 **Low Cost** - Runs for ~$1-2/month on AWS

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/DestinationPriceMonitor.git
cd DestinationPriceMonitor
```

### 2. Deploy to AWS
```bash
./deploy.sh
```

### 3. Visit Your Website
Your CloudFront URL will be displayed after deployment completes.

## 📋 Requirements

- AWS Account
- Python 3.13+
- AWS CLI configured
- AWS SAM CLI installed

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed setup instructions.

## 🏗️ Architecture

```
EventBridge (Daily) → Lambda (Scraper) → S3 (CSV) → CloudFront + S3 (Website)
```

## 💰 Pricing

- Lambda: FREE (within free tier)
- S3: ~$0.50/month
- CloudFront: ~$1/month
- **Total: $1-2/month**

## 📊 Tech Stack

**Frontend:**
- HTML/CSS/JavaScript
- Chart.js for visualization
- Hosted on S3 + CloudFront

**Backend:**
- Python 3.13
- AWS Lambda
- Playwright for web scraping
- EventBridge for scheduling

**Infrastructure:**
- AWS SAM (Infrastructure as Code)
- GitHub Actions (CI/CD)

## 🔧 Development

### Local Testing
```bash
cd PriceParser
python site_price_parser.py
```

### Update Lambda
```bash
sam build --use-container
sam deploy
```

### Update Frontend
```bash
aws s3 sync PriceMonitorFrontend/ s3://YOUR-BUCKET/
```

## 📖 Documentation

- [Deployment Guide](DEPLOYMENT.md) - Complete deployment instructions
- [Frontend README](PriceMonitorFrontend/README.md) - Frontend details
- [Lambda README](PriceParser/README.md) - Backend/scraper details

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Chart.js for beautiful charts
- Playwright for reliable web scraping
- AWS for serverless infrastructure

---

**Made with ❤️ for budget-conscious travelers**
