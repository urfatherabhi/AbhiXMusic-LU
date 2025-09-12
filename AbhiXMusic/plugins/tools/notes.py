import datetime
from inspect import getfullargspec
from re import findall

from config import BANNED_USERS
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from AbhiXMusic import app
from AbhiXMusic.utils.decorators import AdminRightsCheck  # Updated import

# Temporary in-memory storage for notes (will reset on bot restart)
_notes = {}

# Placeholder for database functions
async def save_note(chat_id, name, note):
    global _notes
    _notes[f"{chat_id}:{name}"] = note
    return True

async def get_note(chat_id, name):
    global _notes
    return _notes.get(f"{chat_id}:{name}")

async def get_note_names(chat_id):
    global _notes
    return [k.split(":")[1] for k in _notes.keys() if k.startswith(f"{chat_id}:")]

async def delete_note(chat_id, name):
    global _notes
    key = f"{chat_id}:{name}"
    if key in _notes:
        del _notes[key]
        return True
    return False

async def deleteall_notes(chat_id):
    global _notes
    keys_to_delete = [k for k in _notes.keys() if k.startswith(f"{chat_id}:")]
    for key in keys_to_delete:
        del _notes[key]
    return True

def extract_urls(reply_markup):
    urls = []
    if reply_markup.inline_keyboard:
        buttons = reply_markup.inline_keyboard
        for i, row in enumerate(buttons):
            for j, button in enumerate(row):
                if button.url:
                    name = (
                        "\n~\nbutton"
                        if i * len(row) + j + 1 == 1
                        else f"button{i * len(row) + j + 1}"
                    )
                    urls.append((f"{name}", button.text, button.url))
    return urls

async def eor(msg: Message, **kwargs):
    func = (
        (msg.edit_text if msg.from_user.is_self else msg.reply)
        if msg.from_user
        else msg.reply
    )
    spec = getfullargspec(func.__wrapped__).args
    return await func(**{k: v for k, v in kwargs.items() if k in spec})

# Temporary placeholder for get_data_and_name (simplified)
async def get_data_and_name(replied_message, message):
    if replied_message.text:
        return replied_message.text, message.text.split(None, 1)[1].strip()
    return "error", None

# Temporary placeholder for check_format (simplified)
async def check_format(ikb_func, raw_text):
    return raw_text

# Temporary placeholder for extract_text_and_keyb (simplified)
def extract_text_and_keyb(ikb_func, raw_text):
    return raw_text, None

@app.on_message(filters.command("save") & filters.group & ~BANNED_USERS)
@AdminRightsCheck  # Updated to use AdminRightsCheck
async def save_notee(_, message: Message):
    try:
        if len(message.command) < 2:
            await eor(
                message,
                text="**Usage:**\nReply to a message with /save [NOTE_NAME] to save a new note.",
            )
        else:
            replied_message = message.reply_to_message
            if not replied_message:
                replied_message = message
            data, name = await get_data_and_name(replied_message, message)
            if data == "error":
                return await message.reply_text(
                    "**Usage:**\n__/save [NOTE_NAME] [CONTENT]__\n`-----------OR-----------`\nReply to a message with.\n/save [NOTE_NAME]"
                )
            note = {
                "type": "text",
                "data": data,
                "file_id": None,
            }
            chat_id = message.chat.id
            await save_note(chat_id, name, note)
            await eor(message, text=f"__**Saved note {name}.**__")
    except UnboundLocalError:
        return await message.reply_text(
            "**Replied message is inaccessible.\n`Forward the message and try again`**"
        )

@app.on_message(filters.command("notes") & filters.group & ~BANNED_USERS)
async def get_notes(_, message: Message):
    chat_id = message.chat.id
    _notes = await get_note_names(chat_id)
    if not _notes:
        return await eor(message, text="**No notes in this chat.**")
    _notes.sort()
    msg = f"List of notes in {message.chat.title}\n"
    for note in _notes:
        msg += f"**-** `{note}`\n"
    await eor(message, text=msg)

@app.on_message(filters.command("get") & filters.group & ~BANNED_USERS)
async def get_one_note(_, message: Message):
    if len(message.text.split()) < 2:
        return await eor(message, text="Invalid arguments")
    chat_id = message.chat.id
    name = message.text.split(None, 1)[1]
    if not name:
        return
    _note = await get_note(chat_id, name)
    if not _note:
        return
    type = _note["type"]
    data = _note["data"]
    file_id = _note.get("file_id")
    keyb = None
    if data:
        if "{app.mention}" in data:
            data = data.replace("{app.mention}", app.mention)
        if "{GROUPNAME}" in data:
            data = data.replace("{GROUPNAME}", message.chat.title)
        if "{NAME}" in data:
            data = data.replace("{NAME}", message.from_user.mention)
        if "{ID}" in data:
            data = data.replace("{ID}", f"`{message.from_user.id}`")
        if "{FIRSTNAME}" in data:
            data = data.replace("{FIRSTNAME}", message.from_user.first_name)
        if "{SURNAME}" in data:
            sname = message.from_user.last_name or "None"
            data = data.replace("{SURNAME}", sname)
        if "{USERNAME}" in data:
            susername = message.from_user.username or "None"
            data = data.replace("{USERNAME}", susername)
        if "{DATE}" in data:
            DATE = datetime.datetime.now().strftime("%Y-%m-%d")
            data = data.replace("{DATE}", DATE)
        if "{WEEKDAY}" in data:
            WEEKDAY = datetime.datetime.now().strftime("%A")
            data = data.replace("{WEEKDAY}", WEEKDAY)
        if "{TIME}" in data:
            TIME = datetime.datetime.now().strftime("%H:%M:%S")
            data = data.replace("{TIME}", f"{TIME} UTC")
    await get_reply(message, type, file_id, data, keyb)

@app.on_message(filters.regex(r"^#.+") & filters.text & filters.group & ~BANNED_USERS)
async def get_one_note(_, message: Message):
    chat_id = message.chat.id
    name = message.text.replace("#", "", 1)
    if not name:
        return
    _note = await get_note(chat_id, name)
    if not _note:
        return
    type = _note["type"]
    data = _note["data"]
    file_id = _note.get("file_id")
    keyb = None
    if data:
        if "{app.mention}" in data:
            data = data.replace("{app.mention}", app.mention)
        if "{GROUPNAME}" in data:
            data = data.replace("{GROUPNAME}", message.chat.title)
        if "{NAME}" in data:
            data = data.replace("{NAME}", message.from_user.mention)
        if "{ID}" in data:
            data = data.replace("{ID}", f"`{message.from_user.id}`")
        if "{FIRSTNAME}" in data:
            data = data.replace("{FIRSTNAME}", message.from_user.first_name)
        if "{SURNAME}" in data:
            sname = message.from_user.last_name or "None"
            data = data.replace("{SURNAME}", sname)
        if "{USERNAME}" in data:
            susername = message.from_user.username or "None"
            data = data.replace("{USERNAME}", susername)
        if "{DATE}" in data:
            DATE = datetime.datetime.now().strftime("%Y-%m-%d")
            data = data.replace("{DATE}", DATE)
        if "{WEEKDAY}" in data:
            WEEKDAY = datetime.datetime.now().strftime("%A")
            data = data.replace("{WEEKDAY}", WEEKDAY)
        if "{TIME}" in data:
            TIME = datetime.datetime.now().strftime("%H:%M:%S")
            data = data.replace("{TIME}", f"{TIME} UTC")
    await get_reply(message, type, file_id, data, keyb)

async def get_reply(message, type, file_id, data, keyb):
    if type == "text":
        await message.reply_text(
            text=data,
            reply_markup=keyb,
            disable_web_page_preview=True,
        )
    if type == "sticker":
        await message.reply_sticker(
            sticker=file_id,
        )
    if type == "animation":
        await message.reply_animation(
            animation=file_id,
            caption=data,
            reply_markup=keyb,
        )
    if type == "photo":
        await message.reply_photo(
            photo=file_id,
            caption=data,
            reply_markup=keyb,
        )
    if type == "document":
        await message.reply_document(
            document=file_id,
            caption=data,
            reply_markup=keyb,
        )
    if type == "video":
        await message.reply_video(
            video=file_id,
            caption=data,
            reply_markup=keyb,
        )
    if type == "video_note":
        await message.reply_video_note(
            video_note=file_id,
        )
    if type == "audio":
        await message.reply_audio(
            audio=file_id,
            caption=data,
            reply_markup=keyb,
        )
    if type == "voice":
        await message.reply_voice(
            voice=file_id,
            caption=data,
            reply_markup=keyb,
        )

@app.on_message(filters.command("delete") & filters.group & ~BANNED_USERS)
@AdminRightsCheck  # Updated to use AdminRightsCheck
async def del_note(_, message: Message):
    if len(message.command) < 2:
        return await eor(message, text="**Usage**\n__/delete [NOTE_NAME]__")
    name = message.text.split(None, 1)[1].strip()
    if not name:
        return await eor(message, text="**Usage**\n__/delete [NOTE_NAME]__")
    chat_id = message.chat.id
    deleted = await delete_note(chat_id, name)
    if deleted:
        await eor(message, text=f"**Deleted note {name} successfully.**")
    else:
        await eor(message, text="**No such note.**")

@app.on_message(filters.command("deleteall") & filters.group & ~BANNED_USERS)
@AdminRightsCheck  # Updated to use AdminRightsCheck
async def delete_all(_, message: Message):
    _notes = await get_note_names(message.chat.id)
    if not _notes:
        return await message.reply_text("**No notes in this chat.**")
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("YES, DO IT", callback_data="delete_yes"),
                    InlineKeyboardButton("Cancel", callback_data="delete_no"),
                ]
            ]
        )
        await message.reply_text(
            "**Are you sure you want to delete all the notes in this chat forever ?.**",
            reply_markup=keyboard,
        )

@app.on_callback_query(filters.regex("delete_(.*)"))
async def delete_all_cb(_, cb):
    chat_id = cb.message.chat.id
    input = cb.data.split("_", 1)[1]
    if input == "yes":
        stoped_all = await deleteall_notes(chat_id)
        if stoped_all:
            return await cb.message.edit(
                "**Successfully deleted all notes on this chat.**"
            )
    if input == "no":
        await cb.message.reply_to_message.delete()
        await cb.message.delete()

__MODULE__ = "Nᴏᴛᴇs"
__HELP__ = """
**ɴᴏᴛᴇꜱ:**

• `/save [NOTE_NAME] [CONTENT]`: Sᴀᴠᴇs ᴀ ɴᴏᴛᴇ ᴡɪᴛʜ ᴛʜᴇ ɢɪᴠᴇɴ ɴᴀᴍᴇ ᴀɴᴅ ᴄᴏɴᴛᴇɴᴛ.
• `/notes`: Sʜᴏᴡs ᴀʟʟ sᴀᴠᴇᴅ ɴᴏᴛᴇꜱ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.
• `/get [NOTE_NAME]`: Gᴇᴛs ᴛʜᴇ ᴄᴏɴᴛᴇɴᴛ ᴏғ ᴀ sᴀᴠᴇᴅ ɴᴏᴛᴇ.
• `/delete [NOTE_NAME]`: Dᴇʟᴇᴛᴇs ᴀ sᴀᴠᴇᴅ ɴᴏᴛᴇ.
• `/deleteall`: Dᴇʟᴇᴛᴇs ᴀʟʟ sᴀᴠᴇᴅ ɴᴏᴛᴇꜱ ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.
"""