"""Ryhavean Userbot — idarəedici bot əmrləri (`app` klienti).

Bot yalnız lisenziyalı istifadəçilər üçün işləyir. Lisenziyanı yalnız bot
admini `/ver <user_id>` əmri ilə verir (standart 30 gün). İstifadəçi `/login`
ilə nömrə və kod daxil edərək öz userbotunu EYNİ server üzərində işə salır.
Bütün məlumatlar MongoDB-də saxlanılır və oradan çəkilir.
"""
import os
import sys
import time
import asyncio
import datetime
import logging
import html
from functools import wraps

import psutil
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from pyrogram.enums import ParseMode, ChatMemberStatus, ButtonStyle
from pyrogram.errors import (
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    FloodWait,
)
from utils.conversation import listen_message

from config import *
from tools import *
from utils.message import Msg, plain_text
from licensing import (
    grant_license,
    revoke_license,
    has_license,
    is_bot_admin,
    days_left,
    expiry_text,
    active_licenses,
    get_license,
)
from session_manager import (
    save_session,
    get_session,
    delete_session,
    start_userbot,
    stop_userbot,
)

logger = logging.getLogger("userbot")


def _user_data(user_id: int) -> dict:
    """İstifadəçi parametrlərini təhlükəsiz oxuyur.

    Baza (MongoDB/SQLite) əlçatan olmasa belə handler çökmür — boş dict qaytarır.
    """
    try:
        return user_sessions.find_one({"user_id": user_id}) or {"user_id": user_id}
    except Exception as exc:
        logger.error("Parametrlər oxunmadı (%s): %s", user_id, exc)
        return {"user_id": user_id}


def _save_user_data(user_id: int, changes: dict) -> bool:
    """Parametrləri təhlükəsiz yazır."""
    try:
        user_sessions.update_one({"user_id": user_id}, {"$set": changes}, upsert=True)
        return True
    except Exception as exc:
        logger.error("Parametrlər yazılmadı (%s): %s", user_id, exc)
        return False


def guard(func):
    """Handler-i sarıyır: xəta olsa da səssiz qalmır, istifadəçiyə bildirir.

    Əvvəl `/settings`, `/login`, `/status` kimi əmrlərdə yaranan hər hansı
    exception loga da düşmür, istifadəçi də cavab almırdı. Artıq xəta mətni
    həm loga yazılır, həm də cavab olaraq göndərilir.
    """
    @wraps(func)
    async def wrapper(client, update, *args, **kwargs):
        try:
            return await func(client, update, *args, **kwargs)
        except Exception as exc:
            logger.exception("Handler xətası (%s): %s", func.__name__, exc)
            xeta = (
                f"{Msg.EMOJI_ERROR} <b>Əmr yerinə yetirilmədi</b>\n"
                f"┃ Əmr: <code>{func.__name__}</code>\n"
                f"┃ Xəta: <code>{html.escape(str(exc))[:300]}</code>"
            )
            try:
                if isinstance(update, CallbackQuery):
                    await update.answer("Xəta baş verdi, bir az sonra yenidən yoxlayın.", show_alert=True)
                elif isinstance(update, Message):
                    await update.reply(xeta, parse_mode=ParseMode.HTML)
                elif isinstance(update, InlineQuery):
                    await update.answer(results=[], cache_time=0,
                                        switch_pm_text="Xəta baş verdi", switch_pm_parameter="error")
            except Exception:
                pass
    return wrapper


# ─────────────────────────── Mətnlər ───────────────────────────────────────
brief_explanation = f"""╭━━━ {Msg.EMOJI_ROCKET} <b>RYHAVEAN USERBOT</b> ━━━╮
┃ Telegram Avtomatlaşdırma Sistemi
╰━━━━━━━━━━━━━━━━━━━━━━━━━╯

{Msg.EMOJI_DRAGON} <b>İmkanlar</b>

{Msg.EMOJI_MUSIC} <b>Səsli Söhbət Pleyeri</b>
    {Msg.EMOJI_SPARK} Səsli söhbətdə audio/video yayımı
    {Msg.EMOJI_LOADING} Növbə, keçid, dayandırma və davam etdirmə

{Msg.EMOJI_NOTE} <b>Özünü Məhv Edən Media Yaddaşı</b>
    {Msg.EMOJI_LOCK} İtən foto və videoları saxlayır
    {Msg.EMOJI_SUCCESS} Şəxsi söhbətlərdə avtomatik işləyir

{Msg.EMOJI_SHIELD} <b>Qapalı Söhbətlərə Giriş</b>
    {Msg.EMOJI_LINK} Qapalı kanal/qruplardan yükləmə
    {Msg.EMOJI_SUCCESS} Admin icazəsi tələb olunmur

{Msg.EMOJI_DOWNLOAD} <b>Yükləmə Meneceri</b>
    {Msg.EMOJI_LINK} Telegram linkləri və HTTP/HTTPS ünvanları
    {Msg.EMOJI_STAR} Gedişat izləmə və avtomatik göndərmə

{Msg.EMOJI_GEAR} <b>Avtomatlaşdırma Alətləri</b>
    {Msg.EMOJI_PUZZLE} Süni intellekt, spam qoruması, sudo istifadəçilər
    {Msg.EMOJI_FIRE} Fərdi prefikslər və avtomatik reaksiyalar

────────────────────

{Msg.EMOJI_STAR} <b>Başlamaq üçün</b>
{Msg.EMOJI_USER} /login — öz userbotunu qur
{Msg.EMOJI_PUZZLE} /commands — bütün əmrləri araşdır
{Msg.EMOJI_GEAR} /settings — botunu fərdiləşdir
{Msg.EMOJI_PIN} /status — userbot vəziyyətini yoxla

────────────────────
{Msg.EMOJI_STAR} İcma: {COMMUNITY_GROUP_URL}
{Msg.EMOJI_ROCKET} Yeniliklər: {UPDATES_CHANNEL_URL}"""


def _links_keyboard() -> InlineKeyboardMarkup:
    """"Botlarımız" bölməsi — rəsmi Ryhavean kanal və qrup linkləri."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Yeniliklər Kanalı", url=UPDATES_CHANNEL_URL),
            InlineKeyboardButton("💬 İcma Qrupu", url=COMMUNITY_GROUP_URL),
        ],
        [InlineKeyboardButton("🤖 Botlarımız", callback_data="our_bots", style=ButtonStyle.PRIMARY)],
        [InlineKeyboardButton("🧩 Əmrlər", callback_data="back", style=ButtonStyle.PRIMARY)],
    ])


NO_LICENSE_TEXT = f"""{Msg.EMOJI_LOCK} <b>Giriş icazəniz yoxdur</b>

Bu bot yalnız icazə verilmiş istifadəçilər üçün işləyir.
İstifadə hüququ almaq üçün admin ilə əlaqə saxlayın.

{Msg.EMOJI_ID} Sizin İD: <code>{{user_id}}</code>

{Msg.EMOJI_LINK} İcma: {COMMUNITY_GROUP_URL}
{Msg.EMOJI_ROCKET} Yeniliklər: {UPDATES_CHANNEL_URL}"""


def _license_guard(user_id: int):
    """Lisenziya yoxdursa göstəriləcək mətni qaytarır, varsa None."""
    if has_license(user_id):
        return None
    return NO_LICENSE_TEXT.format(user_id=user_id)


# ─────────────────────────── Parametrlər paneli ────────────────────────────
def build_settings_ui(user_data: dict):
    """Parametrlər mesajını və düymələrini qurur."""
    spam_control  = user_data.get('Spam_control', True)
    game_control  = user_data.get('game', False)
    music_control = user_data.get('music', False)
    react_control = user_data.get('react_control', False)
    delete_count  = user_data.get('delete_count', 0)
    block_count   = user_data.get('block_count', 0)
    react_emojis  = ['👍', '♥️', '🔥', '🎉']

    ON, OFF = '✅', '❌'

    text = f"{Msg.EMOJI_GEAR} <b>Userbot Parametrləri</b> {Msg.EMOJI_GEAR}\n\n"
    text += f"<blockquote>{Msg.EMOJI_WAVE} Şəxsidə yeni istifadəçiləri qarşıla: {ON if spam_control else OFF}</blockquote>\n"
    if spam_control and delete_count > 0:
        text += f"<blockquote>{Msg.EMOJI_NOTE} Avtomatik silmə: {delete_count} mesajdan sonra</blockquote>\n"
    if spam_control and block_count > 0:
        text += f"<blockquote>{Msg.EMOJI_SHIELD} Avtomatik bloklama: {block_count} mesajdan sonra</blockquote>\n"
    text += f"<blockquote>{Msg.EMOJI_PUZZLE} Söz zənciri oyunu avtomatik: {ON if game_control else OFF}</blockquote>\n"
    text += f"<blockquote>{Msg.EMOJI_MUSIC} Musiqi plagini: {ON if music_control else OFF}</blockquote>\n"
    text += f"<blockquote>{Msg.EMOJI_THUMBS_UP} Avtomatik reaksiya: {ON if react_control else OFF}</blockquote>\n"
    if react_control:
        text += f"<blockquote>🎯 Reaksiya: {react_emojis[react_control - 1]}</blockquote>\n"

    welcome_mode = [
        InlineKeyboardButton(
            f"Avto-silmə {'['+str(delete_count)+']' if delete_count else OFF}",
            callback_data="toggle_delete_count",
            style=ButtonStyle.DANGER if delete_count else ButtonStyle.DEFAULT
        ),
        InlineKeyboardButton(
            f"Avto-blok {'['+str(block_count)+']' if block_count else OFF}",
            callback_data="toggle_block_count",
            style=ButtonStyle.DANGER if block_count else ButtonStyle.DEFAULT
        ),
    ]
    react_mode = [
        InlineKeyboardButton(
            f"[{emoji}]" if react_control == i else emoji,
            callback_data=f"toggle_react_{i}",
            style=ButtonStyle.PRIMARY if react_control == i else ButtonStyle.DEFAULT
        )
        for i, emoji in enumerate(react_emojis, 1)
    ]
    buttons = [
        [
            InlineKeyboardButton(f"Oyun {ON if game_control else OFF}",   callback_data="toggle_game",         style=ButtonStyle.SUCCESS if game_control  else ButtonStyle.DANGER),
            InlineKeyboardButton(f"Musiqi {ON if music_control else OFF}", callback_data="toggle_music",        style=ButtonStyle.SUCCESS if music_control else ButtonStyle.DANGER),
        ],
        [InlineKeyboardButton(f"Qarşılama {'⬇️' if spam_control else OFF}", callback_data="toggle_Spam_control", style=ButtonStyle.SUCCESS if spam_control else ButtonStyle.DANGER)],
        *([welcome_mode] if spam_control else []),
        [InlineKeyboardButton(f"Avto-reaksiya {'⬇️' if react_control else OFF}", callback_data="toggle_react_control", style=ButtonStyle.SUCCESS if react_control else ButtonStyle.DANGER)],
        *([react_mode] if react_control else []),
        [InlineKeyboardButton("✅ Hazırdır", callback_data="save_settings", style=ButtonStyle.SUCCESS)],
    ]
    return text, InlineKeyboardMarkup(buttons)


def _commands_keyboard():
    """Kateqoriya seçim düymələri."""
    keyboard_rows, row = [], []
    for category in categories.keys():
        row.append(InlineKeyboardButton(str(category), callback_data=f'category_{category}', style=ButtonStyle.PRIMARY))
        if len(row) == 2:
            keyboard_rows.append(row)
            row = []
    if row:
        keyboard_rows.append(row)
    return InlineKeyboardMarkup(keyboard_rows) if keyboard_rows else None


# ─────────────────────────── /start ────────────────────────────────────────
@Client.on_message(filters.command("start") & filters.private)
@guard
async def start_handler(client, message: Message):
    sender = message.from_user.id
    engel = _license_guard(sender)
    if engel:
        return await message.reply(engel, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    qalan = "limitsiz" if is_bot_admin(sender) else f"{days_left(sender)} gün"
    caption = brief_explanation + f"\n\n{Msg.EMOJI_CALENDAR} <b>Lisenziya:</b> {qalan}"
    try:
        await message.reply_photo(
            photo="userbot.jpg",
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=_links_keyboard(),
        )
    except Exception as e:
        logger.error(f"[BOT] Başlanğıc şəkli göndərilmədi: {e}")
        await message.reply(
            caption, parse_mode=ParseMode.HTML,
            reply_markup=_links_keyboard(), disable_web_page_preview=True,
        )


@Client.on_callback_query(filters.regex(r"^our_bots$"))
@guard
async def our_bots_handler(client, callback_query: CallbackQuery):
    text = (
        f"{Msg.EMOJI_ROCKET} <b>Botlarımız</b>\n\n"
        f"{Msg.EMOJI_STAR} <b>Ryhavean Userbot</b> — Telegram avtomatlaşdırma sistemi\n\n"
        f"📢 <b>Yeniliklər Kanalı:</b> {UPDATES_CHANNEL_URL}\n"
        f"💬 <b>İcma Qrupu:</b> {COMMUNITY_GROUP_URL}\n\n"
        f"{Msg.EMOJI_INFO} Bütün yeniliklər və dəstək üçün kanallarımıza qoşulun."
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📢 Kanal", url=UPDATES_CHANNEL_URL),
            InlineKeyboardButton("💬 İcma", url=COMMUNITY_GROUP_URL),
        ],
        [InlineKeyboardButton("« Geri", callback_data="back", style=ButtonStyle.PRIMARY)],
    ])
    await callback_query.edit_message_text(
        text, reply_markup=keyboard, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


# ─────────────────────────── Lisenziya idarəetməsi ─────────────────────────
@Client.on_message(filters.command("ver") & filters.private)
@guard
async def grant_handler(client, message: Message):
    """/ver <user_id> [gün] — istifadəçiyə 30 günlük icazə verir."""
    sender = message.from_user.id
    if not is_bot_admin(sender):
        return await message.reply(
            f"{Msg.EMOJI_LOCK} <b>Bu əmr yalnız adminlər üçündür.</b>",
            parse_mode=ParseMode.HTML,
        )

    args = message.text.split()
    if len(args) < 2 or not args[1].lstrip('-').isdigit():
        return await message.reply(
            f"{Msg.EMOJI_INFO} <b>İstifadə:</b> <code>/ver &lt;istifadəçi_id&gt; [gün]</code>\n"
            f"╰▸ Nümunə: <code>/ver 123456789</code> (30 gün)",
            parse_mode=ParseMode.HTML,
        )

    hedef = int(args[1])
    gun = int(args[2]) if len(args) > 2 and args[2].isdigit() else LICENSE_DAYS
    grant_license(hedef, gun, granted_by=sender)

    await message.reply(
        f"{Msg.EMOJI_SUCCESS} <b>İcazə verildi</b>\n"
        f"┃ İstifadəçi: <code>{hedef}</code>\n"
        f"┃ Müddət: <b>{gun} gün</b>\n"
        f"┃ Bitmə tarixi: <b>{expiry_text(hedef)}</b>",
        parse_mode=ParseMode.HTML,
    )

    try:
        await client.send_message(
            hedef,
            f"{Msg.EMOJI_PARTY} <b>Təbriklər!</b>\n\n"
            f"Ryhavean Userbot istifadə icazəniz aktivləşdirildi.\n"
            f"┃ Müddət: <b>{gun} gün</b>\n"
            f"┃ Bitmə tarixi: <b>{expiry_text(hedef)}</b>\n\n"
            f"{Msg.EMOJI_ROCKET} Başlamaq üçün /login əmrini göndərin.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        logger.debug("İstifadəçiyə bildiriş göndərilmədi: %s", exc)


@Client.on_message(filters.command("unver") & filters.private)
@guard
async def revoke_handler(client, message: Message):
    """/unver <user_id> — icazəni ləğv edir."""
    sender = message.from_user.id
    if not is_bot_admin(sender):
        return await message.reply(
            f"{Msg.EMOJI_LOCK} <b>Bu əmr yalnız adminlər üçündür.</b>",
            parse_mode=ParseMode.HTML,
        )

    args = message.text.split()
    if len(args) < 2 or not args[1].lstrip('-').isdigit():
        return await message.reply(
            f"{Msg.EMOJI_INFO} <b>İstifadə:</b> <code>/unver &lt;istifadəçi_id&gt;</code>",
            parse_mode=ParseMode.HTML,
        )

    hedef = int(args[1])
    revoke_license(hedef)
    await stop_userbot(hedef)
    await message.reply(
        f"{Msg.EMOJI_SUCCESS} <b>İcazə ləğv edildi:</b> <code>{hedef}</code>",
        parse_mode=ParseMode.HTML,
    )


@Client.on_message(filters.command("users") & filters.private)
@guard
async def users_handler(client, message: Message):
    """/users — aktiv lisenziyaların siyahısı."""
    if not is_bot_admin(message.from_user.id):
        return await message.reply(
            f"{Msg.EMOJI_LOCK} <b>Bu əmr yalnız adminlər üçündür.</b>",
            parse_mode=ParseMode.HTML,
        )

    siyahi = active_licenses()
    if not siyahi:
        return await message.reply(
            f"{Msg.EMOJI_INFO} <b>Aktiv lisenziyalı istifadəçi yoxdur.</b>",
            parse_mode=ParseMode.HTML,
        )

    setirler = [f"{Msg.EMOJI_CROWN} <b>Aktiv istifadəçilər: {len(siyahi)}</b>\n"]
    for doc in siyahi[:50]:
        uid = doc["user_id"]
        aktiv = "🟢" if uid in clients else "🔴"
        setirler.append(f"{aktiv} <code>{uid}</code> — {days_left(uid)} gün ({expiry_text(uid)})")
    await message.reply("\n".join(setirler), parse_mode=ParseMode.HTML)


@Client.on_message(filters.command("mylicense") & filters.private)
@guard
async def my_license_handler(client, message: Message):
    """/mylicense — öz lisenziya məlumatın."""
    sender = message.from_user.id
    doc = get_license(sender)
    if is_bot_admin(sender):
        return await message.reply(
            f"{Msg.EMOJI_CROWN} <b>Siz adminsiniz — limitsiz giriş.</b>",
            parse_mode=ParseMode.HTML,
        )
    if not doc or not has_license(sender):
        return await message.reply(NO_LICENSE_TEXT.format(user_id=sender),
                                   parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await message.reply(
        f"{Msg.EMOJI_CALENDAR} <b>Lisenziya məlumatınız</b>\n"
        f"┃ İD: <code>{sender}</code>\n"
        f"┃ Qalan müddət: <b>{days_left(sender)} gün</b>\n"
        f"┃ Bitmə tarixi: <b>{expiry_text(sender)}</b>",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────── /login ────────────────────────────────────────
@Client.on_message(filters.command("login") & filters.private)
@guard
async def login_handler(client, message: Message):
    """Nömrə və kod ilə userbot qurulumu — hamısı eyni server üzərində işləyir."""
    sender = message.from_user.id
    engel = _license_guard(sender)
    if engel:
        return await message.reply(engel, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    if sender in clients:
        return await message.reply(
            f"{Msg.EMOJI_INFO} <b>Userbotunuz artıq işləyir.</b>\n"
            f"╰▸ Dayandırmaq üçün /logout əmrindən istifadə edin.",
            parse_mode=ParseMode.HTML,
        )

    await message.reply(
        f"{Msg.EMOJI_USER} <b>Userbot qurulumu başladı</b>\n\n"
        f"Telefon nömrənizi beynəlxalq formatda göndərin.\n"
        f"╰▸ Nümunə: <code>+994501234567</code>\n\n"
        f"{Msg.EMOJI_WARNING} Ləğv etmək üçün <code>/cancel</code> yazın.",
        parse_mode=ParseMode.HTML,
    )

    cavab = await listen_message(client, message.chat.id, timeout=180)
    if cavab is None:
        return await message.reply(f"{Msg.EMOJI_ERROR} <b>Vaxt bitdi.</b> Yenidən /login yazın.",
                                   parse_mode=ParseMode.HTML)
    if (cavab.text or "").strip().lower() in ("/cancel", "ləğv", "legv"):
        return await cavab.reply(f"{Msg.EMOJI_INFO} <b>Qurulum ləğv edildi.</b>", parse_mode=ParseMode.HTML)

    nomre = (cavab.text or "").strip().replace(" ", "")
    if not nomre.startswith("+") or not nomre[1:].isdigit():
        return await cavab.reply(
            f"{Msg.EMOJI_ERROR} <b>Nömrə formatı yanlışdır.</b> Yenidən /login yazın.",
            parse_mode=ParseMode.HTML,
        )

    userbot = Client(
        f"login_{sender}",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True,
    )

    try:
        await userbot.connect()
    except Exception as exc:
        return await cavab.reply(
            f"{Msg.EMOJI_ERROR} <b>Serverə qoşulmaq alınmadı:</b> <code>{exc}</code>",
            parse_mode=ParseMode.HTML,
        )

    try:
        kod_info = await userbot.send_code(nomre)
    except PhoneNumberInvalid:
        await userbot.disconnect()
        return await cavab.reply(f"{Msg.EMOJI_ERROR} <b>Telefon nömrəsi yanlışdır.</b>",
                                 parse_mode=ParseMode.HTML)
    except FloodWait as fw:
        await userbot.disconnect()
        return await cavab.reply(
            f"{Msg.EMOJI_WARNING} <b>Çox cəhd edildi.</b> {fw.value} saniyə sonra yenidən yoxlayın.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        await userbot.disconnect()
        return await cavab.reply(f"{Msg.EMOJI_ERROR} <b>Kod göndərilmədi:</b> <code>{exc}</code>",
                                 parse_mode=ParseMode.HTML)

    await cavab.reply(
        f"{Msg.EMOJI_CHAT} <b>Telegram-a gələn təsdiq kodunu göndərin.</b>\n"
        f"╰▸ Kodu <b>aralarına boşluq və ya defis qoyaraq</b> yazın: <code>1 2 3 4 5</code>\n"
        f"╰▸ Bu, Telegram-ın kodu ləğv etməməsi üçündür.",
        parse_mode=ParseMode.HTML,
    )

    kod_mesaj = await listen_message(client, message.chat.id, timeout=300)
    if kod_mesaj is None:
        await userbot.disconnect()
        return await message.reply(f"{Msg.EMOJI_ERROR} <b>Vaxt bitdi.</b> Yenidən /login yazın.",
                                   parse_mode=ParseMode.HTML)

    kod = "".join(ch for ch in (kod_mesaj.text or "") if ch.isdigit())

    try:
        await userbot.sign_in(nomre, kod_info.phone_code_hash, kod)
    except PhoneCodeInvalid:
        await userbot.disconnect()
        return await kod_mesaj.reply(f"{Msg.EMOJI_ERROR} <b>Kod yanlışdır.</b> Yenidən /login yazın.",
                                     parse_mode=ParseMode.HTML)
    except PhoneCodeExpired:
        await userbot.disconnect()
        return await kod_mesaj.reply(f"{Msg.EMOJI_ERROR} <b>Kodun vaxtı bitib.</b> Yenidən /login yazın.",
                                     parse_mode=ParseMode.HTML)
    except SessionPasswordNeeded:
        await kod_mesaj.reply(
            f"{Msg.EMOJI_LOCK} <b>İki mərhələli doğrulama aktivdir.</b>\n"
            f"╰▸ Buludlu şifrənizi (2FA) göndərin.",
            parse_mode=ParseMode.HTML,
        )
        sifre_mesaj = await listen_message(client, message.chat.id, timeout=300)
        if sifre_mesaj is None:
            await userbot.disconnect()
            return await message.reply(f"{Msg.EMOJI_ERROR} <b>Vaxt bitdi.</b> Yenidən /login yazın.",
                                       parse_mode=ParseMode.HTML)
        try:
            await userbot.check_password((sifre_mesaj.text or "").strip())
        except PasswordHashInvalid:
            await userbot.disconnect()
            return await sifre_mesaj.reply(f"{Msg.EMOJI_ERROR} <b>Şifrə yanlışdır.</b> Yenidən /login yazın.",
                                           parse_mode=ParseMode.HTML)
        except Exception as exc:
            await userbot.disconnect()
            return await sifre_mesaj.reply(f"{Msg.EMOJI_ERROR} <b>Xəta:</b> <code>{exc}</code>",
                                           parse_mode=ParseMode.HTML)
        try:
            await sifre_mesaj.delete()
        except Exception:
            pass
    except Exception as exc:
        await userbot.disconnect()
        return await kod_mesaj.reply(f"{Msg.EMOJI_ERROR} <b>Giriş alınmadı:</b> <code>{exc}</code>",
                                     parse_mode=ParseMode.HTML)

    # Sessiyanı MongoDB-yə yaz və userbotu bu serverdə işə sal
    try:
        session_string = await userbot.export_session_string()
        me = await userbot.get_me()
    except Exception as exc:
        await userbot.disconnect()
        return await message.reply(f"{Msg.EMOJI_ERROR} <b>Sessiya alınmadı:</b> <code>{exc}</code>",
                                   parse_mode=ParseMode.HTML)
    finally:
        try:
            await userbot.disconnect()
        except Exception:
            pass

    save_session(sender, session_string, phone=nomre, name=me.first_name or "")

    gozle = await message.reply(f"{Msg.EMOJI_LOADING} <b>Userbot işə salınır...</b>", parse_mode=ParseMode.HTML)
    aktiv = await start_userbot(sender, session_string)

    if aktiv is None:
        return await gozle.edit(
            f"{Msg.EMOJI_ERROR} <b>Userbot işə salına bilmədi.</b> Bir az sonra yenidən cəhd edin.",
            parse_mode=ParseMode.HTML,
        )

    await gozle.edit(
        f"{Msg.EMOJI_SUCCESS} <b>Userbotunuz aktivdir!</b>\n\n"
        f"┃ Hesab: <b>{me.first_name}</b>\n"
        f"┃ İD: <code>{me.id}</code>\n"
        f"┃ Lisenziya: <b>{days_left(sender)} gün</b>\n\n"
        f"{Msg.EMOJI_ROCKET} Rəsmi kanallara avtomatik qoşulduq.\n"
        f"{Msg.EMOJI_PUZZLE} Əmrlər üçün /commands yazın.\n"
        f"{Msg.EMOJI_INFO} Prefikslər: <code>. ! ? ^ _</code>",
        parse_mode=ParseMode.HTML,
    )


@Client.on_message(filters.command("logout") & filters.private)
@guard
async def logout_handler(client, message: Message):
    """Userbotu dayandırır və sessiyanı bazadan çıxarır."""
    sender = message.from_user.id
    dayandi = await stop_userbot(sender)
    delete_session(sender)
    if dayandi:
        await message.reply(
            f"{Msg.EMOJI_SUCCESS} <b>Userbotunuz dayandırıldı və sessiya silindi.</b>\n"
            f"╰▸ Yenidən qurmaq üçün /login yazın.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await message.reply(
            f"{Msg.EMOJI_INFO} <b>Aktiv userbotunuz yoxdur.</b>",
            parse_mode=ParseMode.HTML,
        )


# ─────────────────────────── /ping ─────────────────────────────────────────
@Client.on_message(filters.command("ping") & filters.private)
@guard
async def ping_command(client, message: Message):
    uptime = await get_readable_time((time.time() - StartTime))
    start = datetime.datetime.now()
    xx = await message.reply("**Yoxlanılır...**")
    end = datetime.datetime.now()
    delta_ping = round((end - start).microseconds / 1000, 3)

    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    process = psutil.Process()
    _ping = (
        f"╭━━━ {Msg.EMOJI_PONG} <b>PONQ</b> ━━━╮\n"
        f"┃\n"
        f"┃ {Msg.EMOJI_ROCKET} Sürət: {str(delta_ping).replace('.', ',')} ms\n"
        f"┃ {Msg.EMOJI_LOADING} İşləmə müddəti: {uptime}\n"
        f"┃\n"
        f"┃ {Msg.EMOJI_FOLDER} Server statistikası\n"
        f"┃ ▸ Prosessor: {cpu}%\n"
        f"┃ ▸ Operativ yaddaş: {mem}%\n"
        f"┃ ▸ Disk: {disk}%\n"
        f"┃ ▸ İstifadə olunan yaddaş: {round(process.memory_info()[0] / 1024 ** 2)} MB\n"
        f"╰━━━━━━━━━━━━━━━━━━╯"
    )
    await xx.edit(_ping, parse_mode=ParseMode.HTML)


# ─────────────────────────── /commands ─────────────────────────────────────
@Client.on_message(filters.command(["commands", "help", "menu", "yardim"]) & filters.private)
@guard
async def commands_handler(client, message: Message):
    engel = _license_guard(message.from_user.id)
    if engel:
        return await message.reply(engel, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    markup = _commands_keyboard()
    if markup is None:
        await message.reply(
            f"{Msg.EMOJI_PIN} <b>Heç bir kateqoriya tapılmadı.</b>",
            parse_mode=ParseMode.HTML,
        )
        return
    await message.reply(
        f"{Msg.EMOJI_PIN} <b>Əmrləri görmək üçün kateqoriya seçin:</b>",
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )


@Client.on_callback_query(filters.regex(r'^category_'))
@guard
async def category_handler(client, callback_query: CallbackQuery):
    category = '_'.join(callback_query.data.split('_')[1:])

    category_commands = categories.get(category, [])
    if category_commands:
        items = []
        for cmd in category_commands:
            raw = commands.get(cmd, 'Təsvir mövcud deyil')
            desc, usage, example, note, warning, flags = parse_help_entry(raw)
            clean_cmd = str(cmd).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            clean_desc = str(desc).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            items.append(f"<b>{clean_cmd}</b> - {clean_desc}")
        category_description = "\n\n".join(items)
    else:
        category_description = "<i>Bu kateqoriyada hələ əmr yoxdur.</i>"

    prefix_list = ", ".join(f"<code>{p}</code>" for p in HARDCODED_PREFIXES)
    prefix_info = f"\n\n<b>Mövcud prefikslər:</b> {prefix_list}"

    text = f"{Msg.EMOJI_ROCKET} <b>{category} ƏMRLƏRİ:</b>\n\n{category_description}{prefix_info}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("« Geri", callback_data='back', style=ButtonStyle.PRIMARY)]
    ])
    await callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@Client.on_callback_query(filters.regex(r'^back$'))
@guard
async def back_handler(client, callback_query: CallbackQuery):
    markup = _commands_keyboard()
    if markup is None:
        await callback_query.edit_message_text(
            f"{Msg.EMOJI_PIN} <b>Heç bir kateqoriya tapılmadı.</b>",
            parse_mode=ParseMode.HTML,
        )
        return
    await callback_query.edit_message_text(
        f"{Msg.EMOJI_PIN} <b>Əmrləri görmək üçün kateqoriya seçin:</b>",
        reply_markup=markup,
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────── /settings ─────────────────────────────────────
@Client.on_message(filters.command("settings") & filters.private)
@guard
async def settings_handler(client, message: Message):
    sender_id = message.from_user.id
    engel = _license_guard(sender_id)
    if engel:
        return await message.reply(engel, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    user_data = _user_data(sender_id)
    text, markup = build_settings_ui(user_data)
    await message.reply(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@Client.on_callback_query(filters.regex(r"^toggle_"))
@guard
async def toggle_setting(client, callback_query: CallbackQuery):
    sender_id = callback_query.from_user.id
    user_data = _user_data(sender_id)

    setting = callback_query.data.split("_", 1)[1]
    allowed_counts = [0, 3, 5, 10]

    if setting in ('delete_count', 'block_count'):
        v = user_data.get(setting, 0) + 1
        while v not in allowed_counts:
            v += 1
            if v > 10:
                v = 0
        new_value = v
    elif setting == 'react_control':
        new_value = False if user_data.get('react_control') else 3
    elif setting.startswith('react_'):
        new_value = int(setting.split('_')[1])
        setting = 'react_control'
    else:
        new_value = not user_data.get(setting, False)

    _save_user_data(sender_id, {setting: new_value})

    if setting == 'game':
        games[sender_id] = new_value

    user_data = _user_data(sender_id)
    text, markup = build_settings_ui(user_data)
    await callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)


@Client.on_callback_query(filters.regex(r"^save_settings$"))
@guard
async def save_settings(client, callback_query: CallbackQuery):
    await callback_query.edit_message_text(
        f"{Msg.EMOJI_SUCCESS} <b>Parametrlər yadda saxlanıldı</b>\n\n"
        f"┃ Seçimləriniz tətbiq edildi.",
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────── /status ───────────────────────────────────────
@Client.on_message(filters.command("status") & filters.private)
@guard
async def status_handler(client, message: Message):
    engel = _license_guard(message.from_user.id)
    if engel:
        return await message.reply(engel, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    command_args = message.text.split()
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    elif len(command_args) > 1:
        arg = command_args[1]
        if arg.isdigit():
            user_id = int(arg)
        else:
            try:
                user_id = (await client.get_users(arg)).id
            except Exception:
                return await message.reply("Bu istifadəçi adı ilə hesab tapılmadı.")
    else:
        user_id = message.from_user.id

    try:
        tg_user = await client.get_users(user_id)
        user_name = f"{tg_user.first_name or ''} {tg_user.last_name or ''}".strip() or "Naməlum"
        username_str = f"@{tg_user.username}" if tg_user.username else "Yoxdur"
    except Exception:
        user_name, username_str = "Naməlum", "Yoxdur"

    userbot_status = "Qoşulub 🟢" if clients.get(user_id) is not None else "Bağlıdır 🔴"
    uptime = await get_readable_time((time.time() - StartTime))

    app_data = _user_data(user_id)
    spam_control = "✅" if app_data.get('Spam_control', True) else "❌"
    game = "✅" if app_data.get('game', False) else "❌"
    music = "✅" if app_data.get('music', False) else "❌"

    status_message = f"""┏━━━ {Msg.EMOJI_CROWN} <b>İSTİFADƏÇİ VƏZİYYƏTİ</b> ━━━

👤 <b>Hesab məlumatları:</b>
• <b>Ad:</b> {user_name}
• <b>İstifadəçi adı:</b> {username_str}
• <b>İstifadəçi İD:</b> <code>{user_id}</code>
• <b>Userbot vəziyyəti:</b> {userbot_status}
• <b>İşləmə müddəti:</b> {uptime}
• <b>Lisenziya:</b> {days_left(user_id)} gün ({expiry_text(user_id)})

{Msg.EMOJI_GEAR} <b>Userbot parametrləri:</b>
• Qarşılama mesajı: {spam_control}
• Söz zənciri botu: {game}
• Musiqi botu: {music}
┗━━━━━━━━━━━━━━━━━━"""

    await message.reply(status_message, parse_mode=ParseMode.HTML)


# ─────────────────────────── inline sorğu ──────────────────────────────────
@Client.on_inline_query()
@guard
async def inline_query_handler(client, query: InlineQuery):
    user_id = query.from_user.id
    command_args = query.query.split()

    if len(command_args) == 2 and command_args[0].lower() == 'banall':
        try:
            chat_id = int(command_args[1])
        except ValueError:
            result = InlineQueryResultArticle(
                id="banall_invalid_id",
                title="BANALL - Yanlış İD",
                description="Söhbət İD formatı yanlışdır",
                input_message_content=InputTextMessageContent(plain_text("❌ Söhbət İD formatı yanlışdır")),
            )
            return await query.answer(results=[result], cache_time=0)

        userbot = clients.get(user_id)
        if not userbot:
            result = InlineQueryResultArticle(
                id="banall_no_client",
                title="BANALL - Klient yoxdur",
                description="Userbot aktiv deyil",
                input_message_content=InputTextMessageContent(plain_text("❌ Userbotunuz aktiv deyil")),
            )
            return await query.answer(results=[result], cache_time=0)

        try:
            member = await userbot.get_chat_member(chat_id, user_id)
            is_owner = member.status == ChatMemberStatus.OWNER
            is_admin_ok = (
                member.status == ChatMemberStatus.ADMINISTRATOR
                and member.privileges and member.privileges.can_restrict_members
            )
            if not (is_owner or is_admin_ok):
                result = InlineQueryResultArticle(
                    id="banall_no_perms",
                    title="BANALL - İcazə yoxdur",
                    description="Admin və istifadəçi banlama icazəsi lazımdır",
                    input_message_content=InputTextMessageContent(
                        plain_text("❌ Bu qrupda 'istifadəçiləri banlamaq' icazəsi olan admin olmalısınız.")
                    ),
                )
                return await query.answer(results=[result], cache_time=0)

            chat = await userbot.get_chat(chat_id)
            members_count = await userbot.get_chat_members_count(chat_id)
            banall_message = (
                f"⚠️ <b>Bütün İstifadəçiləri Banlamağı Təsdiqlə</b> ⚠️\n\n"
                f"<b>Qrup:</b> {chat.title}\n"
                f"<b>Ümumi üzv:</b> {members_count}\n\n"
                f"Bu qrupdakı bütün istifadəçiləri banlamaq istədiyinizi təsdiqləyin."
            )
            buttons = InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Ləğv et", callback_data=f"banall_cancel_{chat_id}", style=ButtonStyle.DANGER),
                InlineKeyboardButton("✅ Təsdiqlə", callback_data=f"banall_confirm_{chat_id}", style=ButtonStyle.SUCCESS),
            ]])
            result = InlineQueryResultArticle(
                id=f"banall_{chat_id}",
                title="BANALL - Təsdiq",
                description=f"{chat.title} qrupundakı bütün istifadəçiləri banla",
                input_message_content=InputTextMessageContent(banall_message, parse_mode=ParseMode.HTML),
                reply_markup=buttons,
            )
            return await query.answer(results=[result], cache_time=0)
        except Exception as e:
            result = InlineQueryResultArticle(
                id="banall_error",
                title="BANALL - Xəta",
                description="İcazələr yoxlanıla bilmədi",
                input_message_content=InputTextMessageContent(plain_text(f"❌ Xəta: {e}")),
            )
            return await query.answer(results=[result], cache_time=0)

    info = query.from_user
    name = (info.first_name or "") + (f" {info.last_name}" if info.last_name else "")
    username = f"@{info.username}" if info.username else "İstifadəçi adı yoxdur"
    connected = clients.get(user_id) is not None
    status_message = (
        f"<blockquote>{Msg.EMOJI_STAR} <b>Ryhavean Userbot</b></blockquote>\n"
        f"<b>Ad:</b> {name}\n"
        f"<b>İstifadəçi adı:</b> {username}\n"
        f"<b>İstifadəçi İD:</b> <code>{user_id}</code>\n"
        f"<blockquote><i>Userbot vəziyyəti: {'Qoşulub 🟢' if connected else 'Bağlıdır 🔴'}</i></blockquote>"
    )
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("ƏMRLƏR", callback_data="back", style=ButtonStyle.PRIMARY)]])
    result = InlineQueryResultArticle(
        id=str(user_id),
        title="VƏZİYYƏT",
        description="Userbot vəziyyətinizi yoxlayın",
        input_message_content=InputTextMessageContent(status_message, parse_mode=ParseMode.HTML),
        reply_markup=buttons,
    )
    await query.answer(results=[result], cache_time=0)


# ─────────────────────────── banall düymələri ──────────────────────────────
@Client.on_callback_query(filters.regex(r"^banall_(cancel|confirm)_(-?\d+)"))
@guard
async def banall_callback_handler(client, callback_query: CallbackQuery):
    match = callback_query.matches[0]
    action = match.group(1)
    chat_id = int(match.group(2))
    sender = callback_query.from_user.id

    if action != "confirm":
        return await callback_query.edit_message_text("❌ Əmr ləğv edildi")

    userbot = clients.get(sender)
    if not userbot:
        return await callback_query.edit_message_text("❌ Userbot mövcud deyil")

    try:
        chat = await userbot.get_chat(chat_id)
        banned_count = 0
        total_users = 0
        async for member in userbot.get_chat_members(chat_id):
            total_users += 1
            try:
                if member.user.id != sender:
                    await userbot.ban_chat_member(chat_id, member.user.id)
                    banned_count += 1
                    if banned_count % 10 == 0:
                        try:
                            await callback_query.edit_message_text(
                                f"🔨 <b>Banlama davam edir...</b>\n\n"
                                f"<b>Qrup:</b> {chat.title}\n"
                                f"<b>Banlandı:</b> {banned_count}/{total_users}",
                                parse_mode=ParseMode.HTML,
                            )
                        except Exception:
                            pass
            except Exception:
                continue
        rate = (banned_count / total_users * 100) if total_users else 0
        await callback_query.edit_message_text(
            f"✅ <b>Banlama tamamlandı</b>\n\n"
            f"<b>Qrup:</b> {chat.title}\n"
            f"<b>Ümumi üzv:</b> {total_users}\n"
            f"<b>Uğurla banlandı:</b> {banned_count}\n"
            f"<b>Uğur nisbəti:</b> {rate:.1f}%",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await callback_query.edit_message_text(f"❌ Banlama zamanı xəta: {e}")


# ─────────────────────────── /stop və /restart ─────────────────────────────
_known_owners = set()


def _is_owner(user_id):
    """Sahib yoxlaması — /stop-dan sonra da işləyir."""
    if is_admin(user_id) or is_bot_admin(user_id):
        _known_owners.add(user_id)
        return True
    return user_id in _known_owners


@Client.on_message(filters.command("stop") & filters.private)
@guard
async def stop_handler(client, message: Message):
    sender = message.from_user.id
    if not _is_owner(sender):
        return await message.reply(
            f"{Msg.EMOJI_LOCK} <b>Yalnız sahib üçün.</b> Bu əmr userbot sahibinə məxsusdur.",
            parse_mode=ParseMode.HTML,
        )

    userbot = clients.get(sender)
    if userbot is None:
        return await message.reply(
            f"{Msg.EMOJI_INFO} <b>Userbot artıq dayandırılıb.</b>\n"
            f"╰▸ Yenidən işə salmaq üçün /restart yazın.",
            parse_mode=ParseMode.HTML,
        )
    await message.reply(
        f"{Msg.EMOJI_WARNING} <b>Userbot dayandırılır...</b>\n"
        f"╰▸ Yenidən işə salmaq üçün /restart yazın.",
        parse_mode=ParseMode.HTML,
    )
    try:
        await userbot.stop()
    except Exception as e:
        logger.warning(f"[BOT] Userbot dayandırılarkən xəta: {e}")
    clients.pop(sender, None)


@Client.on_message(filters.command("restart") & filters.private)
@guard
async def restart_handler(client, message: Message):
    sender = message.from_user.id
    if not _is_owner(sender):
        return await message.reply(
            f"{Msg.EMOJI_LOCK} <b>Yalnız sahib üçün.</b> Bu əmr userbot sahibinə məxsusdur.",
            parse_mode=ParseMode.HTML,
        )

    await message.reply(
        f"{Msg.EMOJI_LOADING} <b>Yenidən başladılır...</b>\n"
        f"╰▸ Proses bir neçə saniyəyə yenidən qalxacaq.",
        parse_mode=ParseMode.HTML,
    )
    await asyncio.sleep(1)
    logger.info("[BOT] Yenidən başlatma tələbi: %s", sender)
    os.execv(sys.executable, [sys.executable, *sys.argv])
