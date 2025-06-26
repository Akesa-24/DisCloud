from cryptography.fernet import Fernet


def decrypt(encrypted):
    # Load the key
    with open("secret.key", "rb") as key_file:
        key = key_file.read()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted)

    print("Decryption complete.")

    return decrypted
