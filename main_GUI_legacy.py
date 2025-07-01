import os
import time
import json
import glob
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

from encoding.encoding_to_base64 import split_file_to_txt, append_to_json_file
from decoding.reconstruct_file import reconstruct_file

QUEUE_PATH = "shared/task_queue.json"
READ_FOLDER = "read"
CHANNEL_ID = 1388302333015888032


def wait_for_read_files(file_prefix, timeout=60):
    pattern = os.path.join(READ_FOLDER, f"{file_prefix}_part_*.txt")
    waited = 0

    print(f"⏳ Waiting for '{file_prefix}_part_001.txt' to appear in 'read/'...")

    while waited < timeout:
        matches = glob.glob(pattern)
        has_first_part = any(name.endswith("_part_001.txt") for name in matches)

        if matches and has_first_part:
            print(f"\n Received all parts (at least up to part 001): {len(matches)} files.")
            return True

        print(".", end="", flush=True)
        time.sleep(1)
        waited += 1

    print("\n Timeout: _part_001.txt never appeared.")
    return False


def upload_file():
    path = filedialog.askopenfilename(title="Select a file to upload")
    if not path or not os.path.isfile(path):
        messagebox.showerror("Error", "Invalid file selected.")
        return

    split_file_to_txt(path)
    messagebox.showinfo("Upload Complete", "File uploaded and task queue updated.")


def download_file():
    file_prefix = simpledialog.askstring("Download", "Enter the base name used during encoding:")
    if not file_prefix:
        return

    task = {
        "task": "read",
        "channel_id": CHANNEL_ID,
        "text_pattern": f"{file_prefix}_part_*.txt"
    }
    append_to_json_file(QUEUE_PATH, task)
    messagebox.showinfo("Waiting", f"Read request sent. Waiting for '{file_prefix}_part_001.txt'...")

    if wait_for_read_files(file_prefix):
        time.sleep(1)
        reconstruct_file(file_name=file_prefix)
        messagebox.showinfo("Success", f"File '{file_prefix}' downloaded successfully.")
    else:
        messagebox.showerror("Timeout", f"Failed to download '{file_prefix}' in time.")

def delete_file():
    file_prefix = simpledialog.askstring("Delete", "Enter the base name used during encoding:")
    if not file_prefix:
        return
    task = {
        "task": "delete",
        "channel_id": CHANNEL_ID,
        "text_pattern": f"{file_prefix}"
    }
    append_to_json_file(QUEUE_PATH, task)
    messagebox.showinfo("Waiting", f"Delete request sent. '...")
    messagebox.showinfo("Success", f"File '{file_prefix}' deleted successfully.")


def main():
    root = tk.Tk()
    root.title("DisCloud File Manager")
    root.geometry("800x440")
    root.resizable(False, False)

    tk.Label(root, text="DisCloud", font=("Segoe UI", 16)).pack(pady=20)

    tk.Button(root, text=" Upload File", font=("Segoe UI", 12), width=25, command=upload_file).pack(pady=10)
    tk.Button(root, text=" Download File", font=("Segoe UI", 12), width=25, command=download_file).pack(pady=10)
    tk.Button(root, text=" Delete File", font=("Segoe UI", 12), width=25, command=delete_file).pack(pady=10)
    tk.Button(root, text=" Exit", font=("Segoe UI", 10), width=15, command=root.destroy).pack(pady=15)

    root.mainloop()


if __name__ == "__main__":
    main()
