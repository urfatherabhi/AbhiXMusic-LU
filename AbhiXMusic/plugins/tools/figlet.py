import asyncio
from random import choice
import pyfiglet
from pyrogram import filters
from pyrogram.errors import FloodWait
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from AbhiXMusic import app
from config import BANNED_USERS  # Added for consistency with other plugins


def figle(text: str) -> tuple[str, InlineKeyboardMarkup]:
    try:
        x = pyfiglet.FigletFont.getFonts()
        font = choice(x)
        figled = str(pyfiglet.figlet_format(text, font=font))
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="ᴄʜᴀɴɢᴇ", callback_data=f"figlet_{text}"),
                    InlineKeyboardButton(text="ᴄʟᴏsᴇ", callback_data="close_reply"),
                ]
            ]
        )
        return figled, keyboard
    except Exception as e:
        raise Exception(f"Failed to generate figlet: {str(e)}")


@app.on_message(filters.command("figlet") & ~BANNED_USERS)
async def echo(bot, message: Message):
    try:
        text = message.text.split(" ", 1)[1]
        if not text:
            return await message.reply_text("Example:\n\n`/figlet Yukki`")
        kul_text, keyboard = figle(text)
        await message.reply_text(
            f"ʜᴇʀᴇ ɪs ʏᴏᴜʀ ғɪɢʟᴇᴛ :\n<pre>{kul_text}</pre>",
            quote=True,
            reply_markup=keyboard,
        )
    except IndexError:
        await message.reply_text("Example:\n\n`/figlet Yukki`")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")


@app.on_callback_query(filters.regex(r"figlet_(.*)") & ~BANNED_USERS)
async def figlet_handler(client, query: CallbackQuery):
    try:
        text = query.matches[0].group(1)  # Extract text from callback_data
        kul_text, keyboard = figle(text)
        await query.message.edit_text(
            f"ʜᴇʀᴇ ɪs ʏᴏᴜʀ ғɪɢʟᴇᴛ :\n<pre>{kul_text}</pre>",
            reply_markup=keyboard,
        )
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        await query.answer(f"Error: {str(e)}", show_alert=True)


__MODULE__ = "Fɪɢʟᴇᴛ"
__HELP__ = """
**ғɪɢʟᴇᴛ**

• /figlet <text> - ᴄʀᴇᴀᴛᴇs ᴀ ғɪɢʟᴇᴛ ᴏғ ᴛʜᴇ ɢɪᴠᴇɴ ᴛᴇxᴛ.
"""