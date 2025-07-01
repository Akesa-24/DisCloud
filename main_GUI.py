import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import glob
import time
from encoding.encoding_to_base64 import split_file_to_txt, append_to_json_file
from decoding.reconstruct_file import reconstruct_file

QUEUE_PATH = "shared/task_queue.json"
READ_FOLDER = "read"
CHANNEL_ID = 1388302333015888032
FILE_LIST_PATH = "shared/file_list.json"

def handle_download(filename):
    messagebox.showinfo("Download", f"Downloading: {filename}")
    file_prefix = filename.split(".")[0]
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

def handle_delete(filename):
    result = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{filename}'?")
    if result:
        try:
            with open(FILE_LIST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            data = [item for item in data if item.get("filename") != filename] # very proud of this one

            with open(FILE_LIST_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            refresh_gui()
            messagebox.showinfo("Deleted", f"{filename} removed from file list.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete: {e}")

    file_prefix = filename.split(".")[0]
    task = {
        "task": "delete",
        "channel_id": CHANNEL_ID,
        "text_pattern": f"{file_prefix}"
    }
    append_to_json_file(QUEUE_PATH, task)
    messagebox.showinfo("Waiting", f"Delete request sent. '...")
    messagebox.showinfo("Success", f"File '{file_prefix}' deleted successfully.")



def handle_upload():
    import tkinter.filedialog as fd
    file_path = fd.askopenfilename(title="Select file to upload")
    if not file_path:
        return

    try:
        from encoding.encoding_to_base64 import split_file_to_txt, append_to_json_file
        split_file_to_txt(file_path)

        file_entry = {
            "filename": os.path.basename(file_path),
            "original_size": os.path.getsize(file_path),
        }

        if not os.path.exists(FILE_LIST_PATH):
            with open(FILE_LIST_PATH, "w", encoding="utf-8") as f:
                json.dump([file_entry], f, indent=2)
        else:
            with open(FILE_LIST_PATH, "r+", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.append(file_entry)
                f.seek(0)
                f.truncate()
                json.dump(data, f, indent=2)

        refresh_gui()
        messagebox.showinfo("Uploaded", f"{file_entry['filename']} uploaded and added to list.")
    except Exception as e:
        messagebox.showerror("Upload Error", f"An error occurred:\n{e}")

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
    if not os.path.exists(FILE_LIST_PATH):
        return []
    with open(FILE_LIST_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def refresh_gui():
    """
    lowkey no idea whats happening here, i dont like gui, tutorials help tho

    """
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    file_list = load_file_list()
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


def wait_for_read_files(file_prefix, timeout=60):
    pattern = os.path.join(READ_FOLDER, f"{file_prefix}_part_*.txt")
    waited = 0

    print(f" Waiting for '{file_prefix}_part_001.txt' to appear in 'read/'...")
    # Was running into problem where i would try reconstruct the file before all the parts arrived
    # Figured it was easier to make it so 001 would always arrive last and then wait for that (probably stupid)


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









def main():
    global scrollable_frame
    root = tk.Tk()
    root.title("DisCloud File Manager")
    root.geometry("650x500")

    upload_btn = ttk.Button(root, text="Upload File", command=handle_upload)
    upload_btn.pack(pady=10)

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
    root.mainloop()

if __name__ == "__main__":
    main()
