import os
from pyrogram import Client, filters
from pyrogram.types import Message
from tools import *
from utils.message import Msg


async def resolve_target_id(message):
    """Resolve the target from a reply or a user-id argument.

    Returns a (user_id, user) tuple on success where ``user`` is the replied
    user object (or ``None`` when the id came from a command argument).
    On failure the appropriate error is sent and ``None`` is returned.
    """
    if message.reply_to_message:
        replied_msg = message.reply_to_message
        if replied_msg.from_user is not None:
            return replied_msg.from_user.id, replied_msg.from_user
        await message.reply("Cavab verilən mesaj bir istifadəçidən deyil.")
        return None

    command_parts = message.text.split()
    if len(command_parts) > 1:
        try:
            return int(command_parts[1]), None
        except ValueError:
            await message.reply("Zəhmət olmasa düzgün istifadəçi ID daxil edin.")
            return None

    await message.reply("Bir mesaja cavab verməli və ya istifadəçi ID daxil etməlisiniz.")
    return None


def _target_detail(user_id, user):
    """Build the card detail lines identifying the target."""
    if user is not None:
        user_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
        return [f"İstifadəçi: {user_name}", f"ID: `{user_id}`"]
    return [f"İstifadəçi ID: `{user_id}`"]


@Client.on_message(filters.command("addsudo", prefixes=HARDCODED_PREFIXES) & filters.me)
async def add_to_sudo(client, message):
    resolved = await resolve_target_id(message)
    if resolved is None:
        return
    target_user_id, user = resolved

    # Check if target user is already admin (only when resolved from an id arg)
    if user is None and is_admin(target_user_id):
        return await message.reply(f"**Bu istifadəçi artıq sahibdir!**")

    # Get current sudo users
    users_data = user_sessions.find_one({"user_id": client.me.id})
    if not users_data:
        users_data = {}

    sudoers = users_data.get("sudoers", [])
    detail = _target_detail(target_user_id, user)

    if target_user_id not in sudoers:
        # Add user to sudoers
        user_sessions.update_one(
            {"user_id": client.me.id},
            {"$push": {"sudoers": target_user_id}},
            upsert=True
        )
        await message.edit(Msg.card("Sudo Girişi Verildi", detail + ["İndi sudo əmrlərini icra edə bilər"], emoji=Msg.EMOJI_SUCCESS))
        SUDO[client.me.id].append(target_user_id)
    else:
        await message.edit(Msg.card("Artıq Sudo Girişi Var", detail + ["Artıq sudo girişi mövcuddur"], emoji=Msg.EMOJI_INFO))


@Client.on_message(filters.command("rmsudo", prefixes=HARDCODED_PREFIXES) & filters.me)
async def remove_from_sudo(client, message):
    resolved = await resolve_target_id(message)
    if resolved is None:
        return
    target_user_id, user = resolved

    # Get current sudo users
    users_data = user_sessions.find_one({"user_id": client.me.id})
    if not users_data:
        if user is not None:
            return await message.edit(Msg.card("Sudo İstifadəçisi Yoxdur", ["Hələ heç bir sudo istifadəçisi əlavə edilməyib"], emoji=Msg.EMOJI_INFO, footer="[prefix]addsudo istifadəçi əlavə etmək üçün"))
        return await message.reply("Sudo siyahısı tapılmadı.")

    sudoers = users_data.get("sudoers", [])
    detail = _target_detail(target_user_id, user)

    if target_user_id in sudoers:
        # Remove user from sudoers
        user_sessions.update_one(
            {"user_id": client.me.id},
            {"$pull": {"sudoers": target_user_id}}
        )
        await message.edit(Msg.card("Sudo Girişi Ləğv Edildi", detail + ["Sudo siyahısından çıxarıldı"], emoji=Msg.EMOJI_WARNING))
        SUDO[client.me.id].remove(target_user_id)
    else:
        await message.edit(Msg.card("Sudo Siyahısında Deyil", detail + ["Sudo siyahısında deyil"], emoji=Msg.EMOJI_INFO))


@Client.on_message(filters.command("sudolist", prefixes=HARDCODED_PREFIXES) & filters.me)
async def list_sudoers(client, message):
    # Get current sudo users
    users_data = user_sessions.find_one({"user_id": client.me.id})
    if not users_data:
        return await message.edit(
            f"Sudo İstifadəçisi Yoxdur\n\n"
            f"┃ Hələ heç bir sudo istifadəçisi əlavə edilməyib\n"
            f"╰▸ [prefix]addsudo istifadəçi əlavə etmək üçün"
        )

    sudoers = users_data.get("sudoers", [])

    if sudoers:
        sudoers_lines = [f"`{user_id}`" for user_id in sudoers]
        sudoers_lines.append(f"Toplam: {len(sudoers)} istifadəçi")
        await message.edit(Msg.card("Sudo İstifadəçiləri Siyahısı", sudoers_lines, emoji=Msg.EMOJI_INFO))
    else:
        await message.edit(Msg.card("Sudo İstifadəçisi Yoxdur", ["Siyahı boşdur"], emoji=Msg.EMOJI_INFO, footer="[prefix]addsudo istifadəçi əlavə etmək üçün"))
