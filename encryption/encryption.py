from cryptography.fernet import Fernet

import os

key_path = os.path.join(os.path.dirname(__file__), "secret.key")

def encrypt(raw_data):
    # Load the encryption key
    with open(key_path , "rb") as key_file:
        key = key_file.read()

    fernet = Fernet(key)
    encrypted = fernet.encrypt(raw_data)

    print("Encryption complete.")

    return encrypted