![DisCloud](Banner.png)

# DisCloud

Uses a Discord channel as free cloud storage. Files are base64-encoded, split into ~7 MB chunks, encrypted with Fernet and uploaded as `.txt` attachments by a Discord bot. Downloading pulls the chunks back, decrypts them and reassembles the original file.

Summer project, 2025.

## How it works

```
main_GUI.py  ──writes tasks──►  shared/task_queue.json  ──polled every 2 s──►  bot_setup/discord_worker.py  ◄──►  Discord
     ▲                                                                                  │
     └──────────── reconstructs file from read/ ◄──── downloaded parts ─────────────────┘
```

`main.py` starts both: the bot runs in a background thread, the Tkinter GUI on the main thread.

- `encoding/` – reads a file, base64-encodes and splits it, encrypts each part, queues a `send` task
- `encryption/` – Fernet encrypt/decrypt and the key generator
- `bot_setup/discord_worker.py` – the bot; processes `send`, `read` and `delete` tasks from the queue
- `decoding/` – decrypts downloaded parts and rebuilds the original file into `downloads/`
- `main_GUI.py` – file manager window (upload / download / delete) and the first-run setup
- `config.py` – paths and settings, loaded from `.env`

## Running it

```
pip install -r requirements.txt
python main.py
```

Or build a standalone exe on Windows by running `build.bat`, which gives you `dist/DisCloud.exe`.

On first launch it asks for a bot token and the channel ID to store files in, with instructions for getting both. They get saved to `.env` next to the app (or the exe), and you can change them later under **Settings**. Then click **Invite bot** to add the bot to your server.

A `secret.key` is generated on first run. **Back it up** – without it, uploaded files can't be decrypted.

## Limitations

- The file list is stored locally, so another computer won't see what you uploaded (the files are still in the channel).
- Downloads scan the whole channel history, so they get slower as the channel fills up.
- Files are loaded fully into memory while encrypting, so very large files need a lot of RAM.
