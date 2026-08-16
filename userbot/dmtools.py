import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from tools import (
    HARDCODED_PREFIXES, edit_or_reply, sudoers_filter, retry,
    is_admin, get_args_from_caret
)
from utils.message import Msg

logger = logging.getLogger("userbot")


async def _dm_blast(client, message, *, verb, emoji, needs_text, make_provider, done_msg, sent_emoji):
    """Shared DM flood loop for dmspam.

    make_provider(args) -> callable returning the text to send on each iteration.
    """
    try:
        args = get_args_from_caret(message)

        # Get target user
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
            if needs_text:
                if not args or len(args) < 2:
                    await edit_or_reply(message, f"İstifadə qaydası: cavab + [prefix]dm{verb} <say> <mesaj>")
                    return
            else:
                if not args:
                    await edit_or_reply(message, f"İstifadə qaydası: cavab + [prefix]dm{verb} <say>")
                    return
            try:
                count = int(args[0])
            except ValueError:
                await edit_or_reply(message, Msg.ERR_INVALID_COUNT_NUMBER)
                return
        else:
            await edit_or_reply(message, Msg.ERR_REPLY_USER_MSG)
            return

        if count < 1 or count > 100:
            await edit_or_reply(message, Msg.ERR_COUNT_1_100)
            return

        provider = make_provider(args)

        if needs_text:
            preview = provider()
            if not preview or len(preview.strip()) == 0:
                await edit_or_reply(message, "Spam üçün bir mesaj daxil edin")
                return

        if is_admin(target_user.id):
            return await edit_or_reply(message, f"Sahibinə DM {verb} göndərmək mümkün deyil")

        status = await edit_or_reply(message, f"{emoji} {target_user.mention} istifadəçisinə DM {verb} göndərilir...")

        success_count = 0
        failed_count = 0

        for i in range(count):
            try:
                await client.send_message(target_user.id, provider())
                success_count += 1
                await asyncio.sleep(0.15)  # Delay to avoid flood
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await client.send_message(target_user.id, provider())
                success_count += 1
            except Exception as e:
                failed_count += 1
                if "blocked" in str(e).lower() or "user_is_blocked" in str(e).lower():
                    await status.edit(f"❌ **İstifadəçi botu bloklayıb!**\n✅ Göndərildi: {success_count}/{count}")
                    return

        await status.edit(
            f"{done_msg}\n\n"
            f"┃ {sent_emoji} Göndərildi: {success_count}/{count}\n"
            f"┃ ❌ Uğursuz: {failed_count}\n"
            f"╰━━━━━━━━━━━━━━━━━━━━╯"
        )

    except Exception as e:
        await edit_or_reply(message, f"❌ **Xəta:** {str(e)}")


@Client.on_message(filters.command("dmspam", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()) & filters.group)
async def dmspam(client: Client, message: Message):
    """Spam a user in their DM - works only in groups when replying to a user"""
    await _dm_blast(
        client, message,
        verb="spam", emoji="📨", needs_text=True,
        make_provider=lambda args: (lambda: " ".join(args[1:])),
        done_msg=Msg.OK_DM_SPAM_DONE, sent_emoji="📨",
    )
