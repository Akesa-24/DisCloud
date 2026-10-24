import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.filedialog as fd
import json
import os
import sys
import glob
import time
import threading
import subprocess
import webbrowser

import discord

import config
from encoding.encoding_to_base64 import split_file_to_txt, append_to_json_file
from decoding.reconstruct_file import reconstruct_file
from bot_setup import discord_worker

root = None
scrollable_frame = None
summary_label = None
status_label = None

SETUP_HELP = """How to get a bot:
1. Go to discord.com/developers/applications -> New Application
2. Bot tab: Reset Token and paste it below. Also turn on "Message Content Intent"
3. In Discord: Settings -> Advanced -> Developer Mode on.
    Then right-click the channel you want to store files in -> Copy Channel ID
4. After saving, click "Invite bot" in the main window and add it to that server

A secret.key file gets made next to the app the first time.
Back it up, without it your uploaded files can't be decrypted."""


def handle_download(filename):
    file_prefix = os.path.splitext(filename)[0]
    text_pattern = f"{file_prefix}_part_*.txt"

    # old parts from a failed download would get glued into the new file
    for old_part in glob.glob(os.path.join(config.READ_FOLDER, text_pattern.replace(" ", "_"))):
        os.remove(old_part)

    task = {
        "task": "read",
        "channel_id": config.CHANNEL_ID,
        "text_pattern": text_pattern
    }
    append_to_json_file(config.QUEUE_PATH, task)
    discord_worker.activity = f"Downloading {filename}..."

    # wait in a thread so the window doesn't freeze anymore
    threading.Thread(target=download_worker, args=(filename, text_pattern), daemon=True).start()


def download_worker(filename, text_pattern):
    if not wait_for_read(text_pattern):
        root.after(0, lambda: messagebox.showerror("Download failed", f"Couldn't find any parts of '{filename}' in the channel."))
        return

    try:
        output_path = reconstruct_file(file_name=os.path.splitext(filename)[0])
    except Exception as e:
        # usually means the parts were encrypted with a different secret.key
        root.after(0, lambda err=e: messagebox.showerror("Download failed", f"Couldn't decrypt '{filename}':\n{err}"))
        return

    discord_worker.activity = f"Downloaded {filename} ✅"
    root.after(0, lambda: download_done(output_path))


def download_done(output_path):
    if messagebox.askyesno("Downloaded", f"Saved to:\n{output_path}\n\nOpen the downloads folder?"):
        open_folder(config.DOWNLOADS_FOLDER)


def wait_for_read(text_pattern, timeout=3600):
    # the bot puts the pattern into finished_reads once it went through the whole channel,
    # so no more guessing based on when part 001 shows up
    waited = 0
    while waited < timeout:
        if text_pattern in discord_worker.finished_reads:
            return discord_worker.finished_reads.pop(text_pattern) > 0
        time.sleep(0.5)
        waited += 0.5
    return False


def handle_delete(filename):
    result = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{filename}'?")
    if result:
        try:
            data = load_file_list()
            data = [item for item in data if item.get("filename") != filename]

            with open(config.FILE_LIST_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            refresh_gui()
            file_prefix = os.path.splitext(filename)[0]
            task = {
                "task": "delete",
                "channel_id": config.CHANNEL_ID,
                "text_pattern": f"{file_prefix}"
            }
            append_to_json_file(config.QUEUE_PATH, task)
            discord_worker.activity = f"Deleting {filename}..."
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete: {e}")


def handle_upload():
    file_path = fd.askopenfilename(title="Select file to upload")
    if not file_path:
        return
    discord_worker.activity = f"Encrypting {os.path.basename(file_path)}..."
    # big files take a while to encrypt, same deal as downloads
    threading.Thread(target=upload_worker, args=(file_path,), daemon=True).start()


def upload_worker(file_path):
    try:
        split_file_to_txt(file_path)

        file_entry = {
            "filename": os.path.basename(file_path),
            "original_size": os.path.getsize(file_path),
        }
        data = load_file_list()
        data.append(file_entry)
        with open(config.FILE_LIST_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        root.after(0, refresh_gui)
    except Exception as e:
        root.after(0, lambda err=e: messagebox.showerror("Upload Error", f"An error occurred:\n{err}"))


def format_size(bytes_size):
    kb = 1024
    mb = kb * 1024
    if bytes_size >= mb:
        return f"{bytes_size / mb:.2f} MB"
    elif bytes_size >= kb:
        return f"{bytes_size / kb:.2f} KB"
    else:
        return f"{bytes_size} B"


def load_file_list():
    if not os.path.exists(config.FILE_LIST_PATH):
        return []
    with open(config.FILE_LIST_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def refresh_gui():
    """Rebuild the file list and the summary label from file_list.json."""
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    file_list = load_file_list()
    total_size = sum(file.get("original_size", 0) for file in file_list)
    count = len(file_list)

    if summary_label:
        summary_label.config(text=f"Total files stored: {count} | Total size: {format_size(total_size)}")

    for file_info in file_list:
        filename = file_info.get("filename", "unknown.txt")
        size = file_info.get("original_size", 0)

        row = ttk.Frame(scrollable_frame)
        row.pack(fill="x", pady=2, padx=5)

        label = ttk.Label(row, text=f"{filename} ({format_size(size)})", width=50)
        label.pack(side="left")

        dl_btn = ttk.Button(row, text="Download", command=lambda f=filename: handle_download(f))
        dl_btn.pack(side="left", padx=5)

        del_btn = ttk.Button(row, text="Delete", command=lambda f=filename: handle_delete(f))
        del_btn.pack(side="left", padx=5)


def update_status():
    status_label.config(text=f"Bot: {discord_worker.bot_status}    {discord_worker.activity}")

    if discord_worker.bot_status == "bad token":
        messagebox.showerror("Login failed", "Discord didn't accept that bot token, enter it again.")
        if ask_for_settings(root):
            restart_app()
        root.destroy()
        return

    root.after(1000, update_status)


def invite_bot():
    if not discord_worker.bot.user:
        messagebox.showinfo("Invite bot", "Bot isn't online yet, give it a sec.")
        return
    perms = discord.Permissions(view_channel=True, send_messages=True, attach_files=True, read_message_history=True)
    webbrowser.open(discord.utils.oauth_url(discord_worker.bot.user.id, permissions=perms))


def change_settings():
    if ask_for_settings(root):
        restart_app()


def ask_for_settings(parent):
    win = tk.Toplevel(parent)
    win.title("DisCloud setup")
    win.resizable(False, False)
    set_icon(win)
    saved = {"ok": False}

    ttk.Label(win, text=SETUP_HELP, justify="left").pack(padx=15, pady=(15, 10), anchor="w")

    ttk.Label(win, text="Bot token").pack(anchor="w", padx=15)
    token_entry = ttk.Entry(win, width=70, show="•")
    token_entry.pack(padx=15)

    ttk.Label(win, text="Channel ID").pack(anchor="w", padx=15, pady=(8, 0))
    channel_entry = ttk.Entry(win, width=70)
    channel_entry.pack(padx=15)

    if config.TOKEN:
        token_entry.insert(0, config.TOKEN)
    if config.CHANNEL_ID:
        channel_entry.insert(0, str(config.CHANNEL_ID))

    def save():
        token = token_entry.get().strip()
        channel_id = channel_entry.get().strip()
        if not token or not channel_id.isdigit():
            messagebox.showerror("Missing info", "Need the bot token and the channel ID (just the number).", parent=win)
            return
        config.save_settings(token, int(channel_id))
        saved["ok"] = True
        win.destroy()

    ttk.Button(win, text="Save", command=save).pack(pady=15)
    token_entry.focus()
    win.grab_set()
    parent.wait_window(win)
    return saved["ok"]


def restart_app():
    # easiest way to log in again with the new token is just starting fresh
    env = dict(os.environ, PYINSTALLER_RESET_ENVIRONMENT="1")
    if getattr(sys, "frozen", False):
        subprocess.Popen([sys.executable] + sys.argv[1:], env=env)
    else:
        subprocess.Popen([sys.executable] + sys.argv, env=env)
    os._exit(0)


def open_folder(path):
    if sys.platform == "win32":
        os.startfile(path)
    else:
        webbrowser.open(path)


def set_icon(window):
    try:
        window.iconbitmap(config.ICON_PATH)
    except tk.TclError:
        pass  # .ico only works on windows, not a big deal


def build_window(window):
    global root, scrollable_frame, summary_label, status_label
    root = window
    root.title("DisCloud File Manager")
    root.geometry("650x500")
    set_icon(root)

    top_bar = ttk.Frame(root)
    top_bar.pack(pady=10)
    ttk.Button(top_bar, text="Upload File", command=handle_upload).pack(side="left", padx=5)
    ttk.Button(top_bar, text="Invite bot", command=invite_bot).pack(side="left", padx=5)
    ttk.Button(top_bar, text="Settings", command=change_settings).pack(side="left", padx=5)

    summary_label = ttk.Label(root, text="Loading...", font=("Segoe UI", 10, "bold"))
    summary_label.pack()

    # packed before the list so the list can't push it off the bottom
    status_label = ttk.Label(root, text="", relief="sunken", anchor="w")
    status_label.pack(side="bottom", fill="x")

    container = ttk.Frame(root)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    refresh_gui()
    update_status()


if __name__ == "__main__":
    import main  # main.py does the setup + starts the bot
    main.main()
