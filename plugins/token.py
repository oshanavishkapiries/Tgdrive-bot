import re
import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.types import ReplyParameters
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from config import Config
from helpers import gDrive_sql as db
from helpers import parent_id_sql as sql

OAUTH_SCOPE = "https://www.googleapis.com/auth/drive"
DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"


@Client.on_message(filters.private & filters.incoming & filters.command(["auth"]))
async def _auth(client, message):
    creds = db.get_credential(message.from_user.id)
    if creds is not None:
        await asyncio.to_thread(creds.refresh, GoogleAuthRequest())
        db.set_credential(message.from_user.id, creds)
        await message.reply_text(
            "🔒 **Already authorized your Google Drive Account.**\n__Use /revoke to revoke the current account.__\n__Send me a direct link or a file to upload to Google Drive.__",
            reply_parameters=ReplyParameters(message_id=message.id)
        )
        return

    try:
        device_resp = await asyncio.to_thread(
            requests.post,
            DEVICE_CODE_URL,
            data={"client_id": Config.GDRIVE_CLIENT_ID, "scope": OAUTH_SCOPE},
            timeout=30
        )
        device_resp.raise_for_status()
        device_data = device_resp.json()
    except Exception as e:
        await message.reply_text(f"**ERROR:** ```{e}```", reply_parameters=ReplyParameters(message_id=message.id))
        return

    verification_url = device_data["verification_url"]
    user_code = device_data["user_code"]
    device_code = device_data["device_code"]
    interval = device_data.get("interval", 5)
    expires_in = device_data.get("expires_in", 1800)

    sent = await message.reply_text(
        "⛓️ **To authorize your Google Drive account:**\n"
        f"1. Visit [{verification_url}]({verification_url})\n"
        f"2. Enter this code: `{user_code}`\n"
        f"3. Approve access.\n\n"
        "__I'll detect it automatically once you're done, no need to send anything back here.__",
        reply_parameters=ReplyParameters(message_id=message.id)
    )

    creds = await _poll_for_token(device_code, interval, expires_in)
    if creds is None:
        await sent.edit("❗ **Authorization timed out or was denied.**\n__Send /auth to try again.__")
        return

    db.set_credential(message.from_user.id, creds)
    await sent.edit("✅ **Authorized Google Drive account successfully.**\n__Send me a direct link or a file to upload.__")


async def _poll_for_token(device_code, interval, expires_in):
    elapsed = 0
    while elapsed < expires_in:
        await asyncio.sleep(interval)
        elapsed += interval
        resp = await asyncio.to_thread(
            requests.post,
            TOKEN_URL,
            data={
                "client_id": Config.GDRIVE_CLIENT_ID,
                "client_secret": Config.GDRIVE_CLIENT_SECRET,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            timeout=30
        )
        data = resp.json()
        if resp.status_code == 200:
            return Credentials(
                token=data["access_token"],
                refresh_token=data.get("refresh_token"),
                token_uri=TOKEN_URL,
                client_id=Config.GDRIVE_CLIENT_ID,
                client_secret=Config.GDRIVE_CLIENT_SECRET,
                scopes=[OAUTH_SCOPE],
            )
        error = data.get("error")
        if error == "slow_down":
            interval += 5
        elif error not in ("authorization_pending", None):
            return None
    return None


@Client.on_message(filters.private & filters.incoming & filters.command(["revoke"]))
async def _revoke(client, message):
    if db.get_credential(message.from_user.id) is None:
        await message.reply_text("🔑 **You have not authenticated me to upload to any account.**\n__Send /auth to authenticate.__", reply_parameters=ReplyParameters(message_id=message.id))
    else:
        try:
            db.clear_credential(message.from_user.id)
            await message.reply_text("🔓 **Authenticated account revoked successfully.**", reply_parameters=ReplyParameters(message_id=message.id))
        except Exception as e:
            await message.reply_text(f"**ERROR:** ```{e}```", reply_parameters=ReplyParameters(message_id=message.id))


@Client.on_message(filters.private & filters.incoming & filters.command(["setfolder"]))
async def _set_parent(client, message):
    if len(message.command) > 1:
        cmd_msg = message.command[1]
        if cmd_msg.lower() == "clear":
            sql.del_id(message.from_user.id)
            await message.reply_text("**Custom Folder ID Cleared**\n__Use /setfolder <Folder URL> to set it back.__", reply_parameters=ReplyParameters(message_id=message.id))
        else:
            file_id = getIdFromUrl(cmd_msg)
            if file_id == "NotFound":
                await message.reply_text("❗ **Invalid Folder URL**\n__Copy the custom folder id correctly.__", reply_parameters=ReplyParameters(message_id=message.id))
            else:
                sql.set_id(message.from_user.id, file_id)
                await message.reply_text(f"**Custom Folder ID set successfully**\n__Your custom folder id is set to {file_id}. All uploads (from now) go here.\nUse__ ```/setfolder clear``` __to clear the current Folder ID.__", reply_parameters=ReplyParameters(message_id=message.id))
    else:
        existing = sql.get_id(message.from_user.id)
        if existing:
            await message.reply_text(f"**Your custom folder id is** ```{existing.parent_id}```.", reply_parameters=ReplyParameters(message_id=message.id))
        else:
            await message.reply_text("**You did not set any Custom Folder ID**\n__Use__ ```/setfolder {folder URL}``` __to set your custom folder ID.__", reply_parameters=ReplyParameters(message_id=message.id))


def getIdFromUrl(link: str):
    found = re.search(
        r"https://drive.google.com/[\w\?\./&=]+([-\w]{33}|(?<=/)0A[-\w]{17})", link)
    if found:
        return found.group(1)
    elif len(link.split()[-1]) == 33 or len(link.split()[-1]) == 19:
        return link
    else:
        return "NotFound"
