# Complete Data Flow - Local to Production

## Overview
This document explains how data flows from the parser to the frontend in both local development and AWS production environments.

---

## Local Development Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL TESTING                             │
└─────────────────────────────────────────────────────────────┘

1. Manual Execution:
   $ cd PriceParser
   $ python site_price_parser.py
         ↓
   Fetches Club Med prices (Playwright renders JavaScript)
         ↓
   Saves to: PriceParser/price_history.csv
         ↓
   ✅ File updated with today's prices

2. View Frontend:
   $ cd .. && python3 -m http.server 8000
         ↓
   Open: http://localhost:8000/PriceMonitorFrontend/test-local.html
         ↓
   Frontend fetches: ../PriceParser/price_history.csv
         ↓
   ✅ Chart displays with latest data
```

---

## AWS Production Flow

```
┌─────────────────────────────────────────────────────────────┐
│               AWS PRODUCTION (After Deployment)              │
└─────────────────────────────────────────────────────────────┘

DAILY AUTOMATIC UPDATE:
━━━━━━━━━━━━━━━━━━━━━━
Every day at 12:00 AM EST

EventBridge (Cron)
    ↓
    ├─ Schedule: cron(0 5 * * ? *)  ← 5 AM UTC = 12 AM EST
    └─ Target: PriceScraperLambda
          ↓
AWS Lambda Function
    ├─ Runtime: Python 3.13
    ├─ Code: site_price_parser.py
    ├─ Env Vars: S3_BUCKET=club-med-prices-{account}
    └─ Execution:
          1. Fetch prices from Club Med (Playwright)
          2. Read existing CSV from S3 (if exists)
          3. Update today's entry or append new
          4. Write back to S3 with CacheControl: no-cache
          ↓
S3 Bucket: club-med-prices-{account}
    ├─ Object: price_history.csv
    ├─ Metadata: CacheControl: no-cache
    ├─ Permissions: Public read
    └─ ✅ Updated with today's prices

FRONTEND ACCESS:
━━━━━━━━━━━━━━━━
User visits your website

Browser → CloudFront Distribution
    ↓
    ├─ Domain: xyz123.cloudfront.net
    └─ Origin: S3 Frontend Bucket (index.html, app.js, styles.css)
          ↓
Frontend JavaScript (app.js) executes
    ├─ const csvUrl = 'https://club-med-prices-{account}.s3.amazonaws.com/price_history.csv'
    └─ fetch(csvUrl + '?t=' + Date.now())  ← Timestamp = cache busting
          ↓
Request: GET /price_history.csv?t=1704852000000
    ↓
CloudFront CDN
    ├─ Cache behavior for *.csv:
    ├─   - DefaultTTL: 60 seconds
    ├─   - MaxTTL: 300 seconds
    ├─   - QueryString: true (forwards ?t=)
    └─ Cache key: /price_history.csv?t=1704852000000 ← Unique every time!
          ↓
          ├─ Cache HIT? → Serve from edge (if <60 sec old)
          └─ Cache MISS? → Forward to S3
                ↓
S3 Bucket: club-med-prices-{account}
    ├─ Returns: price_history.csv
    └─ Headers: CacheControl: no-cache
          ↓
CloudFront → Browser
    ↓
Frontend parses CSV
    ├─ Creates Chart.js line graph
    ├─ Populates stats cards
    └─ ✅ User sees latest prices!
```

---

## Key Points

### 1. **Lambda Updates S3 Daily**
- ✅ EventBridge triggers at midnight EST
- ✅ Lambda reads existing S3 CSV, updates/appends today's entry
- ✅ Writes back with `CacheControl: no-cache`
- ✅ One record per day (deduplication by date)

### 2. **Frontend Always Gets Fresh Data**
```javascript
// app.js - Cache busting with timestamp
const cacheBuster = `?t=${Date.now()}`;  // Changes every millisecond
const response = await fetch(CONFIG.csvUrl + cacheBuster, {
    cache: 'no-store',  // Tell browser not to cache
    headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate'
    }
});
```

**Why this works:**
- Every page load has a different `?t=` value
- CloudFront sees each request as unique URL
- Browser cache bypassed
- **Result:** Always fetches from S3 (or recent CloudFront cache <60 sec)

### 3. **No Service Restart Needed**
- Frontend is **static files** (HTML/CSS/JS)
- Each page load executes fetch() with new timestamp
- No server to restart - it's serverless!

---

## Storage Locations

| Environment | CSV Location | Updated By | Read By |
|-------------|--------------|------------|---------|
| **Local** | `PriceParser/price_history.csv` | Manual: `python site_price_parser.py` | `test-local.html` |
| **AWS** | `s3://club-med-prices-{account}/price_history.csv` | Lambda (daily at midnight) | `index.html` via CloudFront |

---

## Data Freshness Guarantees

### Worst Case Scenario:
```
Lambda updates S3 at 12:00:00 AM EST
User visits at 12:00:05 AM EST (5 seconds later)
CloudFront has cached version from yesterday (59 seconds old)
User sees data from 59 seconds ago
Wait 1 more second → CloudFront cache expires (60 sec TTL)
Refresh page → Fetches fresh data from S3
```

### Typical Case:
```
Lambda updates S3 at 12:00:00 AM EST
User visits at 9:00 AM EST
Timestamp cache-busting ensures fresh fetch
User sees today's prices immediately ✅
```

---

## Cost Analysis

**Daily Operations:**
- Lambda execution: 1/day × $0.0000002 = $0.0000002
- S3 PUT: 1/day × $0.000005 = $0.000005
- S3 GET: ~100/day × $0.0000004 = $0.00004
- CloudFront: ~100 requests × $0.000001 = $0.0001
- S3 storage: 1KB × $0.023/GB/month ≈ $0.00000002

**Monthly Total: ~$0.01** 💰

**Free Tier Covers:**
- Lambda: 1M requests/month (you use 30)
- S3: 2,000 PUTs + 20,000 GETs (you use 30 + 3,000)
- CloudFront: 1TB data transfer (you use ~1MB)

**Effective Cost: $0.00/month** ✅

---

## Troubleshooting

### CSV Not Updating?
1. Check Lambda logs: CloudWatch → /aws/lambda/ClubMedPriceScraper
2. Verify S3 object: `aws s3 ls s3://club-med-prices-{account}/`
3. Check Last Modified: `aws s3api head-object --bucket club-med-prices-{account} --key price_history.csv`

### Frontend Shows Old Data?
1. Hard refresh: Cmd+Shift+R (clears browser cache)
2. Check Network tab: Verify ?t= timestamp is changing
3. Check S3 file: Download directly and verify content
4. CloudFront invalidation: `aws cloudfront create-invalidation --distribution-id XXX --paths "/*.csv"`

### Lambda Failing?
1. Check Playwright installed: `playwright install chromium`
2. Check S3_BUCKET env var set
3. Check IAM permissions: Lambda needs s3:GetObject, s3:PutObject
4. Test locally first: `python site_price_parser.py`

---

## Summary

**The Magic Formula:**
1. **Lambda** writes to S3 with `CacheControl: no-cache`
2. **Frontend** fetches with `?t=timestamp` (new every time)
3. **CloudFront** sees each request as unique (1 min TTL max)
4. **Result:** Always fresh data, no restart needed! 🎯

**Single Source of Truth:**
- Local: `PriceParser/price_history.csv`
- AWS: `s3://club-med-prices-{account}/price_history.csv`
- Frontend automatically picks up changes via timestamp cache-busting
