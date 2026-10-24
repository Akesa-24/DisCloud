from cryptography.fernet import Fernet

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

key_path = config.KEY_PATH

def encrypt(raw_data):
    # Load the encryption key
    with open(key_path , "rb") as key_file:
        key = key_file.read()

    fernet = Fernet(key)
    encrypted = fernet.encrypt(raw_data)

    print("Encryption complete.")

    return encrypted