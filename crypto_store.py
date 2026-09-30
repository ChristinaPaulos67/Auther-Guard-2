"""AES-256-CTR encrypted .AG archive storage."""
import os
import csv
import io
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def encrypt_data(data_bytes: bytes, password: str) -> bytes:
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
    key = kdf.derive(password.encode())
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    enc = cipher.encryptor()
    return salt + nonce + enc.update(data_bytes) + enc.finalize()


def decrypt_data(encrypted_bytes: bytes, password: str) -> bytes:
    salt, nonce, ct = encrypted_bytes[:16], encrypted_bytes[16:32], encrypted_bytes[32:]
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100_000)
    key = kdf.derive(password.encode())
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    dec = cipher.decryptor()
    return dec.update(ct) + dec.finalize()


def entries_to_csv_bytes(entries: list) -> bytes:
    if not entries:
        raise ValueError("No data to save.")
    fieldnames = list(entries[0].keys())
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames)
    w.writeheader()
    for e in entries:
        row = {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in e.items()}
        w.writerow(row)
    return buf.getvalue().encode("utf-8")


def csv_bytes_to_entries(data: bytes) -> list:
    text = data.decode("utf-8")
    new_entries = []
    for row in csv.DictReader(io.StringIO(text)):
        entry = {}
        for k, v in row.items():
            if k == "timestamp":
                try:
                    entry[k] = datetime.fromisoformat(v)
                except Exception:
                    entry[k] = v
                continue
            try:
                entry[k] = float(v) if "." in str(v) else int(v)
            except (ValueError, TypeError):
                entry[k] = v
        new_entries.append(entry)
    return new_entries
