import os
import sys
from cryptography.fernet import Fernet

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config


def make_key():
    # only ever make one, a new key means everything already uploaded can't be decrypted anymore
    if os.path.exists(config.KEY_PATH):
        return
    key = Fernet.generate_key()
    with open(config.KEY_PATH, "wb") as key_file:
        key_file.write(key)
    print(f"Key saved to {config.KEY_PATH}")


if __name__ == "__main__":
    make_key()
