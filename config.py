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
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/bot.db")


class Messages:

    START_MSG = "**Hi there {}.**\n__I'm a Google Drive Uploader Bot. You can use me to upload any file / video to Google Drive from a direct link or Telegram files.__\n__You can learn more from /help.__"

    HELP_MSG = [
        ".",
        "**Google Drive Uploader**\n__I can upload files from a direct link or Telegram files to your Google Drive. All I need is to authenticate to your Google Drive account, then you send me a direct download link or Telegram file.__\n\nI have more features... ! Just walk through this tutorial and read the messages carefully.",

        "**Authenticating Google Drive**\n__Send the /auth command and you will receive a URL, visit the URL, follow the steps, and send the received code here. Use /revoke to revoke your currently logged Google Drive account.__",

        "**Direct Links**\n__Send me a direct download link for a file and I will download it on my server and upload it to your Google Drive account. You can rename files before uploading. Just send me the URL and new filename separated by ' | '.__\n\n**__Examples:__**\n```https://example.com/AFileWithDirectDownloadLink.mkv | New FileName.mkv```",

        "**Telegram Files**\n__To upload Telegram files to your Google Drive account just send me the file and I will download and upload it. Note: Telegram file downloads are slow. It may take longer for big files.__",

        "**Custom Folder for Upload**\n__Want to upload to a custom folder or a__ **Shared Drive** __?\nUse /setfolder {Folder ID / Shared Drive ID / Folder URL} to set a custom upload folder.\nAll files are uploaded to the custom folder you provide.__",

        "**Copy Google Drive Files**\n__Yes, clone or copy Google Drive files.\nUse /copy {File id / Folder id or URL} to copy Google Drive files into your account.__",

        "**Rules & Precautions**\n__1. Don't copy BIG Google Drive files/folders. It may hang the bot and your files may be damaged.\n2. Send one request at a time or the bot will stop all processes.\n3. Don't send slow links, transload them first.\n4. Don't misuse, overload or abuse this service.__",

        "**Thanks for using this bot.**"
        ]
