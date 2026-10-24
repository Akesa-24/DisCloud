import threading
import tkinter as tk

import config
import main_GUI
from bot_setup import discord_worker
from encryption.key_gen import make_key


def main():
    root = tk.Tk()
    root.withdraw()  # keep the main window hidden until setup is done

    # first launch -> ask for the bot token and channel
    if not config.TOKEN or not config.CHANNEL_ID:
        if not main_GUI.ask_for_settings(root):
            return  # closed the setup window

    make_key()  # only does something on the very first run

    # bot runs in the background, gui still talks to it through the task queue like before
    threading.Thread(target=discord_worker.run_bot, args=(config.TOKEN,), daemon=True).start()

    main_GUI.build_window(root)
    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
