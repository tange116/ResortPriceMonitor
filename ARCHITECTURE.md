# Architecture Overview

## Data Flow

### Single Source of Truth
- **ONE CSV file**: `PriceParser/price_history.csv`
- This file serves both local development and as the data source

### Local Development
```
site_price_parser.py → PriceParser/price_history.csv ← test-local.html
     (writes)                                              (reads)
```

- Run `python site_price_parser.py` to fetch latest prices
- Writes to `PriceParser/price_history.csv`
- Open http://localhost:8000/test-local.html to view
- Test frontend reads from `../PriceParser/price_history.csv`

### Production (AWS)
```
Lambda Function → S3 Bucket ← CloudFront + Frontend
  (daily 12am EST)  (price_history.csv)  (index.html reads)
```

- **EventBridge**: Triggers Lambda daily at midnight EST
- **Lambda**: Runs `site_price_parser.py`, saves to S3
- **S3 Bucket**: Stores `price_history.csv` with public read access
- **Frontend**: `index.html` fetches from S3 via `app.js`
- **CloudFront**: CDN distribution for fast global access

## File Purposes

| File | Purpose | Updates |
|------|---------|---------|
| `PriceParser/price_history.csv` | Local data storage | Local script runs |
| S3: `price_history.csv` | Production data storage | Lambda (daily) |
| `test-local.html` | Local development UI | Never (reads from PriceParser/) |
| `index.html` + `app.js` | Production UI | Never (reads from S3) |

## Key Points

1. **No file duplication**: Only one local CSV in `PriceParser/`
2. **Local testing**: Frontend reads from `../PriceParser/price_history.csv`
3. **Production**: Completely separate - Lambda writes to S3, frontend reads from S3
4. **Daily updates**: Automatic via EventBridge schedule in production
5. **Cost optimized**: S3 storage (~$0.023/GB/month), Lambda free tier covers daily runs
