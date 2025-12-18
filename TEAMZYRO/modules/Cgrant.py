from pyrogram import filters
from pyrogram.types import Message
from TEAMZYRO import app, user_collection, collection

# ─────────────────────────────
# CONFIG: WHO CAN USE CGRANT
# ─────────────────────────────
CGRANT_ADMINS = {
    1334658171,   # main owner
    7850114307,   # admin 2
}

# ─────────────────────────────
# HELPER: ENSURE USER EXISTS
# ─────────────────────────────
async def ensure_user(user_id: int):
    user = await user_collection.find_one({"id": user_id})
    if not user:
        user = {
            "id": user_id,
            "characters": [],
            "harem": [],
        }
        await user_collection.insert_one(user)
    return user


# ─────────────────────────────
# /cgrant <user_id> <char_id>
# ─────────────────────────────
@app.on_message(filters.command("cgrant"))
async def cgrant_cmd(_, message: Message):
    if message.from_user.id not in CGRANT_ADMINS:
        return await message.reply_text("❌ You are not allowed to use this command.")

    args = message.text.split()
    if len(args) != 3:
        return await message.reply_text(
            "❌ Usage:\n`/cgrant <user_id> <character_id>`"
        )

    target_user_id = args[1]
    char_id = args[2]

    if not target_user_id.isdigit():
        return await message.reply_text("❌ Invalid user ID.")

    # ── FIND CHARACTER (FIXED)
    character = await collection.find_one({"id": char_id})
    if not character:
        return await message.reply_text("❌ Character not found.")

    target_user_id = int(target_user_id)
    await ensure_user(target_user_id)

    # ── ADD CHARACTER
    await user_collection.update_one(
        {"id": target_user_id},
        {"$push": {"characters": character}}
    )

    await message.reply_text(
        f"✅ **Character Granted Successfully**\n\n"
        f"👤 User ID: `{target_user_id}`\n"
        f"🆔 ID: `{character.get('id')}`\n"
        f"📛 Name: {character.get('name')}\n"
        f"📺 Anime: {character.get('anime')}\n"
        f"💎 Rarity: {character.get('rarity')}",
        parse_mode="markdown"
    )


# ─────────────────────────────
# /cgrantbulk <char_id> <id1,id2,id3>
# ─────────────────────────────
@app.on_message(filters.command("cgrantbulk"))
async def cgrantbulk_cmd(_, message: Message):
    if message.from_user.id not in CGRANT_ADMINS:
        return await message.reply_text("❌ You are not allowed to use this command.")

    args = message.text.split()
    if len(args) != 3:
        return await message.reply_text(
            "❌ Usage:\n`/cgrantbulk <character_id> <user_id1,user_id2,...>`"
        )

    char_id = args[1]
    user_ids_raw = args[2].split(",")

    # ── FIND CHARACTER
    character = await collection.find_one({"id": char_id})
    if not character:
        return await message.reply_text("❌ Character not found.")

    success = 0
    failed = 0

    for uid in user_ids_raw:
        uid = uid.strip()
        if not uid.isdigit():
            failed += 1
            continue

        uid = int(uid)
        await ensure_user(uid)

        await user_collection.update_one(
            {"id": uid},
            {"$push": {"characters": character}}
        )
        success += 1

    await message.reply_text(
        f"✅ **Bulk Grant Completed**\n\n"
        f"🆔 Character: {character.get('name')}\n"
        f"🎯 Granted to: {success} users\n"
        f"❌ Failed: {failed}",
        parse_mode="markdown"
    )
