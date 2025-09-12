from pyrogram import filters
from pyrogram.enums import ChatType
from AbhiXMusic import app
import aiohttp
from AbhiXMusic.utils.database import get_assistant

# Hastebin uploader for large messages
async def Yukkibin(text):
    url = "https://hastebin.com/documents"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=text.encode('utf-8')) as response:
            data = await response.json()
            return f"https://hastebin.com/{data['key']}"

@app.on_message(
    filters.command(["vcuser", "vcusers", "vcmember", "vcmembers"]) & filters.admin
)
async def vc_members(client, message):
    msg = await message.reply_text("🔍 ꜰᴇᴛᴄʜɪɴɢ ᴠᴄ ᴍᴇᴍʙᴇʀꜱ...")
    userbot = await get_assistant(message.chat.id)
    TEXT = ""
    try:
        async for m in userbot.get_call_members(message.chat.id):
            try:
                u = await client.get_users(m.chat.id)
                user_id = u.id
                first_name = u.first_name
                username = f"@{u.username}" if u.username else "N/A"
            except Exception:
                user_id = m.chat.id
                first_name = "N/A"
                username = "N/A"

            is_hand_raised = m.is_hand_raised
            is_video_enabled = m.is_video_enabled
            is_left = m.is_left
            is_screen_sharing_enabled = m.is_screen_sharing_enabled
            is_muted = bool(m.is_muted and not m.can_self_unmute)
            is_speaking = not m.is_muted

            TEXT += (
                f"➻ **🆔 Uꜱᴇʀ Iᴅ** ‣ `{user_id}`\n"
                f"➻ **🧑‍💼 Fɪʀꜱᴛ Nᴀᴍᴇ** ‣ {first_name}\n"
                f"➻ **🔗 Uꜱᴇʀɴᴀᴍᴇ** ‣ {username}\n"
                f"➻ **📹 Vɪᴅᴇᴏ** ‣ {is_video_enabled}\n"
                f"➻ **🖥 Sᴄʀᴇᴇɴ Sʜᴀʀᴇ** ‣ {is_screen_sharing_enabled}\n"
                f"➻ **✋ Hᴀɴᴅ Rᴀɪꜱᴇᴅ** ‣ {is_hand_raised}\n"
                f"➻ **🔇 Mᴜᴛᴇᴅ** ‣ {is_muted}\n"
                f"➻ **🗣 Sᴘᴇᴀᴋɪɴɢ** ‣ {is_speaking}\n"
                f"➻ **🚪 Lᴇꜰᴛ** ‣ {is_left}\n"
                f"───────────────\n"
            )

        footer = "๏ 𝐌𝐀𝐃𝐄 𝐁𝐘 ➠ [|Pᴀᴘᴀ Jɪ|](https://t.me/URFather_ABHI)"

        if len(TEXT) < 3900:
            TEXT += "\n" + footer
            await msg.edit(TEXT or "❌ **ɴᴏ ᴍᴇᴍʙᴇʀꜱ ꜰᴏᴜɴᴅ ɪɴ ᴠᴄ.**", disable_web_page_preview=True)
        else:
            link = await Yukkibin(TEXT + "\n" + footer)
            await msg.edit(
                f"📄 ʟɪꜱᴛ ɪꜱ ᴛᴏᴏ ʟᴏɴɢ. ᴄʟɪᴄᴋ ʜᴇʀᴇ ᴛᴏ ᴠɪᴇᴡ: [ᴄʟɪᴄᴋ ʜᴇʀᴇ]({link})\n\n{footer}",
                disable_web_page_preview=True,
            )

    except ValueError:
        await msg.edit("❌ ᴜɴᴀʙʟᴇ ᴛᴏ ꜰᴇᴛᴄʜ ᴍᴇᴍʙᴇʀꜱ ꜰʀᴏᴍ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.")
