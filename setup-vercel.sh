#!/bin/bash

# Price Monitor - Vercel Setup Script
# This script helps you deploy to Vercel with local scheduling

set -e

echo "🚀 Price Monitor - Vercel Setup"
echo "========================================="
echo ""

# Step 1: Update GitHub username
echo "Step 1: Update GitHub Username"
echo "------------------------------"
read -p "Enter your GitHub username: " github_username

# Update app.js with GitHub username
sed -i '' "s|YOUR_USERNAME|$github_username|g" PriceMonitorFrontend/app.js
echo "✅ Updated app.js with GitHub username: $github_username"
echo ""

# Step 2: Verify repository is on GitHub
echo "Step 2: Verify GitHub Remote"
echo "----------------------------"
git remote -v
echo ""
read -p "Is your origin pointing to GitHub? (y/n): " confirm
if [ "$confirm" != "y" ]; then
    echo "❌ Please setup GitHub remote first"
    exit 1
fi
echo "✅ GitHub remote verified"
echo ""

# Step 3: Setup SSH (if needed)
echo "Step 3: Setup SSH Key"
echo "--------------------"
if [ ! -f ~/.ssh/id_rsa ]; then
    echo "⚠️  No SSH key found. Generating..."
    ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""
    echo "✅ SSH key generated at ~/.ssh/id_rsa"
    echo ""
    echo "📋 Copy this and add to GitHub (https://github.com/settings/ssh/new):"
    cat ~/.ssh/id_rsa.pub
    echo ""
    read -p "Press Enter after adding SSH key to GitHub..."
else
    echo "✅ SSH key already exists"
fi
echo ""

# Step 4: Test SSH connection
echo "Step 4: Test SSH Connection"
echo "----------------------------"
ssh -T git@github.com || echo "⚠️  Could not verify SSH key (may already be added)"
echo ""

# Step 5: Switch to SSH remote
echo "Step 5: Configure Git SSH Remote"
echo "--------------------------------"
git remote set-url origin git@github.com:$github_username/DestinationPriceMonitor.git
echo "✅ Remote switched to SSH"
echo ""

# Step 6: Commit and push changes
echo "Step 6: Commit Changes"
echo "---------------------"
git add -A
git commit -m "Configure for Vercel deployment with GitHub CSV source"
git push
echo "✅ Changes pushed to GitHub"
echo ""

# Step 7: Setup local scheduler
echo "Step 7: Setup Local Scheduler"
echo "-----------------------------"
read -p "Setup launchd scheduler? (y/n): " setup_scheduler
if [ "$setup_scheduler" = "y" ]; then
    mkdir -p ~/Library/LaunchAgents
    
    # Create launchd plist
    cat > ~/Library/LaunchAgents/com.resort.pricemonitor.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.resort.pricemonitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor && /Users/tange/Documents/vscodeProjects/DestinationPriceMonitor/.venv/bin/python PriceParser/site_price_parser.py && git add PriceParser/history.csv && git commit -m "Update prices at \$(date)" && git push 2>&1 | tee -a /tmp/pricemonitor_output.log</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>12</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardErrorPath</key>
    <string>/tmp/pricemonitor_error.log</string>
    <key>StandardOutPath</key>
    <string>/tmp/pricemonitor_output.log</string>
</dict>
</plist>
EOF
    
    launchctl load ~/Library/LaunchAgents/com.resort.pricemonitor.plist
    echo "✅ Scheduler loaded (runs daily at 12:00 PM)"
    echo "   View logs: tail -f /tmp/pricemonitor_output.log"
else
    echo "⏭️  Skipping scheduler setup (you can do it manually later)"
fi
echo ""

# Step 8: Instructions for Vercel
echo "Step 8: Deploy to Vercel"
echo "------------------------"
echo ""
echo "📱 Next steps:"
echo "1. Go to https://vercel.com/signup"
echo "2. Sign up with GitHub account"
echo "3. Click 'Import Project'"
echo "4. Select 'DestinationPriceMonitor' repository"
echo "5. Vercel will auto-detect vercel.json"
echo "6. Click 'Deploy'"
echo ""
echo "✅ Your free domain will be: <project-name>.vercel.app"
echo ""

echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Your app will:"
echo "  • Run price scraper daily at 12:00 PM (via launchd)"
echo "  • Update CSV in GitHub"
echo "  • Display on Vercel with fresh data"
echo ""
echo "Cost: $0/month ✅"
echo ""
