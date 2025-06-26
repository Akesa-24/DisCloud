from cryptography.fernet import Fernet

key = Fernet.generate_key() # generates an encryption key, used only once
with open("secret.key", "wb") as key_file:
    key_file.write(key)
print("Key saved to secret.key")