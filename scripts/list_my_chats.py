"""Output list of user's channels and groups as JSON (for selection without link)."""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load_config, SESSION_PATH, get_api_credentials, fix_stdout_encoding
fix_stdout_encoding()

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat


def _peer_id(entity):
    if isinstance(entity, Channel):
        return -1000000000000 - entity.id if entity.id > 0 else entity.id
    if isinstance(entity, Chat):
        return -entity.id
    return None


async def main(channel_only=False, group_only=False):
    api_id, api_hash = get_api_credentials()
    if not api_id or not api_hash:
        print(json.dumps({"error": "No API credentials"}), file=sys.stderr)
        sys.exit(1)
    client = TelegramClient(SESSION_PATH, api_id, api_hash)
    try:
        await client.start()
    except Exception:
        print(json.dumps({"error": "Not authorized"}), file=sys.stderr)
        sys.exit(1)
    out = []
    try:
        async for d in client.iter_dialogs():
            e = d.entity
            if channel_only:
                if not isinstance(e, Channel) or not getattr(e, "broadcast", False):
                    continue
            elif group_only:
                if isinstance(e, Chat):
                    pass
                elif isinstance(e, Channel) and getattr(e, "megagroup", False):
                    pass
                else:
                    continue
            else:
                if isinstance(e, Chat):
                    pass
                elif isinstance(e, Channel) and (getattr(e, "broadcast", False) or getattr(e, "megagroup", False)):
                    pass
                else:
                    continue
            pid = _peer_id(e)
            if pid is None:
                continue
            title = getattr(e, "title", None) or d.name or ""
            username = getattr(e, "username", None)
            out.append({
                "title": title,
                "username": ("@" + username) if username else None,
                "peer_id": pid,
            })
    finally:
        await client.disconnect()
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--channels", action="store_true", help="Only channels")
    p.add_argument("--groups", action="store_true", help="Only groups")
    args = p.parse_args()
    asyncio.run(main(channel_only=args.channels, group_only=args.groups))
