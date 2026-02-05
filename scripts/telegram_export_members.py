"""Экспорт подписчиков канала/чата."""
import re
import asyncio
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load_config, SESSION_PATH, get_api_credentials, write_progress

from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest


def get_invite_hash(link: str):
    match = re.search(r'(?:joinchat/|\+)([A-Za-z0-9_-]+)', link.strip())
    return match.group(1) if match else None


async def run_export(source: str, output_file: str, fmt: str = "simple", include_bots: bool = False):
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
        print("Joining via invite link...")
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
    print("Getting members...")
    write_progress("export", 0, 0)
    members = []
    n = 0
    async for user in client.iter_participants(entity, aggressive=True):
        if user.deleted or (user.bot and not include_bots):
            continue
        n += 1
        write_progress("export", n, 0)
        name = (user.first_name or "") + (" " + (user.last_name or "") if user.last_name else "")
        username = user.username or ""
        if fmt == "csv":
            members.append(f"{user.id};{name};{username}")
        elif fmt == "username":
            if username:
                members.append(f"@{username}")
        else:
            members.append(f"{user.id} | {name}{' @' + username if username else ''}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(members))
    print(f"\nDone! Saved {len(members)} members to {output_file}")
    await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default="members.txt")
    parser.add_argument("--format", choices=["simple", "csv", "username"], default="simple")
    parser.add_argument("--include-bots", action="store_true")
    args = parser.parse_args()
    asyncio.run(run_export(args.source, args.output, args.format, args.include_bots))
