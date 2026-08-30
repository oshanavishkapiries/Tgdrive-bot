import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}. Did you copy .env.example to .env?")
    return value


class Config:
    BOT_TOKEN = _require("BOT_TOKEN")
    APP_ID = _require("APP_ID")
    API_HASH = _require("API_HASH")
    GDRIVE_CLIENT_ID = _require("GDRIVE_CLIENT_ID")
    GDRIVE_CLIENT_SECRET = _require("GDRIVE_CLIENT_SECRET")
    GDRIVE_REDIRECT_URI = _require("GDRIVE_REDIRECT_URI")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/bot.db")


class Messages:

    START_MSG = "**Hi there {}.**\n__I'm a Google Drive Uploader Bot. You can use me to upload any file / video to Google Drive from a direct link or Telegram files.__\n__You can learn more from /help.__"

    HELP_MSG = (
        "**Available Commands**\n\n"
        "/start - __Start the bot__\n"
        "/help - __Show this list of commands__\n"
        "/auth - __Authenticate your Google Drive account__\n"
        "/revoke - __Revoke your authenticated Google Drive account__\n"
        "/setfolder - __Set or view a custom upload folder (`/setfolder {folder id/URL}`, or `/setfolder clear`)__\n"
        "/copy - __Copy a Google Drive file or folder into your account (`/copy {file/folder id or URL}`)__\n"
        "/list - __Browse your Google Drive files and folders (`/list` or `/list {folder id/URL}`). Tapping a file lets you make it public and get a shareable link.__\n\n"
        "__You can also just send me a direct download link, or a Telegram file/photo/video/audio, once you're authenticated with /auth.__"
    )
