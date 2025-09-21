import hashlib
import logging
from datetime import datetime, timezone, timedelta

import jwt
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
        
        
class JWTManager:
    
    @staticmethod
    def generate_jwt(payload: dict, lifetime: timedelta = None) -> str:
        """
        Generate a JWT token with the given payload and lifetime.

        Parameters
        ----------
        payload : dict
            The payload to include in the JWT.
        lifetime : timedelta, optional
            The lifetime of the token. Defaults to 1 hour.

        Returns
        -------
        str
            The generated JWT token.
        """
        exp = datetime.now(timezone.utc) + (lifetime or timedelta(hours=1))
        payload = payload.copy()  # Avoid modifying the original payload
        payload.update({"exp": exp})
        
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    
    
    @staticmethod
    def validate_jwt(token: str) -> dict | None:
        """
        Validate a JWT token and return its payload if valid.

        Parameters
        ----------
        token : str
            The JWT token to validate.

        Returns
        -------
        dict | None
            The payload if the token is valid, None otherwise.
        """
        try:
            payload: dict = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            payload.pop("exp")
            return payload
        
        except jwt.ExpiredSignatureError:
            log.warning("JWT token has expired.")
            return None
        
        except jwt.InvalidTokenError as e:
            log.error(f"Invalid JWT token: {e}")
            return None
        