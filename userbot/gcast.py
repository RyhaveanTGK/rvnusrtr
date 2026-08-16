
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.errors import ChatForwardsRestricted, FileReferenceExpired, MessageIdInvalid, FloodWait
from pyrogram import enums
from config import *
from tools import *

import logging
logger = logging.getLogger("gcast")

@Client.on_message(filters.command("gcast", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def gcast_handler(client, message):
    """Handles the /gcast command."""
    session_name = f'user_{client.me.id}'
    user_dir = session_name
    os.makedirs(user_dir, exist_ok=True)
    user_id = client.me.id
    user_data = user_sessions.find_one({"user_id": user_id}) or {}
    admin_ids = None
    if os.path.exists(admin_file):
       with open(admin_file, "r") as file:
          admin_ids = [int(line.strip()) for line in file.readlines()]
    try:
        parts = message.text.split(maxsplit=2)
        flag = parts[1].lower()
        logger.debug(f"gcast flag: {flag}")
        text_or_file = parts[2] if len(parts) > 2 else None  #handles cases with no message
        file = None
        reply_msg = message.reply_to_message
        if reply_msg:
            text_or_file = reply_msg.text if reply_msg.text else None # handles replies that have just media
            file = reply_msg.media

        if not text_or_file and not file:
            return await message.edit("Gcast üçün heç nə verilmədi.")
        try:
           message_to_cast = await reply_msg.copy(app.me.username) if reply_msg else await client.send_message(app.me.id, text_or_file)
        except (ChatForwardsRestricted, FileReferenceExpired, MessageIdInvalid):
           if reply_msg.media:
               caption = f"{reply_msg.text if reply_msg.caption is None else reply_msg.caption}"
               await message.edit( "Media/sənəd yüklənir......")
               file_path=await reply_msg.download(f"{user_dir}/")
               file_extension = file_path.split('.')[-1]
               if os.path.getsize(file_path) <= 2100000000:
                  if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
                            message_to_cast = await client.send_photo(chat_id=app.me.id, photo=file_path, caption=caption)
                  elif file_extension in ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a']:
                            message_to_cast = await client.send_audio(chat_id=app.me.id, audio=file_path, caption=caption)
                  elif file_extension in ['mp4', 'mov', 'avi', 'mkv', 'webm', 'wmv']:
                            thumb_path = f"{file_path}_thumb.jpg"
                            generate_thumbnail(file_path, thumb_path)
                            duration=with_opencv(file_path)
                            message_to_cast = await client.send_video(chat_id=app.me.id, video=file_path, caption=caption, duration=duration,thumb=thumb_path)
                            os.remove(thumb_path)
                  else:
                            message_to_cast = await client.send_document(app.me.id, file_path, caption=caption)
               else:
                   await message.edit( "2GB-dan böyük fayl ilə əməliyyat aparıla bilmir")
                   return os.remove(file_path)
           else:
                message_to_cast = await client.send_message(app.me.id, reply_msg.text)
        except FloodWait as e:
                    await asyncio.sleep(e.value)

        except Exception as e:
                   await message.edit(f"Mesaj alınarkən xəta: {e}")
        blocked_list = user_data.get("blocked_list", [])
        await message.reply("Mesaj Gcast edilir...")
        sed = 0
        owo = 0
        bl = 0
        async for dialog in client.get_dialogs():
          if flag in ["-all", "-pvt", "-grp"]:
            if dialog.chat.id in blocked_list or dialog.chat.id in admin_ids:
                bl +=1
                continue
            should_send = (
                flag == "-all"
                or (flag == "-pvt" and dialog.chat.type == enums.ChatType.PRIVATE)
                or (flag == "-grp" and dialog.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP])
            )
            if not should_send:
                continue
            try:
                await message_to_cast.copy(dialog.chat.id)
                owo += 1
            except Exception as e:
                sed += 1
          else:
                return await message.edit(
                "Zəhmət olmasa gcast bayrağını daxil edin. \n\nMövcud seçimlər: \n• -all : Bütün söhbətlərdə Gcast et. \n• -pvt : Şəxsi söhbətlərdə Gcast et. \n• -grp : Qruplarda Gcast et."
            )


        UwU = sed + owo
        omk = {"-all": "Söhbətlər", "-pvt": "Şəxsi", "-grp": "Qruplar"}.get(flag, "Söhbətlər") # More concise mapping
        text_to_send = f"📍 Göndərildi : {owo} {omk}\n📍 Uğursuz : {sed} {omk}\n📍Bloklanmış söhbətlərdə keçildi : {bl}\n📍 Toplam : {UwU} {omk}"
        await message.edit(f"Gcast Uğurla Tamamlandı !! \n\n{text_to_send}")
        await client.send_message(app.me.id, f"#GCAST #{flag[1:].upper()} \n\n{text_to_send}")

    except IndexError: # Catches errors if the user didn't give enough arguments.
        await message.edit("İstifadə qaydası: /gcast [-all|-pvt|-grp] [mesaj/cavab]")
    except Exception as e:
        await message.edit(f"Gözlənilməz xəta baş verdi. Zəhmət olmasa logları yoxlayın.")
