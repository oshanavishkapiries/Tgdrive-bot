# Running Tgdrive-bot

Step-by-step commands for running the bot directly, and for keeping it alive in the background with pm2. Assumes you've already followed the **Setup** section in [README.md](./README.md) (venv created, dependencies installed, `.env` filled in).

## 1. Running directly (for testing)

```sh
cd Tgdrive-bot
source venv/bin/activate
python bot.py
```

Stop it with `Ctrl+C`. Nothing is installed outside `Tgdrive-bot/` — the venv and `data/bot.db` both live inside this folder.

### Quick smoke test

Once it's running, message the bot on Telegram and check each of these in order:

1. `/start` — should reply with a greeting
2. `/help` — should reply with the command list
3. `/auth` — should reply with a Google consent link; approve it, copy the code the Cloudflare Worker page shows, paste it back into the chat, and confirm you get "Authorized Google Drive account successfully"
4. `/list` — should show inline buttons for your Drive root (or your `/setfolder` folder); tap into a folder, then tap a file and confirm "Make Public & Get Link" returns a working link
5. Send a direct download link, or a Telegram file/photo — should download and upload to Drive

## 2. Running with pm2 (recommended for a live server)

pm2 is the one thing in this whole setup that installs globally, because it's a process manager, not a project dependency of the bot itself.

### Install pm2 (one-time)

```sh
npm install -g pm2
```

### Start the bot

From inside the project folder:

```sh
cd Tgdrive-bot
pm2 start ecosystem.config.js
```

`ecosystem.config.js` already points pm2 at `./venv/bin/python bot.py`, so it always runs with the project's own venv, not any system Python.

### Everyday pm2 commands

```sh
pm2 list                        # see status of all pm2-managed processes
pm2 logs tgdrive-bot            # tail live logs
pm2 logs tgdrive-bot --lines 200
pm2 restart tgdrive-bot         # restart (e.g. after editing .env)
pm2 stop tgdrive-bot            # stop without removing it from pm2's list
pm2 delete tgdrive-bot          # remove it from pm2 entirely
```

### Make it survive a server reboot

```sh
pm2 save                        # snapshot the current process list
pm2 startup                     # prints a command — copy/run that command with sudo
pm2 save                        # save again once startup is registered
```

## 3. Updating the bot after pulling new code

```sh
cd Tgdrive-bot
git pull
source venv/bin/activate
pip install -r requirements.txt   # in case dependencies changed
pm2 restart tgdrive-bot
```

If `cloudflare-worker/worker.js` changed in the pull, that's not deployed automatically — open the Worker in the Cloudflare dashboard, paste in the updated file, and redeploy it there too.

## 4. Changing config

Edit `.env`, then restart so the new values are picked up (env vars are only read at startup):

```sh
pm2 restart tgdrive-bot
```

## 5. Troubleshooting

```sh
pm2 logs tgdrive-bot --lines 200   # most issues show up here
pm2 monit                           # live CPU/memory view
```

| Symptom | Likely cause |
|---|---|
| `RuntimeError: Missing required environment variable: X` | `.env` doesn't exist yet, or is missing that field — copy `.env.example` to `.env` and fill it in |
| Bot doesn't reply on Telegram at all | Check `pm2 list` shows it `online`; check `BOT_TOKEN` is correct and not revoked |
| `/auth` fails immediately with an error | `GDRIVE_CLIENT_ID`/`GDRIVE_CLIENT_SECRET` wrong, Drive API not enabled on the Google Cloud project, the OAuth client isn't type "Web application", or `GDRIVE_REDIRECT_URI` doesn't exactly match an Authorized redirect URI on that OAuth client |
| Pasting the code back does nothing / says invalid | The code is single-use and expires quickly — run /auth again and paste the fresh code promptly; also check the Cloudflare Worker is still deployed and reachable |
| `/list` says "Could not open that folder" | Credentials expired/revoked (send /auth again), the Drive API isn't enabled on the Google Cloud project, or the folder id/URL passed to `/list` is wrong |
| "Make Public & Get Link" fails | The authenticated Google account doesn't own or have permission-editing rights on that file (e.g. it's someone else's file shared read-only with you) |
| Uploads fail with `LimitExceeded` | Google Drive API daily/user rate limit hit on that Google account — wait 24h |

## 6. Removing the bot entirely

```sh
pm2 delete tgdrive-bot
pm2 save
rm -rf ~/Tgdrive-bot   # or wherever you cloned it — takes the venv and database with it
```

(pm2/Node itself stays installed globally unless you also run `npm uninstall -g pm2` — only remove that if nothing else on the server needs it.)
