import os
import json
import asyncio
import importlib
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo
from telethon.tl.functions.channels import GetFullChannelRequest
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "my_session")
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER", "telegram_videos")

BATCH_SIZE = 50

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


def sanitize_folder_name(name: str) -> str:
    invalid_chars = r'\/:*?"<>|'
    for ch in invalid_chars:
        name = name.replace(ch, "_")
    return name.strip() or "unnamed"


def get_progress_file(folder_path: str) -> str:
    return os.path.join(folder_path, ".download_progress.json")


def load_progress(folder_path: str) -> dict:
    progress_file = get_progress_file(folder_path)
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return json.load(f)
    return {"downloaded_files": [], "last_message_id": None, "total_downloaded": 0}


def save_progress(folder_path: str, progress: dict):
    progress_file = get_progress_file(folder_path)
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)


def get_forum_topics_request_class():
    locations = [
        ("telethon.tl.functions.channels", "GetForumTopicsRequest"),
        ("telethon.tl.functions.messages", "GetForumTopicsRequest"),
        ("telethon.tl.functions", "GetForumTopicsRequest"),
    ]
    for module_path, class_name in locations:
        try:
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name, None)
            if cls:
                return cls
        except Exception:
            continue
    return None


async def force_refresh_channel(channel):
    try:
        await client(GetFullChannelRequest(channel))
        print("  ✅ Channel cache refreshed from server.")
    except Exception as e:
        print(f"  ⚠️  Could not refresh channel cache: {e}")


async def get_topics(channel) -> dict:
    GetForumTopicsRequest = get_forum_topics_request_class()
    if GetForumTopicsRequest is None:
        print("  ℹ️  Topics not supported in this Telethon version — treating as regular channel.")
        return {0: None}
    try:
        full = await client(
            GetForumTopicsRequest(
                channel=channel,
                offset_date=0,
                offset_id=0,
                offset_topic=0,
                limit=100,
            )
        )
        return {topic.id: topic.title for topic in full.topics}
    except Exception:
        return {0: None}


async def count_videos_in_topic(channel, topic_id: int = 0) -> int:
    kwargs = {"filter": InputMessagesFilterVideo()}
    if topic_id != 0:
        kwargs["reply_to"] = topic_id
    count = 0
    async for _ in client.iter_messages(channel, **kwargs):
        count += 1
    return count


async def find_message_id_by_filename(channel, target_filename: str, topic_id: int = 0):
    print(f"\n🔍 Searching for '{target_filename}'...")
    kwargs = {"filter": InputMessagesFilterVideo()}
    if topic_id != 0:
        kwargs["reply_to"] = topic_id

    async for message in client.iter_messages(channel, **kwargs):
        if message.video:
            filename = (message.file.name if message.file and message.file.name
                        else f"video_{message.id}.mp4")
            if filename == target_filename:
                print(f"  ✅ Found at message ID: {message.id}")
                return message.id

    print(f"  ❌ Could not find '{target_filename}'. Starting from the beginning.")
    return None


async def download_videos_for_topic(channel, topic_id, folder_path, start_from_message_id=None):
    os.makedirs(folder_path, exist_ok=True)
    progress = load_progress(folder_path)
    downloaded_files = set(progress.get("downloaded_files", []))

    batch_count = 0

    # KEY FIX: Always use reverse=True (oldest → newest).
    # To resume, use min_id so messages OLDER than last saved are skipped.
    # min_id = last_message_id means "only fetch messages with ID > last_message_id"
    kwargs = {
        "filter": InputMessagesFilterVideo(),
        "reverse": True,  # oldest → newest, always
    }

    if topic_id != 0:
        kwargs["reply_to"] = topic_id

    if start_from_message_id:
        # min_id tells Telethon: skip everything with ID <= start_from_message_id
        # This resumes AFTER the last downloaded video
        kwargs["min_id"] = start_from_message_id
        print(f"   ⏩ Skipping messages up to ID {start_from_message_id}, fetching newer ones...")

    async for message in client.iter_messages(channel, **kwargs):
        if batch_count >= BATCH_SIZE:
            print(f"\n⏸  Batch limit of {BATCH_SIZE} videos reached. Run again to continue.")
            break

        if message.video:
            filename = (message.file.name if message.file and message.file.name
                        else f"video_{message.id}.mp4")
            filepath = os.path.join(folder_path, filename)

            # Skip already downloaded (safety check)
            if filename in downloaded_files or os.path.exists(filepath):
                print(f"  ✓ Already exists: {filename} — skipping")
                if filename not in downloaded_files:
                    downloaded_files.add(filename)
                    progress["downloaded_files"] = list(downloaded_files)
                    progress["last_message_id"] = message.id
                    save_progress(folder_path, progress)
                continue

            batch_count += 1
            print(f"\n  ↓ [{batch_count}/{BATCH_SIZE}] Downloading: {filename}  (msg_id={message.id})")

            try:
                await message.download_media(file=filepath)
                print(f"  ✅ Saved: {filename}")

                # Save progress immediately after each download (crash-safe)
                downloaded_files.add(filename)
                progress["downloaded_files"] = list(downloaded_files)
                progress["last_message_id"] = message.id
                progress["total_downloaded"] = progress.get("total_downloaded", 0) + 1
                save_progress(folder_path, progress)

            except Exception as e:
                print(f"  ❌ Failed: {e}")

            await asyncio.sleep(0.5)

    return batch_count


async def main():
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

    async with client:
        print("Getting your channels...\n")

        dialogs = await client.get_dialogs(ignore_migrated=True)
        channels = [d for d in dialogs if d.is_channel]

        print("Your channels:")
        print("-" * 50)
        for i, ch in enumerate(channels, 1):
            name = ch.name or "Unnamed"
            cid = ch.entity.id
            print(f"{i}. {name}  (ID: -100{cid})")
        print("-" * 50)

        choice = int(input("\nEnter channel number to download from: ")) - 1
        target_channel = channels[choice].entity

        channel_folder = os.path.join(
            DOWNLOAD_FOLDER, sanitize_folder_name(target_channel.title)
        )

        print(f"\n🔄 Refreshing channel data from Telegram servers...")
        await force_refresh_channel(target_channel)

        print(f"\n📥 Fetching topics from: {target_channel.title}\n")
        topics = await get_topics(target_channel)

        print("🔢 Counting total videos (fresh from server)...")
        if len(topics) > 1 or (len(topics) == 1 and 0 not in topics):
            for topic_id, topic_title in topics.items():
                count = await count_videos_in_topic(target_channel, topic_id)
                print(f"   📂 Topic '{topic_title}': {count} video(s) found")
        else:
            count = await count_videos_in_topic(target_channel)
            print(f"   📹 Total videos found: {count}")

        print("\n" + "=" * 50)
        print("📌 WHERE DO YOU WANT TO START?")
        print("=" * 50)
        print("  1. Auto-resume from last saved progress (or from beginning if first run)")
        print("  2. Start from a specific video filename")
        start_choice = input("\nEnter 1 or 2: ").strip()

        custom_start_filename = None
        if start_choice == "2":
            custom_start_filename = input("Enter the exact video filename (e.g. video_12345.mp4): ").strip()

        print("=" * 50 + "\n")

        total_downloaded = 0

        # Forum channel with topics
        if len(topics) > 1 or (len(topics) == 1 and 0 not in topics):
            print(f"📂 Found {len(topics)} topic(s):\n")
            for tid, title in topics.items():
                print(f"  🗂  [{tid}] {title}")
            print()

            for topic_id, topic_title in topics.items():
                safe_title = sanitize_folder_name(topic_title)
                topic_folder = os.path.join(channel_folder, safe_title)

                print(f"\n── Topic: {topic_title} ──")
                print(f"   Saving to: {topic_folder}")

                start_msg_id = None
                if custom_start_filename:
                    start_msg_id = await find_message_id_by_filename(
                        target_channel, custom_start_filename, topic_id
                    )
                else:
                    prog = load_progress(topic_folder)
                    if prog.get("last_message_id"):
                        print(f"   🔁 Resuming after message ID: {prog['last_message_id']}")
                        start_msg_id = prog["last_message_id"]

                downloaded = await download_videos_for_topic(
                    target_channel, topic_id, topic_folder, start_msg_id
                )
                total_downloaded += downloaded
                print(f"   ✅ {downloaded} video(s) downloaded in this batch")

        # Regular channel (no topics)
        else:
            print("No topics found — downloading from the whole channel.\n")

            start_msg_id = None
            if custom_start_filename:
                start_msg_id = await find_message_id_by_filename(
                    target_channel, custom_start_filename
                )
            else:
                prog = load_progress(channel_folder)
                if prog.get("last_message_id"):
                    print(f"🔁 Resuming after message ID: {prog['last_message_id']}")
                    start_msg_id = prog["last_message_id"]

            downloaded = await download_videos_for_topic(
                target_channel, 0, channel_folder, start_msg_id
            )
            total_downloaded += downloaded

        print(f"\n✅ Batch done! Videos downloaded this run: {total_downloaded}")
        print(f"📁 Saved under: ./{channel_folder}/")
        print(f"\n💡 Run the script again to download the next {BATCH_SIZE} videos.")
        print(f"   It will auto-resume from where it left off (Option 1).")


if __name__ == "__main__":
    client.loop.run_until_complete(main())