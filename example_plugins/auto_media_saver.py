"""📸 Auto Media Saver — tək səfərlik (view-once) media yaddaşı.

Bütün şəxsi söhbətlərdə tək səfərlik media gəldikdə avtomatik olaraq
"Qeyd edilmiş mesajlar"-a (Saved Messages) göndərir. Altında kimdən gəldiyi,
tarix və saat yazılır.

    .on   → aktivləşdir
    .off  → söndür

`.pinstall` ilə quraşdırıldıqda dərhal işə düşür. Bütün ayarlar MongoDB-də
hər istifadəçi üçün ayrıca saxlanılır.
"""

import logging
import os
from datetime import datetime

from pyrogram import filters
from pyrogram.errors import FloodWait

import db

log = logging.getLogger("auto_media_saver")

PLUGIN_ID = "auto_media_saver"

# Plagin yükləyicisi bu dəyişənləri təmin edir
_client = client            # noqa: F821 — plagin runtime-ı verir
OWNER_ID = USER_ID          # noqa: F821 — plagini quraşdıran istifadəçi


async def is_active() -> bool:
    try:
        data = await db.get_plugin_config(PLUGIN_ID, OWNER_ID)
        if isinstance(data, dict):
            return data.get("active", True)
    except Exception as exc:
        log.warning("Konfiq oxuma xətası: %s", exc)
    return True


async def set_active(state: bool):
    try:
        await db.save_plugin_config(PLUGIN_ID, {"active": state}, OWNER_ID)
    except Exception as exc:
        log.warning("Konfiq yazma xətası: %s", exc)


def is_view_once(message) -> bool:
    """Mesajın tək səfərlik olub-olmadığını yoxlayır."""
    for attr in ("ttl_seconds", "self_destruct"):
        if getattr(message, attr, None):
            return True
    for media_attr in ("photo", "video", "voice", "video_note", "animation", "document"):
        media = getattr(message, media_attr, None)
        if media is not None and getattr(media, "ttl_seconds", None):
            return True
    return bool(getattr(message, "has_protected_content", False) and False)


async def _sender_info(message):
    user = message.from_user
    if not user:
        chat = message.chat
        return (getattr(chat, "title", None) or "Bilinməyən"), "", getattr(chat, "id", 0)
    name = " ".join(filter(None, [user.first_name, user.last_name])) or "Bilinməyən"
    username = f"@{user.username}" if user.username else ""
    return name, username, user.id


@_client.on_message(filters.private & filters.incoming & filters.media, group=-5)
async def auto_media_saver_handler(client, message):
    if not is_view_once(message):
        return
    if not await is_active():
        return

    name, username, uid = await _sender_info(message)
    if uid == OWNER_ID:
        return

    now = datetime.now()
    caption = (
        f"📨 Kimdən: {name}{' (' + username + ')' if username else ''}\n"
        f"🆔 ID: `{uid}`\n"
        f"⏱ Tarix: {now:%Y-%m-%d}  |  Saat: {now:%H:%M:%S}"
    )

    path = None
    try:
        path = await client.download_media(message)
        if path:
            await client.send_document("me", path, caption=caption)
            log.info("✅ Tək səfərlik media saxlanıldı — %s", uid)
            return
    except FloodWait as exc:
        log.warning("FloodWait: %ss", exc.value)
        return
    except Exception as exc:
        log.error("Media saxlanmadı: %s", exc)
    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    # Son çarə — forward
    try:
        await message.forward("me")
        await client.send_message("me", caption)
    except Exception as exc:
        log.error("Son çarə də alınmadı: %s", exc)


@_client.on_message(filters.me & filters.regex(r"^\.on$"))
async def on_cmd(client, message):
    await set_active(True)
    await message.edit_text(
        "✅ Auto Media Saver aktivləşdi!\nTək səfərlik media avtomatik qeyd ediləcək."
    )


@_client.on_message(filters.me & filters.regex(r"^\.off$"))
async def off_cmd(client, message):
    await set_active(False)
    await message.edit_text("❌ Auto Media Saver söndürüldü!")


log.info("✅ Auto Media Saver yükləndi — istifadəçi %s", OWNER_ID)
