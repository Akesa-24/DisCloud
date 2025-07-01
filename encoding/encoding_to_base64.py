import base64
import json
import os
import math
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from encryption.encryption import encrypt

CHUNK_SIZE_MB = 7
CHUNK_SIZE = CHUNK_SIZE_MB * 1024 * 1024  # 1000-based MB due to Discord
SAVE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "to_send"))
QUEUE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shared/task_queue.json"))



def split_file_to_txt(input_file = '', output_prefix="part"):
    if input_file == '':
        input_file = sys.argv[1]
        input_file = os.path.abspath(input_file)

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

        part_filename = f"{base_name[0:-4]}_{output_prefix}_{i+1:03}.txt"
        out_path = os.path.join(SAVE_PATH, part_filename)

        with open(out_path, "wb") as encrypted_file:
            encrypted_file.write(encrypted_data)

    new_task = {}
    new_task["task"] = "send"
    new_task["channel_id"] = 1388302333015888032
    new_task["filename"] = f"{base_name[:-4]}_part_XXX"
    new_task["path"] = SAVE_PATH
    append_to_json_file(QUEUE_PATH, new_task)

    print("Done encoding and splitting and updating .json file.")



def append_to_json_file(path, new_entry):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(path, "r+", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

        if not isinstance(data, list):
            raise ValueError("JSON file must contain a list at the top level.")

        data.append(new_entry)

        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=2)

# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python split_file_to_txt.py your_file.txt")
    else:
        split_file_to_txt(input_file="C:\\Users\\Lenovo\\Documents\\GitHub\\DisCloud\\encoding\\DSFC7201_4.mp4")