## Use-Case Reference
https://www.reddit.com/r/DataHoarder/comments/1819tvk/how_to_download_all_files_from_a_private_telegram/

## Features

* Download all videos from a selected Telegram channel
* Supports private channels (if you have access)
* Automatically skips already downloaded files
* Uses `.env` for secure API credentials
* Rate-limit protection to avoid Telegram restrictions

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/AnKu-12/Telegram_video_download.git
cd Telegram_video_download
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Create `.env` File

Create a file named `.env` in the project root:

```
API_ID=your_api_id
API_HASH=your_api_hash
SESSION_NAME=my_session
DOWNLOAD_FOLDER=telegram_videos
```

---

## How to Get Telegram API Credentials

### Step-by-Step

1. Go to:
   https://my.telegram.org/auth

2. Login using your phone number
   (with country code, e.g., `+919876543210`)

3. Click **API development tools**
   *(Do NOT choose Bots)*

4. Fill the form:

   * **App title:** VideoDownloader
   * **Short name:** videodl
   * **URL:** localhost
   * **Platform:** Desktop
   * **Description:** Personal video downloader

5. Click **Create application**

You will get:

```
api_id: 12345678
api_hash: a1b2c3d4e5f6xxxxxxxxxxxxxxxx
```

Add these values to your `.env` file.

---

## Usage

Run the script:

```bash
python download_videos.py
```

Steps:

1. Login with your Telegram number (first time only)
2. Select the channel from the list
3. Videos will be downloaded automatically

---

## Output

Downloaded videos will be saved in:

```
./telegram_videos/
```


