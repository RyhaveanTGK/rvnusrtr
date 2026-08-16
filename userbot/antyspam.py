
import datetime
import asyncio
import os
import base64
import magic
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from config import *
from tools import *

logger = logging.getLogger("antyspam")

# Initialize magic for file type detection
mime = magic.Magic(mime=True)

# Support filter
is_support = filters.create(lambda _, __, message: message.chat.is_support)

# Custom filter for spam control
def crcustom_filter():
    def filte_func(_, client, message):
         user_data = cached_get_user_data(client.me.id)
         spam_control = user_data.get('Spam_control', 'True')
         if spam_control == 'False':
            return False
         white_listed = user_data.get('white_listed', [])
         if not message.from_user:
           return False
         sender_id = message.from_user.id
         if sender_id in white_listed:
            return False
         return True
    return filters.create(filte_func)

@Client.on_message(filters.private & ~filters.me & ~filters.bot & crcustom_filter())
@retry()
async def handle_user(client, message):
    if getattr(message, 'service', None):
        return
        
    logger.debug("Handling user...")
    sender_id = message.from_user.id

    # Check if the user is an admin
    if os.path.exists(admin_file):
        with open(admin_file, "r") as file:
            admin_ids = [int(line.strip()) for line in file.readlines()]
            if sender_id in admin_ids:
               return
    if message.chat.id == 777000:
      return
    logger.debug(f"Sender ID: {sender_id}")
    # Check if user is whitelisted
    user_data = user_sessions.find_one({"user_id": client.me.id})
    if user_data:
        users = user_data.get('users', {})
        spam_control = user_data.get('Spam_control', True)
        if not spam_control:
            logger.debug("Spam control is off, returning.")
            return
        white_listed = user_data.get('white_listed', [])
        if sender_id in white_listed:
            logger.debug("User is whitelisted. Skipping...")
            return
    
    # Update user count in user_sessions
    user_sessions.update_one(
        {"user_id": client.me.id},
        {
            "$inc": {f"users.{sender_id}": 1},
        },
        upsert=True
    )
    logger.debug("User count updated.")

    # Check if user should be blocked
    user_data = user_sessions.find_one({"user_id": client.me.id})
    if user_data:
        users = user_data.get('users', {})
        user_count = users.get(str(sender_id), 0)
        session_name = f'user_{client.me.id}'
        user_dir = session_name
        os.makedirs(user_dir, exist_ok=True)
        full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}"
        spam_control = user_data.get('Spam_control', True)

    # Render the settings menu with emojis
        delete_count = user_data.get('delete_count', 0)
        block_count = user_data.get('block_count', 0)
        if user_count == 1:
            session_name = f'user_{client.me.id}'
            user_dir = session_name
            os.makedirs(user_dir, exist_ok=True)
            photu = None
            async for photo in client.get_chat_photos(client.me.id):
                photu = photo.file_id
            logo = gvarstatus(client.me.id, "ALIVE_LOGO") or (await client.download_media(client.me.photo.big_file_id, f"{user_dir}/{'logo.mp4' if client.me.photo.has_animation else 'logo.jpg'}") if client.me.photo else "userbot.jpg")
            alive_logo = logo
            if type(logo) is bytes:
              alive_logo = f"{user_dir}/logo.jpg"
              with open(alive_logo, "wb") as fimage:
                fimage.write(base64.b64decode(logo))
              if 'video' in mime.from_file(alive_logo):
                 alive_logo = rename_file(alive_logo, f"{user_dir}/logo.mp4")
            greet_message = gvarstatus(client.me.id, "WELCOME") or f"""<blockquote>{bold_cool(f"👋 Salam olsun, {full_name}! Şəxsi mesajıma xoş gəlmisiniz.")}</blockquote>

<blockquote>{bold_cool("Mənimlə əlaqə saxladığınız üçün təşəkkür edirəm. Sizə kömək etməkdən məmnun olaram. Zəhmət olmasa mesajınızın məqsədini bildirin, tezliklə cavab verəcəyəm. Rahatlığınız mənim üçün prioritetdir.")}</blockquote>

<blockquote>{bold_cool("Zəhmət olmasa həddindən artıq mesaj göndərməkdən çəkinin, əks halda bloklana bilərsiniz. Vaxtınızdan zövq alın!")}</blockquote>"""
            
            greet_message = greet_message.replace("{full_name}", full_name)
            send = client.send_video if alive_logo.endswith(".mp4") else client.send_photo
            await send(
                message.chat.id,
                alive_logo,
                caption=await format_welcome_message(client, greet_message,
message.chat.id, message.from_user.first_name)
            )

        elif block_count > 0 and user_count >= block_count:
            if user_count == block_count:
               warning_message = bold_cool(f'Avtomatik blok rejimi aktivləşdi.\n\nMesajınız arzuolunmaz kimi qeydə alındı. Sonrakı mesajlarınız hesabınızın bloklanmasına səbəb olacaq.')
               await client.send_message(message.chat.id, warning_message)
            else:
               logger.debug("Blocking user...")
               await client.block_user(sender_id)
        elif delete_count > 0 and user_count >= delete_count:
            if user_count == delete_count:
               warning_message = bold_cool('Avtomatik silmə rejimi aktivləşdi.\n\nMesajınız uyğunsuz kimi qeydə alındı. Bundan sonrakı bütün mesajlarınız avtomatik silinəcək.')
               await client.send_message(message.chat.id, warning_message)
            else:
               logger.debug("Deleting message...")
               await message.delete()

@Client.on_message(filters.command("approve", prefixes=HARDCODED_PREFIXES) & filters.private & filters.me)
@retry()
async def approve_user(client, message):
    logger.debug("Approving user...")
    chat_id = message.chat.id
    try:
        await client.unblock_user(chat_id)
        logger.debug(f"User {chat_id} unblocked.")
    except Exception as e:
        logger.warning(f"Error unblocking user {chat_id}: {e}")

    user_data = user_sessions.find_one({"user_id": client.me.id})
    if user_data:
        white_listed = user_data.get('white_listed', [])
        if chat_id not in white_listed:
            user_sessions.update_one(
                {"user_id": client.me.id},
                {"$push": {"white_listed": chat_id}}
            )
            logger.debug(f"User {chat_id} added to whitelist.")
            await message.edit_text("Təsdiqləndiniz və ağ siyahıya əlavə edildiniz.")
        else:
            logger.debug(f"User {chat_id} is already in the whitelist.")
            await message.edit_text("Siz artıq ağ siyahıdasınız.")
    else:
        user_sessions.insert_one({
            "user_id": client.me.id,
            "white_listed": [chat_id]
        })
        logger.debug(f"User {chat_id} added to whitelist (new entry).")
        await message.edit_text("Təsdiqləndiniz və ağ siyahıya əlavə edildiniz.")

@Client.on_message(filters.command("disapprove", prefixes=HARDCODED_PREFIXES) & filters.private & filters.me)
@retry()
async def disapprove_user(client, message):
    chat_id = message.chat.id
    user_data = user_sessions.find_one({"user_id": client.me.id})
    if user_data:
        white_listed = user_data.get('white_listed', [])
        if chat_id in white_listed:
            user_sessions.update_one(
                {"user_id": client.me.id},
                {
                    "$pull": {"white_listed": chat_id},
                    "$set": {f"users.{chat_id}": 0}
                }
            )
            logger.debug(f"User {chat_id} removed from whitelist and user count reset.")
            await message.edit_text("Ağ siyahıdan çıxarıldınız və mesaj sayınız sıfırlandı.")
        else:
            logger.debug(f"User {chat_id} is not in the whitelist.")
            await message.edit_text("Siz ağ siyahıda deyilsiniz.")
    else:
        logger.warning(f"No data found for user_id {client.me.id}.")
        await message.edit_text("Bot istifadəçisi üçün məlumat tapılmadı.")

@Client.on_message(filters.command("rmall", prefixes=HARDCODED_PREFIXES) & filters.private & filters.me)
@retry()
async def remove_all_whitelisted_users(client, message):
    logger.debug("Removing all whitelisted users...")

    result = user_sessions.update_one(
        {"user_id": client.me.id},
        {"$set": {"white_listed": []}}
    )
    
    if result.modified_count > 0:
        logger.debug("All whitelisted users removed.")
        await message.edit_text("Bütün ağ siyahıdakı istifadəçilər silindi.")
    else:
        logger.debug("No whitelisted users to remove.")
        await message.edit_text("Silinəcək ağ siyahı istifadəçisi yox idi.")

@Client.on_message(filters.command("rstall", prefixes=HARDCODED_PREFIXES) & filters.private & filters.me)
@retry()
async def reset_all_users_count(client, message):
    logger.debug("Resetting all users' counts to 0...")
    
    user_data = user_sessions.find_one({"user_id": client.me.id})
    if user_data:
        users = user_data.get('users', {})
        for user_id in users.keys():
            if user_id != "total_user_count":  # Ensure we don't reset the total_user_count field
                user_sessions.update_one(
                    {"user_id": client.me.id},
                    {"$set": {f"users.{user_id}": 0}}
                )
        logger.debug("All users' counts have been reset to 0.")
        await message.edit_text("Bütün istifadəçilərin mesaj sayı 0-a sıfırlandı.")
    else:
        logger.warning(f"No data found for user_id {client.me.id}.")
        await message.edit_text("Bot istifadəçisi üçün məlumat tapılmadı.")

@Client.on_message(filters.command("rst", prefixes=HARDCODED_PREFIXES) & filters.private & filters.me)
@retry()
async def reset_user_count(client, message):
    logger.debug("Resetting user count for specific chat...")
    chat_id = str(message.chat.id)  # Ensure chat_id is a string to match MongoDB keys

    user_data = user_sessions.find_one({"user_id": client.me.id})
    if user_data:
        users = user_data.get('users', {})
        if chat_id in users:
            user_sessions.update_one(
                {"user_id": client.me.id},
                {"$set": {f"users.{chat_id}": 0}}
            )
            logger.debug(f"User count for {chat_id} has been reset to 0.")
            await message.edit_text(f"Mesaj sayınız 0-a sıfırlandı.")
        else:
            logger.debug(f"No count found for {chat_id}.")
            await message.edit_text("Söhbət ID-niz üçün say tapılmadı.")
    else:
        logger.warning(f"No data found for user_id {client.me.id}.")
        await message.edit_text("Bot istifadəçisi üçün məlumat tapılmadı.")

@Client.on_message(filters.command("addbl", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def add_to_blacklist(client, message):
    chat_id = message.chat.id
    chat = message.chat
    user_data = user_sessions.find_one({"user_id": client.me.id})

    if user_data:
        blocked_list = user_data.get('blocked_list', []) #Changed to blocked_list
        if chat_id in blocked_list:
            await message.edit_text(f"{chat.title or chat.first_name} artıq qara siyahıdadır.")
            return

        user_sessions.update_one(
            {"user_id": client.me.id},
            {"$push": {"blocked_list": chat_id}}  #Changed to blocked_list
        )
        await message.edit_text(f"{chat.title or chat.first_name} qara siyahıya əlavə edildi.")

    else:
        user_sessions.insert_one({
            "user_id": client.me.id,
            "blocked_list": [chat_id]  #Changed to blocked_list
        })
        await message.edit_text(f"{chat.title or chat.first_name} qara siyahıya əlavə edildi (yeni qeyd).")

@Client.on_message(filters.command("rmbl", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def remove_from_blacklist(client, message: Message):
    user_id = client.me.id
    user_data = user_sessions.find_one({"user_id": user_id}) or {}

    blocked_list = user_data.get("blocked_list", [])

    if len(message.command) > 1:  # Chat ID provided as argument
        target_chat_id_str = message.command[1]
        try:
            target_chat_id = int(target_chat_id_str)
        except ValueError:
            await message.reply("Yanlış söhbət ID-si. Zəhmət olmasa düzgün bir rəqəm daxil edin.")
            return
        try:
            target_chat = await client.get_chat(target_chat_id)
            chat_title_or_name = target_chat.title or target_chat.first_name
        except Exception as e:
            chat_title_or_name = None

        if target_chat_id in blocked_list:
            user_sessions.update_one({"user_id": user_id}, {"$pull": {"blocked_list": target_chat_id}})
            await message.reply(f"{chat_title_or_name} qara siyahıdan çıxarıldı.")
        else:
            await message.reply(f"{target_chat_id} qara siyahıda tapılmadı.")

    else:  # Remove current chat from blacklist
        chat_id = message.chat.id
        try:
            chat = await client.get_chat(chat_id)
            chat_title_or_name = chat.title or chat.first_name
        except Exception as e:
            await message.reply(f"Söhbət məlumatını alarkən xəta baş verdi: {e}")
            return

        if chat_id in blocked_list:
            user_sessions.update_one({"user_id": user_id}, {"$pull": {"blocked_list": chat_id}})
            await message.reply(f"{chat_title_or_name} qara siyahıdan çıxarıldı.")
        else:
            await message.reply(f"{chat_title_or_name} qara siyahıda tapılmadı.")

@Client.on_message(filters.command("block", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def block_user(client, message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.edit(styled_error("Bir istifadəçiyə cavab verin və ya istifadəçi ID/username daxil edin."))
        try:
            user = await client.get_users(int(args[1]) if args[1].isdigit() else args[1])
            user_id = user.id
        except Exception as e:
            return await message.edit(styled_error(f"İstifadəçi tapılmadı: {e}"))
    await client.block_user(user_id)
    await message.edit(styled_success(f"`{user_id}` bloklandı."))


@Client.on_message(filters.command("unblock", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def unblock_user(client, message):
    if message.reply_to_message and message.reply_to_message.from_user:
        user_id = message.reply_to_message.from_user.id
    else:
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            return await message.edit(styled_error("Bir istifadəçiyə cavab verin və ya istifadəçi ID/username daxil edin."))
        try:
            user = await client.get_users(int(args[1]) if args[1].isdigit() else args[1])
            user_id = user.id
        except Exception as e:
            return await message.edit(styled_error(f"İstifadəçi tapılmadı: {e}"))
    await client.unblock_user(user_id)
    await message.edit(styled_success(f"`{user_id}` blokdan çıxarıldı."))

@Client.on_message(filters.command("blist", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def show_blacklist(client, message):
    user_data = user_sessions.find_one({"user_id": client.me.id})
    if user_data:
        blocked_list = user_data.get("blocked_list", [])
        if blocked_list:
            await message.reply(f"Qara siyahıdakı söhbətlər:<blockquote> {', '.join(map(str, blocked_list))}</blockquote>")
        else:
            await message.reply("Qara siyahı boşdur.")
    else:
        await message.reply("Bu bot üçün qara siyahı tapılmadı.")
