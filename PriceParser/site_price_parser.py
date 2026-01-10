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

# Initialize S3 client (will be available in Lambda)
try:
    s3_client = boto3.client('s3')
    S3_AVAILABLE = True
except:
    S3_AVAILABLE = False

# Try to import playwright for JavaScript rendering (optional)
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def extract_prices_from_html(html_content: str) -> Dict[str, Optional[str]]:
    """
    Extract initial price and best price from the Club Med webpage HTML.
    
    Args:
        html_content: The HTML content of the webpage
        
    Returns:
        Dictionary containing 'initial_price' and 'best_price'
    """
    prices = {
        'initial_price': None,
        'best_price': None
    }
    
    # Method 1: Try to find prices in sr-only spans (for fully rendered HTML)
    # Pattern to match: <span class="sr-only">Initial price </span>$14,682
    initial_price_pattern = r'<span[^>]*class="sr-only"[^>]*>Initial\s+price\s*</span>\s*\$\s*([\d,]+)'
    initial_match = re.search(initial_price_pattern, html_content, re.IGNORECASE)
    if initial_match:
        prices['initial_price'] = initial_match.group(1)
    
    best_price_pattern = r'<span[^>]*class="sr-only"[^>]*>Best\s+price\s*</span>\s*\$\s*([\d,]+)'
    best_match = re.search(best_price_pattern, html_content, re.IGNORECASE)
    if best_match:
        prices['best_price'] = best_match.group(1)
    
    # Method 2: Look for prices in JSON data embedded in the page
    if not prices['initial_price'] or not prices['best_price']:
        # Try to find JSON data with price information
        json_patterns = [
            r'"initialPrice"\s*:\s*(\d+)',
            r'"bestPrice"\s*:\s*(\d+)',
            r'"price"\s*:\s*\{\s*"initial"\s*:\s*(\d+)',
            r'"price"\s*:\s*\{\s*"best"\s*:\s*(\d+)',
        ]
        
        # Look for initialPrice in JSON
        if not prices['initial_price']:
            for pattern in [r'"initialPrice"\s*:\s*(\d+)', r'"initial[Pp]rice"\s*:\s*["\']?\$?\s*(\d+)']:
                match = re.search(pattern, html_content)
                if match:
                    price_value = match.group(1)
                    # Format with comma if > 999
                    if len(price_value) > 3:
                        prices['initial_price'] = f"{price_value[:-3]},{price_value[-3:]}"
                    else:
                        prices['initial_price'] = price_value
                    break
        
        # Look for bestPrice in JSON
        if not prices['best_price']:
            for pattern in [r'"bestPrice"\s*:\s*(\d+)', r'"best[Pp]rice"\s*:\s*["\']?\$?\s*(\d+)']:
                match = re.search(pattern, html_content)
                if match:
                    price_value = match.group(1)
                    # Format with comma if > 999
                    if len(price_value) > 3:
                        prices['best_price'] = f"{price_value[:-3]},{price_value[-3:]}"
                    else:
                        prices['best_price'] = price_value
                    break
    
    # Method 3: Fallback patterns for del tags and other structures
    if not prices['initial_price']:
        fallback_initial = r'<del[^>]*>.*?Initial\s+price.*?\$\s*([\d,]+)'
        initial_match = re.search(fallback_initial, html_content, re.IGNORECASE | re.DOTALL)
        if initial_match:
            prices['initial_price'] = initial_match.group(1)
    
    if not prices['best_price']:
        fallback_best = r'Best\s+price\s*</span>\s*\$\s*([\d,]+)'
        best_match = re.search(fallback_best, html_content, re.IGNORECASE)
        if best_match:
            prices['best_price'] = best_match.group(1)
    
    return prices
For Lambda: Saves to S3 bucket specified in S3_BUCKET environment variable.
    For local: Saves to local filesystem.
    
    Args:
        result: Dictionary containing price data from fetch_club_med_prices
        csv_path: Path/key for the CSV file
        number_of_adults: Number of adults (default 2)
        number_of_kids: Number of kids (default 2)
    """
    # Get current date in Eastern Time
    eastern_tz = ZoneInfo('America/New_York')
    price_check_date = datetime.now(eastern_tz).strftime('%Y-%m-%d')
    
    # Extract price values (remove commas for CSV storage)
    initial_price = result.get('initial_price', '').replace(',', '') if result.get('initial_price') else ''
    best_price = result.get('best_price', '').replace(',', '') if result.get('best_price') else ''
    start_date = result.get('start_date', '')
    end_date = result.get('end_date', '')
    
    # Prepare new row
    new_row = {
        'price_check_date': price_check_date,
        'initial_price': initial_price,
        'best_price': best_price,
        'start_date': start_date,
        'end_date': end_date,
        'number_of_adults': number_of_adults,
        'number_of_kids': number_of_kids
    }
    
    fieldnames = ['price_check_date', 'initial_price', 'best_price', 'start_date', 
                  'end_date', 'number_of_adults', 'number_of_kids']
    
    # Check if we're in Lambda with S3
    s3_bucket = os.environ.get('S3_BUCKET')
    
    if S3_AVAILABLE and s3_bucket:
        # S3 mode (Lambda)
        save_to_s3(s3_bucket, csv_path, new_row, fieldnames)
    else:
        # Local file mode
        save_to_local_file(csv_path, new_row, fieldnames)


def save_to_s3(bucket: str, key: str, new_row: Dict, fieldnames: list) -> None:
    """Save CSV to S3, updating existing data if present."""
    rows = []
    
    try:
        # Try to get existing CSV from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        
        # Parse existing CSV
        reader = csv.DictReader(StringIO(csv_content))
        rows = list(reader)
    except s3_client.exceptions.NoSuchKey:
        # File doesn't exist yet, start fresh
        pass
    except Exception as e:
        print(f"Error reading from S3: {e}")
    
    # Update or append row
    date_exists = False
    for i, row in enumerate(rows):
        if row['price_check_date'] == new_row['price_check_date']:
            rows[i] = new_row
            date_exists = True
            break
    
    if not date_exists:
        rows.append(new_row)
    
    # Write back to S3
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=output.getvalue(),
        ContentType='text/csv',
        CacheControl='no-cache'
    )
    print(f"CSV saved to S3: s3://{bucket}/{key}")


def save_to_local_file(csv_path: str, new_row: Dict, fieldnames: list) -> None:
    """Save CSV to local filesystem."""
    file_exists = os.path.isfile(csv_path)
    
    if file_exists:
        # Read existing data
        rows = []
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
        
        # Update or append row
        date_exists = False
        for i, row in enumerate(rows):
            if row['price_check_date'] == new_row['price_check_date']
        rows = []
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
        
        # Update or append row
        date_exists = False
        for i, row in enumerate(rows):
            if row['price_check_date'] == price_check_date:
                rows[i] = new_row
                date_exists = True
                break
        
        if not date_exists:
            rows.append(new_row)
        
        # Write back to file
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    else:
        # Create new file
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow(new_row)


def fetch_with_playwright(url: str) -> str:
    """
    Fetch webpage content using Playwright (works better in AWS Lambda than Selenium).
    Install with: pip install playwright && playwright install chromium
    
    Args:
        url: The URL to fetch
        
    Returns:
        HTML content of the page after JavaScript execution
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            # Load the page
            page.goto(url, wait_until='domcontentloaded', timeout=45000)
            # Wait longer for dynamic price content to load
            page.wait_for_timeout(8000)
            
            html_content = page.content()
        finally:
            browser.close()
        return html_content


def fetch_club_med_prices(start_date: str, end_date: str, use_js_rendering: bool = True) -> Dict[str, Any]:
    """
    Fetch prices from Club Med Quebec Charlevoix website.
    Uses Playwright for JavaScript rendering if available, falls back to urllib.
    
    For AWS Lambda: Install playwright and use AWS Lambda Layer with Chromium.
    For FastAPI: Can run playwright in the background or use a task queue.
    
    Args:
        start_date: Start date in format YYYY-MM-DD (e.g., '2026-12-13')
        end_date: End date in format YYYY-MM-DD (e.g., '2026-12-19')
        use_js_rendering: Whether to use Playwright for JS rendering (default True)
        
    Returns:
        Dictionary containing initial_price, best_price, and metadata
    """
    base_url = "https://www.clubmed.ca/r/quebec-charlevoix/w"
    
    # Build query parameters
    params = {
        'adults': '2',
        'children': '2',
        'birthdates': ['2015-05-08', '2018-07-08'],
        'start_date': start_date,
        'end_date': end_date
    }
    
    # Manually build query string to handle multiple birthdates
    query_parts = [
        'adults=2',
        'children=2',
        'birthdates=2015-05-08',
        'birthdates=2018-07-08',
        f'start_date={start_date}',
        f'end_date={end_date}'
    ]
    query_string = '&'.join(query_parts)
    url = f"{base_url}?{query_string}"
    
    try:
        # Try Playwright first if available and requested
        if use_js_rendering and PLAYWRIGHT_AVAILABLE:
            html_content = fetch_with_playwright(url)
        else:
            # Fallback to urllib (limited - won't get JS-rendered content)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            req = urllib.request.Request(url, headers=headers)
            
            # Create SSL context
            # In production Lambda, you can remove the cert verification bypass
            ssl_context = ssl.create_default_context()
            # For local macOS testing (comment out for production):
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                # Handle gzip encoding
                content = response.read()
                if response.headers.get('Content-Encoding') == 'gzip':
                    html_content = gzip.decompress(content).decode('utf-8')
                else:
                    html_content = content.decode('utf-8')
        
        # Extract prices
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


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function to parse Club Med prices.
    
    Expected event format:
    {
        "start_date": "2026-12-13",
        "end_date": "2026-12-19"
    }
    
    Or via API Gateway with query parameters or body:
    {
        "queryStringParameters": {
            "start_date": "2026-12-13",
            "end_date": "2026-12-19"
        }
    }
    
    Returns:
    {
        "statusCodUse S3 in Lambda, local file otherwise
                csv_path = 'price_history.csv'
                save_to_csv(result, csv_path)
                result['csv_saved'] = True
                result['csv_location'] = f"s3://{os.environ.get('S3_BUCKET')}/{csv_path}" if os.environ.get('S3_BUCKET') else
        # Extract parameters from different event sources
        start_date = None
        end_date = None
        
        # Check if parameters are in the event body (direct Lambda invoke)
        if 'start_date' in event and 'end_date' in event:
            start_date = event['start_date']
            end_date = event['end_date']
        
        # Check if parameters are in queryStringParameters (API Gateway)
        elif 'queryStringParameters' in event and event['queryStringParameters']:
            start_date = event['queryStringParameters'].get('start_date')
            end_date = event['queryStringParameters'].get('end_date')
        
        # Check if parameters are in the body (API Gateway POST)
        elif 'body' in event and event['body']:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            start_date = body.get('start_date')
            end_date = body.get('end_date')
        
        # Validate parameters
        if not start_date or not end_date:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Missing required parameters: start_date and end_date (format: YYYY-MM-DD)'
                })
            }
        
        # Validate date format (basic validation)
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, start_date) or not re.match(date_pattern, end_date):
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD (e.g., 2026-12-13)'
                })
            }
        
        # Fetch prices
        result = fetch_club_med_prices(start_date, end_date)
        
        # Save to CSV if successful
        if result['success'] and result.get('initial_price') and result.get('best_price'):
            try:
                # For Lambda, use /tmp directory; for local use current directory
                csv_path = '/tmp/price_history.csv' if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') else 'price_history.csv'
                save_to_csv(result, csv_path)
                result['csv_saved'] = True
                result['csv_path'] = csv_path
            except Exception as csv_error:
                result['csv_saved'] = False
                result['csv_error'] = str(csv_error)
        
        status_code = 200 if result['success'] else 500
        
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': f'Lambda execution error: {str(e)}'
            })
        }


# For local testing
if __name__ == "__main__":
    # Test the function locally
    test_event = {
        'start_date': '2026-12-13',
        'end_date': '2026-12-19'
    }
    
    print("Testing price parser (no Selenium required)...")
    result = lambda_handler(test_event, None)
    response_body = json.loads(result['body'])
    print(json.dumps(response_body, indent=2))
    
    # Check CSV
    if response_body.get('csv_saved'):
        print(f"\nCSV saved to: {response_body['csv_path']}")
        try:
            with open('price_history.csv', 'r') as f:
                lines = f.readlines()
                print(f"Total records in CSV: {len(lines) - 1}")  # -1 for header
                if len(lines) > 1:
                    print(f"Latest entry: {lines[-1].strip()}")
        except Exception as e:
            print(f"Could not read CSV: {e}")
