import os
import time
import json
import glob

from encoding.encoding_to_base64 import split_file_to_txt, append_to_json_file
from decoding.reconstruct_file import reconstruct_file

QUEUE_PATH = "shared/task_queue.json"
READ_FOLDER = "read"
CHANNEL_ID = 1388302333015888032


def upload_file():
    path = input("Enter the full path of the file to upload: ").strip()
    if not os.path.isfile(path):
        print("File not found.")
        return
    split_file_to_txt(path)
    print("✅ File uploaded and task_queue updated.")


def wait_for_read_files(file_prefix, timeout=60):
    pattern = os.path.join(READ_FOLDER, f"{file_prefix}_part_*.txt")
    waited = 0

    print(f"⏳ Waiting for '{file_prefix}_part_001.txt' to appear in 'read/'...")

    while waited < timeout:
        matches = glob.glob(pattern)
        has_first_part = any(name.endswith("_part_001.txt") for name in matches)

        if matches and has_first_part:
            print(f"\n✅ Received all parts (at least up to part 001): {len(matches)} files.")
            return True

        print(".", end="", flush=True)
        time.sleep(1)
        waited += 1

    print("\n Timeout: _part_001.txt never appeared.")
    return False


def download_file():
    file_prefix = input("Enter the base name used during encoding (e.g., 'myfile_123'): ").strip()
    task = {
        "task": "read",
        "channel_id": CHANNEL_ID,
        "text_pattern": f"{file_prefix}_part_*.txt"
    }
    append_to_json_file(QUEUE_PATH, task)
    print("⏳ Read request sent to task queue.")

    # Wait for the files to appear in the read folder
    if wait_for_read_files(file_prefix):
        time.sleep(1)
        reconstruct_file(file_name=file_prefix)
        print("✅ File successfully reconstructed.")
    else:
        print("Read failed: files did not arrive in time.")


def main():
    while True:
        print("\n=== DisCloud File Manager ===")
        print("1. Upload file to Discord")
        print("2. Download file from Discord")
        print("3. Exit")

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            upload_file()
        elif choice == "2":
            download_file()
        elif choice == "3":
            print("Goodbye.")
            break
        else:
            print("Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
