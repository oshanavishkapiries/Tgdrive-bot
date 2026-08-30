import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyParameters
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleAuthRequest
from config import Config
from helpers import gDrive_sql as db
from helpers import parent_id_sql as sql

OAUTH_SCOPE = "https://www.googleapis.com/auth/drive"
G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"

# Per-user in-progress OAuth flows, keyed by Telegram user id. A user has at
# most one pending /auth at a time; starting a new one replaces the old.
_pending_flows: dict[int, Flow] = {}


def _build_flow() -> Flow:
    client_config = {
        "web": {
            "client_id": Config.GDRIVE_CLIENT_ID,
            "client_secret": Config.GDRIVE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [Config.GDRIVE_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=[OAUTH_SCOPE],
        redirect_uri=Config.GDRIVE_REDIRECT_URI,
    )


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

    flow = _build_flow()
    auth_url, _ = flow.authorization_url(access_type="offline", prompt="consent")
    _pending_flows[message.from_user.id] = flow

    await message.reply_text(
        "⛓️ **To authorize your Google Drive account:**\n"
        f"1. Visit [this link]({auth_url})\n"
        "2. Approve access.\n"
        "3. Copy the code shown on the page and send it back here.",
        reply_parameters=ReplyParameters(message_id=message.id)
    )


def _has_pending_flow(_, __, message):
    if not message.from_user or message.from_user.id not in _pending_flows:
        return False
    return not (message.text or "").startswith("/")


pending_auth_filter = filters.create(_has_pending_flow)


@Client.on_message(filters.private & filters.incoming & filters.text & pending_auth_filter)
async def _auth_code(client, message):
    flow = _pending_flows.pop(message.from_user.id)
    code = message.text.strip()

    sent = await message.reply_text("**Checking received code...**", reply_parameters=ReplyParameters(message_id=message.id))
    try:
        await asyncio.to_thread(flow.fetch_token, code=code)
    except Exception as e:
        await sent.edit(f"❗ **Invalid code or it was already used.**\n__Send /auth to try again.__\n```{e}```")
        return

    db.set_credential(message.from_user.id, flow.credentials)
    await sent.edit("✅ **Authorized Google Drive account successfully.**\n__Send me a direct link or a file to upload.__")


@Client.on_message(filters.private & filters.incoming & filters.command(["revoke"]))
async def _revoke(client, message):
    _pending_flows.pop(message.from_user.id, None)
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
