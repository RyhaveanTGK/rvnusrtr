"""`.alive`, `.ping` və alive mesajının tam fərdiləşdirilməsi.

Bütün alive ayarları **hər istifadəçi üçün ayrıca** MongoDB-də
(`user_sessions` kolleksiyası, `user_id` sənədi) saxlanılır və oradan çəkilir.

Saxlanılan açarlar:
    ALIVE_TEXT_CUSTOM  — alive mətni
    ALIVE_EMOJI        — sətir əvvəlindəki emoji
    ALIVE_LOGO         — şəkil/video (file_id və ya URL)
    ALIVE_TEMPLATE     — tam şablon (bütün mesajı özün yazırsan)
    ALIVE_TITLE        — başlıq
    ALIVE_MEDIA        — "on"/"off": mediasız (sadəcə mətn) rejim
"""

import datetime as _dt
import html
from random import choice
from platform import python_version

from pyrogram import __version__ as versipyro

from config import *
from tools import *
from utils.premium_emojis import premiumize

# ─────────────────────────────────────────────────────────────────────────────
# Fərdi ayarlar (MongoDB)
# ─────────────────────────────────────────────────────────────────────────────
ALIVE_KEYS = (
    "ALIVE_TEXT_CUSTOM",
    "ALIVE_EMOJI",
    "ALIVE_LOGO",
    "ALIVE_TEMPLATE",
    "ALIVE_TITLE",
    "ALIVE_MEDIA",
)

DEFAULT_TEMPLATE = """<b>{title}</b>

<b>{text}</b>

<blockquote>{emoji} <b>SAHİB :</b> {mention}
{emoji} <b>Bot Versiyası :</b> <code>{version}</code>
{emoji} <b>Python Versiyası :</b> <code>{python}</code>
{emoji} <b>Pyrogram Versiyası :</b> <code>{pyrogram}</code>
{emoji} <b>Bot İşləmə Müddəti :</b> <code>{uptime}</code></blockquote>

<b><a href="https://t.me/{group}">DƏSTƏK</a></b> | <b><a href="https://t.me/{channel}">KANAL</a></b> | <b><a href="tg://user?id={user_id}">SAHİB</a></b>"""

PLACEHOLDERS = (
    "{mention}", "{first_name}", "{username}", "{user_id}", "{uptime}",
    "{python}", "{pyrogram}", "{version}", "{emoji}", "{text}", "{title}",
    "{group}", "{channel}", "{date}", "{time}",
)

BOT_VERSION = "1.0"


def _get(user_id, key, default=None):
    """MongoDB-dən istifadəçiyə aid alive ayarını oxuyur."""
    try:
        value = gvarstatus(user_id, key)
    except Exception as exc:
        logging.getLogger("userbot.alive").warning("Alive ayarı oxunmadı: %s", exc)
        value = None
    return value if value not in (None, "") else default


async def _render(client, template: str) -> str:
    user_id = client.me.id
    uptime = await get_readable_time((time.time() - StartTime))
    now = _dt.datetime.now()
    values = {
        "mention": client.me.mention,
        "first_name": client.me.first_name or "",
        "username": f"@{client.me.username}" if client.me.username else "—",
        "user_id": user_id,
        "uptime": uptime,
        "python": python_version(),
        "pyrogram": versipyro,
        "version": BOT_VERSION,
        "emoji": _get(user_id, "ALIVE_EMOJI", "⚡️"),
        "text": _get(user_id, "ALIVE_TEXT_CUSTOM", "Salam, mən aktivəm."),
        "title": _get(user_id, "ALIVE_TITLE", "Ryhavean Userbot ⚡"),
        "group": GROUP,
        "channel": CHANNEL,
        "date": now.strftime("%d.%m.%Y"),
        "time": now.strftime("%H:%M:%S"),
    }
    out = template
    for key, val in values.items():
        out = out.replace("{" + key + "}", str(val))
    return premiumize(out)


async def get_globals(client):
    """Alive üçün loqo + emoji + mətni qaytarır (hamısı istifadəçiyə aiddir)."""
    user_id = client.me.id
    user_dir = f"user_{user_id}"
    os.makedirs(user_dir, exist_ok=True)

    logo = _get(user_id, "ALIVE_LOGO")
    if not logo:
        try:
            if client.me.photo:
                fname = "logo.mp4" if client.me.photo.has_animation else "logo.jpg"
                logo = await client.download_media(
                    client.me.photo.big_file_id, f"{user_dir}/{fname}"
                )
            else:
                logo = "userbot.jpg"
        except Exception:
            logo = "userbot.jpg"

    alive_logo = logo
    if isinstance(logo, bytes):
        output = f"{user_dir}/logo.jpg"
        with open(output, "wb") as fimage:
            fimage.write(base64.b64decode(logo))
        alive_logo = output
        try:
            if "video" in mime.from_file(output):
                alive_logo = rename_file(output, f"{user_dir}/logo.mp4")
        except Exception:
            pass

    emoji = _get(user_id, "ALIVE_EMOJI", "⚡️")
    alive_text = _get(user_id, "ALIVE_TEXT_CUSTOM", "Salam, mən aktivəm.")
    return user_id, alive_logo, emoji, alive_text


@Client.on_message(filters.command(["alive", "awake"], prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
@retry()
async def alive(client, message):
    user_id = client.me.id
    template = _get(user_id, "ALIVE_TEMPLATE", DEFAULT_TEMPLATE)
    text = await _render(client, template)

    xx = await edit_or_reply(message, premiumize("⚡️"))

    media_off = str(_get(user_id, "ALIVE_MEDIA", "on")).lower() in ("off", "0", "false", "no")
    if media_off:
        await xx.edit_text(text, disable_web_page_preview=True)
        return

    _, alive_logo, _, _ = await get_globals(client)
    is_video = isinstance(alive_logo, str) and alive_logo.lower().endswith((".mp4", ".gif", ".webm"))
    send = client.send_video if is_video else client.send_photo
    try:
        await send(message.chat.id, alive_logo, caption=text)
        with contextlib.suppress(Exception):
            await xx.delete()
    except Exception as exc:
        logging.getLogger("userbot.alive").warning("Alive media göndərilmədi: %s", exc)
        await xx.edit_text(text, disable_web_page_preview=True)


@Client.on_message(filters.command("ping", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
@retry()
async def pingme(client, message):
    uptime = await get_readable_time((time.time() - StartTime))
    start = datetime.datetime.now()

    loading_emojis = ["🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚", "🕛"]
    ping_frames = [
        "█▒▒▒▒▒▒▒▒▒▒ 10%",
        "███▒▒▒▒▒▒▒ 30%",
        "█████▒▒▒▒▒ 50%",
        "███████▒▒▒ 70%",
        "█████████▒ 90%",
        "██████████ 100%",
    ]

    msg = await edit_or_reply(message, "🏓 <b>Ping edilir...</b>")

    for frame in ping_frames:
        with contextlib.suppress(Exception):
            await msg.edit_text(f"<pre>{frame}</pre>{choice(loading_emojis)}")
        await asyncio.sleep(0.3)

    end = datetime.datetime.now()
    ping_duration = (end - start).total_seconds() * 1000

    if ping_duration < 100:
        status = "ƏLA 🟢"
    elif ping_duration < 200:
        status = "YAXŞI 🟡"
    else:
        status = "ORTA 🔴"

    response = (
        "╭──────────────────\n"
        "│   PONQ! 🏓\n"
        "├──────────────────\n"
        f"│ ⌚ Sürət: {ping_duration:.2f}ms\n"
        f"│ 📊 Status: {status}\n"
        f"│ ⏱️ İşləmə müddəti: {uptime}\n"
        f"│ 👑 Sahib: {client.me.mention}\n"
        "╰──────────────────\n"
    )

    quotes = ["İşıq sürəti! ⚡", "Sürət şeytanı! 🔥", "İldırım sürəti! ⚡", "Səs sürəti! 💨"]
    await msg.edit_text(response + f"\n<b>{choice(quotes)}</b>")


# ─────────────────────────────────────────────────────────────────────────────
# Alive ayarları
# ─────────────────────────────────────────────────────────────────────────────
@Client.on_message(filters.command("setalivetext", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def setalivetext(client, message):
    user_id = client.me.id
    text = get_arg(message)
    if not text and message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption
    if not text:
        return await edit_or_reply(
            message, "<b>Zəhmət olmasa mətn daxil edin və ya mətnə cavab verin.</b>"
        )
    set_gvar(user_id, "ALIVE_TEXT_CUSTOM", text)
    await edit_or_reply(message, f"✅ <b>ALIVE MƏTNİ dəyişdirildi:</b>\n\n{html.escape(text)}")


@Client.on_message(filters.command("setalivetitle", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def setalivetitle(client, message):
    title = get_arg(message)
    if not title:
        return await edit_or_reply(message, "<b>İstifadə:</b> <code>.setalivetitle Başlıq</code>")
    set_gvar(client.me.id, "ALIVE_TITLE", title)
    await edit_or_reply(message, f"✅ <b>ALIVE BAŞLIĞI dəyişdirildi:</b> {html.escape(title)}")


@Client.on_message(filters.command("setemoji", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def setemoji(client, message):
    emoji = get_arg(message)
    if not emoji:
        return await edit_or_reply(message, "<b>Zəhmət olmasa bir emoji daxil edin.</b>")
    set_gvar(client.me.id, "ALIVE_EMOJI", emoji)
    await edit_or_reply(message, f"✅ <b>ALIVE EMOJİSİ dəyişdirildi:</b> {emoji}")


@Client.on_message(filters.command(["setalivelogo", "setalivepic"], prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def setalivelogo(client, message):
    """Şəklə/videoya cavab verin və ya birbaşa URL yazın."""
    user_id = client.me.id
    reply = message.reply_to_message
    value = None
    if reply:
        if reply.photo:
            value = reply.photo.file_id
        elif reply.video:
            value = reply.video.file_id
        elif reply.animation:
            value = reply.animation.file_id
        elif reply.document:
            value = reply.document.file_id
    if not value:
        arg = get_arg(message)
        if arg and arg.startswith("http"):
            value = arg
    if not value:
        return await edit_or_reply(
            message,
            "<b>İstifadə:</b> şəklə/videoya cavab verin və ya "
            "<code>.setalivelogo https://...</code> yazın.",
        )
    set_gvar(user_id, "ALIVE_LOGO", value)
    await edit_or_reply(message, "✅ <b>ALIVE LOQOSU yeniləndi.</b>")


@Client.on_message(filters.command("setalivetemplate", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def setalivetemplate(client, message):
    """Alive mesajını tam olaraq öz şablonunla əvəz edir."""
    template = get_arg(message)
    if not template and message.reply_to_message:
        template = message.reply_to_message.text or message.reply_to_message.caption
    if not template:
        holders = " ".join(f"<code>{p}</code>" for p in PLACEHOLDERS)
        return await edit_or_reply(
            message,
            "<b>İstifadə:</b> <code>.setalivetemplate &lt;şablon&gt;</code> "
            "(və ya mətnə cavab verin)\n\n<b>Dəyişənlər:</b>\n" + holders,
        )
    set_gvar(client.me.id, "ALIVE_TEMPLATE", template)
    await edit_or_reply(message, "✅ <b>ALIVE ŞABLONU yadda saxlanıldı.</b> Yoxlamaq üçün <code>.alive</code>")


@Client.on_message(filters.command("alivemedia", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def alivemedia(client, message):
    """Alive mesajının şəkilli/şəkilsiz göndərilməsini idarə edir."""
    user_id = client.me.id
    current = str(_get(user_id, "ALIVE_MEDIA", "on")).lower()
    arg = (get_arg(message) or "").strip().lower()
    new = arg if arg in ("on", "off") else ("off" if current == "on" else "on")
    set_gvar(user_id, "ALIVE_MEDIA", new)
    await edit_or_reply(message, f"✅ <b>Alive medyası:</b> <code>{new}</code>")


@Client.on_message(filters.command(["alivesettings", "aliveinfo"], prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def alivesettings(client, message):
    user_id = client.me.id
    tmpl = _get(user_id, "ALIVE_TEMPLATE")
    lines = [
        "⚙️ <b>ALIVE AYARLARI</b> (MongoDB — yalnız sizə aiddir)\n",
        f"┃ 🏷 Başlıq: <code>{html.escape(str(_get(user_id, 'ALIVE_TITLE', 'Ryhavean Userbot ⚡')))}</code>",
        f"┃ 📝 Mətn: <code>{html.escape(str(_get(user_id, 'ALIVE_TEXT_CUSTOM', 'Salam, mən aktivəm.')))}</code>",
        f"┃ ⚡ Emoji: {_get(user_id, 'ALIVE_EMOJI', '⚡️')}",
        f"┃ 🖼 Loqo: <code>{'fərdi' if _get(user_id, 'ALIVE_LOGO') else 'profil şəkli'}</code>",
        f"┃ 🎞 Media: <code>{_get(user_id, 'ALIVE_MEDIA', 'on')}</code>",
        f"┃ 🧩 Şablon: <code>{'fərdi' if tmpl else 'standart'}</code>",
        "",
        "<b>Əmrlər:</b> <code>.setalivetext</code>, <code>.setalivetitle</code>, "
        "<code>.setemoji</code>, <code>.setalivelogo</code>, "
        "<code>.setalivetemplate</code>, <code>.alivemedia</code>, <code>.resetalive</code>",
    ]
    await edit_or_reply(message, "\n".join(lines))


@Client.on_message(filters.command(["resetalive", "resetallalive"], prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def deletealivekeys(client, message):
    user_id = client.me.id
    status = await edit_or_reply(message, "<code>Ayarlar silinir...</code>")
    try:
        user_sessions.update_one(
            {"user_id": user_id},
            {"$unset": {key: "" for key in ALIVE_KEYS}},
            upsert=True,
        )
        invalidate_session_cache(user_id)
    except Exception as exc:
        return await status.edit_text(styled_error(f"Silinmədi: {exc}"))
    await status.edit_text("✅ <b>Bütün alive ayarları standart hala qaytarıldı.</b>")
