# Arduino / ESP32 Daily YouTube Shorts Automation (100% Local & VPS)

Zero-cost (`$0/video`), **no APIs, no Composio, no Google Cloud Console**:
- Renders `1080×1920` (`9:16`) animated Arduino & ESP32 Shorts locally (`edge-tts` + Pillow + FFmpeg).
- Uses a persistent browser session (`browser_profile/`) to upload directly to **YouTube Studio** (Microsoft Edge on Windows, Chromium on Linux VPS).

## Windows Quick Start
1. Double-click `launch_ui.bat` (or run `python app.py`).
2. Click **1. Install Dependencies**.
3. Click **2. Sign In to YouTube** (logs in once and saves `browser_profile/`).
4. Click **4. Render & Upload Now** (or **5. Schedule Daily 8 PM**).

## Hostinger KVM 2 (Ubuntu/Debian) Quick Start
```bash
git clone https://github.com/kumhartechsolutions-creator/yt-shorts-automation.git /opt/yt-shorts-automation
cd /opt/yt-shorts-automation
chmod +x deploy_kvm2.sh
./deploy_kvm2.sh
```
Optional Web Dashboard (`http://YOUR_VPS_IP:8080`):
```bash
nohup /opt/yt-shorts-automation/.venv/bin/python /opt/yt-shorts-automation/web_ui.py > /opt/yt-shorts-automation/webui.log 2>&1 &
```
