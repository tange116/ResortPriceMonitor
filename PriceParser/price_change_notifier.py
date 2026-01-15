"""
Price Change Notifier - Sends email alerts when prices change

This script:
1. Compares the latest two CSV entries
2. Detects if the best_price changed
3. Sends email notification to configured recipients
"""

import os
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


def load_env_file():
    """Load .env file from project root."""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def get_csv_path() -> Path:
    """Get the path to history.csv in PriceMonitorFrontend directory."""
    script_dir = Path(__file__).parent
    csv_path = script_dir.parent / 'PriceMonitorFrontend' / 'history.csv'
    return csv_path


def read_csv_entries() -> List[Dict]:
    """Read all entries from CSV file."""
    csv_path = get_csv_path()
    entries = []
    
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            entries = list(reader)
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    return entries


def detect_price_change(entries: List[Dict]) -> Optional[Dict]:
    """
    Compare last two entries to detect price changes.
    
    Returns: dict with change details or None if no change
    """
    if len(entries) < 2:
        print("Not enough entries to compare")
        return None
    
    latest = entries[-1]
    previous = entries[-2]
    
    latest_date = latest.get('price_check_date')
    previous_date = previous.get('price_check_date')
    latest_best = latest.get('best_price')
    previous_best = previous.get('best_price')
    
    print(f"Comparing: {previous_date} (${previous_best}) vs {latest_date} (${latest_best})")
    
    if latest_best != previous_best:
        return {
            'changed': True,
            'previous_date': previous_date,
            'previous_best_price': previous_best,
            'previous_initial_price': previous.get('initial_price'),
            'latest_date': latest_date,
            'latest_best_price': latest_best,
            'latest_initial_price': latest.get('initial_price'),
            'start_date': latest.get('start_date'),
            'end_date': latest.get('end_date'),
            'price_difference': int(latest_best) - int(previous_best) if latest_best.isdigit() and previous_best.isdigit() else 0
        }
    
    return None


def send_email_notification(change_info: Dict, recipient_list: List[str]) -> bool:
    """
    Send email notification about price change.
    
    Args:
        change_info: Dict with price change details
        recipient_list: List of email addresses
    
    Returns: True if successful, False otherwise
    """
    if not recipient_list:
        print("No email recipients configured")
        return False
    
    # Email configuration from environment
    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    if not sender_email or not sender_password:
        print("❌ EMAIL_SENDER or EMAIL_PASSWORD not configured in .env")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 Price Alert: Resort Price Changed on {change_info['latest_date']}"
        msg['From'] = sender_email
        msg['To'] = ', '.join(recipient_list)
        
        # Calculate price change
        price_diff = change_info['price_difference']
        price_change_text = f"📈 UP by ${abs(price_diff)}" if price_diff > 0 else f"📉 DOWN by ${abs(price_diff)}"
        
        # Create HTML email body
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2 style="color: #d32f2f;">🚨 Price Alert: Resort Price Changed</h2>
                
                <h3 style="color: #1976d2;">Trip Details</h3>
                <p><strong>Check-in:</strong> {change_info['start_date']}</p>
                <p><strong>Check-out:</strong> {change_info['end_date']}</p>
                
                <h3 style="color: #1976d2;">Price Comparison</h3>
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background-color: #f5f5f5;">
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Date</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Best Price</th>
                        <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Initial Price</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 10px;">{change_info['previous_date']}</td>
                        <td style="border: 1px solid #ddd; padding: 10px;">${change_info['previous_best_price']}</td>
                        <td style="border: 1px solid #ddd; padding: 10px;">${change_info['previous_initial_price']}</td>
                    </tr>
                    <tr style="background-color: #fff3cd;">
                        <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">{change_info['latest_date']}</td>
                        <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">${change_info['latest_best_price']}</td>
                        <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">${change_info['latest_initial_price']}</td>
                    </tr>
                </table>
                
                <h3 style="color: #1976d2;">{price_change_text}</h3>
                <p style="font-size: 18px; color: #d32f2f;"><strong>${abs(price_diff)} change</strong></p>
                
                <hr style="margin: 20px 0;">
                <p style="color: #666; font-size: 12px;">
                    This is an automated notification from Resort Price Monitor.<br>
                    Check <a href="https://p-monitor-rho.vercel.app/">https://p-monitor-rho.vercel.app/</a> for full details.
                </p>
            </body>
        </html>
        """
        
        # Create plain text version
        text = f"""
Price Alert: Resort Price Changed on {change_info['latest_date']}

Trip Details:
Check-in: {change_info['start_date']}
Check-out: {change_info['end_date']}

Price Comparison:
{change_info['previous_date']}: ${change_info['previous_best_price']} (best) / ${change_info['previous_initial_price']} (initial)
{change_info['latest_date']}: ${change_info['latest_best_price']} (best) / ${change_info['latest_initial_price']} (initial)

{price_change_text}
Change: ${abs(price_diff)}

---
Resort Price Monitor: https://p-monitor-rho.vercel.app/
        """
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        print(f"Sending email to {len(recipient_list)} recipient(s)...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_list, msg.as_string())
        
        print(f"✅ Email sent successfully to: {', '.join(recipient_list)}")
        return True
    
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


def main():
    """Main entry point for price change notifier."""
    load_env_file()
    
    print("=" * 60)
    print("PRICE CHANGE NOTIFIER")
    print("=" * 60)
    
    # Get email list from environment
    email_list_str = os.getenv('PRICE_ALERT_EMAILS', '')
    recipient_list = [e.strip() for e in email_list_str.split(',') if e.strip()]
    
    if not recipient_list:
        print("⏭️  No email recipients configured (PRICE_ALERT_EMAILS in .env)")
        return
    
    # Read CSV entries
    entries = read_csv_entries()
    if not entries:
        print("❌ No entries found in CSV")
        return
    
    # Detect price changes
    change_info = detect_price_change(entries)
    if not change_info:
        print("✅ No price changes detected")
        return
    
    print(f"\n🚨 Price change detected!")
    print(f"   Previous best price: ${change_info['previous_best_price']}")
    print(f"   New best price: ${change_info['latest_best_price']}")
    print(f"   Change: ${change_info['price_difference']}")
    
    # Send notifications
    send_email_notification(change_info, recipient_list)
    print("=" * 60)


if __name__ == "__main__":
    main()
