# Visual Data Flow Diagram

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    Price Monitor PRICE MONITOR                       ┃
┃                    Complete Data Flow                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛


┌─────────────────────────────────────────────────────────────────┐
│  PART 1: LOCAL DEVELOPMENT (Testing Before Deployment)         │
└─────────────────────────────────────────────────────────────────┘

Developer's Machine:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  $ python site_price_parser.py                                  │
│         │                                                        │
│         ├─ Launches Playwright + Chromium                       │
│         ├─ Fetches Price Monitor website                             │
│         ├─ Waits 8 seconds for JavaScript to render             │
│         ├─ Extracts: Initial Price, Best Price                  │
│         └─ Detects: No S3_BUCKET env var                        │
│                │                                                 │
│                ↓                                                 │
│  ┌─────────────────────────────────────┐                        │
│  │  PriceParser/price_history.csv      │                        │
│  │  ─────────────────────────────────  │                        │
│  │  price_check_date,initial_price,... │                        │
│  │  2026-01-09,14682,7443,...          │                        │
│  │  2026-01-10,14682,7443,...  ← NEW!  │                        │
│  └─────────────────────────────────────┘                        │
│                │                                                 │
│                ↓                                                 │
│  $ python3 -m http.server 8000                                  │
│                │                                                 │
│                ↓                                                 │
│  Browser: http://localhost:8000/PriceMonitorFrontend/test-...  │
│         │                                                        │
│         ├─ test-local.html loads                                │
│         ├─ fetch('../PriceParser/price_history.csv')            │
│         ├─ Parses CSV                                            │
│         ├─ Creates Chart.js graph                               │
│         └─ ✅ Displays prices!                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│  PART 2: AWS PRODUCTION (After ./deploy.sh)                    │
└─────────────────────────────────────────────────────────────────┘

AWS Cloud Architecture:
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ┌────────────────────┐                                         │
│  │  EventBridge Rule  │  cron(0 5 * * ? *)  ← 12 AM EST daily  │
│  │  ─────────────────  │                                         │
│  │  Schedule: Daily    │                                         │
│  │  Time: Midnight EST │                                         │
│  └──────────┬──────────┘                                         │
│             │ Triggers                                           │
│             ↓                                                    │
│  ┌──────────────────────────────┐                               │
│  │  Lambda Function             │                               │
│  │  ───────────────────────────  │                               │
│  │  Name: ClubMedPriceScraper   │                               │
│  │  Runtime: Python 3.13        │                               │
│  │  Memory: 512 MB              │                               │
│  │  Timeout: 60 seconds         │                               │
│  │                              │                               │
│  │  Code: site_price_parser.py  │                               │
│  │  Layer: Playwright + Chrome  │                               │
│  │                              │                               │
│  │  Env Vars:                   │                               │
│  │  └─ S3_BUCKET=club-med-...   │                               │
│  │                              │                               │
│  │  Execution:                  │                               │
│  │  1. Fetch Price Monitor prices    │                               │
│  │  2. GET existing CSV from S3 │──┐                            │
│  │  3. Update today's entry     │  │                            │
│  │  4. PUT back to S3           │──┤                            │
│  └──────────────────────────────┘  │                            │
│                                     │                            │
│                                     ↓                            │
│  ┌────────────────────────────────────────────┐                 │
│  │  S3 Bucket: club-med-prices-{account}      │                 │
│  │  ──────────────────────────────────────     │                 │
│  │  ┌────────────────────────────────────┐    │                 │
│  │  │  price_history.csv                 │    │                 │
│  │  │                                    │    │                 │
│  │  │  Metadata:                         │    │                 │
│  │  │  └─ CacheControl: no-cache         │    │                 │
│  │  │                                    │    │                 │
│  │  │  Content:                          │    │                 │
│  │  │  price_check_date,initial_price... │    │                 │
│  │  │  2026-01-09,14682,7443,...         │    │                 │
│  │  │  2026-01-10,14682,7443,... ← NEW!  │    │                 │
│  │  │                                    │    │                 │
│  │  │  Permissions: Public Read          │    │                 │
│  │  │  URL: https://club-med-prices-...  │    │                 │
│  │  └────────────────────────────────────┘    │                 │
│  └────────────────────────────────────────────┘                 │
│                          ↑                                      │
│                          │ GET request                          │
│                          │                                      │
│  ┌───────────────────────┴──────────────┐                       │
│  │  CloudFront Distribution             │                       │
│  │  ────────────────────────────────     │                       │
│  │  Domain: xyz123.cloudfront.net       │                       │
│  │                                      │                       │
│  │  Origin 1: Frontend S3 Bucket        │                       │
│  │  └─ index.html, app.js, styles.css   │                       │
│  │                                      │                       │
│  │  Origin 2: Data S3 Bucket            │                       │
│  │  └─ price_history.csv                │                       │
│  │                                      │                       │
│  │  Cache Behavior for *.csv:           │                       │
│  │  ├─ DefaultTTL: 60 seconds           │                       │
│  │  ├─ MaxTTL: 300 seconds              │                       │
│  │  └─ QueryString: true (forwards ?t=) │                       │
│  └──────────────────────────────────────┘                       │
│                          ↑                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
                           │ HTTPS request
                           │
              ┌────────────┴────────────┐
              │   User's Browser        │
              │   ─────────────────     │
              │                         │
              │   Visits CloudFront URL │
              │         ↓                │
              │   index.html loads      │
              │         ↓                │
              │   app.js executes       │
              │         ↓                │
              │   Line 26:              │
              │   const timestamp =     │
              │     Date.now()          │
              │   // = 1704852000000    │
              │         ↓                │
              │   fetch(csvUrl +        │
              │     '?t=' + timestamp)  │
              │         ↓                │
              │   GET /price_history.   │
              │      csv?t=1704852...   │
              │         ↓                │
              │   ✅ Fresh data!         │
              │   ✅ Chart renders!      │
              │                         │
              └─────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│  WHY FRONTEND ALWAYS GETS FRESH DATA                            │
└─────────────────────────────────────────────────────────────────┘

Cache-Busting Mechanism:
─────────────────────────

Every page load/refresh:

  1. JavaScript generates new timestamp:
     ┌────────────────────────────────────┐
     │ const t = Date.now()               │
     │ // Returns: 1704852000000 (ms)     │
     │                                    │
     │ Next second:                       │
     │ // Returns: 1704852001000 ← DIFFERENT! │
     └────────────────────────────────────┘

  2. Appends to URL:
     ┌────────────────────────────────────────────────────────┐
     │ OLD: price_history.csv                                 │
     │ NEW: price_history.csv?t=1704852000000 ← Unique URL!   │
     └────────────────────────────────────────────────────────┘

  3. Browser sees "new" URL:
     ┌────────────────────────────────────────────────────────┐
     │ Cache key: /price_history.csv?t=1704852000000          │
     │                                                        │
     │ Browser cache lookup: MISS (never seen this URL)       │
     │ → Must fetch from network!                             │
     └────────────────────────────────────────────────────────┘

  4. CloudFront sees unique request:
     ┌────────────────────────────────────────────────────────┐
     │ Query string forwarding: Enabled                       │
     │ Cache key includes: /price_history.csv?t=...           │
     │                                                        │
     │ CloudFront cache lookup:                               │
     │ - If cached < 60 sec: Return cached                    │
     │ - If cached > 60 sec: Fetch from S3                    │
     │ - If new ?t= value: Fetch from S3                      │
     └────────────────────────────────────────────────────────┘

Result: Maximum 60 second staleness, typically instant! ✅


┌─────────────────────────────────────────────────────────────────┐
│  COMPARISON: LOCAL vs AWS                                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┬────────────────────┬────────────────────────┐
│  Aspect          │  Local Dev         │  AWS Production        │
├──────────────────┼────────────────────┼────────────────────────┤
│  Trigger         │  Manual            │  EventBridge (daily)   │
│  Execution       │  python script     │  Lambda function       │
│  Storage         │  Local file        │  S3 bucket             │
│  CSV Path        │  PriceParser/...   │  s3://club-med-...     │
│  Frontend        │  test-local.html   │  index.html            │
│  Server          │  Python http.server│  CloudFront CDN        │
│  URL             │  localhost:8000    │  xyz.cloudfront.net    │
│  Fetch Path      │  ../PriceParser/...│  S3 URL + ?t=timestamp │
│  Cache           │  None              │  CloudFront 60s TTL    │
│  Cost            │  $0 (local)        │  ~$0.01/month          │
│  Freshness       │  Instant           │  Max 60 sec old        │
└──────────────────┴────────────────────┴────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│  KEY TAKEAWAYS                                                  │
└─────────────────────────────────────────────────────────────────┘

✅ ONE Python file: site_price_parser.py
   └─ Works locally AND in Lambda (detects S3_BUCKET env var)

✅ ONE CSV file per environment:
   ├─ Local: PriceParser/price_history.csv
   └─ AWS: s3://club-med-prices-{account}/price_history.csv

✅ Frontend automatically picks up updates:
   ├─ No restart needed (serverless!)
   ├─ Timestamp cache-busting (new ?t= every load)
   └─ Max 60 second staleness (CloudFront TTL)

✅ Cost: ~$0.00/month (free tier covers everything)

✅ Deployment: One command
   └─ ./deploy.sh → deploys everything!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
