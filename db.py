"""Plaginlər üçün sadə MongoDB konfiqurasiya bazası.

Hər plaginin ayarları **hər istifadəçi üçün ayrıca** saxlanılır:
    {"user_id": 123, "plugin_id": "auto_media_saver", "data": {...}}

Plagin kodunda istifadə:
    import db
    cfg = await db.get_plugin_config("my_plugin", USER_ID)
    await db.save_plugin_config("my_plugin", {"active": True}, USER_ID)

`user_id` verilməzsə qlobal (ümumi) ayar kimi saxlanılır.
"""

from __future__ import annotations

import asyncio
import logging
import time

from config import get_collection

logger = logging.getLogger("userbot.db")

config_col = get_collection("plugin_configs")


def _filt(plugin_id: str, user_id: int | None):
    return {"plugin_id": str(plugin_id), "user_id": int(user_id) if user_id else 0}


def _get_sync(plugin_id: str, user_id: int | None):
    doc = None
    try:
        doc = config_col.find_one(_filt(plugin_id, user_id))
    except Exception as exc:
        logger.warning("Konfiq oxunmadı (%s): %s", plugin_id, exc)
    if not doc:
        return {}
    return doc.get("data") or {}


def _save_sync(plugin_id: str, data: dict, user_id: int | None):
    try:
        config_col.update_one(
            _filt(plugin_id, user_id),
            {"$set": {
                **_filt(plugin_id, user_id),
                "data": data,
                "updated_at": time.time(),
            }},
            upsert=True,
        )
        return True
    except Exception as exc:
        logger.warning("Konfiq yazılmadı (%s): %s", plugin_id, exc)
        return False


async def get_plugin_config(plugin_id: str, user_id: int | None = None) -> dict:
    return await asyncio.to_thread(_get_sync, plugin_id, user_id)


async def save_plugin_config(plugin_id: str, data: dict, user_id: int | None = None) -> bool:
    return await asyncio.to_thread(_save_sync, plugin_id, data, user_id)


async def update_plugin_config(plugin_id: str, key: str, value, user_id: int | None = None) -> dict:
    cfg = await get_plugin_config(plugin_id, user_id)
    cfg[key] = value
    await save_plugin_config(plugin_id, cfg, user_id)
    return cfg
