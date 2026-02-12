"""
Merge several groups into one clone. Chronological order, forum topics preserved.
Supports checkpoint/resume and configurable delay (anti-flood).
"""
import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load_config, SESSION_PATH, get_api_credentials, write_progress, fix_stdout_encoding
fix_stdout_encoding()

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import CreateChannelRequest, EditPhotoRequest, GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest, GetForumTopicsRequest, GetForumTopicsByIDRequest, CreateForumTopicRequest
from telethon.tl.types import InputChatUploadedPhoto, Channel, Chat, MessageService, MessageMediaWebPage

# Reuse helpers from clone_group
from telegram_clone_group import (
    get_source_entity,
    is_group,
    get_message_topic_id,
    get_all_forum_topics,
    get_topics_by_ids,
    GENERAL_TOPIC_ID,
)


def _peer_id(entity):
    if isinstance(entity, Channel):
        return -1000000000000 - entity.id if entity.id > 0 else entity.id
    if isinstance(entity, Chat):
        return -entity.id
    return None


def get_checkpoint_path():
    return Path(os.environ.get("TELEGRAM_APP_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / ".merge_checkpoint.json"


def load_checkpoint():
    p = get_checkpoint_path()
    if not p.exists():
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_checkpoint(data):
    p = get_checkpoint_path()
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


async def main(sources_str: str, new_title: str, delay_sec: float):
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

    # Parse sources: comma or newline
    raw = [s.strip() for s in sources_str.replace(",", "\n").split("\n") if s.strip()]
    if not raw:
        print("Error: provide at least one group (links or @username, comma/newline separated).")
        await client.disconnect()
        return

    print("\n1. Resolving source groups...")
    source_entities = []
    source_ids = []
    for s in raw:
        try:
            ent = await get_source_entity(client, s)
            if not is_group(ent):
                print(f"   Skip (not a group): {s}")
                continue
            pid = _peer_id(ent)
            if pid in source_ids:
                print(f"   Skip (duplicate): {s}")
                continue
            source_entities.append(ent)
            source_ids.append(pid)
            print(f"   OK: {getattr(ent, 'title', s)}")
        except Exception as e:
            print(f"   Error: {s} -> {e}")
            await client.disconnect()
            return

    if not source_entities:
        print("Error: no valid groups.")
        await client.disconnect()
        return

    checkpoint = load_checkpoint()
    new_group = None
    topic_mapping = {}  # key "src_pid:topic_id" -> new_topic_message_id
    copied_set = set()
    any_forum = False
    for ent in source_entities:
        if isinstance(ent, Channel) and getattr(ent, "forum", False):
            any_forum = True
            break

    if checkpoint and "target_peer_id" in checkpoint:
        # Resume
        try:
            target_id = checkpoint["target_peer_id"]
            if set(checkpoint.get("sources", [])) != set(source_ids):
                print("Error: checkpoint sources don't match current list. Start a new merge or use same sources.")
                await client.disconnect()
                return
            new_group = await client.get_entity(target_id)
            topic_mapping = checkpoint.get("topic_mapping", {})
            copied_set = set(checkpoint.get("copied", []))
            print(f"\n   Resuming: target group exists, {len(copied_set)} messages already copied.")
        except Exception as e:
            print(f"   Checkpoint invalid or target not found: {e}. Starting fresh.")
            checkpoint = None

    if new_group is None:
        title = new_title.strip() or "Merged"
        print(f"\n2. Creating new group: {title} (forum={any_forum})...")
        created = await client(CreateChannelRequest(
            title=title, about="", broadcast=False, megagroup=True, forum=any_forum))
        new_group = created.chats[0]
        topic_mapping = {}
        if any_forum:
            print("3. Creating topics from all sources...")
            for ent in source_entities:
                if not (isinstance(ent, Channel) and getattr(ent, "forum", False)):
                    continue
                pid = _peer_id(ent)
                try:
                    topics = await get_all_forum_topics(client, ent)
                    for t in topics:
                        tid = getattr(t, "id", None)
                        ttitle = getattr(t, "title", "") or f"Topic {tid}"
                        if not tid or tid == GENERAL_TOPIC_ID:
                            continue
                        src_title = getattr(ent, "title", "") or str(pid)
                        new_title_topic = f"{src_title}: {ttitle}"[:128]
                        try:
                            result = await client(CreateForumTopicRequest(peer=new_group, title=new_title_topic))
                            new_topic_id = None
                            for upd in getattr(result, "updates", []):
                                if hasattr(upd, "id"):
                                    new_topic_id = upd.id
                                    break
                                if hasattr(upd, "message") and hasattr(upd.message, "id"):
                                    new_topic_id = upd.message.id
                                    break
                            if new_topic_id:
                                topic_mapping[f"{pid}:{tid}"] = new_topic_id
                            await asyncio.sleep(0.5)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"   Topics from {getattr(ent, 'title', pid)}: {e}")
        save_checkpoint({
            "target_peer_id": _peer_id(new_group),
            "sources": source_ids,
            "topic_mapping": topic_mapping,
            "copied": [],
            "delay": delay_sec,
            "title": title,
        })
        copied_set = set()

    print("\n4. Collecting messages from all groups (chronological order)...")
    write_progress("collect", 0, len(source_entities))
    all_items = []  # (date, source_pid, msg)
    for idx, ent in enumerate(source_entities):
        pid = _peer_id(ent)
        n = 0
        async for msg in client.iter_messages(ent, reverse=True):
            if isinstance(msg, MessageService):
                continue
            text = getattr(msg, "message", None) or getattr(msg, "text", None) or ""
            if not msg.media and not text:
                continue
            all_items.append((msg.date, pid, msg))
            n += 1
        write_progress("collect", idx + 1, len(source_entities))
        print(f"   {getattr(ent, 'title', pid)}: {n} messages")
    all_items.sort(key=lambda x: x[0])
    total = len(all_items)
    print(f"\n   Total: {total} messages (merged by date)")

    if total == 0:
        print("\nNothing to copy.")
        await client.disconnect()
        return

    is_forum = isinstance(new_group, Channel) and getattr(new_group, "forum", False)
    print(f"\n5. Copying to new group (delay={delay_sec}s, anti-flood)...")
    write_progress("copy", 0, total)
    count = 0
    for i, (_, src_pid, msg) in enumerate(all_items, 1):
        key = f"{src_pid}:{msg.id}"
        if key in copied_set:
            count += 1
            write_progress("copy", count, total)
            continue
        try:
            text = getattr(msg, "message", None) or getattr(msg, "text", None) or ""
            reply_to = None
            if is_forum:
                tid = get_message_topic_id(msg)
                reply_to = topic_mapping.get(f"{src_pid}:{tid}") or topic_mapping.get(f"{src_pid}:{GENERAL_TOPIC_ID}")
            entities = getattr(msg, "entities", None)
            for attempt in range(3):
                try:
                    if msg.media and not isinstance(msg.media, MessageMediaWebPage):
                        await client.send_file(
                            new_group, msg.media, caption=text or None,
                            formatting_entities=entities, reply_to=reply_to,
                            link_preview=False, parse_mode=None if entities else ())
                    else:
                        await client.send_message(
                            new_group, text, formatting_entities=entities,
                            reply_to=reply_to,
                            link_preview=isinstance(msg.media, MessageMediaWebPage),
                            parse_mode=None if entities else ())
                    break
                except FloodWaitError as e:
                    wait = e.seconds + 2
                    print(f"\n   FloodWait: pause {wait}s...")
                    await asyncio.sleep(wait)
            count += 1
            copied_set.add(key)
            cp = load_checkpoint()
            if cp and cp.get("target_peer_id") == _peer_id(new_group):
                cp["copied"] = list(copied_set)
                cp["topic_mapping"] = topic_mapping
                save_checkpoint(cp)
            write_progress("copy", count, total)
            if count % 10 == 0 or count == total:
                print(f"   Copied: {count}/{total}", end="\r")
            await asyncio.sleep(max(0.5, delay_sec))
        except Exception as e:
            print(f"\n   Error msg {i} ({key}): {e}")
    print(f"\n\nDone! Copied {count} messages. Checkpoint saved; you can resume later if needed.")
    await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge several groups into one clone.")
    parser.add_argument("--sources", required=True, help="Comma or newline separated group links / @username")
    parser.add_argument("--title", default="", help="Title for the new merged group")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between messages (anti-flood)")
    args = parser.parse_args()
    asyncio.run(main(args.sources, args.title, args.delay))
