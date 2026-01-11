"""
Price Monitor Price Parser - AWS Lambda Function

FLOW OVERVIEW:
==============
LOCAL TESTING:
  python site_price_parser.py → PriceParser/price_history.csv

AWS PRODUCTION:
  EventBridge (midnight EST) → Lambda → S3 bucket/price_history.csv
                                            ↓
  Frontend → fetch CSV?t=timestamp → CloudFront → S3 (always fresh!)
"""

import json
import re
import urllib.request
import ssl
import os
import csv
import gzip
import boto3
from io import StringIO
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional
from pathlib import Path

# Load environment variables from .env file if it exists
def load_env_file():
    """Load .env file from project root (one level up from PriceParser/)."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

load_env_file()

# Initialize S3 client (available in Lambda)
try:
    s3_client = boto3.client('s3')
    S3_AVAILABLE = True
except Exception:
    S3_AVAILABLE = False
    s3_client = None

# Try to import Playwright for JavaScript rendering
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def extract_prices_from_html(html_content: str) -> Dict[str, Optional[str]]:
    """Extract initial price and best price from Price Monitor HTML."""
    prices = {'initial_price': None, 'best_price': None}
    
    # Method 1: sr-only spans
    initial_pattern = r'<span[^>]*class="sr-only"[^>]*>Initial\s+price\s*</span>\s*\$\s*([\d,]+)'
    initial_match = re.search(initial_pattern, html_content, re.IGNORECASE)
    if initial_match:
        prices['initial_price'] = initial_match.group(1)
    
    best_pattern = r'<span[^>]*class="sr-only"[^>]*>Best\s+price\s*</span>\s*\$\s*([\d,]+)'
    best_match = re.search(best_pattern, html_content, re.IGNORECASE)
    if best_match:
        prices['best_price'] = best_match.group(1)
    
    # Method 2: JSON data
    if not prices['initial_price'] or not prices['best_price']:
        if not prices['initial_price']:
            for pattern in [r'"initialPrice"\s*:\s*(\d+)', r'"initial[Pp]rice"\s*:\s*["\']?\$?\s*(\d+)']:
                match = re.search(pattern, html_content)
                if match:
                    price_value = match.group(1)
                    prices['initial_price'] = f"{price_value[:-3]},{price_value[-3:]}" if len(price_value) > 3 else price_value
                    break
        
        if not prices['best_price']:
            for pattern in [r'"bestPrice"\s*:\s*(\d+)', r'"best[Pp]rice"\s*:\s*["\']?\$?\s*(\d+)']:
                match = re.search(pattern, html_content)
                if match:
                    price_value = match.group(1)
                    prices['best_price'] = f"{price_value[:-3]},{price_value[-3:]}" if len(price_value) > 3 else price_value
                    break
    
    # Method 3: Fallback
    if not prices['initial_price']:
        match = re.search(r'<del[^>]*>.*?Initial\s+price.*?\$\s*([\d,]+)', html_content, re.IGNORECASE | re.DOTALL)
        if match:
            prices['initial_price'] = match.group(1)
    
    if not prices['best_price']:
        match = re.search(r'Best\s+price\s*</span>\s*\$\s*([\d,]+)', html_content, re.IGNORECASE)
        if match:
            prices['best_price'] = match.group(1)
    
    return prices


def fetch_with_playwright(url: str) -> str:
    """Fetch webpage using Playwright (handles JavaScript)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=45000)
            page.wait_for_timeout(8000)  # Wait for JS to render prices
            html_content = page.content()
        finally:
            browser.close()
        return html_content


def fetch_club_med_prices(start_date: str, end_date: str, use_js_rendering: bool = True) -> Dict[str, Any]:
    """
    Fetch prices from Price Monitor Destination Pricing.
    
    Args:
        start_date: Format YYYY-MM-DD
        end_date: Format YYYY-MM-DD
        use_js_rendering: Use Playwright (default True)
    
    Returns:
        {success, initial_price, best_price, start_date, end_date, url}
    """
    # Base URL is read from environment to avoid hard-coding the destination domain
    base_url = os.getenv("PRICE_MONITOR_BASE_URL", "https://example.com/path")
    query_parts = [
        'adults=2', 'children=2',
        'birthdates=2015-05-08', 'birthdates=2018-07-08',
        f'start_date={start_date}', f'end_date={end_date}'
    ]
    url = f"{base_url}?{'&'.join(query_parts)}"
    
    try:
        if use_js_rendering and PLAYWRIGHT_AVAILABLE:
            html_content = fetch_with_playwright(url)
        else:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
            }
            req = urllib.request.Request(url, headers=headers)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                content = response.read()
                if response.headers.get('Content-Encoding') == 'gzip':
                    html_content = gzip.decompress(content).decode('utf-8')
                else:
                    html_content = content.decode('utf-8')
        
        prices = extract_prices_from_html(html_content)
        
        return {
            'success': True,
            'start_date': start_date,
            'end_date': end_date,
            'initial_price': prices['initial_price'],
            'best_price': prices['best_price'],
            'url': url
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'start_date': start_date,
            'end_date': end_date
        }


def save_to_csv(result: Dict[str, Any], csv_path: str, 
                number_of_adults: int = 2, number_of_kids: int = 2) -> None:
    """
    Save price data to CSV.
    
    STORAGE MODE:
    - Lambda with S3_BUCKET env var → S3 bucket
    - Local → PriceParser/price_history.csv
    """
    eastern_tz = ZoneInfo('America/New_York')
    price_check_date = datetime.now(eastern_tz).strftime('%Y-%m-%d')
    
    initial_price = result.get('initial_price', '').replace(',', '') if result.get('initial_price') else ''
    best_price = result.get('best_price', '').replace(',', '') if result.get('best_price') else ''
    
    new_row = {
        'price_check_date': price_check_date,
        'initial_price': initial_price,
        'best_price': best_price,
        'start_date': result.get('start_date', ''),
        'end_date': result.get('end_date', ''),
        'number_of_adults': number_of_adults,
        'number_of_kids': number_of_kids
    }
    
    fieldnames = ['price_check_date', 'initial_price', 'best_price', 'start_date', 
                  'end_date', 'number_of_adults', 'number_of_kids']
    
    s3_bucket = os.environ.get('S3_BUCKET')
    
    if S3_AVAILABLE and s3_bucket:
        save_to_s3(s3_bucket, csv_path, new_row, fieldnames)
    else:
        save_to_local_file(csv_path, new_row, fieldnames)


def save_to_s3(bucket: str, key: str, new_row: Dict, fieldnames: list) -> None:
    """
    Save CSV to S3 (AWS Production).
    
    IMPORTANT: CacheControl='no-cache' ensures fresh data.
    Frontend uses ?t=timestamp for cache-busting.
    """
    rows = []
    
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        reader = csv.DictReader(StringIO(csv_content))
        rows = list(reader)
    except s3_client.exceptions.NoSuchKey:
        print(f"Creating new CSV in S3: s3://{bucket}/{key}")
    except Exception as e:
        print(f"Error reading from S3: {e}")
    
    # Update existing date or append new
    date_exists = False
    for i, row in enumerate(rows):
        if row['price_check_date'] == new_row['price_check_date']:
            rows[i] = new_row
            date_exists = True
            print(f"Updated entry for {new_row['price_check_date']}")
            break
    
    if not date_exists:
        rows.append(new_row)
        print(f"Added entry for {new_row['price_check_date']}")
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    
    # CRITICAL: CacheControl prevents stale data
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=output.getvalue(),
        ContentType='text/csv',
        CacheControl='no-cache'  # Frontend always gets fresh data
    )
    print(f"✅ CSV saved to S3: s3://{bucket}/{key} (Total: {len(rows)} records)")


def save_to_local_file(csv_path: str, new_row: Dict, fieldnames: list) -> None:
    """Save CSV to local filesystem (for testing)."""
    file_exists = os.path.isfile(csv_path)
    
    if file_exists:
        rows = []
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
        
        date_exists = False
        for i, row in enumerate(rows):
            if row['price_check_date'] == new_row['price_check_date']:
                rows[i] = new_row
                date_exists = True
                print(f"Updated entry for {new_row['price_check_date']}")
                break
        
        if not date_exists:
            rows.append(new_row)
            print(f"Added entry for {new_row['price_check_date']}")
        
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(new_row)
        print(f"Created new CSV: {csv_path}")
    
    print(f"✅ CSV saved locally: {csv_path}")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler - Triggered daily by EventBridge.
    
    PRODUCTION FLOW:
    1. EventBridge → Lambda (midnight EST)
    2. Lambda → Fetch prices from Price Monitor
    3. Lambda → Save to S3 (CacheControl: no-cache)
    4. Frontend → Fetch from S3 (?t=timestamp for cache-busting)
    
    Event formats:
    - Direct: {"start_date": "2026-12-13", "end_date": "2026-12-19"}
    - API Gateway: {"queryStringParameters": {...}}
    - Scheduled: {} (EventBridge)
    """
    try:
        start_date = None
        end_date = None
        
        # Extract parameters from event
        if 'start_date' in event and 'end_date' in event:
            start_date = event['start_date']
            end_date = event['end_date']
        elif 'queryStringParameters' in event and event['queryStringParameters']:
            start_date = event['queryStringParameters'].get('start_date')
            end_date = event['queryStringParameters'].get('end_date')
        elif 'body' in event and event['body']:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            start_date = body.get('start_date')
            end_date = body.get('end_date')
        
        # Validate
        if not start_date or not end_date:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing start_date and end_date (format: YYYY-MM-DD)'
                })
            }
        
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, start_date) or not re.match(date_pattern, end_date):
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                })
            }
        
        # Fetch prices
        print(f"Fetching prices for {start_date} to {end_date}...")
        result = fetch_club_med_prices(start_date, end_date)
        
        # Save to CSV
        if result['success'] and result.get('initial_price') and result.get('best_price'):
            try:
                csv_path = 'history.csv'
                save_to_csv(result, csv_path)
                result['csv_saved'] = True
                result['csv_location'] = f"s3://{os.environ.get('S3_BUCKET')}/{csv_path}" if os.environ.get('S3_BUCKET') else csv_path
            except Exception as csv_error:
                result['csv_saved'] = False
                result['csv_error'] = str(csv_error)
        
        return {
            'statusCode': 200 if result['success'] else 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(result)
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': f'Lambda error: {str(e)}'})
        }


# Local testing
if __name__ == "__main__":
    print("=" * 60)
    print("LOCAL TEST - Price Monitor Price Parser")
    print("=" * 60)
    
    test_event = {'start_date': '2026-12-13', 'end_date': '2026-12-19'}
    
    print(f"\nFetching prices: {test_event['start_date']} to {test_event['end_date']}")
    print("Using Playwright for JavaScript rendering...\n")
    
    result = lambda_handler(test_event, None)
    response_body = json.loads(result['body'])
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(json.dumps(response_body, indent=2))
    
    if response_body.get('csv_saved'):
        print(f"\n✅ CSV saved to: history.csv")
        try:
            with open('history.csv', 'r') as f:
                lines = f.readlines()
                print(f"   Total records: {len(lines) - 1}")
                if len(lines) > 1:
                    print(f"   Latest: {lines[-1].strip()}")
        except Exception as e:
            print(f"   Error reading CSV: {e}")
    
    print("\n" + "=" * 60)
    print("AWS PRODUCTION FLOW (After Deployment)")
    print("=" * 60)
    print("1. EventBridge triggers Lambda at midnight EST")
    print("2. Lambda fetches prices → S3 bucket/price_history.csv")
    print("3. Frontend fetches from S3 with ?t=timestamp")
    print("4. Users see fresh data (max 1 min CDN delay)")
    print("=" * 60)
