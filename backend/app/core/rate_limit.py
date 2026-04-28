"""
Rate limiting middleware
"""
from fastapi import HTTPException, Request, status
from collections import defaultdict
import time
import threading


class RateLimiter:
    """
    Simple rate limiter based on client IP (thread-safe)
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self._lock = threading.Lock()
    
    async def __call__(self, request: Request):
        client_ip = request.client.host
        current_time = time.time()
        
        with self._lock:
            self.requests[client_ip] = [
                timestamp for timestamp in self.requests[client_ip]
                if current_time - timestamp < self.window_seconds
            ]
            
            if len(self.requests[client_ip]) >= self.max_requests:
                retry_after = self.window_seconds - (current_time - self.requests[client_ip][0])
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Try again in {int(retry_after)} seconds.",
                    headers={"Retry-After": str(int(retry_after))}
                )
            
            self.requests[client_ip].append(current_time)


# Rate limiter instances
login_limiter = RateLimiter(max_requests=10, window_seconds=60)  # Login: 10 per minute
api_limiter = RateLimiter(max_requests=100, window_seconds=60)   # General API: 100 per minute
