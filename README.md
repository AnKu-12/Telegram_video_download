Features

Download all videos from a selected Telegram channel

Supports private channels (if you have access)

Automatically skips already downloaded files

Uses .env for secure API credentials

Rate-limit protection to avoid Telegram restrictions


Setup
1. Clone the repository
git clone https://github.com/your-username/telegram-video-downloader.git
cd telegram-video-downloader
2. Install dependencies
pip install -r requirements.txt
3. Create .env file

Create a .env file in the project root:

API_ID=your_api_id
API_HASH=your_api_hash
SESSION_NAME=my_session
DOWNLOAD_FOLDER=telegram_videos



Step-by-Step: Get Correct Credentials
Go to: https://my.telegram.org/auth
Login with your phone number (with country code, e.g., +919876543210)
Click "API development tools" (NOT "Bots")
Fill the form:
App title: VideoDownloader (or anything)
Short name: videodl (lowercase, no spaces)
URL: localhost
Platform: Desktop
Description: Personal video downloader
Click "Create application"
You'll see this:
plain
Copy
App configuration

App api_id: 12345678          ← 8 digits, NUMBERS ONLY
App api_hash: a1b2c3d4e5f6...  ← 32 characters, WITH QUOTES in code