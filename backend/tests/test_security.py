"""
Test per middleware di sicurezza
"""
import pytest
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
import time

from middleware.security import RateLimiter, APIKeyAuth


class TestRateLimiter:
    """Test rate limiter"""
    
    def test_rate_limit_allows_within_limit(self):
        """Test che permette richieste entro il limite"""
        limiter = RateLimiter(requests=5, window=60)
        
        # Mock request
        class MockRequest:
            def __init__(self):
                self.client = type('obj', (object,), {'host': '127.0.0.1'})()
                self.headers = {}
        
        request = MockRequest()
        
        # Prime 5 richieste dovrebbero passare
        for i in range(5):
            assert limiter.check_rate_limit(request) == True
    
    def test_rate_limit_blocks_over_limit(self):
        """Test che blocca richieste oltre il limite"""
        limiter = RateLimiter(requests=3, window=60)
        
        class MockRequest:
            def __init__(self):
                self.client = type('obj', (object,), {'host': '127.0.0.1'})()
                self.headers = {}
        
        request = MockRequest()
        
        # Prime 3 richieste OK
        for i in range(3):
            assert limiter.check_rate_limit(request) == True
        
        # 4a richiesta dovrebbe essere bloccata
        assert limiter.check_rate_limit(request) == False
    
    def test_rate_limit_resets_after_window(self):
        """Test che il limite si resetta dopo la finestra"""
        limiter = RateLimiter(requests=2, window=1)  # 1 secondo
        
        class MockRequest:
            def __init__(self):
                self.client = type('obj', (object,), {'host': '127.0.0.1'})()
                self.headers = {}
        
        request = MockRequest()
        
        # Prime 2 richieste OK
        assert limiter.check_rate_limit(request) == True
        assert limiter.check_rate_limit(request) == True
        
        # 3a bloccata
        assert limiter.check_rate_limit(request) == False
        
        # Aspetta reset
        time.sleep(1.1)
        
        # Dovrebbe funzionare di nuovo
        assert limiter.check_rate_limit(request) == True


class TestAPIKeyAuth:
    """Test autenticazione API key"""
    
    def test_auth_disabled_allows_all(self):
        """Test che con auth disabilitata permette tutto"""
        auth = APIKeyAuth(enabled=False)
        
        # Qualsiasi key dovrebbe passare
        assert auth.verify_api_key(None) == True
        assert auth.verify_api_key("invalid") == True
    
    def test_auth_enabled_requires_valid_key(self):
        """Test che con auth abilitata richiede key valida"""
        import os
        os.environ["API_KEYS"] = "valid-key-1,valid-key-2"
        
        auth = APIKeyAuth(enabled=True)
        
        # Key valide
        assert auth.verify_api_key("valid-key-1") == True
        assert auth.verify_api_key("valid-key-2") == True
        
        # Key invalide
        assert auth.verify_api_key("invalid-key") == False
        assert auth.verify_api_key(None) == False
        
        # Cleanup
        del os.environ["API_KEYS"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
