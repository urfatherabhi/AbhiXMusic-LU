from AbhiXMusic import app
from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from io import BytesIO
from typing import Union, Optional
from PIL import Image, ImageDraw, ImageFont
import asyncio
from datetime import datetime

# --------------------------------------------------------------------------------- #

get_font = lambda font_size, font_path: ImageFont.truetype(font_path, font_size)
resize_text = (
    lambda text_size, text: (text[:text_size] + "...").upper()
    if len(text) > text_size
    else text.upper()
)

# --------------------------------------------------------------------------------- #

async def get_userinfo_img(
    bg_path: str,
    font_path: str,
    user_id: Union[int, str],
    profile_path: Optional[str] = None
):
    bg = Image.open(bg_path)

    if profile_path:
        img = Image.open(profile_path).convert("RGBA")
        mask = Image.new("L", (400, 400), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 400, 400), fill=255)
        resized = img.resize((400, 400), Image.LANCZOS)
        circular_img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
        circular_img.paste(resized, (0, 0), mask)
        bg.paste(circular_img, (440, 160), mask)

    img_draw = ImageDraw.Draw(bg)

    img_draw.text(
        (529, 627),
        text=str(user_id).upper(),
        font=get_font(46, font_path),
        fill=(255, 255, 255),
    )

    # Save to BytesIO instead of disk
    img_byte_arr = BytesIO()
    bg.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# --------------------------------------------------------------------------------- #

bg_path = "AbhiXMusic/assets/userinfo.png"
font_path = "AbhiXMusic/assets/hiroko.ttf"

# --------------------------------------------------------------------------------- #

@app.on_chat_member_updated(filters.group, group=20)
async def member_has_left(client: app, member: ChatMemberUpdated):
    if (
        not member.new_chat_member
        and member.old_chat_member.status not in {
            "banned", "left", "restricted"
        }
        and member.old_chat_member
    ):
        pass
    else:
        return

    user = (
        member.old_chat_member.user
        if member.old_chat_member
        else member.from_user
    )

    # Get last seen (approximate, based on available data)
    last_seen = "Unknown"
    if user.status:
        if user.status == "online":
            last_seen = "Online"
        elif user.status == "offline":
            last_seen = datetime.fromtimestamp(user.status.date).strftime("%Y-%m-%d %H:%M:%S")
    bio = getattr(user, 'bio', "None")  # Safely handle bio attribute

    # Check if the user has a profile photo
    if user.photo and user.photo.big_file_id:
        try:
            # Download profile photo
            photo = await app.download_media(user.photo.big_file_id)

            welcome_photo = await get_userinfo_img(
                bg_path=bg_path,
                font_path=font_path,
                user_id=user.id,
                profile_path=photo,
            )
        
            # Use username if available, otherwise use user_id link
            redirect_link = f"tg://resolve?domain={user.username}" if user.username else f"tg://openmessage?user_id={user.id}"
            button_text = "๏ ᴠɪᴇᴡ ᴜsᴇʀ ๏"

            caption = (
                f"#New_Member_Left\n"
                f"➻ ᴜsᴇʀ ɪᴅ ‣ {user.id}\n"
                f"➻ ғɪʀsᴛ ɴᴀᴍᴇ ‣ {user.first_name}\n"
                f"➻ ʟᴀsᴛ ɴᴀᴍᴇ ‣ {user.last_name if user.last_name else 'None'}\n"
                f"➻ ᴜsᴇʀɴᴀᴍᴇ ‣ @{user.username if user.username else 'None'}\n"
                f"➻ ᴍᴇɴᴛɪᴏɴ ‣ {user.mention}\n"
                f"➻ ʟᴀsᴛ sᴇᴇɴ ‣ {last_seen}\n"
                f"➻ ᴅᴄ ɪᴅ ‣ {user.dc_id if user.dc_id else 'Unknown'}\n"
                f"➻ ʙɪᴏ ‣ {bio}\n"
                f"➻ ᴛᴇʟᴇɢʀᴀᴍ ᴘʀᴇᴍɪᴜᴍ ‣ {'True' if user.is_premium else 'False'}\n"
                f"➖➖➖➖➖➖➖➖➖➖➖\n"
                f"๏ 𝐌𝐀𝐃𝐄 𝐁𝐘 ➠ [Aʙнɪ 𓆩🇽𓆪 KI𝗡𝗚 📿](https://t.me/imagine_iq)"
            )

            # Send the message with the photo from BytesIO, caption, and button
            message = await client.send_photo(
                chat_id=member.chat.id,
                photo=welcome_photo,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(button_text, url=redirect_link)]
                ])
            )

            async def delete_message():
                await asyncio.sleep(20)
                await message.delete()

            asyncio.create_task(delete_message())
            
        except RPCError as e:
            print(e)
            return
    else:
        print(f"User {user.id} has no profile photo.")
