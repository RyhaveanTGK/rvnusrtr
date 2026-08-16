"""Ryhavean Userbot — qlobal premium emoji patch-i.

Bu modul Pyrogram `Client` metodlarını sarıyaraq göndərilən/redaktə edilən
bütün mətnlərdəki emojiləri avtomatik premium (custom) emojilərə çevirir.
Həm bot, həm də userbot klientləri üçün eyni cür işləyir.

main.py-də bir dəfə `apply_premium_patch()` çağırmaq kifayətdir.
"""

from __future__ import annotations

import logging

from pyrogram import Client
from pyrogram.enums import ParseMode

from utils.premium_emojis import premiumize

logger = logging.getLogger("userbot")

_PATCHED = False

# Mətn arqumenti olan metodlar
_TEXT_METHODS = (
    "send_message",
    "edit_message_text",
    "edit_inline_text",
)

# Caption arqumenti olan metodlar
_CAPTION_METHODS = (
    "send_photo",
    "send_video",
    "send_audio",
    "send_document",
    "send_animation",
    "send_voice",
    "send_video_note",
    "edit_message_caption",
    "copy_message",
)

# Bu parse mode-larda HTML teqi işləmir — toxunmuruq
_SKIP_MODES = (ParseMode.MARKDOWN, ParseMode.DISABLED)


def _should_skip(kwargs: dict) -> bool:
    mode = kwargs.get("parse_mode")
    return mode in _SKIP_MODES


def _wrap(func, arg_name: str, arg_index: int):
    async def wrapper(*args, **kwargs):
        try:
            if not _should_skip(kwargs):
                if arg_name in kwargs and isinstance(kwargs[arg_name], str):
                    kwargs[arg_name] = premiumize(kwargs[arg_name])
                elif len(args) > arg_index and isinstance(args[arg_index], str):
                    args = list(args)
                    args[arg_index] = premiumize(args[arg_index])
                    args = tuple(args)
        except Exception as exc:  # heç vaxt mesaj göndərməyi dayandırma
            logger.debug("Premium emoji çevrilməsi alınmadı: %s", exc)
        return await func(*args, **kwargs)

    wrapper.__name__ = getattr(func, "__name__", "wrapped")
    wrapper.__doc__ = getattr(func, "__doc__", None)
    return wrapper


def apply_premium_patch() -> None:
    """Bütün Pyrogram klientlərinə premium emoji dəstəyini tətbiq edir."""
    global _PATCHED
    if _PATCHED:
        return

    # send_message(self, chat_id, text, ...) -> text index 2
    for name in _TEXT_METHODS:
        func = getattr(Client, name, None)
        if func is None:
            continue
        index = 2 if name != "edit_inline_text" else 2
        setattr(Client, name, _wrap(func, "text", index))

    # send_photo(self, chat_id, photo, caption=...) -> caption adətən kwargs
    for name in _CAPTION_METHODS:
        func = getattr(Client, name, None)
        if func is None:
            continue
        setattr(Client, name, _wrap(func, "caption", 99))

    _PATCHED = True
    logger.info("Premium emoji sistemi aktivləşdirildi.")
