"""Массовая рассылка в личку участникам канала/группы."""
import re
import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load_config, SESSION_PATH, get_api_credentials, write_progress, fix_stdout_encoding
fix_stdout_encoding()

from telethon import TelegramClient
from telethon.errors import FloodWaitError, UserIsBlockedError, InputUserDeactivatedError
from telethon.tl.functions.messages import ImportChatInviteRequest


def get_invite_hash(link: str):
    match = re.search(r'(?:joinchat/|\+)([A-Za-z0-9_-]+)', link.strip())
    return match.group(1) if match else None


async def run_mass_send(source: str, message: str, delay_sec: float = 2.0):
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
    print("Authorization OK!")
    entity = source
    invite_hash = get_invite_hash(source)
    if invite_hash:
        try:
            updates = await client(ImportChatInviteRequest(invite_hash))
            if hasattr(updates, 'chats') and updates.chats:
                entity = updates.chats[0]
            elif hasattr(updates, 'chat'):
                entity = updates.chat
            else:
                entity = updates
        except Exception as e:
            if "already" in str(e).lower() or "participant" in str(e).lower():
                entity = await client.get_entity(source)
            else:
                raise
    print("Getting participants...")
    write_progress("send", 0, 0)
    users = []
    async for user in client.iter_participants(entity, aggressive=True):
        if user.bot or user.deleted:
            continue
        if not getattr(user, 'id', None):
            continue
        users.append(user)
    total = len(users)
    print(f"Sending to {total} users (delay {delay_sec}s between messages)...")
    sent = 0
    for i, user in enumerate(users):
        try:
            await client.send_message(user.id, message)
            sent += 1
            write_progress("send", sent, total)
            print(f"   Sent: {sent}/{total}", end="\r")
            await asyncio.sleep(delay_sec)
        except FloodWaitError as e:
            print(f"\n   FloodWait {e.seconds}s...")
            await asyncio.sleep(e.seconds + 2)
        except (UserIsBlockedError, InputUserDeactivatedError):
            pass
        except Exception as e:
            print(f"\n   Skip {user.id}: {e}")
    print(f"\n\nDone! Sent to {sent}/{total} users.")
    await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--message", default="")
    parser.add_argument("--message-file", default="")
    parser.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()
    msg = args.message
    if args.message_file and os.path.exists(args.message_file):
        with open(args.message_file, "r", encoding="utf-8") as f:
            msg = f.read()
    if not msg:
        print("Error: message is empty.")
        sys.exit(1)
    asyncio.run(run_mass_send(args.source, msg, args.delay))
