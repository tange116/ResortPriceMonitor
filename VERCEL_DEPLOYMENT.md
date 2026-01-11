# Local Scheduling & Vercel Deployment Guide

## Architecture: Local + Vercel + GitHub

```
Your Mac
└─ Run Python daily (scheduled via cron or launchd)
   ├─ Updates: PriceParser/price_history.csv
   └─ Commits to GitHub

GitHub
└─ Stores CSV (versioned history)
   └─ Serves via raw.githubusercontent.com

Vercel
└─ Hosts Static Frontend
   ├─ Fetches CSV from GitHub
   └─ Free DNS: yourapp.vercel.app
```

---

## Part 1: Setup Local Scheduler (Mac)

### Option A: Using `launchd` (Recommended - Native Mac)

**1. Create scheduler script:**

```bash
mkdir -p ~/Library/LaunchAgents
cat > ~/Library/LaunchAgents/com.clubmed.pricemonitor.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.clubmed.pricemonitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor && /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor/.venv/bin/python PriceParser/site_price_parser.py && git add PriceParser/price_history.csv && git commit -m "Update prices at $(date)" && git push</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>12</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardErrorPath</key>
    <string>/tmp/clubmed_error.log</string>
    <key>StandardOutPath</key>
    <string>/tmp/clubmed_output.log</string>
</dict>
</plist>
EOF
```

**2. Load the scheduler:**

```bash
launchctl load ~/Library/LaunchAgents/com.clubmed.pricemonitor.plist
```

**3. Verify it's loaded:**

```bash
launchctl list | grep clubmed
```

**4. To unload (stop):**

```bash
launchctl unload ~/Library/LaunchAgents/com.clubmed.pricemonitor.plist
```

**5. View logs:**

```bash
tail -f /tmp/clubmed_output.log
tail -f /tmp/clubmed_error.log
```

---

### Option B: Using `cron` (Alternative)

**1. Edit crontab:**

```bash
crontab -e
```

**2. Add this line (runs at 12 PM daily):**

```cron
0 12 * * * cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor && /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor/.venv/bin/python PriceParser/site_price_parser.py && git add PriceParser/price_history.csv && git commit -m "Update prices" && git push 2>&1 | tee -a /tmp/clubmed_cron.log
```

**3. View scheduled jobs:**

```bash
crontab -l
```

---

## Part 2: Setup GitHub Push with SSH (Auto-commit)

For auto-push to work, configure SSH:

**1. Check for existing SSH key:**

```bash
ls -la ~/.ssh/id_rsa
```

**2. If not found, generate one:**

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
```

**3. Add SSH key to GitHub:**

```bash
cat ~/.ssh/id_rsa.pub
# Copy output and paste at: https://github.com/settings/ssh/new
```

**4. Test SSH connection:**

```bash
ssh -T git@github.com
```

**5. Configure Git to use SSH:**

```bash
cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor
git remote set-url origin git@github.com:YOUR_USERNAME/DestinationPriceMonitor.git
```

---

## Part 3: Deploy Frontend to Vercel

### Step 1: Update GitHub Username in app.js

**Edit:** [PriceMonitorFrontend/app.js](../PriceMonitorFrontend/app.js)

Replace `YOUR_USERNAME` with your actual GitHub username:

```javascript
// Before:
csvUrl: 'https://raw.githubusercontent.com/YOUR_USERNAME/DestinationPriceMonitor/master/PriceParser/price_history.csv',

// After (example):
csvUrl: 'https://raw.githubusercontent.com/tange116/DestinationPriceMonitor/master/PriceParser/price_history.csv',
```

### Step 2: Push Changes to GitHub

```bash
cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor
git add -A
git commit -m "Configure for Vercel deployment"
git push
```

### Step 3: Deploy to Vercel

**Option A: Via Vercel Web (Easiest)**

1. Go to https://vercel.com/signup (sign up with GitHub)
2. Click "Import Project"
3. Select your `DestinationPriceMonitor` repository
4. Vercel auto-detects `vercel.json` configuration
5. Click "Deploy"
6. Get your free domain: `your-project.vercel.app`

**Option B: Via Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor
vercel

# Follow prompts:
# - Confirm project scope
# - Set project name
# - Confirm settings
```

---

## Part 4: Test Everything

### Test Local Script

```bash
cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor/PriceParser
/Users/tange/Documents/vscodeProjects/DestinationPriceMonitor/.venv/bin/python site_price_parser.py
```

### Check CSV Updated

```bash
cat PriceParser/price_history.csv | tail -1
```

### Manually Push (Test)

```bash
git add PriceParser/price_history.csv
git commit -m "Test manual update"
git push
```

### Test Vercel Frontend

Visit: `https://your-project.vercel.app`

Should show your price history chart!

---

## Part 5: Monitoring & Troubleshooting

### Check Scheduler Logs

```bash
# launchd logs
tail -f /tmp/clubmed_output.log
tail -f /tmp/clubmed_error.log

# Or use macOS Console:
# Applications → Utilities → Console
# Search for "clubmed"
```

### Test CSV Fetch from GitHub

```bash
curl -L https://raw.githubusercontent.com/YOUR_USERNAME/DestinationPriceMonitor/master/PriceParser/price_history.csv
```

### Check if app.js has correct URL

```bash
grep "csvUrl" PriceMonitorFrontend/app.js
```

### Vercel Logs

```bash
vercel logs
```

---

## Part 6: Daily Workflow

**System is automatic!** Your Mac will:

1. **12:00 AM EST**: Scheduler triggers
2. **Runs script**: Fetches prices, updates CSV
3. **Auto-commits**: Pushes to GitHub
4. **Frontend updates**: Next page load fetches latest CSV
5. **You see fresh data**: On Vercel site!

---

## Customization

### Change Scheduler Time

**Edit launchd plist:**

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>0</integer>      <!-- 12 AM (midnight) EST -->
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

**Or edit crontab:**

```cron
0 0 * * *  # Change first number for time (0-23 hour)
```

---

## Cost Summary

- **Vercel**: Free tier (100 GB bandwidth, custom domain)
- **GitHub**: Free (public repo)
- **Your Mac**: Runs 24/7 (one small Python script daily)
- **Total Cost**: **$0/month** ✅

---

## Next Steps

1. ✅ Update `app.js` with your GitHub username
2. ✅ Push to GitHub
3. ✅ Deploy to Vercel
4. ✅ Setup scheduler on your Mac
5. ✅ Test by visiting Vercel domain

Done! Your price monitor is live! 🚀
