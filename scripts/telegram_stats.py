"""Статистика канала или группы."""
import re
import asyncio
import argparse
import sys
import os
import traceback
from datetime import datetime, timedelta
from collections import defaultdict

# Фикс кодировки на Windows (emoji, кириллица и т.д.)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load_config, SESSION_PATH, get_api_credentials

from telethon import TelegramClient
from telethon.tl.types import Channel, MessageService
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, GetFullChatRequest


def get_invite_hash(link: str):
    match = re.search(r'(?:joinchat/|\+)([A-Za-z0-9_-]+)', link.strip())
    return match.group(1) if match else None


async def run_stats(source: str, output_file: str = ""):
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
    entity = await client.get_entity(entity)
    title = getattr(entity, 'title', None) or getattr(entity, 'username', '') or str(entity.id)
    stats = {"title": title, "type": "", "participants": 0, "online": 0, "admins": 0, "messages_24h": 0}
    if hasattr(entity, 'broadcast') and entity.broadcast:
        stats["type"] = "channel"
        full = await client(GetFullChannelRequest(entity))
        fc = full.full_chat
        stats["participants"] = getattr(fc, 'participants_count', 0) or 0
        stats["online"] = getattr(fc, 'online_count', 0) or 0
        stats["admins"] = getattr(fc, 'admins_count', 0) or 0
        if hasattr(fc, 'pts'):
            stats["pts"] = fc.pts
    else:
        stats["type"] = "group"
        try:
            if isinstance(entity, Channel):
                full = await client(GetFullChannelRequest(entity))
                fc = full.full_chat
                stats["participants"] = getattr(fc, 'participants_count', 0) or 0
                stats["online"] = getattr(fc, 'online_count', 0) or 0
                stats["admins"] = getattr(fc, 'admins_count', 0) or 0
            else:
                chat_id = getattr(entity, 'id', None)
                if chat_id is not None:
                    full = await client(GetFullChatRequest(chat_id))
                    fc = full.full_chat
                    p = getattr(fc, 'participants', None)
                    stats["participants"] = len(p.participants) if p and hasattr(p, 'participants') else 0
        except Exception as e:
            print(f"Warning: could not get full group info: {e}")

    # Avg views (channels) and posts per week
    stats["avg_views"] = None
    stats["posts_per_week"] = None
    limit = 300
    try:
        print("Analyzing recent posts...")
        views_list = []
        posts_by_week = defaultdict(int)
        count = 0
        async for msg in client.iter_messages(entity, limit=limit):
            if isinstance(msg, MessageService):
                continue
            count += 1
            v = getattr(msg, 'views', None)
            if v is not None and v > 0:
                views_list.append(v)
            if msg.date:
                week_key = msg.date.strftime("%Y-W%W")
                posts_by_week[week_key] += 1
        if views_list:
            stats["avg_views"] = round(sum(views_list) / len(views_list))
        if posts_by_week:
            total_posts = sum(posts_by_week.values())
            weeks = len(posts_by_week) or 1
            stats["posts_per_week"] = round(total_posts / weeks, 1)
    except Exception as e:
        print(f"  (stats skip: {e})")

    print("\n" + "=" * 40)
    print(f"  {title}")
    print("=" * 40)
    print(f"  Type: {stats['type']}")
    print(f"  Participants: {stats['participants']}")
    if stats.get('online'):
        print(f"  Online now: {stats['online']}")
    if stats.get('admins'):
        print(f"  Admins: {stats['admins']}")
    if stats.get('avg_views') is not None:
        print(f"  Avg views per post: {stats['avg_views']}")
    if stats.get('posts_per_week') is not None:
        print(f"  Avg posts per week: {stats['posts_per_week']}")
    print("=" * 40)
    text = f"Psylocyba Stats\n{'='*40}\n{title}\n{'='*40}\nType: {stats['type']}\nParticipants: {stats['participants']}\n"
    if stats.get('online'):
        text += f"Online: {stats['online']}\n"
    if stats.get('admins'):
        text += f"Admins: {stats['admins']}\n"
    if stats.get('avg_views') is not None:
        text += f"Avg views per post: {stats['avg_views']}\n"
    if stats.get('posts_per_week') is not None:
        text += f"Avg posts per week: {stats['posts_per_week']}\n"
    text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\nSaved to {output_file}")
    await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    try:
        asyncio.run(run_stats(args.source, args.output))
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
