import base64
import os
import math

CHUNK_SIZE_MB = 10
CHUNK_SIZE = CHUNK_SIZE_MB * 1024 * 1000 # in bytes, 1000 bc discord is being bitchy and not accurate

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
        part_filename = f"{output_prefix}_{i+1:03}.txt"
        with open(part_filename, "w") as out:
            # Add header with part info
            out.write(f"--{base_name}--PART {i+1}/{num_parts}--\n")
            out.write(chunk)

    print("Done.")

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python split_file_to_txt.py your_file.ext")
    else:
        split_file_to_txt(sys.argv[1])
