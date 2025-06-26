from cryptography.fernet import Fernet



def encrypt(raw_data):
    # Load the encryption key
    with open("secret.key", "rb") as key_file:
        key = key_file.read()

    fernet = Fernet(key)
    encrypted = fernet.encrypt(raw_data)

    print("Encryption complete.")

    return encrypted