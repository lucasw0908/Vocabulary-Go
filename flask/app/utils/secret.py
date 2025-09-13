import base64
import hashlib
import logging
import os
from datetime import datetime, timezone, timedelta

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from flask_bcrypt import Bcrypt

from ..config import PASSWORD_HASHING_ALGORITHM, PASSWORD_HASHING_ROUNDS, SECRET_KEY


log = logging.getLogger(__name__)
bcrypt = Bcrypt()


def hash_password(password: str) -> str:
    """
    Hash a password using the specified algorithm and rounds.

    Parameters
    ----------
    password : str
        The password to hash.

    Returns
    -------
    str
        The hashed password.
    """
    if PASSWORD_HASHING_ALGORITHM == "bcrypt":
        return bcrypt.generate_password_hash(password, rounds=PASSWORD_HASHING_ROUNDS).decode("utf-8")
    
    elif PASSWORD_HASHING_ALGORITHM == "sha256":
        return hashlib.sha256(password.encode()).hexdigest()
    
    else:
        raise ValueError(f"Unsupported hashing algorithm: {PASSWORD_HASHING_ALGORITHM}")  
    
    
def check_password(hashed_password: str, password: str) -> bool:
    """
    Check if the provided password matches the hashed password.

    Parameters
    ----------
    hashed_password : str
        The hashed password to check against.
    password : str
        The password to verify.

    Returns
    -------
    bool
        True if the password matches, False otherwise.
    """
    if PASSWORD_HASHING_ALGORITHM == "bcrypt":
        return bcrypt.check_password_hash(hashed_password, password)
    
    elif PASSWORD_HASHING_ALGORITHM == "sha256":
        return hashed_password == hashlib.sha256(password.encode()).hexdigest()
    
    else:
        raise ValueError(f"Unsupported hashing algorithm: {PASSWORD_HASHING_ALGORITHM}")  
    
    
class Token:
    
    def __init__(self, value: bytes, lifetime: timedelta):
        self.value = value
        self.lifetime = lifetime
        self.created_at = datetime.now(timezone.utc)
    

class TokenManager:
    """
    A class to manage token generation and validation.
    """
    default_lifetime = timedelta(minutes=10)
    available_tokens: list[Token] = []
    
    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PASSWORD_HASHING_ROUNDS,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    @staticmethod
    def generate_token(message: str, lifetime: timedelta = None) -> Token:
        """
        Generate a new token and store it in the available tokens list.
        """
        salt = os.urandom(16)
        key = TokenManager.derive_key(SECRET_KEY, salt)
        f = Fernet(key)

        token = f.encrypt(message.encode())

        combined = base64.urlsafe_b64encode(salt + token)
        token = Token(combined, lifetime or TokenManager.default_lifetime)
        TokenManager.available_tokens.append(token)
        return token
    

    @staticmethod
    def get_data_from_token(token_value: bytes) -> str | None:
        """
        Decode the data from a base64-encoded token.
        """
        try:
            decoded = base64.urlsafe_b64decode(token_value)
            salt, real_token = decoded[:16], decoded[16:]

            key = TokenManager.derive_key(SECRET_KEY, salt)
            f = Fernet(key)

            return f.decrypt(real_token).decode()
        except Exception as e:
            log.error(f"Failed to decrypt token: {e}")
            return None
    
    
    @staticmethod
    def validate_token(token_value: bytes) -> bool:
        """
        Validate a token and remove it from the available tokens list if valid.

        Parameters
        ----------
        token_value : bytes
            The token to validate.

        Returns
        -------
        bool
            True if the token is valid, False otherwise.
        """
        current_time = datetime.now(timezone.utc)
        
        # Remove expired tokens
        TokenManager.available_tokens = [
            token for token in TokenManager.available_tokens 
            if current_time - token.created_at < token.lifetime
        ]
        
        for token in TokenManager.available_tokens:
            if token.value == token_value:
                return True
        
        log.debug(f"Token {token_value} is invalid or expired.")
        return False
    
    
    @staticmethod
    def clear_tokens() -> None:
        """
        Clear all available tokens.
        """
        TokenManager.available_tokens.clear()
        log.info("Cleared all available tokens.")