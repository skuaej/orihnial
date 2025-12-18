from pyrogram import filters
from TEAMZYRO import app, top_global_groups_collection


@app.on_message(filters.group)
async def auto_save_group(_, message):
    chat = message.chat

    # Ignore private & channels
    if chat.type not in ("group", "supergroup"):
        return

    await top_global_groups_collection.update_one(
        {"group_id": chat.id},
        {
            "$set": {
                "group_id": chat.id,
                "group_name": chat.title,
                "username": chat.username
            }
        },
        upsert=True
    )
