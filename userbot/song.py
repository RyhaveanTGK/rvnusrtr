"""`.song` — @KeepMediaBot vasitəsilə musiqi endirmə.

İstifadə:
    .song <mahnı adı>          → adla axtarır
    audio/video-ya reply + .song → həmin faylı bota göndərib nəticəni alır
"""

import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

from tools import *  # noqa: F401,F403

logger = logging.getLogger("userbot.song")

TARGET_BOT = "KeepMediaBot"
CAPTION = '<a href="https://t.me/ryhaveanupdates/3">Ryhavean Download</a> 🪜'


class _BotListener:
    """@KeepMediaBot-dan gələn mesajları müvəqqəti olaraq tutur."""

    def __init__(self, client, bot_id):
        self.client = client
        self.queue = asyncio.Queue()
        self.handler = MessageHandler(self._on_message, filters.chat(bot_id) & filters.incoming)
        self.group = -99

    async def _on_message(self, _client, message):
        await self.queue.put(message)

    def __enter__(self):
        self.client.add_handler(self.handler, self.group)
        return self

    def __exit__(self, *exc):
        try:
            self.client.remove_handler(self.handler, self.group)
        except Exception:
            pass

    async def next(self, timeout: int = 30):
        return await asyncio.wait_for(self.queue.get(), timeout=timeout)


async def _click(msg, index):
    try:
        await msg.click(index)
        return True
    except Exception as exc:
        logger.debug("Düymə klikləmə xətası: %s", exc)
        return False


@Client.on_message(
    filters.command("song", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter())
)
async def song_handler(client, message):
    args = message.text.split(maxsplit=1)
    query = args[1].strip() if len(args) > 1 else ""
    reply = message.reply_to_message

    if not query and not reply:
        return await edit_or_reply(
            message,
            "ℹ️ **İstifadə:** `.song <mahnı adı>` və ya audio/video faylına reply edin.",
        )

    await edit_or_reply(message, "🔍 Axtarılır...")

    try:
        bot = await client.get_chat(TARGET_BOT)
    except Exception as exc:
        return await edit_or_reply(message, f"❌ Bota çatmaq olmadı: `{exc}`")

    try:
        with _BotListener(client, bot.id) as listener:
            await client.send_message(bot.id, "/start")
            await asyncio.sleep(2)
            # Salamlama mesajını təmizlə
            while not listener.queue.empty():
                listener.queue.get_nowait()

            if reply and reply.media:
                await reply.forward(bot.id)
                await asyncio.sleep(2)
                try:
                    first = await listener.next(timeout=45)
                except asyncio.TimeoutError:
                    return await edit_or_reply(message, "❌ Bot cavab vermədi.")
                if first.reply_markup:
                    await _click(first, 0)
            else:
                await client.send_message(bot.id, query)
                await asyncio.sleep(1)
                try:
                    first = await listener.next(timeout=45)
                except asyncio.TimeoutError:
                    return await edit_or_reply(message, "❌ Bot cavab vermədi.")
                if first.reply_markup:
                    await _click(first, 0)

            media_msg = None
            deadline = asyncio.get_event_loop().time() + 120
            while asyncio.get_event_loop().time() < deadline:
                try:
                    resp = await listener.next(timeout=20)
                except asyncio.TimeoutError:
                    break
                if resp.audio or resp.video or resp.document or resp.voice:
                    media_msg = resp
                    break
                if resp.reply_markup:
                    await _click(resp, 0)

        if not media_msg:
            return await edit_or_reply(message, "❌ Musiqi tapılmadı.")

        await media_msg.copy(message.chat.id, caption=CAPTION, parse_mode=enums.ParseMode.HTML)
        try:
            await message.delete()
        except Exception:
            pass

    except Exception as exc:
        logger.exception("song xətası")
        await edit_or_reply(message, f"❌ Xəta: `{exc}`")
