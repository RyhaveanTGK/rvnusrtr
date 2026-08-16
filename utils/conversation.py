"""Ryhavean Userbot — daxili (dependency-siz) söhbət dinləyicisi.

`convopyro` paketi PyPI-də artıq mövcud olmayan versiyaya bağlı idi və onun
`listen` implementasiyası asyncio lock-u səhv istifadə edirdi (RuntimeError
verib `/login` axınını səssizcə dayandıra bilir). Bu modul həmin funksiyanı
sıfırdan, sadə və etibarlı şəkildə həyata keçirir.

İstifadə:
    from utils.conversation import listen_message
    cavab = await listen_message(client, chat_id, timeout=180)
    # cavab None-dursa vaxt bitib
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional, Tuple

from pyrogram import filters as pyro_filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

logger = logging.getLogger("userbot")

# {(client_id, chat_id): Future}
_WAITERS: Dict[Tuple[int, int], asyncio.Future] = {}
_HOOKED: set = set()

# Dinləyici ən aşağı qrupda oturur: digər qruplardaki əmr handler-ləri
# normal işləməyə davam edir.
_GROUP = -999


def _hook(client) -> None:
    """Klientə bir dəfəlik "hər mesajı gör" handler-i əlavə edir."""
    key = id(client)
    if key in _HOOKED:
        return

    async def _catch(cli, message: Message):
        fut = _WAITERS.get((id(cli), message.chat.id))
        if fut is not None and not fut.done():
            fut.set_result(message)

    try:
        client.add_handler(MessageHandler(_catch, pyro_filters.all), group=_GROUP)
        _HOOKED.add(key)
    except Exception as exc:
        logger.error("Söhbət dinləyicisi qurula bilmədi: %s", exc)


async def listen_message(client, chat_id: int, timeout: Optional[int] = 180) -> Optional[Message]:
    """Verilən söhbətdən növbəti mesajı gözləyir.

    Vaxt bitərsə və ya gözləmə ləğv edilərsə `None` qaytarır — heç vaxt
    exception atmır, buna görə handler-lər səssizcə ölmür.
    """
    _hook(client)
    key = (id(client), chat_id)

    old = _WAITERS.get(key)
    if old is not None and not old.done():
        old.cancel()

    fut: asyncio.Future = asyncio.get_running_loop().create_future()
    _WAITERS[key] = fut
    try:
        return await asyncio.wait_for(fut, timeout)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        return None
    except Exception as exc:
        logger.warning("Söhbət gözləməsi xəta ilə bitdi: %s", exc)
        return None
    finally:
        if _WAITERS.get(key) is fut:
            _WAITERS.pop(key, None)


async def cancel_listen(client, chat_id: int) -> bool:
    """Aktiv gözləməni ləğv edir."""
    fut = _WAITERS.pop((id(client), chat_id), None)
    if fut is not None and not fut.done():
        fut.cancel()
        return True
    return False


# convopyro ilə eyni adlar (köçürməni asanlaşdırmaq üçün)
ask = listen_message
