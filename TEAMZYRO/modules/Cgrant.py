from pyrogram import filters
from pyrogram.types import Message
from TEAMZYRO import app, user_collection, collection

# ONLY THIS USER CAN USE THE COMMAND
CGRANT_ADMIN_ID = 1334658171


@app.on_message(filters.command("cgrant"))
async def cgrant_cmd(_, message: Message):
    # Permission check
    if message.from_user.id != CGRANT_ADMIN_ID:
        return await message.reply_text("❌ You are not allowed to use this command.")

    # Format: /cgrant <target_user_id> <character_id>
    args = message.text.split()
    if len(args) != 3:
        return await message.reply_text(
            "❌ Usage:\n"
            "`/cgrant <user_id> <character_id>`"
        )

    try:
        target_user_id = int(args[1])
        character_id = int(args[2])
    except ValueError:
        return await message.reply_text("❌ User ID and Character ID must be numbers.")

    # Fetch character
    char = await collection.find_one({"id": character_id})
    if not char:
        return await message.reply_text("❌ Character not found.")

    # Ensure target user exists
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

    # Add character to user's collection
    await user_collection.update_one(
        {"id": target_user_id},
        {"$push": {"characters": char}}
    )

    await message.reply_text(
        f"✅ **Character Granted Successfully!**\n\n"
        f"👤 User ID: `{target_user_id}`\n"
        f"🌸 Character: **{char.get('name', 'Unknown')}**\n"
        f"🆔 Character ID: `{char.get('id')}`\n"
        f"⭐ Rarity: `{char.get('rarity', 'N/A')}`"
    )
