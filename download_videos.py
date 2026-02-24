import os
import asyncio
from telethon import TelegramClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "my_session")
DOWNLOAD_FOLDER = os.getenv("DOWNLOAD_FOLDER", "telegram_videos")

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def main():
    os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

    async with client:
        print("Getting your channels...\n")

        dialogs = await client.get_dialogs()
        channels = [d for d in dialogs if d.is_channel]

        print("Your channels:")
        print("-" * 50)
        for i, channel in enumerate(channels, 1):
            name = channel.name or "Unnamed"
            cid = channel.entity.id
            print(f"{i}. {name}")
            print(f"   ID: -100{cid}")
            print("-" * 50)

        choice = int(input("\nEnter channel number to download from: ")) - 1
        target_channel = channels[choice].entity

        print(f"\n📥 Downloading videos from: {target_channel.title}\n")

        count = 0

        async for message in client.iter_messages(target_channel):
            if message.video:
                count += 1

                # Filename
                if message.file and message.file.name:
                    filename = message.file.name
                else:
                    filename = f"video_{message.id}.mp4"

                filepath = os.path.join(DOWNLOAD_FOLDER, filename)

                if os.path.exists(filepath):
                    print(f"✓ Already exists: {filename}")
                    continue

                print(f"↓ [{count}] Downloading: {filename}")
                await message.download_media(file=filepath)
                print(f"✓ Saved: {filename}\n")

                await asyncio.sleep(0.5)

        print(f"\n✅ Done! Downloaded {count} videos to ./{DOWNLOAD_FOLDER}/")


if __name__ == "__main__":
    client.loop.run_until_complete(main())