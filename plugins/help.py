from pyrogram import Client, filters, enums
from pyrogram.types import ReplyParameters
from config import Messages as tr


@Client.on_message(filters.private & filters.incoming & filters.command(["start"]))
async def _start(client, message):
    await client.send_message(
        chat_id=message.chat.id,
        text=tr.START_MSG.format(message.from_user.first_name),
        parse_mode=enums.ParseMode.MARKDOWN,
        disable_notification=True,
        reply_parameters=ReplyParameters(message_id=message.id)
    )


@Client.on_message(filters.private & filters.incoming & filters.command(["help"]))
async def _help(client, message):
    await client.send_message(
        chat_id=message.chat.id,
        text=tr.HELP_MSG,
        parse_mode=enums.ParseMode.MARKDOWN,
        disable_notification=True,
        reply_parameters=ReplyParameters(message_id=message.id)
    )
