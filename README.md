# Tgdrive-bot

A Telegram bot that uploads files, direct download links, and cloned Google Drive files/folders straight into a user's own Google Drive account.

This is a modernized fork of an older (2019-era) project: the Telegram library, Google auth flow, database layer, and downloader have all been rewritten to work with current APIs and libraries. See the commit history for what changed and why.

## Features
- Upload Telegram files (photo/video/document/audio) to your Google Drive
- Upload from a direct download link, with optional rename (`url | New Name.ext`)
- Set a custom upload folder or Shared Drive (`/setfolder`)
- Clone/copy Google Drive files or folders into your account (`/copy`)

## Requirements
- Python 3.10+
- A Telegram API ID/Hash from https://my.telegram.org/apps
- A Telegram bot token from https://t.me/BotFather
- A Google Cloud project with the Drive API enabled and an OAuth 2.0 client of type **"TVs and Limited Input devices"** (required for the device-code auth flow this bot uses)

## Setup (local dependencies only, nothing installed globally)

```sh
git clone https://github.com/oshanavishkapiries/Tgdrive-bot.git
cd Tgdrive-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and fill in APP_ID, API_HASH, BOT_TOKEN, GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET
```

## Running

Directly (useful while testing):
```sh
source venv/bin/activate
python bot.py
```

With pm2 (keeps the bot running and restarts it on crash/reboot):
```sh
npm install -g pm2   # one-time, pm2 itself is a global process manager
pm2 start ecosystem.config.js
pm2 save
pm2 logs tgdrive-bot
```

Deleting the project folder removes the venv and the SQLite database with it — nothing this project needs is installed outside `Tgdrive-bot/`.

## How Google Drive auth works

Users run `/auth` in the bot. The bot starts a Google **device authorization** flow: it replies with a short URL and a code. The user opens the URL on any device, enters the code, and approves access. The bot polls Google in the background and finishes automatically — no code needs to be pasted back into the chat.

## Data storage

User credentials and per-user folder settings are stored in a local SQLite file (path set by `DATABASE_PATH` in `.env`, default `data/bot.db`). This file is not committed to git.

## Contributing

1. Fork and branch off `main`.
2. Keep changes scoped and use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, etc.) for commit messages.
3. Test that `python bot.py` starts cleanly against a real `.env` before opening a PR.
4. Open a PR describing what changed and why.

## License

GPLv3 — see [LICENSE](./LICENSE). This project is a derivative of an earlier GPLv3-licensed bot, so it remains under the same license.
