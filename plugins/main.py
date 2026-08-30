import os
import requests
import asyncio
from pyrogram import Client, filters
from plugins.uploader import upload_file
from helpers import gDrive_sql as db
from helpers import parent_id_sql as sql


@Client.on_message(filters.private & filters.incoming & (filters.audio | filters.photo | filters.video | filters.document | filters.regex(r"^(ht|f)tps?://")))
async def _start(client, message):
    creds = db.get_credential(message.from_user.id)
    if creds is None:
        await message.reply_text("🔑 **You have not authenticated me to upload to any account.**\n__Send /auth to authenticate.__", quote=True)
        return
    parent_row = sql.get_id(message.from_user.id)
    parent_id = parent_row.parent_id if parent_row else None

    filename = None
    if message.text:
        sent_message = await message.reply_text("**Checking Link...**", quote=True)
        filename = await download_file(message, sent_message)
        if filename is None:
            await sent_message.edit("**❗ Invalid URL**\n__Make sure it's a direct link and in a working state.__")
            return
    elif message.media:
        sent_message = await message.reply_text("📥 **Downloading File...**", quote=True)
        try:
            filename = await client.download_media(message=message)
        except Exception as e:
            await sent_message.edit(f"**ERROR:** ```{e}```")
            return

    filesize = humanbytes(os.path.getsize(filename))
    file_name = os.path.basename(filename)
    await sent_message.edit(f"✅ **Download Completed**\n**Filename:** ```{file_name}```\n**Size:** ```{filesize}```\n__Now starting upload...__")
    file_id = await upload_file(
        creds=creds,
        file_path=filename,
        filesize=filesize,
        parent_id=parent_id,
        message=sent_message)
    if file_id not in ("error", "LimitExceeded"):
        await sent_message.edit("✅ **Uploaded Successfully.**\n<a href='https://drive.google.com/open?id={}'>{}</a> __({})__".format(file_id, file_name, filesize))
    elif file_id == "LimitExceeded":
        await sent_message.edit("❗ **Upload limit exceeded**\n__Try after 24 hours__")
    else:
        await sent_message.edit("❗ **Uploading Error**\n__Please try again later.__")
    os.remove(filename)


async def download_file(message, sent_message):
    separated = message.text.strip()
    url = separated
    custom_file_name = os.path.basename(url)
    if "|" in separated:
        url, custom_file_name = separated.split("|", 1)
        url = url.strip()
        custom_file_name = custom_file_name.strip()

    os.makedirs("downloads", exist_ok=True)
    dest_path = os.path.join("downloads", custom_file_name or os.path.basename(url))

    await sent_message.edit(f"📥 **Downloading...**\n**Filename:** ```{os.path.basename(dest_path)}```")
    try:
        return await asyncio.to_thread(_stream_download, url, dest_path)
    except requests.RequestException:
        return None


def _stream_download(url, dest_path):
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    return dest_path


def humanbytes(size: int) -> str:
    if not size:
        return ""
    power = 2 ** 10
    number = 0
    dict_power_n = {
        0: " ",
        1: "K",
        2: "M",
        3: "G",
        4: "T",
        5: "P"
    }
    while size > power:
        size /= power
        number += 1
    return str(round(size, 2)) + " " + dict_power_n[number] + "B"
