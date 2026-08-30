from pyrogram import Client, filters
from pyrogram.types import ReplyParameters, InlineKeyboardMarkup, InlineKeyboardButton
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from helpers import gDrive_sql as db
from helpers import parent_id_sql as sql
from plugins.token import getIdFromUrl
from plugins.main import humanbytes

PAGE_SIZE = 25
G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"

# Tracks which folder each browsing message is currently showing, keyed by
# (chat_id, message_id), so a file preview's Back button can return to the
# right folder without needing to cram a second Drive id into callback_data
# (Telegram caps callback_data at 64 bytes, too tight for two ids).
_message_folder: dict[tuple[int, int], str] = {}


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
    header, markup, error, real_folder_id = await _render_folder(service, folder_id)
    if error:
        await sent.edit(error)
        return
    _message_folder[(sent.chat.id, sent.id)] = real_folder_id
    await sent.edit(header, reply_markup=markup, disable_web_page_preview=True)


list_folder_filter = filters.create(lambda _, __, query: query.data.startswith("lst:"))
file_preview_filter = filters.create(lambda _, __, query: query.data.startswith("filepv:"))
file_public_filter = filters.create(lambda _, __, query: query.data.startswith("filepub:"))
list_back_filter = filters.create(lambda _, __, query: query.data == "lstback")


@Client.on_callback_query(list_folder_filter)
async def _list_callback(client, callback_query):
    creds = db.get_credential(callback_query.from_user.id)
    if creds is None:
        await callback_query.answer("You're no longer authorized. Send /auth to reconnect.", show_alert=True)
        return

    folder_id = callback_query.data.split(":", 1)[1]
    await _show_folder(callback_query, creds, folder_id)


@Client.on_callback_query(list_back_filter)
async def _list_back_callback(client, callback_query):
    creds = db.get_credential(callback_query.from_user.id)
    if creds is None:
        await callback_query.answer("You're no longer authorized. Send /auth to reconnect.", show_alert=True)
        return

    key = (callback_query.message.chat.id, callback_query.message.id)
    folder_id = _message_folder.get(key, "root")
    await _show_folder(callback_query, creds, folder_id)


async def _show_folder(callback_query, creds, folder_id):
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    header, markup, error, real_folder_id = await _render_folder(service, folder_id)
    if error:
        await callback_query.answer(error, show_alert=True)
        return
    key = (callback_query.message.chat.id, callback_query.message.id)
    _message_folder[key] = real_folder_id
    await callback_query.edit_message_text(header, reply_markup=markup, disable_web_page_preview=True)
    await callback_query.answer()


@Client.on_callback_query(file_preview_filter)
async def _file_preview_callback(client, callback_query):
    creds = db.get_credential(callback_query.from_user.id)
    if creds is None:
        await callback_query.answer("You're no longer authorized. Send /auth to reconnect.", show_alert=True)
        return

    file_id = callback_query.data.split(":", 1)[1]
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    try:
        meta = service.files().get(fileId=file_id, fields="name,size,mimeType", supportsAllDrives=True).execute()
    except HttpError as err:
        await callback_query.answer(f"Could not open that file.\n{str(err).replace('<', '').replace('>', '')}", show_alert=True)
        return

    size = humanbytes(int(meta["size"])) if meta.get("size") else "unknown size"
    text = f"📄 **{meta.get('name')}**\n__{size}__\n\nMaking this public lets anyone with the link view it."
    buttons = [
        [InlineKeyboardButton("📤 Make Public & Get Link", callback_data=f"filepub:{file_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="lstback")],
    ]
    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    await callback_query.answer()


@Client.on_callback_query(file_public_filter)
async def _file_public_callback(client, callback_query):
    creds = db.get_credential(callback_query.from_user.id)
    if creds is None:
        await callback_query.answer("You're no longer authorized. Send /auth to reconnect.", show_alert=True)
        return

    file_id = callback_query.data.split(":", 1)[1]
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    try:
        permissions = service.permissions().list(fileId=file_id, fields="permissions(type)", supportsAllDrives=True).execute()
        already_public = any(p.get("type") == "anyone" for p in permissions.get("permissions", []))
        if not already_public:
            service.permissions().create(fileId=file_id, body={"type": "anyone", "role": "reader"}, supportsAllDrives=True).execute()
        meta = service.files().get(fileId=file_id, fields="name,webViewLink", supportsAllDrives=True).execute()
    except HttpError as err:
        await callback_query.answer(f"Could not make that file public.\n{str(err).replace('<', '').replace('>', '')}", show_alert=True)
        return

    text = f"✅ **{meta.get('name')} is now public.**\n🔗 {meta.get('webViewLink')}"
    buttons = [[InlineKeyboardButton("🔙 Back", callback_data="lstback")]]
    await callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)
    await callback_query.answer()


async def _render_folder(service, folder_id: str):
    try:
        folder_meta = service.files().get(
            fileId=folder_id, fields="id,name,parents", supportsAllDrives=True
        ).execute()
    except HttpError as err:
        return None, None, f"❗ Could not open that folder.\n{str(err).replace('<', '').replace('>', '')}", None

    real_id = folder_meta["id"]
    folder_name = folder_meta.get("name", "My Drive")

    try:
        response = service.files().list(
            q=f"'{real_id}' in parents and trashed = false",
            spaces="drive",
            pageSize=PAGE_SIZE,
            orderBy="folder,name",
            fields="files(id, name, mimeType, size)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
    except HttpError as err:
        return None, None, f"❗ Could not list that folder.\n{str(err).replace('<', '').replace('>', '')}", None

    items = response.get("files", [])
    buttons = []
    for item in items:
        if item.get("mimeType") == G_DRIVE_DIR_MIME_TYPE:
            buttons.append([InlineKeyboardButton(f"📁 {_truncate(item['name'])}", callback_data=f"lst:{item['id']}")])
        else:
            size = humanbytes(int(item["size"])) if item.get("size") else ""
            label = f"📄 {_truncate(item['name'])}" + (f" ({size})" if size else "")
            buttons.append([InlineKeyboardButton(label, callback_data=f"filepv:{item['id']}")])

    parents = folder_meta.get("parents")
    if parents:
        buttons.append([InlineKeyboardButton("🔙 Back", callback_data=f"lst:{parents[0]}")])

    header = f"📂 **{folder_name}**"
    if not items:
        header += "\n__This folder is empty.__"
    elif len(items) == PAGE_SIZE:
        header += f"\n__Showing the first {PAGE_SIZE} items.__"

    markup = InlineKeyboardMarkup(buttons) if buttons else None
    return header, markup, None, real_id


def _truncate(name: str, limit: int = 40) -> str:
    return name if len(name) <= limit else name[: limit - 1] + "…"
