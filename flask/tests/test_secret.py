from datetime import timedelta

from app.utils.secret import TokenManager, Token


def test_token_manager():
    data = "test_data"
    token = TokenManager.generate_token(data)
    assert isinstance(token, Token), "Token should be a Token object"
    
    assert TokenManager.validate_token(token.value) is True, "Token should be valid"
    
    assert TokenManager.get_data_from_token(token.value) == data, "Data retrieved from token should match original data"
    assert TokenManager.get_data_from_token("invalid_token") is None, "Invalid token should return None"
    
    
def test_token_expiry():
    data = "expiring_data"
    token = TokenManager.generate_token(data, lifetime=timedelta(seconds=1))
    
    assert TokenManager.validate_token(token.value) is True, "Token should be valid immediately after creation"
    
    import time
    time.sleep(2)  # Wait for token to expire
    
    assert TokenManager.validate_token(token.value) is False, "Token should be invalid after expiry"
    