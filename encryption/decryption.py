from cryptography.fernet import Fernet

import os

key_path = os.path.join(os.path.dirname(__file__), "secret.key")

def decrypt(encrypted):
    # Load the key
    with open(key_path, "rb") as key_file:
        key = key_file.read()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)

    print("Decryption complete.")

    return decrypted
