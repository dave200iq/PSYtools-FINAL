"""Клонирование Telegram-канала."""
import re
import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load_config, SESSION_PATH, get_api_credentials, write_progress

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import CreateChannelRequest, EditPhotoRequest, GetFullChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import InputChatUploadedPhoto, MessageService


def get_invite_hash(link: str):
    match = re.search(r'(?:joinchat/|\+)([A-Za-z0-9_-]+)', link.strip())
    return match.group(1) if match else None


async def get_source_entity(client, source):
    invite_hash = get_invite_hash(source)
    if invite_hash:
        try:
            updates = await client(ImportChatInviteRequest(invite_hash))
            if hasattr(updates, 'chats') and updates.chats:
                return updates.chats[0]
            if hasattr(updates, 'chat'):
                return updates.chat
        except Exception as e:
            if "already" in str(e).lower() or "participant" in str(e).lower():
                pass
    return await client.get_entity(source)


async def main(source: str, new_title: str):
    api_id, api_hash = get_api_credentials()
    if not api_id or not api_hash:
        print("Error: fill API ID and API Hash in settings.")
        return
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    try:
        await client.start()
    except Exception:
        phone = load_config().get("phone", "").strip()
        if not phone:
            phone = input("Phone (e.g. +79001234567): ").strip()
        await client.start(phone=phone if phone else None)
    print("\n1. Getting source channel...")
    source_entity = await get_source_entity(client, source)
    if not hasattr(source_entity, 'broadcast') or not source_entity.broadcast:
        print("Error: not a channel.")
        await client.disconnect()
        return
    full = await client(GetFullChannelRequest(source_entity))
    title = new_title or source_entity.title
    about = full.full_chat.about or ""
    print("\n2. Creating new channel...")
    created = await client(CreateChannelRequest(
        title=title, about=about, broadcast=True, megagroup=False))
    new_channel = created.chats[0]
    if full.full_chat.chat_photo:
        print("\n3. Copying avatar...")
        try:
            photo_path = await client.download_media(full.full_chat.chat_photo)
            if photo_path:
                uploaded = await client.upload_file(photo_path)
                await client(EditPhotoRequest(new_channel, InputChatUploadedPhoto(file=uploaded)))
        except Exception:
            pass
    print("\n4. Copying posts...")
    write_progress("collect", 0, 0)
    count = 0
    messages = []
    n = 0
    async for msg in client.iter_messages(source_entity, reverse=True):
        messages.append(msg)
        n += 1
        if n % 50 == 0:
            write_progress("collect", n, 0)
    total = len(messages)
    write_progress("copy", 0, total)
    for i, msg in enumerate(messages, 1):
        try:
            if isinstance(msg, MessageService):
                continue
            text = getattr(msg, 'message', None) or getattr(msg, 'text', None) or ""
            for attempt in range(5):
                try:
                    if msg.media:
                        await client.send_file(new_channel, msg.media, caption=text or None)
                    else:
                        await client.send_message(new_channel, text or "")
                    break
                except FloodWaitError as e:
                    wait = e.seconds + 2
                    print(f"\n   Pause {wait} sec...")
                    await asyncio.sleep(wait)
            count += 1
            write_progress("copy", count, total)
            print(f"   Copied: {count}/{len(messages)}", end="\r")
            await asyncio.sleep(1.5)
        except Exception as e:
            print(f"\n   Error post {i}: {e}")
    print(f"\n\nDone! Copied {count} posts.")
    await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--title", default="")
    args = parser.parse_args()
    asyncio.run(main(args.source, args.title))
