"""
Rate limiting tests
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException


class TestRateLimiter:
    """Tests for rate limiting functionality"""
    
    def test_rate_limiter_allows_under_limit(self):
        """Test that requests under limit are allowed"""
        from app.core.rate_limit import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        request = MagicMock()
        request.client.host = "192.168.1.1"
        
        import asyncio
        
        for _ in range(5):
            asyncio.run(limiter(request))
    
    def test_rate_limiter_blocks_over_limit(self):
        """Test that requests over limit are blocked"""
        from app.core.rate_limit import RateLimiter
        
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        request = MagicMock()
        request.client.host = "192.168.1.2"
        
        import asyncio
        
        for _ in range(3):
            asyncio.run(limiter(request))
        
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(limiter(request))
        
        assert exc_info.value.status_code == 429
    
    def test_rate_limiter_tracks_different_ips(self):
        """Test that rate limiter tracks different IPs separately"""
        from app.core.rate_limit import RateLimiter
        
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        import asyncio
        
        request1 = MagicMock()
        request1.client.host = "192.168.1.3"
        
        request2 = MagicMock()
        request2.client.host = "192.168.1.4"
        
        asyncio.run(limiter(request1))
        asyncio.run(limiter(request1))
        
        asyncio.run(limiter(request2))
        asyncio.run(limiter(request2))
        
        with pytest.raises(HTTPException):
            asyncio.run(limiter(request1))
        
        with pytest.raises(HTTPException):
            asyncio.run(limiter(request2))
    
    def test_rate_limiter_has_lock(self):
        """Test that rate limiter has thread lock"""
        from app.core.rate_limit import RateLimiter
        
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert hasattr(limiter, '_lock')
        import threading
        assert isinstance(limiter._lock, type(threading.Lock()))
