"""Cipher Toolkit — Automatic encryption/decryption with cipher detection.

Comprehensive toolkit for cipher identification, encoding, and decoding.
Supports multiple cipher types with automatic detection capabilities.
"""

import os
import base64
import hashlib
import re
from collections import Counter


# Cipher detection functions
def detect_base64(text):
    """Check if text is Base64 encoded."""
    try:
        if isinstance(text, str):
            text_bytes = bytes(text, 'utf-8')
        else:
            text_bytes = text
        return base64.b64encode(base64.b64decode(text_bytes)) == text_bytes
    except Exception:
        return False


def detect_hex(text):
    """Check if text is hexadecimal."""
    return bool(re.match(r'^[0-9a-fA-F]+$', text))


def detect_caesar(text):
    """Check if text might be Caesar cipher."""
    text = text.lower()
    text = ''.join(c for c in text if c.isalpha())
    if len(text) < 10:
        return False
    return len(text) > len(''.join(c for c in text if c.isalpha())) * 0.7


def detect_rot13(text):
    """Check if text is ROT13 encoded."""
    decoded = rot13(text)
    vowels = sum(1 for c in decoded.lower() if c in 'aeiou')
    return vowels > len(decoded) * 0.2


def detect_substitution(text):
    """Check if text might be a substitution cipher."""
    text = text.lower()
    text = ''.join(c for c in text if c.isalpha())
    if len(text) < 20:
        return False
    unique_chars = len(set(text))
    return 15 < unique_chars <= 26


# Encoding/Decoding functions
def base64_encode(text):
    """Encode text to Base64."""
    return base64.b64encode(text.encode()).decode()


def base64_decode(text):
    """Decode Base64 text."""
    try:
        return base64.b64decode(text.encode()).decode()
    except Exception as e:
        return f"Decoding failed: {e}"


def hex_encode(text):
    """Encode text to hexadecimal."""
    return text.encode().hex()


def hex_decode(text):
    """Decode hexadecimal text."""
    try:
        return bytes.fromhex(text).decode()
    except Exception as e:
        return f"Decoding failed: {e}"


def rot13(text):
    """ROT13 cipher (rotate by 13)."""
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr((ord(char) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= char <= 'Z':
            result.append(chr((ord(char) - ord('A') + 13) % 26 + ord('A')))
        else:
            result.append(char)
    return ''.join(result)


def caesar_encrypt(text, shift=3):
    """Caesar cipher encryption."""
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
        elif 'A' <= char <= 'Z':
            result.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
        else:
            result.append(char)
    return ''.join(result)


def caesar_decrypt(text, shift=3):
    """Caesar cipher decryption (try all shifts)."""
    results = {}
    for s in range(26):
        decrypted = caesar_encrypt(text, s)
        results[f"Shift {s}"] = decrypted
    return results


def vigenere_encrypt(text, key):
    """Vigenère cipher encryption."""
    result = []
    key_index = 0
    key = key.upper()
    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('A')
            if char.isupper():
                result.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
            else:
                result.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
            key_index += 1
        else:
            result.append(char)
    return ''.join(result)


def vigenere_decrypt(text, key):
    """Vigenère cipher decryption."""
    result = []
    key_index = 0
    key = key.upper()
    for char in text:
        if char.isalpha():
            shift = ord(key[key_index % len(key)]) - ord('A')
            if char.isupper():
                result.append(chr((ord(char) - ord('A') - shift) % 26 + ord('A')))
            else:
                result.append(chr((ord(char) - ord('a') - shift) % 26 + ord('a')))
            key_index += 1
        else:
            result.append(char)
    return ''.join(result)


def atbash(text):
    """Atbash cipher (reverse alphabet: A↔Z, B↔Y, etc)."""
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr(ord('z') - (ord(char) - ord('a'))))
        elif 'A' <= char <= 'Z':
            result.append(chr(ord('Z') - (ord(char) - ord('A'))))
        else:
            result.append(char)
    return ''.join(result)


def url_encode(text):
    """URL encoding."""
    import urllib.parse
    return urllib.parse.quote(text)


def url_decode(text):
    """URL decoding."""
    import urllib.parse
    return urllib.parse.unquote(text)


def md5_hash(text):
    """Generate MD5 hash."""
    return hashlib.md5(text.encode()).hexdigest()


def sha1_hash(text):
    """Generate SHA1 hash."""
    return hashlib.sha1(text.encode()).hexdigest()


def sha256_hash(text):
    """Generate SHA256 hash."""
    return hashlib.sha256(text.encode()).hexdigest()


# Auto-detection and analysis
def analyze_cipher(text):
    """Analyze text and suggest cipher type."""
    analysis = {
        'Base64': detect_base64(text),
        'Hexadecimal': detect_hex(text),
        'Caesar Cipher': detect_caesar(text),
        'ROT13': detect_rot13(text),
        'Substitution': detect_substitution(text),
    }

    suggestions = [k for k, v in analysis.items() if v]
    return analysis, suggestions


def auto_decrypt(text):
    """Try to automatically decrypt text."""
    results = {}

    # Try Base64
    if detect_base64(text):
        try:
            results['Base64 Decoded'] = base64_decode(text)
        except Exception:
            pass

    # Try Hexadecimal
    if detect_hex(text):
        try:
            results['Hex Decoded'] = hex_decode(text)
        except Exception:
            pass

    # Try ROT13
    results['ROT13'] = rot13(text)

    # Try Caesar (all shifts)
    caesar_results = caesar_decrypt(text)
    results.update(caesar_results)

    # Try Atbash
    results['Atbash'] = atbash(text)

    # Try URL decode
    try:
        results['URL Decoded'] = url_decode(text)
    except Exception:
        pass

    return results


def ready():
    """Cipher toolkit is always ready (built-in)."""
    return True, 'built-in (Python crypto)'


def is_installed():
    """Cipher toolkit is always available."""
    return True
