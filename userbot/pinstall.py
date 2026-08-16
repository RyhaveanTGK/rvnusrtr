"""Plagin quraşdırma əmrləri — `.pinstall` / `.unpinstall`.

`.pinstall`   → `.py` faylına reply edib yazın; plagin dərhal işə düşür.
`.unpinstall` → `.unpinstall <ad>` — plagini söndürüb bazadan silir.
`.plugins`    → quraşdırılmış plaginlərin siyahısı.

Bütün plaginlər MongoDB-də **hər istifadəçi üçün ayrıca** saxlanılır, ona görə
də serverdə neçə userbot işləməsindən asılı olmayaraq plaginlər qarışmır.
"""

import logging
import os

from pyrogram import Client, filters

from tools import *  # noqa: F401,F403  (HARDCODED_PREFIXES, edit_or_reply, sudoers_filter)
from user_plugins import (
    install_plugin,
    list_plugins,
    loaded_names,
    uninstall_plugin,
)

logger = logging.getLogger("userbot.plugins")

MAX_FILE_SIZE = 512 * 1024


@Client.on_message(
    filters.command("pinstall", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter())
)
async def pinstall_handler(client, message):
    reply = message.reply_to_message
    if not reply or not reply.document:
        return await edit_or_reply(
            message,
            "ℹ️ **İstifadə:** bir `.py` faylına **reply** edib `.pinstall` yazın.",
        )

    filename = reply.document.file_name or "plugin.py"
    if not filename.endswith(".py"):
        return await edit_or_reply(message, "❌ Yalnız `.py` faylları quraşdırıla bilər.")
    if (reply.document.file_size or 0) > MAX_FILE_SIZE:
        return await edit_or_reply(message, "❌ Fayl çox böyükdür (max 512 KB).")

    name = os.path.splitext(os.path.basename(filename))[0]
    await edit_or_reply(message, f"⏳ `{name}` quraşdırılır...")

    path = None
    try:
        path = await client.download_media(reply)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()
    except Exception as exc:
        return await edit_or_reply(message, f"❌ Fayl oxunmadı: `{exc}`")
    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    ok, info = await install_plugin(client, name, code)
    if not ok:
        return await edit_or_reply(message, f"❌ **{name}** quraşdırılmadı:\n`{info}`")

    await edit_or_reply(
        message,
        f"✅ **{name}** quraşdırıldı və dərhal işə düşdü ({info}).\n"
        f"🗄 MongoDB-də saxlanıldı — restartdan sonra avtomatik yüklənəcək.\n"
        f"🗑 Silmək üçün: `.unpinstall {name}`",
    )


@Client.on_message(
    filters.command(["unpinstall", "puninstall"], prefixes=HARDCODED_PREFIXES)
    & (filters.me | sudoers_filter())
)
async def unpinstall_handler(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        return await edit_or_reply(message, "ℹ️ **İstifadə:** `.unpinstall <plagin adı>`")

    name = args[1].strip().removesuffix(".py")
    ok = await uninstall_plugin(client, name)
    if ok:
        await edit_or_reply(message, f"🗑 **{name}** söndürüldü və bazadan silindi.")
    else:
        await edit_or_reply(message, f"❌ **{name}** adlı plagin tapılmadı.")


@Client.on_message(
    filters.command(["pluginlist", "myplugins"], prefixes=HARDCODED_PREFIXES)
    & (filters.me | sudoers_filter())
)
async def pluginlist_handler(client, message):
    docs = [d for d in list_plugins(client.me.id) if d.get("code") and not d.get("removed")]
    active = set(loaded_names(client.me.id))
    if not docs:
        return await edit_or_reply(
            message,
            "🧩 **Heç bir plagin quraşdırılmayıb.**\n"
            "`.py` faylına reply edib `.pinstall` yazın.",
        )
    lines = "\n".join(
        f"┃ {'🟢' if d['name'] in active else '🔴'} `{d['name']}`" for d in sorted(docs, key=lambda x: x["name"])
    )
    await edit_or_reply(
        message,
        f"🧩 **Plaginləriniz** ({len(docs)})\n{lines}\n╰━━━━━━━━━━━━━━━━━━━━╯",
    )
