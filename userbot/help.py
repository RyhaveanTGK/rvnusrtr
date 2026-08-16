"""`.help` — userbot kömək menyusu.

Menyu **hər istifadəçi üçün ayrıca** işləyir: başlıq, alt yazı, stil, səhifə
ölçüsü və emoji kimi bütün ayarlar MongoDB-də (`user_sessions`, `user_id`
sənədi) saxlanılır və hər `.help` çağırışında oradan çəkilir.

İstifadə:
    .help                 — kateqoriyalar (səhifələnmiş)
    .help 2               — 2-ci səhifə
    .help <kateqoriya>    — kateqoriyadakı bütün əmrlər
    .help <əmr>           — əmrin ətraflı kartı
    .helpset <açar> <dəyər>  — fərdi ayar (header/footer/style/perpage/emoji)
    .helpreset            — ayarları sıfırla
"""

import logging
import html

from pyrogram import Client, filters

from config import *
from tools import *
from utils.premium_emojis import premiumize

logger = logging.getLogger("userbot.help")

HELP_KEYS = ("HELP_HEADER", "HELP_FOOTER", "HELP_STYLE", "HELP_PER_PAGE", "HELP_EMOJI")

DEFAULT_HEADER = "📖 <b>RYHAVEAN — ƏMR KATEQORİYALARI</b>"
DEFAULT_FOOTER = "💡 Ətraflı üçün <code>{prefix}help &lt;əmr&gt;</code> yazın"
DEFAULT_EMOJI = "▪"
DEFAULT_PER_PAGE = 6


def _settings(user_id: int) -> dict:
    """İstifadəçinin help ayarlarını MongoDB-dən çəkir."""
    def _g(key, default):
        try:
            value = gvarstatus(user_id, key)
        except Exception as exc:
            logger.warning("[HELP] Ayar oxunmadı (%s): %s", key, exc)
            value = None
        return default if value in (None, "") else value

    per_page = _g("HELP_PER_PAGE", DEFAULT_PER_PAGE)
    try:
        per_page = max(1, min(30, int(per_page)))
    except (TypeError, ValueError):
        per_page = DEFAULT_PER_PAGE

    style = str(_g("HELP_STYLE", "compact")).lower()
    if style not in ("compact", "detailed", "list"):
        style = "compact"

    return {
        "header": _g("HELP_HEADER", DEFAULT_HEADER),
        "footer": _g("HELP_FOOTER", DEFAULT_FOOTER),
        "style": style,
        "per_page": per_page,
        "emoji": _g("HELP_EMOJI", DEFAULT_EMOJI),
    }


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def _find_category(query: str):
    q = _norm(query)
    for name in categories:
        clean = _norm("".join(ch for ch in name if ch.isalpha() or ch.isspace()))
        if q == clean or q in clean or clean.startswith(q):
            return name
    return None


def _render_categories(cfg: dict, prefix: str, page: int) -> str:
    names = [name for name in categories]
    per_page = cfg["per_page"]
    pages = max(1, (len(names) + per_page - 1) // per_page)
    page = max(1, min(page, pages))
    chunk = names[(page - 1) * per_page: page * per_page]

    total_cmds = sum(len(v) for v in categories.values())
    lines = [cfg["header"], ""]
    for name in chunk:
        cmds = categories.get(name, [])
        if cfg["style"] == "list":
            lines.append(f"{cfg['emoji']} <b>{name}</b> — {len(cmds)} əmr")
        elif cfg["style"] == "detailed":
            body = ", ".join(f"<code>{prefix}{c}</code>" for c in cmds)
            lines.append(f"{cfg['emoji']} <b>{name}</b>\n┃ {body or '—'}")
        else:
            shown = ", ".join(f"<code>{prefix}{c}</code>" for c in cmds[:5])
            extra = f" +{len(cmds) - 5}" if len(cmds) > 5 else ""
            lines.append(f"{cfg['emoji']} <b>{name}</b>\n┃ {shown or '—'}{extra}")
    lines.append("")
    lines.append(f"📄 Səhifə <b>{page}/{pages}</b> · Ümumi <b>{total_cmds}</b> əmr")
    if pages > 1:
        lines.append(f"➡️ Növbəti: <code>{prefix}help {min(page + 1, pages)}</code>")
    lines.append(cfg["footer"].replace("{prefix}", prefix))
    return "\n".join(lines)


def _render_category(name: str, cfg: dict, prefix: str) -> str:
    cmds = categories.get(name, [])
    lines = [f"📂 <b>{name}</b>", ""]
    for cmd in cmds:
        raw = commands.get(cmd, "")
        desc = parse_help_entry(raw)[0] if raw else "Təsvir yoxdur"
        lines.append(f"{cfg['emoji']} <code>{prefix}{cmd}</code> — {desc}")
    lines.append("")
    lines.append(f"💡 <code>{prefix}help &lt;əmr&gt;</code> ilə ətraflı baxın")
    return "\n".join(lines)


@Client.on_message(filters.command("help", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
async def help_handler(client, message):
    """Kömək menyusu — .help, .help <əmr>, .help <kateqoriya>, .help <səhifə>"""
    try:
        prefix = message.text[0] if message.text else "."
        user_id = client.me.id
        cfg = _settings(user_id)

        raw_args = get_args(message)
        if isinstance(raw_args, list):
            args = " ".join(str(a) for a in raw_args).strip()
        elif isinstance(raw_args, str):
            args = raw_args.strip()
        else:
            args = ""

        # 1) Arqumentsiz və ya səhifə nömrəsi → kateqoriyalar
        if not args or args.isdigit():
            page = int(args) if args.isdigit() else 1
            await edit_or_reply(message, premiumize(_render_categories(cfg, prefix, page)))
            return

        query = args.split()[0]
        cmd_name = query.lstrip("".join(HARDCODED_PREFIXES)).lower()

        # 2) Konkret əmr
        if cmd_name in commands:
            desc, usage, example, note, warning, flags = parse_help_entry(commands[cmd_name])
            usage = usage.replace("[prefix]", prefix)
            example = example.replace("[prefix]", prefix)
            flags = flags.replace("[prefix]", prefix)
            card = styled_help_card(
                cmd_name, desc, usage,
                example=example, note=note, flags=flags, warning=warning,
            )
            await edit_or_reply(message, premiumize(card))
            return

        # 3) Kateqoriya adı
        category = _find_category(args)
        if category:
            await edit_or_reply(message, premiumize(_render_category(category, cfg, prefix)))
            return

        # 4) Bənzər əmrlər
        matches = [c for c in commands if cmd_name in c or c in cmd_name]
        if matches:
            match_list = ", ".join(f"<code>{prefix}{m}</code>" for m in matches[:10])
            await edit_or_reply(message, premiumize(
                f"⚠️ <b>Əmr tapılmadı</b>\n\n"
                f"┃ 🔍 Bunu nəzərdə tutdunuz?\n"
                f"┃ {match_list}"
            ))
            return

        await edit_or_reply(message, premiumize(
            f"❌ <b>Naməlum əmr:</b> <code>{cmd_name}</code>\n\n"
            f"┃ 💡 Bütün kateqoriyalar üçün <code>{prefix}help</code> yazın"
        ))

    except Exception as e:
        logger.exception("[HELP] Error: %s", e)
        await edit_or_reply(message, styled_error(f"Kömək xətası: {str(e)[:200]}"))


@Client.on_message(filters.command("helpset", prefixes=HARDCODED_PREFIXES) & filters.me)
async def helpset_handler(client, message):
    """Kömək menyusunu fərdiləşdirir (ayarlar MongoDB-də saxlanılır)."""
    user_id = client.me.id
    prefix = message.text[0] if message.text else "."
    arg = (get_arg(message) or "").strip()

    if not arg:
        cfg = _settings(user_id)
        return await edit_or_reply(message, premiumize(
            "⚙️ <b>HELP AYARLARI</b> (yalnız sizin hesabınız üçün)\n\n"
            f"┃ header: <code>{html.escape(str(cfg['header']))}</code>\n"
            f"┃ footer: <code>{html.escape(str(cfg['footer']))}</code>\n"
            f"┃ style: <code>{cfg['style']}</code> (compact | detailed | list)\n"
            f"┃ perpage: <code>{cfg['per_page']}</code>\n"
            f"┃ emoji: {cfg['emoji']}\n\n"
            f"<b>İstifadə:</b> <code>{prefix}helpset style detailed</code>\n"
            f"<b>Sıfırla:</b> <code>{prefix}helpreset</code>"
        ))

    parts = arg.split(None, 1)
    key = parts[0].lower()
    value = parts[1].strip() if len(parts) > 1 else ""

    mapping = {
        "header": "HELP_HEADER",
        "footer": "HELP_FOOTER",
        "style": "HELP_STYLE",
        "perpage": "HELP_PER_PAGE",
        "emoji": "HELP_EMOJI",
    }
    if key not in mapping:
        return await edit_or_reply(message, styled_error(
            "Naməlum açar. Mümkün: header, footer, style, perpage, emoji"
        ))
    if not value:
        return await edit_or_reply(message, styled_error("Dəyər boş ola bilməz."))
    if key == "style" and value.lower() not in ("compact", "detailed", "list"):
        return await edit_or_reply(message, styled_error("style: compact | detailed | list"))
    if key == "perpage" and not value.isdigit():
        return await edit_or_reply(message, styled_error("perpage rəqəm olmalıdır (1-30)."))

    set_gvar(user_id, mapping[key], value.lower() if key == "style" else value)
    await edit_or_reply(message, premiumize(f"✅ <b>{key}</b> yeniləndi."))


@Client.on_message(filters.command("helpreset", prefixes=HARDCODED_PREFIXES) & filters.me)
async def helpreset_handler(client, message):
    user_id = client.me.id
    try:
        user_sessions.update_one(
            {"user_id": user_id},
            {"$unset": {key: "" for key in HELP_KEYS}},
            upsert=True,
        )
        invalidate_session_cache(user_id)
    except Exception as exc:
        return await edit_or_reply(message, styled_error(f"Sıfırlanmadı: {exc}"))
    await edit_or_reply(message, premiumize("✅ <b>Kömək ayarları standart hala qaytarıldı.</b>"))
