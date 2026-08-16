"""Ryhavean Userbot — qlobal premium emoji patch-i.

Bu modul Pyrogram `Client` metodlarını sarıyaraq göndərilən/redaktə edilən
bütün mətnlərdəki emojiləri avtomatik premium (custom) emojilərə çevirir.

ÖNƏMLİ: adi (premium olmayan) bot hesabları sahibi olmadığı paketdən custom
emoji göndərə bilmir — Telegram `CUSTOM_EMOJI_INVALID` xətası verir və mesaj
HEÇ GÖNDƏRİLMİR. Bu, `/settings`, `/status`, `/login` kimi əmrlərin səssizcə
işləməməsinə səbəb olurdu. Ona görə burada iki qat qoruma var:
  1) mətn premium emojilərlə göndərilməyə çalışılır;
  2) emoji ilə bağlı xəta gəlsə, teqlər təmizlənib mesaj yenidən göndərilir.

main.py-də bir dəfə `apply_premium_patch()` çağırmaq kifayətdir.
"""

from __future__ import annotations

import logging
import re

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

_EMOJI_TAG_RE = re.compile(r'<emoji id="?\d+"?>(.*?)</emoji>', re.DOTALL)

# Custom emoji ilə bağlı Telegram xətaları
_EMOJI_ERRORS = (
    "CUSTOM_EMOJI",
    "EMOJI_INVALID",
    "EMOJI_NOT_MODIFIED",
    "DOCUMENT_INVALID",
    "ENTITY_BOUNDS_INVALID",
    "ENTITIES_TOO_LONG",
    "PREMIUM",
)


def strip_premium(text: str) -> str:
    """`<emoji id="...">🚀</emoji>` -> `🚀` (adi hesablar üçün fallback)."""
    if not text:
        return text
    return _EMOJI_TAG_RE.sub(r"\1", text)


def _should_skip(kwargs: dict) -> bool:
    mode = kwargs.get("parse_mode")
    return mode in _SKIP_MODES


def _is_emoji_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".upper()
    return any(token in text for token in _EMOJI_ERRORS)


def _transform(args, kwargs, arg_name, arg_index, func):
    """Mətn arqumentini `func` ilə dəyişir və (args, kwargs) qaytarır."""
    if arg_name in kwargs and isinstance(kwargs[arg_name], str):
        kwargs = dict(kwargs)
        kwargs[arg_name] = func(kwargs[arg_name])
    elif len(args) > arg_index and isinstance(args[arg_index], str):
        args = list(args)
        args[arg_index] = func(args[arg_index])
        args = tuple(args)
    return args, kwargs


def _wrap(func, arg_name: str, arg_index: int):
    async def wrapper(*args, **kwargs):
        skip = _should_skip(kwargs)
        if not skip:
            try:
                args, kwargs = _transform(args, kwargs, arg_name, arg_index, premiumize)
            except Exception as exc:  # heç vaxt mesaj göndərməyi dayandırma
                logger.debug("Premium emoji çevrilməsi alınmadı: %s", exc)

        try:
            return await func(*args, **kwargs)
        except Exception as exc:
            if skip or not _is_emoji_error(exc):
                raise
            # Premium emoji qəbul edilmədi -> teqləri təmizləyib yenidən göndər
            logger.warning("Premium emoji qəbul edilmədi (%s); adi emoji ilə göndərilir.", exc)
            args, kwargs = _transform(args, kwargs, arg_name, arg_index, strip_premium)
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
        setattr(Client, name, _wrap(func, "text", 2))

    # send_photo(self, chat_id, photo, caption=...) -> caption adətən kwargs
    for name in _CAPTION_METHODS:
        func = getattr(Client, name, None)
        if func is None:
            continue
        setattr(Client, name, _wrap(func, "caption", 99))

    _PATCHED = True
    logger.info("Premium emoji sistemi aktivləşdirildi.")
