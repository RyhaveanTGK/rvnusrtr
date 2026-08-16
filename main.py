"""Ryhavean Userbot — əsas giriş nöqtəsi.

Bütün sistem tək server üzərində işləyir: idarəedici bot + hər istifadəçi üçün
ayrıca userbot klienti. Sessiyalar və bütün məlumatlar MongoDB-də saxlanılır.
"""

import asyncio
import logging

from pyrogram import Client, idle
from convopyro import Conversation

from config import *
from plugin_loader import load_extra_plugins
from keepalive import start_keepalive
from utils.premium_patch import apply_premium_patch
from session_manager import restore_all_sessions, start_userbot, license_watchdog

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)

logger = logging.getLogger("userbot")

print("Ryhavean Userbot başladılır...")


async def main():
    # Premium emoji sistemini bütün klientlərə tətbiq et
    apply_premium_patch()

    # Render / UptimeRobot üçün keep-alive serveri
    start_keepalive(PORT)

    # İdarəedici bot klienti
    app = None
    if BOT_TOKEN:
        app = Client(
            "main_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True,
            sleep_threshold=30,
            plugins=dict(root="bot")
        )
        Conversation(app)

        try:
            await app.start()
            apps["app"] = app
            print("Bot uğurla başladıldı!")
            print(f"Bot hesabı: {app.me.first_name} (@{app.me.username})")
        except Exception as e:
            print(f"Bot klienti başlamadı (bot olmadan davam edilir): {e}")

    # MongoDB-dəki bütün aktiv userbot sessiyalarını bərpa et
    try:
        restored = await restore_all_sessions()
        print(f"MongoDB-dən {restored} userbot bərpa edildi.")
    except Exception as e:
        print(f"Sessiyalar bərpa edilə bilmədi: {e}")

    # Əlavə olaraq .env-dəki sahib sessiyası (varsa) işə salınır
    if SESSION_STR:
        try:
            owner_client = Client(
                "userbot_session",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=SESSION_STR,
                plugins=dict(root="userbot"),
            )
            Conversation(owner_client)
            await owner_client.start()
            clients[owner_client.me.id] = owner_client
            print(f"Sahib userbotu aktiv: {owner_client.me.first_name} ({owner_client.me.id})")

            data = user_sessions.find_one({"user_id": owner_client.me.id})
            if data and "sudoers" in data:
                SUDO[owner_client.me.id] = data["sudoers"]

            loaded_extra_plugins.extend(load_extra_plugins(owner_client, EXTRA_PLUGINS_DIR))
            if loaded_extra_plugins:
                print(f"{len(loaded_extra_plugins)} əlavə plagin yükləndi: {', '.join(loaded_extra_plugins)}")
        except Exception as e:
            print(f"Sahib userbotu başladıla bilmədi: {e}")

    # Lisenziya nəzarətçisi (bitən lisenziyaların userbotunu dayandırır)
    asyncio.create_task(license_watchdog())

    await idle()


if __name__ == "__main__":
    asyncio.run(main())
