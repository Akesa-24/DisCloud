import glob
import os
import re
import io
import base64
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from encryption.decryption import decrypt

READ_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "read"))
DOWNLOADS_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "downloads"))

def reconstruct_file(file_name=None, txt_pattern=None):
    if file_name and not txt_pattern:
        txt_pattern = f"{file_name}_part_*.txt"
    elif not txt_pattern:
        txt_pattern = "part_*.txt"

    print(txt_pattern)
    search_path = os.path.join(READ_FOLDER, txt_pattern)
    print(f"Searching for: {search_path}")
    print("Files in read/:")
    for file in os.listdir(READ_FOLDER):
        print(file)
    parts = sorted(glob.glob(search_path))

    if not parts:
        print("No parts found in 'read/' folder.")
        return

    print(f"Found {len(parts)} parts.")
    b64_combined = ""
    filename = None

    for part in parts:
        with open(part, "r", encoding="utf-8") as f:
            encrypted = f.read()
            decrypted = decrypt(encrypted)
            f_dec = io.StringIO(decrypted.decode("utf-8"))
            header = f_dec.readline().strip()
            match = re.match(r"--(.+)--PART (\d+)/(\d+)--", header)
            if not match:
                raise ValueError(f"Header not found or invalid in {part}")
            if filename is None:
                filename = match.group(1)
            b64_chunk = f_dec.read()
            b64_combined += b64_chunk
        os.remove(part)
        print(f"Deleted part file: {part}")

    raw_data = base64.b64decode(b64_combined)

    output_path = os.path.join(DOWNLOADS_FOLDER, f"{filename}")
    with open(output_path, "wb") as out:
        out.write(raw_data)

    print(f"Reconstructed file: {output_path}")
