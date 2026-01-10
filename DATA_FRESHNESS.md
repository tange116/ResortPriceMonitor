# Data Freshness Guarantee

## How Fresh Data Works in Production

### Question: Will the frontend automatically pick up CSV updates without restart?

**YES!** ✅ The system is designed to always show fresh data. Here's how:

## Multi-Layer Freshness Strategy

### 1. **No Server Restart Needed**
- The frontend is **static files** (HTML/CSS/JS) served from CloudFront
- Each page load/refresh fetches the CSV **fresh** from S3
- There's no "service" to restart - it's serverless!

### 2. **S3 Cache Headers** (Backend)
```python
# In site_price_parser.py line 185-190
s3_client.put_object(
    Bucket=bucket,
    Key=key,
    Body=output.getvalue(),
    ContentType='text/csv',
    CacheControl='no-cache'  # ← Tells browsers/CDNs not to cache
)
```

### 3. **Browser Cache-Busting** (Frontend)
```javascript
// In app.js - adds timestamp to every request
const cacheBuster = `?t=${Date.now()}`;
const response = await fetch(CONFIG.csvUrl + cacheBuster, {
    cache: 'no-store',  // Tell browser not to cache
    headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
    }
});
```

**How it works:**
- Every time you load the page, it adds `?t=1704852000000` to the URL
- The timestamp changes each time, forcing a fresh download
- Browser sees it as a "new" URL and bypasses cache

### 4. **CloudFront CDN Settings** (Infrastructure)
```yaml
# In template.yaml - CSV-specific cache behavior
CacheBehaviors:
  - PathPattern: '*.csv'
    ForwardedValues:
      QueryString: true  # Forwards the ?t= parameter
    MinTTL: 0
    DefaultTTL: 60      # Cache for only 1 minute
    MaxTTL: 300         # Max 5 minutes
```

## Data Flow Timeline

```
Day 1, 12:00 AM EST:
  EventBridge → Lambda → S3 (writes new CSV with CacheControl: no-cache)
                           ↓
Day 1, 8:00 AM:
  User visits page → fetch CSV?t=1704790800000 → CloudFront
                                                    ↓
                                                (cache miss or expired)
                                                    ↓
                                                  S3 (fresh data)
                                                    ↓
                                                  User sees latest prices ✅

Day 1, 8:01 AM (same user refreshes):
  User refreshes → fetch CSV?t=1704790860000 ← Different timestamp!
                                  ↓
                            CloudFront (new query = new cache key)
                                  ↓
                            S3 (fresh data again)
```

## Guarantees

| Layer | Max Staleness | How |
|-------|---------------|-----|
| **S3** | 0 seconds | Strong consistency, CacheControl: no-cache |
| **CloudFront** | 1 minute | DefaultTTL: 60 seconds |
| **Browser** | 0 seconds | Cache-busting with timestamp |
| **Overall** | **~1 minute max** | Even if CloudFront cached, timestamp forces fresh fetch |

## Testing Fresh Data

### Local Testing
1. Update CSV: `cd PriceParser && python site_price_parser.py`
2. Refresh browser: The `?t=` timestamp changes automatically
3. See new data immediately ✅

### Production Testing
1. Lambda updates S3 at midnight EST
2. User visits page anytime after
3. Timestamp query parameter bypasses all caches
4. Fresh data guaranteed ✅

## Why This Works Better Than Traditional Approaches

❌ **Bad**: Relying only on cache headers
- Problem: Different browsers interpret differently
- Problem: Users might have aggressive caching plugins

❌ **Bad**: Short cache TTL only
- Problem: Still 1-5 minute delays possible
- Problem: Increased S3 costs from constant requests

✅ **Good**: Our multi-layer approach
- ✅ Cache-busting guarantees browser freshness
- ✅ Low TTL minimizes CDN staleness
- ✅ S3 headers prevent intermediate caching
- ✅ Timestamp makes every request "unique"

## Cost Impact

**Daily Operations:**
- Lambda: 1 execution/day = FREE (1M free/month)
- S3 PUT: 1 request/day = ~$0.000005/day
- S3 GET: ~100 page loads/day = ~$0.00004/day
- CloudFront: ~100 requests/day = ~$0.0001/day

**Monthly:** ~$0.01/month (essentially free) 💰

## Monitoring Freshness

Check S3 Last Modified time:
```bash
aws s3api head-object \
  --bucket club-med-prices-YOUR-ACCOUNT \
  --key price_history.csv \
  --query 'LastModified'
```

Verify cache headers:
```bash
curl -I https://YOUR-CLOUDFRONT-DOMAIN/price_history.csv
# Should see: Cache-Control: no-cache
```

Test frontend timestamp:
```bash
# Open browser DevTools → Network tab
# Refresh page
# Look for: price_history.csv?t=1704852000000
# Each refresh should show different ?t= value
```

## Summary

**Will the frontend pick up updates automatically?**
- ✅ YES - Every page load fetches fresh data
- ✅ NO restart needed - It's serverless
- ✅ Guaranteed fresh within ~1 minute worst case
- ✅ Usually instant due to cache-busting timestamp
- ✅ Works even if user has aggressive browser caching
- ✅ Costs pennies per month

**The secret:** Three layers of defense (S3 headers + CloudFront TTL + timestamp cache-busting) ensure you ALWAYS see fresh data! 🎯
