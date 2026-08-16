from pyrogram import Client, filters
from pyrogram.types import Message, MessageEntity
from pyrogram.enums import MessageEntityType
import asyncio
from config import *
from tools import *
from utils.message import Msg

async def _mentioned_me(_, client, message: Message):
    if not message.entities:
        return False

    for entity in message.entities:
        if entity.type == MessageEntityType.MENTION:
            mentioned_user = message.text[entity.offset:entity.offset + entity.length]
            if mentioned_user == f"@{client.me.username}":
                return True
        elif entity.type == MessageEntityType.TEXT_MENTION:
            if entity.user and entity.user.id == client.me.id:
                return True
    return False

mentioned_me = filters.create(_mentioned_me)

react_emojis = ['👍', '♥️', '🔥', '🎉']

@Client.on_message(mentioned_me & ~filters.bot, group=1)
async def auto_react_handler(client: Client, message: Message):
    try:
        user = await client.get_me()
        user_data = user_sessions.find_one({"user_id": user.id})
        if not user_data:
            return

        rc = user_data.get('react_control')
        if not isinstance(rc, int) or not (1 <= rc <= len(react_emojis)):
            return

        selected = react_emojis[rc - 1]

        chat = await client.get_chat(message.chat.id)
        cr = getattr(chat, "available_reactions", None)

        # Case 1: reactions disabled
        if cr is None:
            logger.debug(f"[REACTION] Disabled in chat {message.chat.id} for user {user.id}")
            return

        # Prepare usable emojis list
        if getattr(cr, "reactions", None):
            # Subset of allowed
            available = [r.emoji for r in cr.reactions if getattr(r, "emoji", None)]
        elif getattr(cr, "all_are_enabled", False):
            # All default emojis allowed, use your set
            available = react_emojis.copy()
        else:
            logger.debug(f"[REACTION] No usable reactions in chat {message.chat.id} for user {user.id}")
            return

        if not available:
            logger.debug(f"[REACTION] Empty available list in chat {message.chat.id} for user {user.id}")
            return

        # Determine which emoji to send
        emoji_to_send = selected if selected in available else available[0]

        await client.send_reaction(chat_id=message.chat.id,
                                   message_id=message.id,
                                   emoji=emoji_to_send)

    except Exception as e:
        logger.error(f"[REACTION] Auto-react error for user {client.me.id}: {e}")

# Reaction control commands with dynamic prefix
@Client.on_message(filters.command("react", prefixes=HARDCODED_PREFIXES) & filters.me)
async def react_control_command(client, message):
    """Control auto-reaction settings"""
    # Extract arguments using command args (filters.command automatically handles this)
    args = message.command[1:] if len(message.command) > 1 else []
    
    if not args:
        help_text = Msg.card(
            "Reaksiya Tənzimləmələri",
            [
                "[prefix]react on - reaksiyaları aktivləşdir",
                "[prefix]react off - reaksiyaları deaktiv et",
                "[prefix]react 1-4 - reaksiya seç",
                "[prefix]react status - cari vəziyyəti göstər",
            ],
            emoji=Msg.EMOJI_INFO,
            footer=f"1={Msg.EMOJI_THUMBS_UP}  2={Msg.EMOJI_HEART}  3={Msg.EMOJI_FIRE}  4={Msg.EMOJI_PARTY}",
        )
        await message.edit(help_text)
        return
    
    command = args[0].lower()
    user_id = client.me.id
    
    if command == "on":
        user_sessions.update_one(
            {"user_id": user_id},
            {"$set": {"react_control": 1}},
            upsert=True
        )
        await message.edit(Msg.card("Reaksiyalar Aktivləşdirildi", [f"Standart reaksiya: {Msg.EMOJI_THUMBS_UP}"], emoji=Msg.EMOJI_SUCCESS, footer="[prefix]react <1-4> dəyişmək üçün"))
        
    elif command == "off":
        user_sessions.update_one(
            {"user_id": user_id},
            {"$unset": {"react_control": ""}},
            upsert=True
        )
        await message.edit(Msg.card("Reaksiyalar Deaktiv Edildi", ["Avtomatik reaksiyalar söndürüldü"], emoji=Msg.EMOJI_WARNING, footer="[prefix]react on yenidən aktivləşdirmək üçün"))
        
    elif command == "status":
        user_data = user_sessions.find_one({"user_id": user_id})
        if user_data and "react_control" in user_data:
            rc = user_data["react_control"]
            if isinstance(rc, int) and 1 <= rc <= len(react_emojis):
                selected = react_emojis[rc - 1]
                await message.edit(Msg.card("Reaksiya Statusu", ["Status: Aktiv", f"Emoji: {selected}"], emoji=Msg.EMOJI_INFO))
            else:
                await message.edit(Msg.card("Reaksiya Statusu", ["Status: Deaktiv"], emoji=Msg.EMOJI_INFO))
        else:
            await message.edit(Msg.card("Reaksiya Statusu", ["Status: Deaktiv"], emoji=Msg.EMOJI_INFO))
            
    elif command.isdigit():
        try:
            reaction_num = int(command)
            if 1 <= reaction_num <= len(react_emojis):
                user_sessions.update_one(
                    {"user_id": user_id},
                    {"$set": {"react_control": reaction_num}},
                    upsert=True
                )
                selected = react_emojis[reaction_num - 1]
                await message.edit(Msg.card("Reaksiya Yeniləndi", [f"Yeni reaksiya: {selected}"], emoji=Msg.EMOJI_SUCCESS))
            else:
                await message.edit(Msg.card("Yanlış Nömrə", [f"1-dən {len(react_emojis)}-ə qədər istifadə edin"], emoji=Msg.EMOJI_ERROR))
        except ValueError:
            await message.edit(Msg.card("Yanlış Əmr", ["İstifadə üçün [prefix]react help əmrini işlədin"], emoji=Msg.EMOJI_ERROR))
    else:
        await message.edit(Msg.card("Yanlış Əmr", ["İstifadə üçün [prefix]react help əmrini işlədin"], emoji=Msg.EMOJI_ERROR))

@Client.on_message(filters.command("reactlist", prefixes=HARDCODED_PREFIXES) & filters.me)
async def react_list_command(client, message):
    """List available reactions"""
    await message.edit(Msg.card(
        "Mövcud Reaksiyalar",
        [f"{i}. {emoji}" for i, emoji in enumerate(react_emojis, 1)],
        emoji=Msg.EMOJI_INFO,
        footer="[prefix]react <nömrə> təyin etmək üçün",
    ))
