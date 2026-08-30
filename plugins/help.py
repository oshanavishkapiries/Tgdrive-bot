from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyParameters
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
        text=tr.HELP_MSG[1],
        parse_mode=enums.ParseMode.MARKDOWN,
        disable_notification=True,
        reply_markup=InlineKeyboardMarkup(help_keyboard(1)),
        reply_parameters=ReplyParameters(message_id=message.id)
    )


help_callback_filter = filters.create(lambda _, __, query: query.data.startswith("help+"))


@Client.on_callback_query(help_callback_filter)
async def help_answer(client, callback_query):
    chat_id = callback_query.from_user.id
    message_id = callback_query.message.id
    msg = int(callback_query.data.split("+")[1])
    await client.edit_message_text(
        chat_id=chat_id, message_id=message_id,
        text=tr.HELP_MSG[msg], reply_markup=InlineKeyboardMarkup(help_keyboard(msg))
    )


def help_keyboard(pos):
    if pos == 1:
        buttons = [
            [InlineKeyboardButton(text="-->", callback_data="help+2")]
        ]
    elif pos == len(tr.HELP_MSG) - 1:
        buttons = [
            [InlineKeyboardButton(text="<--", callback_data=f"help+{pos-1}")]
        ]
    else:
        buttons = [
            [
                InlineKeyboardButton(text="<--", callback_data=f"help+{pos-1}"),
                InlineKeyboardButton(text="-->", callback_data=f"help+{pos+1}")
            ],
        ]
    return buttons
