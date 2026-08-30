from pyrogram import Client, filters
from pyrogram.types import ReplyParameters, InlineKeyboardMarkup, InlineKeyboardButton
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from helpers import gDrive_sql as db
from helpers import parent_id_sql as sql
from plugins.token import getIdFromUrl

PAGE_SIZE = 25
G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"


@Client.on_message(filters.private & filters.incoming & filters.command(["list"]))
async def _list(client, message):
    creds = db.get_credential(message.from_user.id)
    if creds is None:
        await message.reply_text("❗ **Not an authorized user.**\n__Authorize your Google Drive account by running the /auth command in order to use this bot.__", reply_parameters=ReplyParameters(message_id=message.id))
        return

    if len(message.command) > 1:
        folder_id = getIdFromUrl(message.command[1])
        if folder_id == "NotFound":
            await message.reply_text("❗ **Invalid Folder URL**\n__Copy the folder id or link correctly.__", reply_parameters=ReplyParameters(message_id=message.id))
            return
    else:
        existing = sql.get_id(message.from_user.id)
        folder_id = existing.parent_id if existing else "root"

    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    sent = await message.reply_text("**Loading...**", reply_parameters=ReplyParameters(message_id=message.id))
    header, markup, error = await _render_folder(service, folder_id)
    if error:
        await sent.edit(error)
        return
    await sent.edit(header, reply_markup=markup, disable_web_page_preview=True)


list_folder_filter = filters.create(lambda _, __, query: query.data.startswith("lst:"))


@Client.on_callback_query(list_folder_filter)
async def _list_callback(client, callback_query):
    creds = db.get_credential(callback_query.from_user.id)
    if creds is None:
        await callback_query.answer("You're no longer authorized. Send /auth to reconnect.", show_alert=True)
        return

    folder_id = callback_query.data.split(":", 1)[1]
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    header, markup, error = await _render_folder(service, folder_id)
    if error:
        await callback_query.answer(error, show_alert=True)
        return
    await callback_query.edit_message_text(header, reply_markup=markup, disable_web_page_preview=True)
    await callback_query.answer()


async def _render_folder(service, folder_id: str):
    try:
        folder_meta = service.files().get(
            fileId=folder_id, fields="id,name,parents", supportsAllDrives=True
        ).execute()
    except HttpError as err:
        return None, None, f"❗ Could not open that folder.\n{str(err).replace('<', '').replace('>', '')}"

    real_id = folder_meta["id"]
    folder_name = folder_meta.get("name", "My Drive")

    try:
        response = service.files().list(
            q=f"'{real_id}' in parents and trashed = false",
            spaces="drive",
            pageSize=PAGE_SIZE,
            orderBy="folder,name",
            fields="files(id, name, mimeType, size, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
    except HttpError as err:
        return None, None, f"❗ Could not list that folder.\n{str(err).replace('<', '').replace('>', '')}"

    items = response.get("files", [])
    buttons = []
    for item in items:
        if item.get("mimeType") == G_DRIVE_DIR_MIME_TYPE:
            buttons.append([InlineKeyboardButton(f"📁 {_truncate(item['name'])}", callback_data=f"lst:{item['id']}")])
        else:
            link = item.get("webViewLink") or f"https://drive.google.com/file/d/{item['id']}/view"
            size = _humanbytes(int(item["size"])) if item.get("size") else ""
            label = f"📄 {_truncate(item['name'])}" + (f" ({size})" if size else "")
            buttons.append([InlineKeyboardButton(label, url=link)])

    parents = folder_meta.get("parents")
    if parents:
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"lst:{parents[0]}")])

    header = f"📂 **{folder_name}**"
    if not items:
        header += "\n__This folder is empty.__"
    elif len(items) == PAGE_SIZE:
        header += f"\n__Showing the first {PAGE_SIZE} items.__"

    markup = InlineKeyboardMarkup(buttons) if buttons else None
    return header, markup, None


def _truncate(name: str, limit: int = 40) -> str:
    return name if len(name) <= limit else name[: limit - 1] + "…"


def _humanbytes(size: int) -> str:
    if not size:
        return ""
    power = 2 ** 10
    number = 0
    dict_power_n = {0: " ", 1: "K", 2: "M", 3: "G", 4: "T", 5: "P"}
    while size > power:
        size /= power
        number += 1
    return str(round(size, 2)) + " " + dict_power_n[number] + "B"
