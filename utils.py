
import base64
import random
import string

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import os

# needs to be 16, 24, or 32 bytes
KEY = b"1234567890123456"

def encrypt_payload_AES_then_b64(plain_text):
    if len(plain_text) > 9999:
        raise ValueError("Message too long for 4-digit framing. Use chunking.") #

    # Prefix the final message with info about the length (4-digit - 0005 for 'hello')
    msg_len = f"{len(plain_text):04d}"

    # add junk until fixed large size is met so EVERY packet looks the same length
    target_total_size = 512
    current_payload = msg_len + plain_text

    # payload is too big -> MUST get sent here already chunked
    if len(current_payload) > target_total_size:
        # For now, we raise an error to force the use of a chunking function
        raise ValueError(f"Payload ({len(current_payload)}) exceeds max size.")

    junk_needed = target_total_size - len(current_payload)
    junk = ''.join(random.choice(string.ascii_letters) for _ in range(junk_needed))
    final_plain = current_payload + junk

    # Add padding so that AES block size is met
    aes_padder = padding.PKCS7(128).padder()
    aes_padded_data = aes_padder.update(final_plain.encode()) + aes_padder.finalize()

    # AES-CBC encryption
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(aes_padded_data) + encryptor.finalize()

    # return as B64 string
    return base64.b64encode(iv + ciphertext).decode()

def decrypt_payload(b64_data):
    # Standard Decryption
    raw = base64.b64decode(b64_data)
    iv, ciphertext = raw[:16], raw[16:]
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    full_decrypted = (unpadder.update(padded_data) + unpadder.finalize()).decode()

    try:
        # Extract the length from the first 4 characters
        msg_len = int(full_decrypted[:4])
        # Return only the actual command/data
        return full_decrypted[4 : 4 + msg_len]
    except (ValueError, IndexError):
        # Fallback if the message is malformed
        print("[WARNING]: Malformed decrypted payload, returning full content.")
        return full_decrypted
