# Club Med Price Parser - Setup Guide

## Overview
This AWS Lambda function parses prices from Club Med Quebec Charlevoix website and maintains a CSV history of price changes.

## Key Features
- ✅ **No Selenium dependency** - Uses Playwright which works better with AWS Lambda
- ✅ **Python 3.13 compatible** - Latest version supported by AWS Lambda
- ✅ **CSV tracking** - Automatically maintains price history
- ✅ **One record per day** - Deduplicates entries by date
- ✅ **FastAPI ready** - Can be integrated into FastAPI backend

## Dependencies

```bash
pip install playwright
playwright install chromium
```

## For AWS Lambda Deployment

### Option 1: Using Playwright (Recommended)
1. Create a Lambda Layer with Playwright and Chromium
2. Use the `playwright-aws-lambda` package or similar
3. Or use a container image with Playwright pre-installed

### Option 2: Using Docker Container
```dockerfile
FROM public.ecr.aws/lambda/python:3.13
RUN pip install playwright
RUN playwright install chromium --with-deps
COPY site_price_parser.py ${LAMBDA_TASK_ROOT}/
CMD ["site_price_parser.lambda_handler"]
```

### Option 3: Third-party Scraping Service
- For production, consider using ScrapingBee, ScraperAPI, or similar
- These handle JavaScript rendering without needing browser dependencies

## For FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks
from site_price_parser import fetch_club_med_prices, save_to_csv

app = FastAPI()

@app.post("/check-prices")
async def check_prices(start_date: str, end_date: str, background_tasks: BackgroundTasks):
    result = fetch_club_med_prices(start_date, end_date)
    if result['success']:
        background_tasks.add_task(save_to_csv, result)
    return result
```

## Local Testing

```bash
python site_price_parser.py
```

## CSV Format

| price_check_date | initial_price | best_price | start_date | end_date | number_of_adults | number_of_kids |
|------------------|---------------|------------|------------|----------|------------------|----------------|
| 2026-01-09       | 14682         | 7443       | 2026-12-13 | 2026-12-19 | 2              | 2              |

## Performance
- Average execution time: ~10 seconds (with Playwright)
- Timeout: 45 seconds
- Lambda recommended memory: 512MB - 1GB

## Notes
- SSL certificate verification is bypassed for local macOS testing only
- In production Lambda, certificates work correctly without bypass
- CSV is stored in `/tmp/` directory in Lambda (ephemeral storage)
- Consider using S3 for persistent CSV storage in Lambda

## Cost Optimization
- Use Lambda container images for faster cold starts
- Consider scheduled CloudWatch Events instead of API Gateway if running on a schedule
- Playwright adds ~150MB to deployment package

## Alternative: API-based Solution
If you want to avoid browser automation entirely, you could:
1. Contact Club Med to ask if they have an API
2. Use a third-party travel API aggregator
3. Use a managed scraping service with built-in browser rendering
