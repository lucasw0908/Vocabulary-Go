import time
from datetime import timedelta

from app.utils.secret import JWTManager


def test_jwt_manager():
    data = {"user_id": 123, "role": "admin"}
    token = JWTManager.generate_jwt(data)

    assert isinstance(token, str), "Token should be a string"
    
    assert JWTManager.validate_jwt(token) == data, "Data retrieved from token should match original data"
    assert JWTManager.validate_jwt("invalid_token") is None, "Invalid token should return None"
    
    
def test_jwt_expiry():
    data = {"user_id": 456, "role": "user"}
    token = JWTManager.generate_jwt(data, lifetime=timedelta(seconds=1))
    
    time.sleep(2)  # Wait for token to expire
    
    assert JWTManager.validate_jwt(token) is None, "Token should be invalid after expiry"