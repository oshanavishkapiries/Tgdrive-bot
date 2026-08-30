# Tgdrive-bot

A Telegram bot that uploads files, direct download links, and cloned Google Drive files/folders straight into a user's own Google Drive account.

This is a modernized fork of an older (2019-era) project: the Telegram library, Google auth flow, database layer, and downloader have all been rewritten to work with current APIs and libraries. See the commit history for what changed and why.

## Features
- Upload Telegram files (photo/video/document/audio) to your Google Drive
- Upload from a direct download link, with optional rename (`url | New Name.ext`)
- Set a custom upload folder or Shared Drive (`/setfolder`)
- Clone/copy Google Drive files or folders into your account (`/copy`)
- Browse your Drive with interactive folder navigation (`/list`)

## Requirements
- Python 3.10+
- A Telegram API ID/Hash from https://my.telegram.org/apps
- A Telegram bot token from https://t.me/BotFather
- A Google Cloud project with the Drive API enabled and an OAuth 2.0 client of type **"Web application"** (the full `drive` scope this bot needs is not available on the device-code/TV flow, only the standard web Authorization Code flow)
- A free Cloudflare account, to deploy the tiny redirect-catcher Worker in [cloudflare-worker/worker.js](./cloudflare-worker/worker.js) — this stands in for a real domain + SSL certificate, since Google requires an HTTPS redirect URI and Cloudflare Workers get one for free on `*.workers.dev`

## Setup (local dependencies only, nothing installed globally)

```sh
git clone https://github.com/oshanavishkapiries/Tgdrive-bot.git
cd Tgdrive-bot

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and fill in APP_ID, API_HASH, BOT_TOKEN, GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REDIRECT_URI
```

### Setting up Google OAuth + the Cloudflare Worker

1. In the [Cloudflare dashboard](https://dash.cloudflare.com/), go to Workers & Pages → Create → Create Worker, paste in the contents of [cloudflare-worker/worker.js](./cloudflare-worker/worker.js), and deploy. Note the resulting URL, e.g. `https://tgdrive-oauth.<your-subdomain>.workers.dev`.
2. In [Google Cloud Console](https://console.cloud.google.com/apis/credentials), create an OAuth 2.0 Client ID of type **Web application**, and add that exact Worker URL as an Authorized redirect URI.
3. Put the client ID, client secret, and the Worker URL into `.env` as `GDRIVE_CLIENT_ID`, `GDRIVE_CLIENT_SECRET`, `GDRIVE_REDIRECT_URI`.

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

See [RUNNING.md](./RUNNING.md) for the full command reference — pm2 management, updating after a `git pull`, changing config, troubleshooting, and removal.

Deleting the project folder removes the venv and the SQLite database with it — nothing this project needs is installed outside `Tgdrive-bot/`.

## How Google Drive auth works

Users run `/auth` in the bot. The bot replies with a Google consent URL. The user opens it, approves access, and Google redirects their browser to the Cloudflare Worker, which displays a short code on the page. The user copies that code and pastes it back into the Telegram chat, and the bot exchanges it for real credentials.

## Data storage

User credentials and per-user folder settings are stored in a local SQLite file (path set by `DATABASE_PATH` in `.env`, default `data/bot.db`). This file is not committed to git.

## Contributing

1. Fork and branch off `main`.
2. Keep changes scoped and use [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, etc.) for commit messages.
3. Test that `python bot.py` starts cleanly against a real `.env` before opening a PR.
4. Open a PR describing what changed and why.

## License

GPLv3 — see [LICENSE](./LICENSE). This project is a derivative of an earlier GPLv3-licensed bot, so it remains under the same license.
