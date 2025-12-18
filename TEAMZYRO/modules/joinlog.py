from pyrogram import Client, filters
from pyrogram.types import Message
from TEAMZYRO import app, GLOG, top_global_groups_collection


# ─────────────────────────────────────
# SEND LOG MESSAGE
# ─────────────────────────────────────
async def send_log_message(chat_id: int, text: str):
    await app.send_message(chat_id=chat_id, text=text)


# ─────────────────────────────────────
# BOT ADDED TO GROUP
# ─────────────────────────────────────
@app.on_message(filters.new_chat_members)
async def on_new_chat_members(client: Client, message: Message):
    bot = await client.get_me()

    # Check if bot was added
    if bot.id not in [u.id for u in message.new_chat_members]:
        return

    chat = message.chat
    added_by = message.from_user.mention if message.from_user else "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"

    chat_title = chat.title
    chat_id = chat.id
    chat_username = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ"

    # ✅ SAVE GROUP FOR BROADCAST
    await top_global_groups_collection.update_one(
        {"group_id": chat_id},
        {
            "$set": {
                "group_id": chat_id,
                "group_name": chat_title,
                "username": chat.username
            }
        },
        upsert=True
    )

    # LOG NEW GROUP
    log_message = (
        f"#newgoroup\n\n"
        f"chat name : {chat_title}\n"
        f"username : {chat_username}\n"
        f"added by : {added_by}"
    )
    await send_log_message(GLOG, log_message)

    # ─────────────────────────────
    # MEMBER COUNT CHECK
    # ─────────────────────────────
    try:
        members = await client.get_chat_members_count(chat_id)
        if members < 15:
            leave_log = (
                f"#leftgroup\n\n"
                f"chat name : {chat_title}\n"
                f"chat username : {chat_username}\n"
                f"reason : Group has less than 15 members"
            )

            await send_log_message(chat_id, leave_log)
            await client.leave_chat(chat_id)

            # REMOVE FROM DB
            await top_global_groups_collection.delete_one(
                {"group_id": chat_id}
            )

            await send_log_message(GLOG, leave_log)
    except Exception:
        pass


# ─────────────────────────────────────
# BOT REMOVED / LEFT GROUP
# ─────────────────────────────────────
@app.on_message(filters.left_chat_member)
async def on_left_chat_member(_, message: Message):
    bot = await app.get_me()

    if message.left_chat_member.id != bot.id:
        return

    chat = message.chat
    removed_by = message.from_user.mention if message.from_user else "ᴜɴᴋɴᴏᴡɴ ᴜsᴇʀ"

    chat_title = chat.title
    chat_id = chat.id
    chat_username = f"@{chat.username}" if chat.username else "ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ"

    # ✅ REMOVE GROUP FROM DB
    await top_global_groups_collection.delete_one(
        {"group_id": chat_id}
    )

    log_message = (
        f"#leftgroup\n\n"
        f"chat name : {chat_title}\n"
        f"chat username : {chat_username}\n"
        f"remove by : {removed_by}"
    )

    await send_log_message(GLOG, log_message)
