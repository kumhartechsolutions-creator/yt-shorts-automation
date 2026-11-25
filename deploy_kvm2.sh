#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

sudo apt-get update
sudo apt-get install -y python3-venv python3-pip xvfb fonts-dejavu-core

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
sudo "$(pwd)/.venv/bin/playwright" install-deps chromium

# Register daily 8:00 PM IST (14:30 UTC) cron job
CRON_LINE="30 14 * * * cd $APP_DIR && $APP_DIR/.venv/bin/python run_daily.py >> $APP_DIR/cron.log 2>&1"
(crontab -l 2>/dev/null | grep -v "run_daily.py"; echo "$CRON_LINE") | crontab -

echo "Setup complete! Cron scheduled for 8:00 PM IST (14:30 UTC) daily."
echo "Next:"
echo "  1) Sign in once to YouTube Studio (copy browser_profile/ from Windows OR run: xvfb-run -a .venv/bin/python auth_youtube.py)"
echo "  2) Optional Web UI: .venv/bin/python web_ui.py  (http://YOUR_VPS_IP:8080)"
