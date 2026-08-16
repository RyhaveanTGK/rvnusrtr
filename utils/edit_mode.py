"""Ryhavean Userbot — "edit ilə cavab" rejimi.

Userbot-da hər hansı əmr yazıldıqda cavab YENİ mesaj kimi göndərilmir, əmrin
özü redaktə (edit) edilir. Bu, klassik userbot davranışıdır və söhbəti
zibilləmir.

`apply_edit_mode()` `pyrogram.types.Message.reply/reply_text` metodlarını
sarıyır:
  • mesaj bizim tərəfimizdən göndərilibsə (outgoing, mətn mesajı)  -> edit
  • başqasının mesajına cavabdırsa (sudo, bot, qrup üzvü)          -> reply
Edit alınmasa (media, silinmiş mesaj, MESSAGE_NOT_MODIFIED ...) avtomatik
olaraq köhnə davranışa qayıdır.
"""

from __future__ import annotations

import logging

from pyrogram.types import Message

logger = logging.getLogger("userbot")

_APPLIED = False

# edit_text-in qəbul etdiyi arqumentlər
_EDIT_KWARGS = (
    "parse_mode",
    "entities",
    "disable_web_page_preview",
    "link_preview_options",
    "reply_markup",
)


def _should_edit(message: Message) -> bool:
    try:
        if not getattr(message, "outgoing", False):
            return False
        # Media mesajının mətni edit_text ilə dəyişdirilə bilməz
        if getattr(message, "media", None):
            return False
        if not (message.text or message.caption):
            return False
        # Kanal/anonim göndərişlərdə edit icazəsi olmaya bilər
        return True
    except Exception:
        return False


def apply_edit_mode() -> None:
    """Userbot cavablarını edit rejiminə keçirir (bir dəfə çağırmaq kifayətdir)."""
    global _APPLIED
    if _APPLIED:
        return

    original_reply_text = Message.reply_text

    async def reply_text(self: Message, text, *args, **kwargs):
        if _should_edit(self):
            edit_kwargs = {k: v for k, v in kwargs.items() if k in _EDIT_KWARGS}
            try:
                return await self.edit_text(text, **edit_kwargs)
            except Exception as exc:
                logger.debug("Edit rejimi alınmadı, adi cavab göndərilir: %s", exc)
        return await original_reply_text(self, text, *args, **kwargs)

    reply_text.__name__ = "reply_text"
    Message.reply_text = reply_text
    # `message.reply` pyrogram-da ayrı bir alias-dır, onu da əvəz edirik
    Message.reply = reply_text

    _APPLIED = True
    logger.info("Edit rejimi aktivləşdirildi (userbot cavabları edit ilə).")
