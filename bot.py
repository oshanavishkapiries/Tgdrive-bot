import asyncio
from pyrogram import Client, idle
from pyrogram.types import BotCommand
from config import Config

plugins = dict(root="plugins")

app = Client(
    "GDrive-Bot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.APP_ID,
    api_hash=Config.API_HASH,
    plugins=plugins
)

BOT_COMMANDS = [
    BotCommand("start", "Start the bot"),
    BotCommand("help", "Show all available commands"),
    BotCommand("auth", "Authenticate your Google Drive account"),
    BotCommand("revoke", "Revoke your authenticated Google Drive account"),
    BotCommand("setfolder", "Set or view a custom upload folder"),
    BotCommand("copy", "Copy a Google Drive file or folder into your account"),
]


async def main():
    await app.start()
    await app.set_bot_commands(BOT_COMMANDS)
    await idle()
    await app.stop()


asyncio.run(main())
