# Quick Start: Deploy to Vercel

Get your Price Monitor price monitor live in 5 minutes.

## 1️⃣ Update GitHub Username

Edit `PriceMonitorFrontend/app.js` and replace `YOUR_USERNAME` with your actual GitHub username:

```bash
# Find and replace (macOS)
sed -i '' 's/YOUR_USERNAME/tange116/g' PriceMonitorFrontend/app.js

# Or manually edit line 3 in app.js
```

## 2️⃣ Push to GitHub

```bash
cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor

git add -A
git commit -m "Configure for Vercel deployment"
git push
```

## 3️⃣ Deploy to Vercel (2 minutes)

### Option A: Web Dashboard (Easiest)
1. Go to [vercel.com/signup](https://vercel.com/signup)
2. Sign up with GitHub
3. Click **"Import Project"**
4. Select **"DestinationPriceMonitor"**
5. Click **"Deploy"** (vercel.json is auto-detected)
6. Get your free domain: `your-project.vercel.app`

### Option B: CLI
```bash
npm install -g vercel
cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor
vercel
```

## 4️⃣ Setup Daily Updates (2 minutes)

### macOS launchd (Automatic)

```bash
mkdir -p ~/Library/LaunchAgents

# Create scheduler file
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
        <string>cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor && source .venv/bin/activate && python PriceParser/site_price_parser.py && git add PriceParser/price_history.csv && git commit -m "Update prices" && git push 2>&1 | tee -a /tmp/clubmed_run.log</string>
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

# Load the scheduler
launchctl load ~/Library/LaunchAgents/com.clubmed.pricemonitor.plist

# Verify it loaded
launchctl list | grep clubmed
```

### macOS cron (Alternative)

```bash
crontab -e

# Add this line (runs daily at 12:00 PM):
0 12 * * * cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor && source .venv/bin/activate && python PriceParser/site_price_parser.py && git add PriceParser/price_history.csv && git commit -m "Update prices" && git push 2>&1 >> /tmp/clubmed_run.log
```

## ✅ Verify Everything Works

### Test 1: Check launchd scheduler
```bash
launchctl list | grep clubmed  # Should show loaded job
tail -f /tmp/clubmed_output.log  # Watch for runs
```

### Test 2: Test CSV fetch from GitHub
```bash
curl -s https://raw.githubusercontent.com/YOUR_USERNAME/DestinationPriceMonitor/master/PriceParser/price_history.csv | tail -5
```

### Test 3: Visit your Vercel site
```
https://your-project.vercel.app
```
You should see the price chart loading!

### Test 4: Manual test of scraper
```bash
cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor
source .venv/bin/activate
python PriceParser/site_price_parser.py
tail PriceParser/price_history.csv  # Check latest entry
```

## 🎯 Your Workflow

1. **Daily at 12 PM**: launchd automatically:
   - ✅ Runs `site_price_parser.py` 
   - ✅ Updates `price_history.csv`
   - ✅ Commits to GitHub
   - ✅ Pushes changes

2. **Vercel dashboard**: 
   - ✅ Fetches latest CSV from GitHub
   - ✅ Displays on your domain
   - ✅ Free SSL/TLS

3. **Your users**:
   - ✅ See live price data
   - ✅ Beautiful chart visualization
   - ✅ Price statistics

## 💰 Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| Vercel | Free | 100GB bandwidth/month |
| GitHub | Free | Unlimited private repos |
| Local Mac | Free | Your computer runs the scraper |
| **Total** | **$0** | ✅ Zero cloud costs |

## 🆘 Troubleshooting

### "CSV not loading on Vercel"
- Verify GitHub username in app.js is correct
- Check: `curl https://raw.githubusercontent.com/YOUR_USERNAME/DestinationPriceMonitor/master/PriceParser/price_history.csv`
- Ensure file is committed to GitHub: `git log --name-only PriceParser/price_history.csv`

### "Scheduler not running"
```bash
# Check if loaded
launchctl list | grep clubmed

# View logs
tail /tmp/clubmed_error.log
tail /tmp/clubmed_output.log

# Reload if needed
launchctl unload ~/Library/LaunchAgents/com.clubmed.pricemonitor.plist
launchctl load ~/Library/LaunchAgents/com.clubmed.pricemonitor.plist
```

### "Python script errors when running via launchd"
- Always use full paths or `cd` to repo first
- Use `source .venv/bin/activate` to activate venv
- Check `/tmp/clubmed_error.log` for details

## 📚 More Help

- See [VERCEL_DEPLOYMENT.md](VERCEL_DEPLOYMENT.md) for detailed setup
- See [DATA_FRESHNESS.md](DATA_FRESHNESS.md) for architecture details
- See [README.md](README.md) for project overview

---

**That's it!** You now have a completely automated, free price monitoring system. 🎉
