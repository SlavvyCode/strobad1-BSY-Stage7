
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import os

# needs to be 16, 24, or 32 bytes
KEY = b"1234567890123456"

def encrypt_payload_AES_then_b64(plain_text):
    # Add padding so that AES block size is met
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plain_text.encode()) + padder.finalize()

    # AES-CBC encryption
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    # return as B64 string
    return base64.b64encode(iv + ciphertext).decode()

def decrypt_payload(b64_data):
    raw = base64.b64decode(b64_data)
    iv, ciphertext = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded_data) + unpadder.finalize()).decode()

