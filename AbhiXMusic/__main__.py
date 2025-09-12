import asyncio
import importlib
from sys import argv
from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from AbhiXMusic import LOGGER, app, userbot
from AbhiXMusic.core.call import Hotty
from AbhiXMusic.misc import sudo
from AbhiXMusic.plugins import ALL_MODULES
from AbhiXMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


from AbhiXMusic.plugins.tools.chatbot import start_riya_chatbot, stop_riya_chatbot



async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()
    await sudo()
    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass
    
    await app.start() # आपका मुख्य बॉट स्टार्ट होता है
    
    # --- ADD THESE CALLS FOR RIYA CHATBOT STARTUP ---
    try:
        await start_riya_chatbot()
        LOGGER(__name__).info("Riya Chatbot Client Started!")
    except Exception as ex:
        LOGGER(__name__).error(
            f"Error starting Riya Chatbot Client: {ex}"
        )
    # --- END RIYA CHATBOT STARTUP ---

    for all_module in ALL_MODULES:
        importlib.import_module("AbhiXMusic.plugins" + all_module)
    LOGGER("AbhiXMusic.plugins").info("Successfully Imported Modules...")
    
    await userbot.start() 
    await Hotty.start() 
    
    try:
        await Hotty.stream_call("https://graph.org/file/e999c40cb700e7c684b75.mp4")
    except NoActiveGroupCall:
        LOGGER("AbhiXMusic").error(
            "Please turn on the videochat of your log group\channel.\n\nStopping Bot..."
        )
        exit()
    except:
        pass
    await Hotty.decorators()
    LOGGER("AbhiXMusic").info(
        "ᴅʀᴏᴘ ʏᴏᴜʀ ɢɪʀʟꜰʀɪᴇɴᴅ'ꜱ ɴᴜᴍʙᴇʀ ᴀᴛ @URFather_ABHI ᴊᴏɪɴ @imagine_iq , @The_vision_1 ꜰᴏʀ ᴀɴʏ ɪꜱꜱᴜᴇꜱ"
    )
    
    await idle() # बॉट तब तक चलता रहेगा जब तक Ctrl+C न दबाया जाए
    
    await app.stop() # मुख्य बॉट स्टॉप होता है
    await userbot.stop() # असिस्टेंट बॉट स्टॉप होता है
    LOGGER("AbhiXMusic").info("Stopping AbhiXMusic Bot...")

    # --- ADD THESE CALLS FOR RIYA CHATBOT SHUTDOWN ---
    try:
        await stop_riya_chatbot()
        LOGGER(__name__).info("Riya Chatbot Client Stopped.")
    except Exception as ex:
        LOGGER(__name__).error(
            f"Error stopping Riya Chatbot Client: {ex}"
        )
    # --- END RIYA CHATBOT SHUTDOWN ---

    # --- Stop PyTgCalls client (Hotty) ---
    # यह Hotty.stop() से अलग है, लेकिन अगर आपके पास कोई अलग PyTgCalls स्टॉप लॉजिक है तो उसे यहीं रखा जा सकता है।
    # Hotty.stop() शायद Hotty.py में होगा।
    # यहाँ यह सुनिश्चित करने के लिए छोड़ दिया गया है कि कोई भी PyTgCalls cleanup होता है।
    pass # अगर Hotty.stop() पहले से Hotty.py में है, तो इसे पास ही रहने दें, वरना Hotty.stop() को यहाँ कॉल करें।


if __name__ == "__main__":
    # यह सुनिश्चित करता है कि init() फंक्शन को एक asyncio इवेंट लूप में चलाया जाए।
    asyncio.get_event_loop().run_until_complete(init())
