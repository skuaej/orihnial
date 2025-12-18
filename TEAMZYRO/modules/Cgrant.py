from pyrogram import filters
from pyrogram.types import Message
from TEAMZYRO import app, user_collection, collection

CGRANT_ADMIN_ID = 1334658171


@app.on_message(filters.command("cgrant"))
async def cgrant_cmd(_, message: Message):
    if message.from_user.id != CGRANT_ADMIN_ID:
        return await message.reply_text("❌ You are not allowed to use this command.")

    args = message.text.split()
    if len(args) != 3:
        return await message.reply_text(
            "❌ Usage:\n"
            "`/cgrant <user_id> <character_id>`"
        )

    try:
        target_user_id = int(args[1])
    except ValueError:
        return await message.reply_text("❌ User ID must be a number.")

    character_id = args[2]  # ✅ KEEP STRING (IMPORTANT)

    # 🔍 Find character (STRING ID)
    char = await collection.find_one({"id": character_id})
    if not char:
        return await message.reply_text("❌ Character not found.")

    # Ensure user exists
    await user_collection.update_one(
        {"id": target_user_id},
        {
            "$setOnInsert": {
                "id": target_user_id,
                "characters": [],
                "harem": [],
                "balance": 0
            }
        },
        upsert=True
    )

    # Add character
    await user_collection.update_one(
        {"id": target_user_id},
        {"$push": {"characters": char}}
    )

    await message.reply_text(
        f"✅ **Character Granted Successfully!**\n\n"
        f"👤 User ID: `{target_user_id}`\n"
        f"🌸 Name: **{char.get('name')}**\n"
        f"🆔 ID: `{char.get('id')}`\n"
        f"💎 Rarity: `{char.get('rarity')}`"
    )
