
import os
import base64
import re
from pyrogram import Client, filters
from tools import *
import magic
import logging

logger = logging.getLogger("welcome")
mime = magic.Magic(mime=True)

async def convert_to_image(message, client):
    """Convert sticker to image format"""
    try:
        if message.sticker:
            file_path = await message.download()
            return file_path
        return None
    except Exception as e:
        logger.warning(f"Error converting sticker: {e}")
        return None

@Client.on_message(filters.command("setwelkm", prefixes=HARDCODED_PREFIXES) & filters.private & filters.me)
async def set_welcome_handler(client, message):
    try:
        sender_id = message.from_user.id
        session_name = f'user_{client.me.id}'
        user_dir = session_name
        os.makedirs(user_dir, exist_ok=True)

        replied_msg = message.reply_to_message
        if not replied_msg:
            usage_text = (
                "Onu xoş gəlmisiniz mesajı kimi təyin etmək üçün bir mesaja cavab verin.\n\n"
                "Nəyi təyin edə bilərsiniz:\n"
                "• Mətn mesajı\n"
                "• Media (şəkil/video/gif/stiker)\n"
                "• Yazılı media\n\n"
                "Mövcud yer tutucular:\n"
                "• {name} - İstifadəçinin adı\n"
                "• {id} - İstifadəçinin ID-si\n"
                "• {yourname} - Sizin adınız\n\n"
                "Ölçü limitləri:\n"
                "• Mətn: Maksimum 4096 simvol\n"
                "• Media: Maksimum 5MB\n\n"
                "İstifadə nümunəsi:\n"
                "• 'Xoş gəlmisiniz {name}! Sizin ID-niz {id}'\n"
                "• Yazısı 'Xoş gəlmisiniz {botname}!' olan şəkil/videoya cavab verin"
            )
            return await message.reply_text(usage_text)

        updates = []

        # Handle text if present
        if replied_msg.text or replied_msg.caption:
            text_obj = replied_msg.text or replied_msg.caption
            welcome_text = text_obj.strip()
            if len(welcome_text) > 4096:
                return await message.reply_text("Xoş gəlmisiniz mesajı çox uzundur. Maksimum 4096 simvola icazə verilir.")

            processed_text = text_obj.html

            # Validate placeholders
            ALLOWED_PLACEHOLDERS = {"{name}", "{id}", "{botname}"}
            placeholder_regex = r'\{([^{}]+)\}'
            found_placeholders = set(re.findall(placeholder_regex, processed_text))

            invalid_placeholders = [f"{{{p}}}" for p in found_placeholders
                                  if f"{{{p}}}" not in ALLOWED_PLACEHOLDERS]

            if invalid_placeholders:
                error_msg = "❌ Yanlış yer tutucular tapıldı:\n"
                error_msg += "\n".join(f"• {p}" for p in invalid_placeholders)
                error_msg += "\n\nİcazə verilən yer tutucular:\n"
                error_msg += "\n".join(f"• {p}" for p in sorted(ALLOWED_PLACEHOLDERS))
                error_msg += "\n\nİstifadə nümunəsi:\n"
                error_msg += "• Xoş gəlmisiniz {name}!\n"
                error_msg += "• Sizin ID-niz: {id}\n"
                error_msg += "• Xoş gəlmisiniz {botname}!"
                return await message.reply_text(error_msg)

            set_gvar(sender_id, "WELCOME", processed_text)
            updates.append("welcome message")
            
        if replied_msg.media:
            m_d = None
            try:
                # Check if media type is allowed
                if not (replied_msg.photo or replied_msg.video or
                       replied_msg.sticker or replied_msg.animation):
                    return await message.reply_text("Yalnız şəkillərə, videolara, GIF-lərə və stikerlərə icazə verilir.")

                # Check file size (5MB = 5 * 1024 * 1024 bytes)
                file_size = getattr(replied_msg, 'file_size', 0)
                if file_size > 5242880:  # 5MB in bytes
                    return await message.reply_text("Media ölçüsü 5MB-dan çox ola bilməz.")

                # Process media based on type
                if replied_msg.sticker:
                    m_d = await convert_to_image(replied_msg, client)
                else:
                    m_d = await replied_msg.download()

                if m_d:
                    with open(m_d, "rb") as imageFile:
                        logo_data = base64.b64encode(imageFile.read())
                    os.remove(m_d)
                    set_gvar(sender_id, "ALIVE_LOGO", logo_data)
                    updates.append("logo")

            except Exception as e:
                if m_d and os.path.exists(m_d):
                    os.remove(m_d)
                return await message.reply_text(f"Media emal edilərkən xəta: {str(e)}")

        if not updates:
            return await message.reply_text("Yeniləmək üçün heç nə yoxdur. Mesajda mətn və/və ya media olmalıdır.")

        # Send confirmation and preview
        success_msg = f"✅ {" ".join(updates).replace("welcome message", "xoş gəlmisiniz mesajı").replace("logo", "loqo")} yeniləndi!"
        await client.send_message(message.chat.id, success_msg + "\n\nÖncədən baxış:")

        # Show preview
        try:
            logo = gvarstatus(sender_id, "ALIVE_LOGO")
            if not logo and client.me.photo:
                photos = await client.get_profile_photos("me")
                if photos:
                    logo = await client.download_media(photos[0].file_id, f"{user_dir}/logo.jpg")
            if not logo:
                logo = "userbot.jpg"

            alive_logo = logo
            if isinstance(logo, bytes):
                alive_logo = f"{user_dir}/logo.jpg"
                with open(alive_logo, "wb") as fimage:
                    fimage.write(base64.b64decode(logo))
                if 'video' in mime.from_file(alive_logo):
                    alive_logo = rename_file(alive_logo, f"{user_dir}/logo.mp4")

            welcome_text = gvarstatus(sender_id, "WELCOME") or f"""
<blockquote>{bold_cool(f"👋 Xoş salamlar, {'full_name'}! Şəxsi mesajıma xoş gəlmisiniz.")}</blockquote>

<blockquote>{bold_cool("Mənimlə əlaqə qurduğunuz üçün təşəkkür edirəm. Sizə kömək etməkdən məmnunam. Zəhmət olmasa mesajınızın məqsədini bildirin, tez cavab verəcəyəm. Sizin rahatlığınız mənim üçün prioritetdir.")}</blockquote>

<blockquote>{bold_cool("Zəhmət olmasa həddindən artıq mesaj göndərməyin, əks halda bloklana bilərsiniz. Buradakı vaxtınızdan zövq alın!")}</blockquote>"""
            


            if alive_logo.endswith(".mp4"):
                await client.send_video(
                    message.chat.id,
                    alive_logo,
                    caption=welcome_text,
                )
            else:
                await client.send_photo(
                    message.chat.id,
                    alive_logo,
                    caption=welcome_text,
                )

        except Exception as e:
            logger.warning(f"Error showing preview: {e}")
            welcome_text = gvarstatus(sender_id, "WELCOME")
            if welcome_text:
                await client.send_message(
                    message.chat.id,
                    welcome_text,
                )

    except Exception as e:
        error_msg = f"❌ Xəta: `{str(e)}`"
        logger.warning(f"Welcome error for user {message.from_user.id}: {e}")
        return await message.reply_text(error_msg)

@Client.on_message(filters.command("resetwelkm", prefixes=HARDCODED_PREFIXES) & filters.me)
async def reset_welcome_handler(client, message):
    user_id = message.from_user.id

    # Reset both LOGO and WELCOME
    unset_user_data(user_id, 'ALIVE_LOGO')
    unset_user_data(user_id, 'WELCOME')

    await message.edit("Xoş gəlmisiniz loqosu və mesajı uğurla sıfırlandı")
