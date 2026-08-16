"""Ryhavean Userbot — çoxistifadəçili sessiya meneceri.

Bütün userbot-lar EYNİ serverdə işləyir, hər istifadəçi üçün ayrıca Pyrogram
klienti yaradılır. Sessiya string-ləri və bütün məlumatlar MongoDB-də saxlanılır
və server yenidən başlayanda oradan çəkilir.
"""

from __future__ import annotations

import asyncio
import logging
import time

from pyrogram import Client
from convopyro import Conversation

from config import (
    API_ID,
    API_HASH,
    AUTO_JOIN_CHATS,
    clients,
    userbot_sessions,
    user_sessions,
    SUDO,
)
from licensing import has_license
from user_plugins import load_user_plugins

logger = logging.getLogger("userbot")


# ── Bazada sessiya əməliyyatları ────────────────────────────────────────────
def save_session(user_id: int, session_string: str, phone: str = "", name: str = "") -> None:
    userbot_sessions.update_one(
        {"user_id": int(user_id)},
        {"$set": {
            "user_id": int(user_id),
            "session_string": session_string,
            "phone": phone,
            "name": name,
            "active": True,
            "created_at": time.time(),
        }},
        upsert=True,
    )


def get_session(user_id: int):
    return userbot_sessions.find_one({"user_id": int(user_id)})


def delete_session(user_id: int) -> None:
    userbot_sessions.update_one(
        {"user_id": int(user_id)},
        {"$set": {"active": False, "session_string": ""}},
        upsert=True,
    )


def all_sessions() -> list:
    try:
        return [d for d in userbot_sessions.find({}) if d.get("active") and d.get("session_string")]
    except Exception:
        return []


# ── Klient idarəetməsi ──────────────────────────────────────────────────────
async def auto_join_chats(client: Client) -> None:
    """İlk qurulumda rəsmi Ryhavean kanal və qruplarına avtomatik qoşulur."""
    for link in AUTO_JOIN_CHATS:
        try:
            await client.join_chat(link.strip().replace("https://t.me/", "@").replace("@+", "+"))
            logger.info("Kanala qoşuldu: %s", link)
        except Exception as exc:
            logger.debug("Kanala qoşulmaq alınmadı (%s): %s", link, exc)
        await asyncio.sleep(1)


async def start_userbot(user_id: int, session_string: str) -> Client | None:
    """Verilmiş sessiya ilə userbot klientini bu serverdə işə salır."""
    user_id = int(user_id)
    if user_id in clients:
        return clients[user_id]

    client = Client(
        f"ryhavean_{user_id}",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=session_string,
        in_memory=True,
        plugins=dict(root="userbot"),
    )
    Conversation(client)

    try:
        await client.start()
    except Exception as exc:
        logger.error("Userbot başladıla bilmədi (%s): %s", user_id, exc)
        return None

    clients[client.me.id] = client

    data = user_sessions.find_one({"user_id": client.me.id})
    if data and "sudoers" in data:
        SUDO[client.me.id] = data["sudoers"]

    # İlk dəfə qoşulanda rəsmi kanallara üzv olur
    doc = get_session(user_id) or {}
    if not doc.get("joined_channels"):
        await auto_join_chats(client)
        userbot_sessions.update_one(
            {"user_id": user_id}, {"$set": {"joined_channels": True}}, upsert=True
        )

    # İstifadəçinin MongoDB-dəki şəxsi plaginlərini bərpa et
    try:
        user_plugins = await load_user_plugins(client)
        if user_plugins:
            logger.info(
                "Şəxsi plaginlər yükləndi (%s): %s", client.me.id, ", ".join(user_plugins)
            )
    except Exception as exc:
        logger.warning("Şəxsi plaginlər yüklənmədi (%s): %s", client.me.id, exc)

    logger.info("Userbot işə düşdü: %s (%s)", client.me.first_name, client.me.id)
    return client


async def stop_userbot(user_id: int) -> bool:
    """İstifadəçinin userbotunu dayandırır."""
    user_id = int(user_id)
    client = clients.pop(user_id, None)
    if client is None:
        return False
    try:
        await client.stop()
    except Exception as exc:
        logger.debug("Userbot dayandırılarkən xəta: %s", exc)
    return True


async def restore_all_sessions() -> int:
    """Server başlayanda MongoDB-dəki bütün aktiv sessiyaları bərpa edir."""
    started = 0
    for doc in all_sessions():
        uid = int(doc["user_id"])
        if not has_license(uid):
            logger.info("Lisenziyası bitib, keçilir: %s", uid)
            continue
        client = await start_userbot(uid, doc["session_string"])
        if client:
            started += 1
        await asyncio.sleep(1)
    return started


async def license_watchdog(interval: int = 3600) -> None:
    """Lisenziyası bitən istifadəçilərin userbotlarını avtomatik dayandırır."""
    while True:
        await asyncio.sleep(interval)
        for doc in all_sessions():
            uid = int(doc["user_id"])
            if not has_license(uid) and uid in clients:
                logger.info("Lisenziya bitdi, userbot dayandırılır: %s", uid)
                await stop_userbot(uid)
