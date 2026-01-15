# Price Change Email Notification Setup

This guide shows how to configure email notifications for price changes.

## How It Works

1. `site_price_parser.py` runs and updates `PriceMonitorFrontend/history.csv`
2. `price_change_notifier.py` automatically runs after the update
3. The notifier compares the last two CSV entries
4. If the `best_price` changed, it sends an email to your configured recipients

## Setup Instructions

### Step 1: Get Your Email Credentials

#### Option A: Gmail (Recommended)

1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or your device)
3. Google will generate a 16-character app password
4. Copy this password (you'll use it in `.env`)

**Note:** You need 2-Factor Authentication enabled on your Google account.

#### Option B: Other Email Providers

Check your email provider's documentation for app-specific passwords:
- **Outlook/Hotmail:** https://account.microsoft.com/account/manage-my-microsoft-account
- **Yahoo:** https://login.yahoo.com/account/security
- **Custom SMTP:** Contact your email provider for SMTP details

### Step 2: Configure .env File

Edit `.env` in the project root and add:

```env
# Your email address (the one sending notifications)
EMAIL_SENDER=your-email@gmail.com

# Your app-specific password (not your regular password!)
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx

# SMTP server settings (for Gmail, use these defaults)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Recipients (comma-separated, can be the same as sender or others)
PRICE_ALERT_EMAILS=your-email@gmail.com,friend@gmail.com
```

### Step 3: Test the Notifier

Run the price parser to test:

```bash
cd /Users/tange/Documents/vscodeProjects/ResortPriceMonitor
source .venv/bin/activate
python3 PriceParser/site_price_parser.py
```

You should see output like:
```
============================================================
CHECKING FOR PRICE CHANGES...
============================================================
Comparing: 2026-01-15 ($7443) vs 2026-01-16 ($7443)
✅ No price changes detected
```

Or if there's a change:
```
🚨 Price change detected!
   Previous best price: $7443
   New best price: $7200
   Change: $-243

Sending email to 1 recipient(s)...
✅ Email sent successfully to: your-email@gmail.com
```

### Step 4: Automatic Daily Runs

The `site_price_parser.py` now automatically runs at **7:00 PM EST** via:
- **Local:** macOS launchd (if you set it up)
- **Cloud:** AWS EventBridge (when deployed)

Both will trigger the email notifier automatically.

## Email Notification Format

You'll receive an HTML email with:
- ✅ Trip dates (check-in/check-out)
- ✅ Side-by-side price comparison
- ✅ Price change amount (UP ⬆️ or DOWN ⬇️)
- ✅ Direct link to your monitoring dashboard

Example:

```
🚨 Price Alert: Resort Price Changed on 2026-01-16

Trip Details
Check-in: 2026-12-13
Check-out: 2026-12-19

Price Comparison
Date          Best Price    Initial Price
2026-01-15    $7,443        $14,682
2026-01-16    $7,200        $14,200

📉 DOWN by $243
Change: $-243
```

## Troubleshooting

### ❌ "EMAIL_SENDER or EMAIL_PASSWORD not configured"
- Make sure both values are set in `.env`
- Don't use quotes around the values

### ❌ "SMTP authentication failed"
- Double-check your password/app-specific password
- Make sure you copied the full 16-character string (including spaces)
- For Gmail: Ensure 2-Factor Authentication is enabled

### ❌ "No email recipients configured"
- Check that `PRICE_ALERT_EMAILS` is set in `.env`
- Use comma-separated emails with no spaces: `email1@gmail.com,email2@gmail.com`

### ❌ Email arrives in spam
- This is common for automated emails
- Add the sender email to your contacts to improve delivery
- Check spam/junk folder

### ❌ "No price changes detected" every time
- This is normal! Only sends email when price actually changes
- The prices must be different from the previous day
- Check your CSV file to verify new data is being added

## Environment Variables Reference

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `EMAIL_SENDER` | No | your@gmail.com | Email address to send FROM |
| `EMAIL_PASSWORD` | No | xxxx xxxx xxxx xxxx | App-specific password (Gmail: 16 chars with spaces) |
| `SMTP_SERVER` | No | smtp.gmail.com | SMTP server address |
| `SMTP_PORT` | No | 587 | SMTP port (usually 587 for TLS) |
| `PRICE_ALERT_EMAILS` | No | email1@gmail.com,email2@gmail.com | Recipient emails, comma-separated |

## Testing Manually

To test without waiting for schedule:

```bash
# Run price parser (updates CSV)
python3 PriceParser/site_price_parser.py

# Run notifier directly
python3 PriceParser/price_change_notifier.py
```

## Disabling Notifications

To disable email notifications:
- Comment out or remove `PRICE_ALERT_EMAILS` from `.env`
- The notifier will skip silently

## Questions?

Check the `.env` file for detailed comments and examples.
