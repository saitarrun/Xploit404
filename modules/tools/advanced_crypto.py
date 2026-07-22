"""Advanced Crypto — Modern encryption/decryption support.

Supports AES, RSA, and other modern cryptographic algorithms.
Requires cryptography library for full functionality.
"""

import os
import json


def try_import_crypto():
    """Try to import cryptography libraries."""
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.backends import default_backend
        return True, {
            'Fernet': Fernet,
            'hashes': hashes,
            'PBKDF2': PBKDF2HMAC,
            'backend': default_backend(),
        }
    except ImportError:
        return False, None


def fernet_encrypt(text, key=None):
    """Encrypt text using Fernet (symmetric encryption)."""
    available, crypto = try_import_crypto()
    if not available:
        return "cryptography library not installed: pip install cryptography"

    try:
        if key is None:
            key = crypto['Fernet'].generate_key()
        cipher = crypto['Fernet'](key)
        encrypted = cipher.encrypt(text.encode())
        return {
            'encrypted': encrypted.decode(),
            'key': key.decode() if isinstance(key, bytes) else key,
            'note': 'Save the key to decrypt later!'
        }
    except Exception as e:
        return f"Encryption failed: {e}"


def fernet_decrypt(encrypted_text, key):
    """Decrypt text using Fernet."""
    available, crypto = try_import_crypto()
    if not available:
        return "cryptography library not installed: pip install cryptography"

    try:
        if isinstance(encrypted_text, str):
            encrypted_text = encrypted_text.encode()
        if isinstance(key, str):
            key = key.encode()
        cipher = crypto['Fernet'](key)
        decrypted = cipher.decrypt(encrypted_text)
        return decrypted.decode()
    except Exception as e:
        return f"Decryption failed: {e}"


def generate_fernet_key():
    """Generate a new Fernet encryption key."""
    available, crypto = try_import_crypto()
    if not available:
        return "cryptography library not installed: pip install cryptography"

    key = crypto['Fernet'].generate_key()
    return {
        'key': key.decode(),
        'note': 'Keep this key safe! You need it to decrypt data.'
    }


def derive_key_from_password(password, salt=None):
    """Derive an encryption key from a password."""
    available, crypto = try_import_crypto()
    if not available:
        return "cryptography library not installed: pip install cryptography"

    try:
        if salt is None:
            salt = os.urandom(16)

        kdf = crypto['PBKDF2'](
            algorithm=crypto['hashes'].SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=crypto['backend']
        )

        key = kdf.derive(password.encode())

        import base64
        fernet_key = base64.urlsafe_b64encode(key)

        return {
            'key': fernet_key.decode(),
            'salt': base64.b64encode(salt).decode(),
            'note': 'Store salt with encrypted data to decrypt later'
        }
    except Exception as e:
        return f"Key derivation failed: {e}"


def try_common_passwords(encrypted_text, common_passwords_file=None):
    """Try to decrypt with common passwords."""
    available, crypto = try_import_crypto()
    if not available:
        return "cryptography library not installed"

    common_passwords = [
        'password', '123456', 'password123', '12345678', 'qwerty',
        'abc123', 'monkey', '1234567', 'letmein', 'trustno1',
        'dragon', 'baseball', 'iloveyou', 'master', 'sunshine',
        'ashley', 'bailey', 'passw0rd', 'shadow', '123123',
        '654321', 'superman', 'qazwsx', 'michael', 'football',
        'admin', 'root', 'toor', 'changeme', 'default',
    ]

    if common_passwords_file and os.path.isfile(common_passwords_file):
        try:
            with open(common_passwords_file, 'r') as f:
                common_passwords.extend([line.strip() for line in f])
        except Exception:
            pass

    results = {}
    for password in common_passwords[:100]:
        try:
            key_data = derive_key_from_password(password)
            if isinstance(key_data, dict):
                key = key_data['key']
                decrypted = fernet_decrypt(encrypted_text, key)
                if not decrypted.startswith('Decryption failed'):
                    results[password] = decrypted
        except Exception:
            continue

    return results if results else {'status': 'No successful decryptions with common passwords'}


def aes_info():
    """Return information about AES encryption."""
    return {
        'algorithm': 'Advanced Encryption Standard (AES)',
        'key_sizes': [128, 192, 256],
        'modes': ['CBC', 'ECB', 'CTR', 'GCM'],
        'status': 'Use Fernet for simpler symmetric encryption, or pycryptodome for AES',
        'install': 'pip install pycryptodome'
    }


def ready():
    """Check if advanced crypto is ready."""
    available, _ = try_import_crypto()
    if available:
        return True, 'ready (cryptography library installed)'
    return False, 'cryptography library not installed (pip install cryptography)'


def is_installed():
    """Check if cryptography is installed."""
    available, _ = try_import_crypto()
    return available
