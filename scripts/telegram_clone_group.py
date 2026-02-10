"""ИДЕАЛЬНАЯ КОПИЯ Telegram-группы."""
import re
import asyncio
import argparse
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _config import load_config, SESSION_PATH, get_api_credentials, write_progress

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.functions.channels import (
    CreateChannelRequest, EditPhotoRequest, GetFullChannelRequest
)
from telethon.tl.functions.messages import (
    ImportChatInviteRequest, GetFullChatRequest, GetForumTopicsRequest,
    GetForumTopicsByIDRequest, CreateForumTopicRequest
)
from telethon.tl.types import (
    InputChatUploadedPhoto, Channel, Chat, MessageService,
    MessageMediaWebPage
)

GENERAL_TOPIC_ID = 1


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
            # Frozen / restricted accounts cannot use CheckChatInviteRequest/ImportChatInviteRequest
            if "frozen" in str(e).lower() or "not available for frozen accounts" in str(e).lower():
                raise RuntimeError(
                    "Account is frozen/restricted by Telegram. "
                    "Invite links (joinchat/+) cannot be checked/joined from this account. "
                    "Use another account or a public @username link."
                )
            if "already" in str(e).lower() or "participant" in str(e).lower():
                pass
    return await client.get_entity(source)


def is_group(entity):
    if isinstance(entity, Chat):
        return True
    if isinstance(entity, Channel) and entity.megagroup:
        return True
    return False


def get_message_topic_id(msg):
    reply_to = getattr(msg, 'reply_to', None)
    if not reply_to:
        return GENERAL_TOPIC_ID
    if getattr(reply_to, 'forum_topic', False):
        return reply_to.reply_to_top_id or reply_to.reply_to_msg_id or GENERAL_TOPIC_ID
    return GENERAL_TOPIC_ID


async def get_all_forum_topics(client, entity):
    topics = []
    offset_date = datetime(2030, 1, 1)
    offset_id = 0
    offset_topic = 0
    seen_ids = set()
    while True:
        result = await client(GetForumTopicsRequest(
            peer=entity, offset_date=offset_date, offset_id=offset_id,
            offset_topic=offset_topic, limit=100))
        if not result.topics:
            break
        for t in result.topics:
            tid = getattr(t, 'id', None)
            if tid and tid not in seen_ids and hasattr(t, 'title') and tid != GENERAL_TOPIC_ID:
                seen_ids.add(tid)
                topics.append(t)
        if len(result.topics) < 100:
            break
        last = result.topics[-1]
        offset_date = getattr(last, 'date', offset_date) or datetime.utcnow()
        offset_id = getattr(last, 'top_message', offset_id) or 0
        offset_topic = getattr(last, 'id', 0)
    return topics


async def get_topics_by_ids(client, entity, topic_ids):
    if not topic_ids:
        return {}
    topic_ids = list(set(topic_ids))
    id_to_topic = {}
    for i in range(0, len(topic_ids), 50):
        batch = topic_ids[i:i + 50]
        try:
            result = await client(GetForumTopicsByIDRequest(peer=entity, topics=batch))
            for t in getattr(result, 'topics', []):
                tid = getattr(t, 'id', None)
                if tid and hasattr(t, 'title'):
                    id_to_topic[tid] = t
        except Exception:
            pass
    return id_to_topic


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
    
    print("\n1. Getting source group...")
    source_entity = await get_source_entity(client, source)
    if not is_group(source_entity):
        print("Error: not a group.")
        await client.disconnect()
        return

    # Быстрая проверка доступа к истории
    try:
        probe = await client.get_messages(source_entity, limit=1)
        if not probe:
            print("\nError: No messages found or no access to history.")
            print("Tip: you must be a member of the group (or be approved if join request is enabled).")
            await client.disconnect()
            return
    except Exception as e:
        print(f"\nError: can't read group history: {e}")
        print("Tip: you must be a member of the group (or be approved if join request is enabled).")
        await client.disconnect()
        return
    is_forum = isinstance(source_entity, Channel) and getattr(source_entity, 'forum', False)
    if isinstance(source_entity, Channel):
        full = await client(GetFullChannelRequest(source_entity))
        full_chat = full.full_chat
    else:
        full = await client(GetFullChatRequest(source_entity.id))
        full_chat = full.full_chat
    title = new_title or getattr(source_entity, 'title', None) or "Copy"
    about = getattr(full_chat, 'about', None) or ""
    print(f"   Title: {title}")
    print("\n2. Creating new group...")
    created = await client(CreateChannelRequest(
        title=title, about=about, broadcast=False, megagroup=True, forum=is_forum))
    new_group = created.chats[0]
    topic_mapping = {GENERAL_TOPIC_ID: GENERAL_TOPIC_ID}
    if is_forum:
        print("\n3. Creating topics...")
        src_topics = await get_all_forum_topics(client, source_entity)
        for t in src_topics:
            tid = getattr(t, 'id', None)
            ttitle = getattr(t, 'title', '') or ''
            if not tid or tid == GENERAL_TOPIC_ID:
                continue
            try:
                result = await client(CreateForumTopicRequest(peer=new_group, title=ttitle))
                new_topic_id = None
                for upd in getattr(result, 'updates', []):
                    if hasattr(upd, 'id'):
                        new_topic_id = upd.id
                        break
                    if hasattr(upd, 'message') and hasattr(upd.message, 'id'):
                        new_topic_id = upd.message.id
                        break
                if new_topic_id:
                    topic_mapping[tid] = new_topic_id
                await asyncio.sleep(0.5)
            except Exception:
                pass
    if getattr(full_chat, 'chat_photo', None):
        print("\n4. Copying avatar...")
        try:
            photo_path = await client.download_media(full_chat.chat_photo)
            if photo_path:
                uploaded = await client.upload_file(photo_path)
                await client(EditPhotoRequest(new_group, InputChatUploadedPhoto(file=uploaded)))
        except Exception:
            pass
    print("\n5. Collecting messages...")
    write_progress("collect", 0, 0)
    messages = []
    n = 0
    async for msg in client.iter_messages(source_entity, reverse=True):
        messages.append(msg)
        n += 1
        if n % 50 == 0:
            write_progress("collect", n, 0)
    if is_forum:
        needed_topic_ids = set()
        for msg in messages:
            if isinstance(msg, MessageService):
                continue
            tid = get_message_topic_id(msg)
            if tid != GENERAL_TOPIC_ID:
                needed_topic_ids.add(tid)
        missing_ids = needed_topic_ids - set(topic_mapping.keys())
        if missing_ids:
            extra_topics = await get_topics_by_ids(client, source_entity, list(missing_ids))
            for tid in sorted(missing_ids):
                ttitle = f'Topic {tid}'
                if tid in extra_topics:
                    ttitle = getattr(extra_topics[tid], 'title', '') or ttitle
                try:
                    result = await client(CreateForumTopicRequest(peer=new_group, title=ttitle))
                    new_topic_id = None
                    for upd in getattr(result, 'updates', []):
                        if hasattr(upd, 'id'):
                            new_topic_id = upd.id
                            break
                        if hasattr(upd, 'message') and hasattr(upd.message, 'id'):
                            new_topic_id = upd.message.id
                            break
                    if new_topic_id:
                        topic_mapping[tid] = new_topic_id
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
    total = len(messages)
    write_progress("copy", 0, total)
    print(f"\n6. Copying {total} messages...")
    if total == 0:
        print("\nError: 0 messages collected. Nothing to copy.")
        print("Tip: join the group first or use an invite link. Some groups require admin approval.")
        await client.disconnect()
        return
    count = 0
    for i, msg in enumerate(messages, 1):
        try:
            if isinstance(msg, MessageService):
                continue
            text = getattr(msg, 'message', None) or getattr(msg, 'text', None) or ""
            if not msg.media and not text:
                continue
            reply_to = None
            if is_forum:
                topic_id = get_message_topic_id(msg)
                reply_to = topic_mapping.get(topic_id, GENERAL_TOPIC_ID)
            entities = getattr(msg, 'entities', None)
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
                    print(f"\n   Pause {wait} sec...")
                    await asyncio.sleep(wait)
            count += 1
            write_progress("copy", count, total)
            print(f"   Copied: {count}/{len(messages)}", end="\r")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"\n   Error msg {i}: {e}")
    print(f"\n\nDone! Copied {count} messages.")
    await client.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--title", default="")
    args = parser.parse_args()
    asyncio.run(main(args.source, args.title))
