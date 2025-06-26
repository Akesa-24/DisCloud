import base64
import os
import math
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from encryption.encryption import encrypt

CHUNK_SIZE_MB = 10
CHUNK_SIZE = CHUNK_SIZE_MB * 1024 * 1000  # 1000-based MB due to Discord

def split_file_to_txt(input_file, output_prefix="part"):
    with open(input_file, "rb") as f:
        raw_data = f.read()

    b64_data = base64.b64encode(raw_data).decode('ascii')
    total_length = len(b64_data)
    num_parts = math.ceil(total_length / CHUNK_SIZE)

    base_name = os.path.basename(input_file)
    print(f"Splitting '{base_name}' into {num_parts} parts of up to {CHUNK_SIZE_MB} MB")

    for i in range(num_parts):
        chunk = b64_data[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]

        header = f"--{base_name}--PART {i+1}/{num_parts}--\n"
        full_text = header + chunk

        # Encrypt
        encrypted_data = encrypt(full_text.encode('utf-8'))

        part_filename = f"{output_prefix}_{i+1:03}.txt"
        with open(part_filename, "wb") as encrypted_file:
            encrypted_file.write(encrypted_data)

    print("Done.")

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python split_file_to_txt.py your_file.ext")
    else:
        split_file_to_txt(sys.argv[1])
