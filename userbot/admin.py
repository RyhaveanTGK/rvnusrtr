import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import UserAdminInvalid, ChatAdminRequired
from pyrogram.types import Message, ChatPermissions
from tools import (
    HARDCODED_PREFIXES, edit_or_reply, styled_error, styled_success,
    sudoers_filter, retry, can_grant_privilege
)
from utils.message import Msg

try:
    from pyrogram.types import ChatPrivileges
except ImportError:
    ChatPrivileges = ChatPermissions

logger = logging.getLogger("userbot")

async def is_user_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """Check if user is admin in the chat"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
    except Exception as e:
        logger.debug(f"is_user_admin check failed: {e}")
        return False

async def get_user_from_arg(client: Client, arg: str):
    """Get user object from username or ID"""
    try:
        if arg.startswith('@'):
            arg = arg[1:]
        
        if arg.isdigit():
            user = await client.get_users(int(arg))
        else:
            user = await client.get_users(arg)
        return user
    except Exception as e:
        logger.debug(f"get_user_from_arg failed for {arg!r}: {e}")
        return None

async def get_user_privileges(client: Client, chat_id: int, user_id: int):
    """Get user's admin privileges in the chat"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status == ChatMemberStatus.OWNER:
            # Owner has all privileges
            return ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_manage_topics=True
            )
        elif member.status == ChatMemberStatus.ADMINISTRATOR:
            return member.privileges
        else:
            return None
    except Exception as e:
        logger.debug(f"get_user_privileges failed: {e}")
        return None

async def get_target_user(client: Client, message: Message, parts: list):
    """Get target user from reply or arguments"""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    elif len(parts) > 1:
        return await get_user_from_arg(client, parts[1])
    return None

# Ban Handler
@Client.on_message(filters.command("ban", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
async def ban_handler(client: Client, message: Message):
    """Handle ^ban command"""
    if not await is_user_admin(client, message.chat.id, message.from_user.id):
        await message.reply(Msg.ERR_ADMIN_REQUIRED)
        return
    
    parts = message.text.split()
    target_user = await get_target_user(client, message, parts)
    
    if not target_user:
        await message.reply(Msg.ERR_REPLY_USER_OR_ID)
        return
    
    try:
        delete_messages = "-d" in parts or "--delete" in parts
        
        await client.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id
        )
        
        action_text = "ban edildi və mesajlar silindi" if delete_messages else "ban edildi"
        await message.reply(styled_success(f"{target_user.mention} {action_text}"))
        
    except UserAdminInvalid:
        await message.reply("Bu admini ban etmək mümkün deyil")
    except Exception as e:
        await message.reply(styled_error(f"Ban uğursuz oldu: {str(e)}"))

@Client.on_message(filters.command("kick", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
async def kick_handler(client: Client, message: Message):
    """Handle ^kick command - bans user then unbans (removes from chat)"""
    if not await is_user_admin(client, message.chat.id, message.from_user.id):
        await message.reply(Msg.ERR_ADMIN_REQUIRED)
        return

    parts = message.text.split()
    target_user = await get_target_user(client, message, parts)

    if not target_user:
        await message.reply(Msg.ERR_REPLY_USER_OR_ID)
        return

    try:
        await client.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id
        )
        
        await asyncio.sleep(1)
        await client.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id
        )

        await message.reply(styled_success(f"{target_user.mention} kick edildi"))

    except UserAdminInvalid:
        await message.reply("Bu admini kick etmək mümkün deyil")
    except Exception as e:
        await message.reply(styled_error(f"Kick uğursuz oldu: {str(e)}"))

# Mute Handler
@Client.on_message(filters.command("mute", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
async def mute_handler(client: Client, message: Message):
    """Handle ^mute command"""
    if not await is_user_admin(client, message.chat.id, message.from_user.id):
        await message.reply(Msg.ERR_ADMIN_REQUIRED)
        return
    
    parts = message.text.split()
    target_user = await get_target_user(client, message, parts)
    
    if not target_user:
        await message.reply(Msg.ERR_REPLY_USER_OR_ID)
        return
    
    try:
        mute_permissions = ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
        mute_type = "susduruldu"
        
        await client.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=mute_permissions
        )
        
        await message.reply(styled_success(f"{target_user.mention} {mute_type}"))
        
    except UserAdminInvalid:
        await message.reply("Bu admini susdurmaq mümkün deyil")
    except Exception as e:
        await message.reply(styled_error(f"Susdurma uğursuz oldu: {str(e)}"))


@Client.on_message(filters.command("unmute", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
async def unmute_handler(client: Client, message: Message):
    """Handle ^unmute command"""
    if not await is_user_admin(client, message.chat.id, message.from_user.id):
        await message.reply(Msg.ERR_ADMIN_REQUIRED)
        return

    parts = message.text.split()
    target_user = await get_target_user(client, message, parts)

    if not target_user:
        await message.reply(Msg.ERR_REPLY_USER_OR_ID)
        return

    try:
        # Get the chat's default permissions for regular users
        chat = await client.get_chat(message.chat.id)
        default_permissions = chat.permissions
        
        # If no default permissions set, use standard user permissions
        if not default_permissions:
            default_permissions = ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False
            )

        await client.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            permissions=default_permissions
        )

        await message.reply(styled_success(f"{target_user.mention} artıq susdurulmayıb"))

    except UserAdminInvalid:
        await message.reply("Bu adminin susdurmasını qaldırmaq mümkün deyil")
    except Exception as e:
        await message.reply(styled_error(f"Susdurmanın ləğvi uğursuz oldu: {str(e)}"))
# Promote Handler
@Client.on_message(filters.command("promote", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
async def promote_handler(client: Client, message: Message):
    """Handle ^promote command with privilege checking"""
    if not await is_user_admin(client, message.chat.id, message.from_user.id):
        await message.reply(Msg.ERR_ADMIN_REQUIRED)
        return
    
    parts = message.text.split()
    target_user = await get_target_user(client, message, parts)
    
    if not target_user:
        await message.reply(Msg.ERR_REPLY_USER_OR_ID)
        return
    
    promoter_privileges = await get_user_privileges(client, message.chat.id, message.from_user.id)
    if not promoter_privileges:
        await message.reply("Admin səlahiyyətləri yoxlanıla bilmədi")
        return
    
    try:
        # Default privileges (none)
        privileges = ChatPrivileges(
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_topics=False
        )
        
        args = parts[2:] if len(parts) > 2 else []
        permissions_granted = []
        permissions_denied = []

        # flag aliases -> (ChatPrivileges attr, display name)
        FLAG_PRIVILEGES = [
            (("-d", "--delete"), "can_delete_messages", "mesajları sil"),
            (("-r", "--restrict"), "can_restrict_members", "üzvləri məhdudlaşdır"),
            (("-i", "--invite"), "can_invite_users", "istifadəçi dəvət et"),
            (("-p", "--pin"), "can_pin_messages", "mesajları bərkit"),
            (("-c", "--change"), "can_change_info", "məlumatı dəyiş"),
            (("-v", "--video"), "can_manage_video_chats", "video söhbətləri idarə et"),
            (("-t", "--topics"), "can_manage_topics", "mövzuları idarə et"),
            (("-m", "--manage"), "can_manage_chat", "söhbəti idarə et"),
        ]
        grant_all = "-all" in args or "--all" in args
        any_flag = any(a in args for aliases, _, _ in FLAG_PRIVILEGES for a in aliases)

        if grant_all or any_flag:
            for aliases, attr, name in FLAG_PRIVILEGES:
                if not (grant_all or any(a in args for a in aliases)):
                    continue
                if can_grant_privilege(promoter_privileges, attr):
                    setattr(privileges, attr, True)
                    permissions_granted.append(name)
                else:
                    permissions_denied.append(name)
        else:
            # No specific permissions requested: give basic available permissions
            for attr, name in (
                ("can_delete_messages", "mesajları sil"),
                ("can_restrict_members", "üzvləri məhdudlaşdır"),
                ("can_pin_messages", "mesajları bərkit"),
            ):
                if can_grant_privilege(promoter_privileges, attr):
                    setattr(privileges, attr, True)
                    permissions_granted.append(name)
        
        if not permissions_granted:
            await message.reply("Veriləcək səlahiyyət yoxdur")
            return
        
        # Extract custom title if provided
        title = None
        title_args = [arg for arg in args if not arg.startswith('-')]
        if title_args:
            title = ' '.join(title_args)[:16]  # Telegram limit
        
        await client.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id,
            privileges=privileges
        )
        
        # Set custom title if provided
        if title:
            try:
                await client.set_administrator_title(
                    chat_id=message.chat.id,
                    user_id=target_user.id,
                    title=title
                )
            except Exception as e:
                logger.warning(f"set_administrator_title failed: {e}")
        
        # Build response message
        response = f"✅ {target_user.mention} bu səlahiyyətlərlə admin edildi: {', '.join(permissions_granted)}"
        if title:
            response += f" (Titul: '{title}')"
        if permissions_denied:
            response += f"\n⚠️ Verilə bilmədi: {', '.join(permissions_denied)} (kifayət qədər səlahiyyət yoxdur)"
        
        await message.reply(response)
        
    except UserAdminInvalid:
        await message.reply("İstifadəçi artıq admindir və ya admin edilə bilməz")
    except Exception as e:
        await message.reply(styled_error(f"Admin etmə uğursuz oldu: {str(e)}"))

@Client.on_message(filters.command("unban", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
async def unban_handler(client: Client, message: Message):
    """Handle ^unban command"""
    if not await is_user_admin(client, message.chat.id, message.from_user.id):
        await message.reply(Msg.ERR_ADMIN_REQUIRED)
        return
    
    parts = message.text.split()
    target_user = await get_target_user(client, message, parts)
    
    if not target_user:
        await message.reply(Msg.ERR_REPLY_USER_OR_ID)
        return
    
    try:
        await client.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target_user.id
        )
        
        await message.reply(styled_success(f"{target_user.mention} banı ləğv edildi"))
        
    except Exception as e:
        await message.reply(styled_error(f"Ban ləğvi uğursuz oldu: {str(e)}"))

# Pin Handler
@Client.on_message((filters.me | sudoers_filter()) & filters.command("pin",prefixes=HARDCODED_PREFIXES))
async def pin_handler(client: Client, message: Message):
    """Handle ^pin command"""
    if not await is_user_admin(client, message.chat.id, message.from_user.id):
        await message.reply(Msg.ERR_ADMIN_REQUIRED)
        return
    
    try:
        if not message.reply_to_message:
            await message.reply("Bərkitmək üçün bir mesaja cavab verin")
            return
            
        parts = message.text.split()
        disable_notification = "-s" not in parts and "--sound" not in parts
        
        await client.pin_chat_message(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.id,
            disable_notification=disable_notification
        )
        
        pin_text = "səssiz şəkildə bərkidildi" if disable_notification else "bildirişlə bərkidildi"
        await message.reply(styled_success(f"Mesaj {pin_text}"))
        
    except ChatAdminRequired:
        await message.reply("Bərkitmək üçün admin hüququ lazımdır")
    except Exception as e:
        await message.reply(styled_error(f"Bərkitmə uğursuz oldu: {str(e)}"))

# Unpin Handler
@Client.on_message(filters.command("unpin", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()))
async def unpin_handler(client: Client, message: Message):
    """Handle ^unpin command"""
    if not await is_user_admin(client, message.chat.id, message.from_user.id):
        await message.reply(Msg.ERR_ADMIN_REQUIRED)
        return
    
    try:
        parts = message.text.split()
        
        if "-a" in parts or "--all" in parts:
            await client.unpin_all_chat_messages(chat_id=message.chat.id)
            await message.reply("Bütün mesajların bərkidilməsi ləğv edildi")
        else:
            if message.reply_to_message:
                await client.unpin_chat_message(
                    chat_id=message.chat.id,
                    message_id=message.reply_to_message.id
                )
                await message.reply(Msg.OK_MSG_UNPINNED)
            else:
                await client.unpin_chat_message(chat_id=message.chat.id)
                await message.reply("Son bərkidilən mesajın bərkidilməsi ləğv edildi")
        
    except ChatAdminRequired:
        await message.reply("Bərkitməni ləğv etmək üçün admin hüququ lazımdır")
    except Exception as e:
        await message.reply(styled_error(f"Bərkitmənin ləğvi uğursuz oldu: {str(e)}"))





@Client.on_message(filters.command("acceptall", prefixes=HARDCODED_PREFIXES) & (filters.me | sudoers_filter()) & filters.group)
async def accept_join_requests(client, message):
    # Get chat_id from command or use current chat
    chat_id = message.chat.id
    
    USERBOT = await edit_or_reply(message, f"🚀 Qoşulma sorğuları qəbul edilir...")
    
    try:
        accepted_count = 0
        failed_count = 0
        
        # Get and approve each join request
        async for request in client.get_chat_join_requests(chat_id):
            try:
                await client.approve_chat_join_request(
                    chat_id=chat_id,
                    user_id=request.from_user.id
                )
                
                user = request.from_user
                logger.info(f"✅ ACCEPTED: {user.first_name} (@{user.username or 'no username'})")
                accepted_count += 1
                
            except Exception as e:
                logger.warning(f"❌ Failed to accept request from {request.from_user.first_name}: {e}")
                failed_count += 1
        
        if accepted_count == 0 and failed_count == 0:
            await USERBOT.edit("Gözləyən qoşulma sorğusu yoxdur")
        else:
            await USERBOT.edit(
                f"{Msg.OK_JOIN_REQUESTS_DONE}\n\n"
                f"┃ ✅ Qəbul edildi: {accepted_count}\n"
                f"┃ ❌ Uğursuz: {failed_count}\n"
                f"╰━━━━━━━━━━━━━━━━━━━━╯"
            )
            
    except Exception as e:
        await USERBOT.edit(styled_error(f"Xəta: {e}"))








