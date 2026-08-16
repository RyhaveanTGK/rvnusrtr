"""Ryhavean Userbot — lisenziya (icazə) sistemi.

Bota yalnız admin tərəfindən `/ver <user_id>` ilə icazə verilmiş istifadəçilər
daxil ola bilər. Hər lisenziya standart olaraq 30 gündür və bütün məlumatlar
MongoDB-də saxlanılır.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from config import licenses, BOT_ADMINS, LICENSE_DAYS

logger = logging.getLogger("userbot")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def is_bot_admin(user_id: int) -> bool:
    """İstifadəçi bot admini (lisenziya verə bilən şəxs) sayılırmı?"""
    return int(user_id) in BOT_ADMINS


def grant_license(user_id: int, days: int = None, granted_by: int = 0) -> dict:
    """İstifadəçiyə `days` günlük lisenziya verir (default 30 gün).

    Mövcud aktiv lisenziya varsa, müddət onun üstünə əlavə olunur.
    """
    days = int(days or LICENSE_DAYS)
    user_id = int(user_id)
    doc = licenses.find_one({"user_id": user_id}) or {}

    base = _now()
    old_expiry = doc.get("expires_at")
    if old_expiry:
        try:
            old_dt = datetime.fromtimestamp(float(old_expiry), tz=timezone.utc)
            if old_dt > base:
                base = old_dt
        except Exception:
            pass

    expires_at = base + timedelta(days=days)
    payload = {
        "user_id": user_id,
        "active": True,
        "days": days,
        "granted_by": int(granted_by),
        "granted_at": time.time(),
        "expires_at": expires_at.timestamp(),
    }
    licenses.update_one({"user_id": user_id}, {"$set": payload}, upsert=True)
    logger.info("Lisenziya verildi: %s (%s gün)", user_id, days)
    return payload


def revoke_license(user_id: int) -> bool:
    """İstifadəçinin lisenziyasını ləğv edir."""
    user_id = int(user_id)
    doc = licenses.find_one({"user_id": user_id})
    if not doc:
        return False
    licenses.update_one(
        {"user_id": user_id},
        {"$set": {"active": False, "expires_at": 0, "revoked_at": time.time()}},
    )
    logger.info("Lisenziya ləğv edildi: %s", user_id)
    return True


def get_license(user_id: int) -> dict | None:
    return licenses.find_one({"user_id": int(user_id)})


def has_license(user_id: int) -> bool:
    """Adminlər həmişə icazəlidir; digərləri üçün müddət yoxlanılır."""
    user_id = int(user_id)
    if is_bot_admin(user_id):
        return True
    doc = licenses.find_one({"user_id": user_id})
    if not doc or not doc.get("active"):
        return False
    try:
        return float(doc.get("expires_at", 0)) > time.time()
    except Exception:
        return False


def days_left(user_id: int) -> int:
    """Lisenziyanın bitməsinə neçə gün qaldığını qaytarır."""
    doc = licenses.find_one({"user_id": int(user_id)})
    if not doc:
        return 0
    remaining = float(doc.get("expires_at", 0)) - time.time()
    return max(0, int(remaining // 86400))


def expiry_text(user_id: int) -> str:
    """Bitmə tarixini oxunaqlı formada qaytarır."""
    doc = licenses.find_one({"user_id": int(user_id)})
    if not doc or not doc.get("expires_at"):
        return "yoxdur"
    try:
        dt = datetime.fromtimestamp(float(doc["expires_at"]), tz=timezone.utc)
        return dt.strftime("%d.%m.%Y %H:%M UTC")
    except Exception:
        return "naməlum"


def list_licenses() -> list:
    """Bütün lisenziyaları qaytarır."""
    try:
        return list(licenses.find({}))
    except Exception:
        return []


def active_licenses() -> list:
    now = time.time()
    return [
        d for d in list_licenses()
        if d.get("active") and float(d.get("expires_at", 0)) > now
    ]
