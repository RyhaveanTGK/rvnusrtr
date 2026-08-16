"""Ryhavean Userbot — qlobal premium emoji patch-i.

Bu modul Pyrogram `Client` və `Message` metodlarını sarıyaraq göndərilən,
redaktə edilən və inline şəkildə qaytarılan BÜTÜN mətnlərdəki emojiləri
avtomatik premium (custom) emojilərə çevirir. Həm idarəedici bot, həm də
bütün userbot klientləri üçün eyni anda işləyir (patch `Client` sinfinə
tətbiq olunur).

ÖNƏMLİ: adi (premium olmayan) hesablar sahibi olmadığı paketdən custom emoji
göndərə bilmir — Telegram `CUSTOM_EMOJI_INVALID` xətası verir və mesaj HEÇ
GÖNDƏRİLMİR. Ona görə burada iki qat qoruma var:
  1) mətn premium emojilərlə göndərilməyə çalışılır;
  2) emoji ilə bağlı xəta gəlsə, teqlər təmizlənib mesaj yenidən göndərilir
     (və həmin klient üçün bir müddət premium rejim söndürülür).

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

# metod adı -> (arqument adı, pozisiya indeksi)
_TEXT_METHODS = {
    "send_message": ("text", 2),
    "edit_message_text": ("text", 3),
    "edit_inline_text": ("text", 2),
}

_CAPTION_METHODS = {
    "send_photo": ("caption", 3),
    "send_video": ("caption", 3),
    "send_audio": ("caption", 3),
    "send_document": ("caption", 3),
    "send_animation": ("caption", 3),
    "send_voice": ("caption", 3),
    "send_video_note": ("caption", 99),
    "send_sticker": ("caption", 99),
    "edit_message_caption": ("caption", 3),
    "edit_inline_caption": ("caption", 2),
    "copy_message": ("caption", 4),
    "send_cached_media": ("caption", 3),
}

# Bu parse mode-larda HTML teqi işləmir — toxunmuruq
_SKIP_MODES = (ParseMode.MARKDOWN, ParseMode.DISABLED)

_EMOJI_TAG_RE = re.compile(r'<emoji[^>]*>(.*?)</emoji>', re.DOTALL)

# Custom emoji ilə bağlı Telegram xətaları
_EMOJI_ERRORS = (
    "CUSTOM_EMOJI",
    "EMOJI_INVALID",
    "DOCUMENT_INVALID",
    "ENTITY_BOUNDS_INVALID",
    "ENTITIES_TOO_LONG",
    "PREMIUM_ACCOUNT_REQUIRED",
)

# Premium emoji qəbul etməyən klientlər (id-lərinə görə) — təkrar xəta olmasın
_NO_PREMIUM: set[int] = set()


def strip_premium(text: str) -> str:
    """`<emoji id="...">🚀</emoji>` -> `🚀` (adi hesablar üçün fallback)."""
    if not text:
        return text
    return _EMOJI_TAG_RE.sub(r"\1", text)


def _client_key(args) -> int:
    client = args[0] if args else None
    return id(client)


def _should_skip(args, kwargs: dict) -> bool:
    if kwargs.get("parse_mode") in _SKIP_MODES:
        return True
    return _client_key(args) in _NO_PREMIUM


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
        skip = _should_skip(args, kwargs)
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
            _NO_PREMIUM.add(_client_key(args))
            args, kwargs = _transform(args, kwargs, arg_name, arg_index, strip_premium)
            return await func(*args, **kwargs)

    wrapper.__name__ = getattr(func, "__name__", "wrapped")
    wrapper.__doc__ = getattr(func, "__doc__", None)
    wrapper.__ryhavean_premium__ = True
    return wrapper


def _premiumize_media_list(media):
    """`send_media_group` üçün InputMedia obyektlərinin caption-larını çevirir."""
    for item in media or []:
        caption = getattr(item, "caption", None)
        if isinstance(caption, str) and caption:
            try:
                item.caption = premiumize(caption)
            except Exception:
                pass
    return media


def _wrap_media_group(func):
    async def wrapper(*args, **kwargs):
        if not _should_skip(args, kwargs):
            if "media" in kwargs:
                kwargs["media"] = _premiumize_media_list(kwargs["media"])
            elif len(args) > 2:
                args = list(args)
                args[2] = _premiumize_media_list(args[2])
                args = tuple(args)
        return await func(*args, **kwargs)

    wrapper.__name__ = getattr(func, "__name__", "wrapped")
    return wrapper


def _premiumize_inline_results(results):
    """Inline nəticələrin mətn/caption sahələrini premium emojiyə çevirir."""
    for res in results or []:
        for attr in ("title", "description", "caption"):
            val = getattr(res, attr, None)
            if isinstance(val, str) and val and attr == "caption":
                try:
                    setattr(res, attr, premiumize(val))
                except Exception:
                    pass
        content = getattr(res, "input_message_content", None)
        if content is not None:
            text = getattr(content, "message_text", None)
            if isinstance(text, str) and text:
                try:
                    content.message_text = premiumize(text)
                except Exception:
                    pass
    return results


def _wrap_inline(func):
    async def wrapper(*args, **kwargs):
        if not _should_skip(args, kwargs):
            if "results" in kwargs:
                kwargs["results"] = _premiumize_inline_results(kwargs["results"])
            elif len(args) > 2:
                args = list(args)
                args[2] = _premiumize_inline_results(args[2])
                args = tuple(args)
        return await func(*args, **kwargs)

    wrapper.__name__ = getattr(func, "__name__", "wrapped")
    return wrapper


def apply_premium_patch() -> None:
    """Bütün Pyrogram klientlərinə premium emoji dəstəyini tətbiq edir."""
    global _PATCHED
    if _PATCHED:
        return

    for name, (arg_name, arg_index) in {**_TEXT_METHODS, **_CAPTION_METHODS}.items():
        func = getattr(Client, name, None)
        if func is None or getattr(func, "__ryhavean_premium__", False):
            continue
        setattr(Client, name, _wrap(func, arg_name, arg_index))

    for name in ("send_media_group",):
        func = getattr(Client, name, None)
        if func is not None:
            setattr(Client, name, _wrap_media_group(func))

    for name in ("answer_inline_query",):
        func = getattr(Client, name, None)
        if func is not None:
            setattr(Client, name, _wrap_inline(func))

    _PATCHED = True
    logger.info("Premium emoji sistemi aktivləşdirildi (bot + userbot).")
