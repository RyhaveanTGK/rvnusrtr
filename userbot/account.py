
from pyrogram.raw.functions.contacts import GetBlocked
from config import *
from tools import *

# NOTE: approve/disapprove/addbl/rmbl/blist/rmall/rstall/rst live in antyspam.py.
# They previously existed here too as byte-identical duplicates on the same
# userbot client (dead double-registration) and were removed. This file keeps
# only the commands unique to it: `stats` and `sessions`.

async def get_all_blocked_users(client):
    blocked_users = []
    offset = 0
    limit = 100  # Adjust as needed

    while True:
        blocked = await client.invoke(
            GetBlocked(
                offset=offset,
                limit=limit
            )
        )
        blocked_users.extend(blocked.blocked)
        offset += len(blocked.blocked)

        if len(blocked.blocked) < limit:  # Break if we've fetched all blocked users
            break

    return [user.peer_id.user_id for user in blocked_users if user.peer_id]  # Extract user IDs

async def categorize_blocked_users(client, blocked_user_ids):
    users = []
    bots = []

    if blocked_user_ids:
        # Fetch all user details using get_users
        user_details = await client.get_users(blocked_user_ids)
        for user in user_details:
            if user.is_bot:
                bots.append(user.id)
            else:
                users.append(user.id)

    return users, bots

@Client.on_message(filters.command("stats", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def status(client, message):
    RYHAVEAN = await message.edit_text("`Statistika toplanır...`")
    start = datetime.datetime.now()
    u = g = sg = c = b = um = a_chat = up = blocked_bots = blocked_users = approved_users = 0
    progress_msg = ""

    # Fetch approved users from the database
    user_data = user_sessions.find_one({"user_id": client.me.id}) or {}
    approved_users_list = user_data.get('white_listed', [])

    # Get all blocked users using the Raw API
    blocked_user_ids = await get_all_blocked_users(client)
    blocked_users_list, blocked_bots_list = await categorize_blocked_users(client, blocked_user_ids)

    async for dialog in client.get_dialogs():
        um += dialog.unread_mentions_count
        up += dialog.unread_messages_count

        if dialog.chat.type == enums.ChatType.PRIVATE:
            u += 1
        elif dialog.chat.type == enums.ChatType.BOT:
            b += 1
            # Check if the bot is blocked
            if dialog.chat.id in blocked_bots_list:
                blocked_bots += 1
        elif dialog.chat.type == enums.ChatType.GROUP:
            g += 1
        elif dialog.chat.type == enums.ChatType.SUPERGROUP:
            sg += 1
            user_s = await dialog.chat.get_member(int(client.me.id))
            if user_s.status in (
                enums.ChatMemberStatus.OWNER,
                enums.ChatMemberStatus.ADMINISTRATOR,
            ):
                a_chat += 1
        elif dialog.chat.type == enums.ChatType.CHANNEL:
            c += 1

        # Count blocked users from the blocklist
        if dialog.chat.id in blocked_users_list:
            blocked_users += 1

        # Count approved users from the database
        if dialog.chat.id in approved_users_list:
            approved_users += 1

        # Update progress message dynamically
        progress_msg = (
            f"<b>`Statistika toplanır...`\n"
            f"<b>`Şəxsi Mesajlar: {u}`\n"
            f"<b>`Qruplar: {g}`\n"
            f"<b>`Super Qruplar: {sg}`\n"
            f"<b>`Kanallar: {c}`\n"
            f"<b>`Admin olduğu: {a_chat} Söhbət`\n"
            f"<b>`Botlar: {b}`\n"
            f"<b>`Bloklanmış Botlar: {len(blocked_bots_list)}`\n"
            f"<b>`Bloklanmış İstifadəçilər: {len(blocked_users_list)}`\n"
            f"<b>`Təsdiqlənmiş İstifadəçilər: {approved_users}`\n"
            f"<b>`Oxunmamış Mesajlar: {up}`\n"
            f"<b>`Oxunmamış Qeydlər: {um}`"
        )
        if random.choices([True, False], weights=[1, 10])[0]:
            await RYHAVEAN.edit_text(progress_msg)

    end = datetime.datetime.now()
    ms = (end - start).seconds

    # Final message with stats
    await RYHAVEAN.edit_text(
        f"""<b>`Statistikanız {ms} saniyəyə əldə edildi`
<blockquote><b>`Şəxsi Mesajlar = {u}`
<b>`Qruplar = {g}`
<b>`Super Qruplar = {sg}`<b>
<b>`Kanallar = {c}`<b>
<b>`Admin olduğu söhbətlər = {a_chat}`<b>
`<b>Botlar</b> = {b}`<b>
`<b>Bloklanmış Botlar</b> = {len(blocked_bots_list)}`<b>
`<b>Bloklanmış İstifadəçilər</b> = {len(blocked_users_list)}`
`<b>Təsdiqlənmiş İstifadəçilər</b> = {approved_users}`
`<b>Oxunmamış mesajlar</b> {up}`
`<b>Oxunmamış qeydlər</b> {um}`</blockquote>"""
    )


import datetime
from pyrogram import Client, filters
from pyrogram.raw import functions
from tools import *

def format_timestamp(ts):
    return datetime.datetime.utcfromtimestamp(ts).strftime('%B %d, %Y, %H:%M:%S')

@Client.on_message(filters.command("sessions", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def session_handler(client, message):
    result = await client.invoke(functions.account.GetAuthorizations())
    
    session_info = "**AKTİV SESSİYALAR**"
    
    # Iterate through each session and build the session info string
    for session in result.authorizations:
        session_info += (f"""
<blockquote>Cihaz: {session.device_model}</blockquote>
<blockquote>Platforma: {session.platform}</blockquote>
<blockquote>Tətbiq Adı: {session.app_name} (Versiya: {session.app_version}</blockquote>
<blockquote>Ölkə: {session.country}</blockquote>
<blockquote>Cari Sessiya: {session.current}</blockquote>
<blockquote>Yaradılma Tarixi: {format_timestamp(session.date_created)}</blockquote>
<blockquote>Son Aktivlik: {format_timestamp(session.date_active)}</blockquote>\n\n""")
    
    # Edit the message with the session details
    await message.edit_text(session_info)


@Client.on_message(filters.command("bio", prefixes=HARDCODED_PREFIXES) & filters.me)
@retry()
async def set_bio(client, message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.edit(styled_error("İstifadə qaydası: `.bio <mətn>` (maksimum 70 simvol)"))
    bio = args[1]
    if len(bio) > 70:
        return await message.edit(styled_error("Bio 70 simvoldan çox olmamalıdır."))
    await client.update_profile(bio=bio)
    await message.edit(styled_success(f"Bio yeniləndi:\n`{bio}`"))


@Client.on_message(filters.command("pfp", prefixes=HARDCODED_PREFIXES) & filters.me & filters.reply)
@retry()
async def set_pfp(client, message):
    reply = message.reply_to_message
    if not (reply.photo or (reply.document and "image" in (reply.document.mime_type or ""))):
        return await message.edit(styled_error("Profil şəkli olaraq təyin etmək üçün bir şəklə cavab verin."))
    await message.edit("`Profil şəkli yenilənir...`")
    path = await reply.download()
    try:
        await client.set_profile_photo(photo=path)
        await message.edit(styled_success("Profil şəkli yeniləndi."))
    finally:
        if path and os.path.exists(path):
            os.remove(path)
