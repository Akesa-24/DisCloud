import base64
import glob
import re
import os
import sys
import io

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from encryption.decryption import decrypt

def reconstruct_file(txt_pattern="part_*.txt"):
    parts = sorted(glob.glob(txt_pattern))
    if not parts:
        print("No parts found.")
        return

    print(f"Found {len(parts)} parts.")
    b64_combined = ""
    filename = None

    for part in parts:
        with open(part, "r") as f:
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

    raw_data = base64.b64decode(b64_combined)

    with open(f"reconstructed_unencrypted_{filename}", "wb") as out:
        out.write(raw_data)

    print(f"Reconstructed file: reconstructed_unencrypted_{filename}")




reconstruct_file()