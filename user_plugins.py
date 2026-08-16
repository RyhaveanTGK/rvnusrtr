"""Ryhavean Userbot — istifadəçiyə xas plagin sistemi (MongoDB).

Hər istifadəçi öz plaginlərini `.pinstall` ilə quraşdırır. Plagin kodu
MongoDB-də `user_plugins` kolleksiyasında **istifadəçi ID-si üzrə ayrıca**
saxlanılır, ona görə də bir istifadəçinin plagini digərinə təsir etmir.

İş prinsipi:
  • `.py` faylına reply edib `.pinstall` yazılır.
  • Kod bazaya yazılır və **dərhal** həmin istifadəçinin klientinə qoşulur
    (restart tələb olunmur).
  • Server yenidən başlayanda `load_user_plugins()` bazadan hər istifadəçinin
    plaginlərini bərpa edir.

Plagin kodu Pyrogram üslubunda yazıla bilər:
    @Client.on_message(filters.command("test", prefixes="."))
    async def _t(client, message): ...
və ya modul səviyyəsində hazır `client` obyektindən istifadə edə bilər:
    @client.on_message(...)
Əlavə olaraq `def register(client)` və `async def on_load(client)` funksiyaları
varsa, avtomatik çağırılır.
"""

from __future__ import annotations

import ast
import importlib.util
import logging
import sys
import time
import types

from pyrogram.handlers.handler import Handler

from config import get_collection

logger = logging.getLogger("userbot.plugins")

# Bütün plagin kodları burada — istifadəçi ID-si ilə birlikdə
plugins_col = get_collection("user_plugins")

# Yaddaşdakı qeydiyyat: {user_id: {name: {"handlers": [(handler, group)], "module": mod}}}
_registry: dict[int, dict[str, dict]] = {}

MAX_CODE_SIZE = 512 * 1024  # 512 KB


# ── Baza əməliyyatları ──────────────────────────────────────────────────────
def save_plugin(user_id: int, name: str, code: str) -> None:
    plugins_col.update_one(
        {"user_id": int(user_id), "name": name},
        {"$set": {
            "user_id": int(user_id),
            "name": name,
            "code": code,
            "installed_at": time.time(),
        }},
        upsert=True,
    )


def get_plugin(user_id: int, name: str):
    for doc in list_plugins(user_id):
        if doc.get("name") == name:
            return doc
    return None


def list_plugins(user_id: int) -> list:
    try:
        return [d for d in plugins_col.find({"user_id": int(user_id)})]
    except Exception as exc:
        logger.warning("Plagin siyahısı alınmadı (%s): %s", user_id, exc)
        return []


def remove_plugin(user_id: int, name: str) -> bool:
    try:
        if hasattr(plugins_col, "delete_one"):
            res = plugins_col.delete_one({"user_id": int(user_id), "name": name})
            return bool(getattr(res, "deleted_count", 0))
        # Sadə (memory/sqlite) backend üçün ehtiyat yol
        doc = get_plugin(user_id, name)
        if doc:
            plugins_col.update_one(
                {"user_id": int(user_id), "name": name},
                {"$set": {"code": "", "removed": True}},
                upsert=True,
            )
            return True
    except Exception as exc:
        logger.warning("Plagin silinmədi (%s/%s): %s", user_id, name, exc)
    return False


# ── Yükləmə / çıxarma ───────────────────────────────────────────────────────
def _make_module(name: str, code: str, client) -> types.ModuleType:
    mod_name = f"ryhavean_plugins.{client.me.id}.{name}"
    spec = importlib.util.spec_from_loader(mod_name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__dict__.update({
        "__name__": mod_name,
        "client": client,          # istifadəçinin öz klienti
        "app": client,
        "USER_ID": client.me.id,
        "PLUGIN_NAME": name,
    })
    sys.modules[mod_name] = module
    exec(compile(code, f"<plugin:{name}>", "exec"), module.__dict__)
    return module


def unload_plugin(client, name: str) -> bool:
    """Plaginin bütün handler-lərini klientdən çıxarır."""
    user_id = client.me.id
    entry = _registry.get(user_id, {}).pop(name, None)
    if not entry:
        return False
    for handler, group in entry.get("handlers", []):
        try:
            client.remove_handler(handler, group)
        except Exception as exc:
            logger.debug("Handler çıxarıla bilmədi (%s): %s", name, exc)
    sys.modules.pop(getattr(entry.get("module"), "__name__", ""), None)
    return True


async def load_plugin(client, name: str, code: str) -> tuple[int, str | None]:
    """Kodu icra edib handler-ləri həmin klientə qoşur.

    Qaytarır: (qoşulan handler sayı, xəta mətni və ya None)
    """
    if len(code) > MAX_CODE_SIZE:
        return 0, "Fayl çox böyükdür (max 512 KB)."
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return 0, f"Sintaksis xətası: sətir {exc.lineno} — {exc.msg}"

    unload_plugin(client, name)

    try:
        module = _make_module(name, code, client)
    except Exception as exc:
        return 0, f"İdxal xətası: {type(exc).__name__}: {exc}"

    added: list[tuple] = []

    # 1) @Client.on_message(...) ilə yazılmış handler-lər
    for attr in list(vars(module)):
        try:
            for handler, group in getattr(getattr(module, attr), "handlers", []) or []:
                if isinstance(handler, Handler) and isinstance(group, int):
                    client.add_handler(handler, group)
                    added.append((handler, group))
        except Exception as exc:
            logger.debug("Handler oxunmadı (%s.%s): %s", name, attr, exc)

    # 2) register(client) / on_load(client)
    try:
        reg = getattr(module, "register", None)
        if callable(reg):
            res = reg(client)
            if hasattr(res, "__await__"):
                await res
        onload = getattr(module, "on_load", None)
        if callable(onload):
            res = onload(client)
            if hasattr(res, "__await__"):
                await res
    except Exception as exc:
        return 0, f"register() xətası: {type(exc).__name__}: {exc}"

    _registry.setdefault(client.me.id, {})[name] = {"handlers": added, "module": module}
    logger.info("[PLUGIN] %s yükləndi (%s handler) — user %s", name, len(added), client.me.id)
    return len(added), None


async def install_plugin(client, name: str, code: str) -> tuple[bool, str]:
    """Plagini yükləyir və uğurlu olarsa bazaya yazır."""
    count, err = await load_plugin(client, name, code)
    if err:
        return False, err
    save_plugin(client.me.id, name, code)
    return True, f"{count} handler"


async def uninstall_plugin(client, name: str) -> bool:
    unloaded = unload_plugin(client, name)
    deleted = remove_plugin(client.me.id, name)
    return unloaded or deleted


async def load_user_plugins(client) -> list[str]:
    """Server başlayanda istifadəçinin bütün plaginlərini bazadan bərpa edir."""
    loaded = []
    for doc in list_plugins(client.me.id):
        name, code = doc.get("name"), doc.get("code")
        if not name or not code or doc.get("removed"):
            continue
        _, err = await load_plugin(client, name, code)
        if err:
            logger.warning("[PLUGIN] %s bərpa edilmədi: %s", name, err)
        else:
            loaded.append(name)
    return loaded


def loaded_names(user_id: int) -> list[str]:
    return sorted(_registry.get(int(user_id), {}).keys())
