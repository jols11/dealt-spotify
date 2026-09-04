import base64
import hashlib
import os
import secrets

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def generate_code_verifier() -> str:
    return secrets.token_urlsafe(64)[:128]


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def generate_state() -> str:
    return secrets.token_urlsafe(24)


def _fernet() -> Fernet:
    settings = get_settings()
    digest = hashlib.sha256(settings.session_secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_token(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_token(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return value


def random_hex(n: int = 16) -> str:
    return os.urandom(n).hex()
