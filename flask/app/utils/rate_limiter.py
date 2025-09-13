import logging
from collections import defaultdict, deque
from datetime import datetime
from typing import Deque, Literal, Optional

from flask import request, Response

from ..config import RATE_LIMITING, DATETIME_FORMAT


log = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter to prevent DDoS and spam attacks"""
    
    def __init__(self, requests_per_minute: Optional[int] = None, requests_per_hour: Optional[int] = None,
                 requests_per_day: Optional[int] = None, ban_duration_minutes: Optional[int] = None):
        """Initialize the rate limiter with configuration from settings or parameters."""
        
        self.enabled: bool = RATE_LIMITING["enabled"]
        self.requests_per_minute: int = requests_per_minute or RATE_LIMITING["requests_per_minute"]
        self.requests_per_hour: int = requests_per_hour or RATE_LIMITING["requests_per_hour"]
        self.requests_per_day: int = requests_per_day or RATE_LIMITING["requests_per_day"]
        self.ban_duration_minutes: int = ban_duration_minutes or RATE_LIMITING["ban_duration_minutes"]
        self.whitelist_ips = set(RATE_LIMITING["whitelist_ips"])
        self.banned_ips: dict[str, float] = {}
        
        # Storage for IP requests tracking
        self.ip_requests: dict[str, dict[Literal["minute", "hour", "day"], Deque[float]]] = defaultdict(
            lambda: {
                "minute": deque(),
                "hour": deque(),
                "day": deque()
            }
        )
        
        log.info(f"Rate limiter initialized. Enabled: {self.enabled}")
        if self.enabled:
            log.info(f"Rate limits: {self.requests_per_minute}/min, "
                    f"{self.requests_per_hour}/hour, "
                    f"{self.requests_per_day}/day")
            
    
    def _get_client_ip(self) -> str:
        """Get the real client IP address"""
        # Check for forwarded headers (for proxy/load balancer setups)
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
        
    
    def _cleanup_old_requests(self, ip: str, current_time: float):
        """Remove old requests outside the time windows"""
        # Clean minute requests (older than 1 minute)
        while (self.ip_requests[ip]["minute"] and 
               current_time - self.ip_requests[ip]["minute"][0] > 60):
            self.ip_requests[ip]["minute"].popleft()
        
        # Clean hour requests (older than 1 hour)
        while (self.ip_requests[ip]["hour"] and 
               current_time - self.ip_requests[ip]["hour"][0] > 3600):
            self.ip_requests[ip]["hour"].popleft()
        
        # Clean day requests (older than 1 day)
        while (self.ip_requests[ip]["day"] and 
               current_time - self.ip_requests[ip]["day"][0] > 86400):
            self.ip_requests[ip]["day"].popleft()
    
    
    def _check_rate_limits(self, ip: str, current_time: float) -> tuple[bool, str]:
        """Check if IP has exceeded rate limits"""
        # Check if IP is banned
        if ip in self.banned_ips:
            if current_time < self.banned_ips[ip]:
                ban_end = datetime.fromtimestamp(self.banned_ips[ip])
                return False, f"IP banned until {ban_end.strftime(DATETIME_FORMAT)}"
            else:
                # Ban expired, remove from banned list
                del self.banned_ips[ip]
        
        # Clean up old requests
        self._cleanup_old_requests(ip, current_time)
        
        # Check minute limit
        if len(self.ip_requests[ip]["minute"]) >= self.requests_per_minute:
            self._ban_ip(ip, current_time)
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        # Check hour limit
        if len(self.ip_requests[ip]["hour"]) >= self.requests_per_hour:
            self._ban_ip(ip, current_time)
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        # Check day limit
        if len(self.ip_requests[ip]["day"]) >= self.requests_per_day:
            self._ban_ip(ip, current_time)
            return False, f"Rate limit exceeded: {self.requests_per_day} requests per day"
        
        return True, "OK"
    
    
    def _ban_ip(self, ip: str, current_time: float):
        """Ban an IP for the configured duration"""
        ban_duration = self.ban_duration_minutes * 60  # Convert to seconds
        self.banned_ips[ip] = current_time + ban_duration
        
        ban_end = datetime.fromtimestamp(self.banned_ips[ip])
        log.warning(f"IP {ip} banned until {ban_end.strftime(DATETIME_FORMAT)} "
                   f"due to rate limit violation")
        
    
    def _record_request(self, ip: str, current_time: float):
        """Record a request for the IP"""
        self.ip_requests[ip]["minute"].append(current_time)
        self.ip_requests[ip]["hour"].append(current_time)
        self.ip_requests[ip]["day"].append(current_time)
        
    
    def check_request(self) -> tuple[bool, str]:
        """Check if the current request should be allowed"""
        if not self.enabled:
            return True, "Rate limiting disabled"
        
        ip = self._get_client_ip()
        current_time = datetime.now().timestamp()
        
        # Check whitelist
        if ip in self.whitelist_ips:
            return True, "IP whitelisted"
        
        # Check rate limits
        allowed, message = self._check_rate_limits(ip, current_time)
        
        if allowed:
            # Record the request
            self._record_request(ip, current_time)
        
        return allowed, message
    
    
    def get_ip_stats(self, ip: str = None) -> dict:
        """Get statistics for an IP (for admin/debugging)"""
        if ip is None:
            ip = self._get_client_ip()
        
        current_time = datetime.now().timestamp()
        self._cleanup_old_requests(ip, current_time)
        
        stats = {
            "ip": ip,
            "requests_minute": len(self.ip_requests[ip]["minute"]),
            "requests_hour": len(self.ip_requests[ip]["hour"]),
            "requests_day": len(self.ip_requests[ip]["day"]),
            "is_banned": ip in self.banned_ips,
            "whitelisted": ip in self.whitelist_ips
        }
        
        if ip in self.banned_ips:
            ban_end = datetime.fromtimestamp(self.banned_ips[ip])
            stats["ban_until"] = ban_end.strftime(DATETIME_FORMAT)
        
        return stats


rate_limiter = RateLimiter()


def rate_limit_middleware(rate_limiter: RateLimiter=rate_limiter) -> Optional[Response]:
    """Flask middleware for rate limiting"""
    if not rate_limiter.enabled:
        return None
    
    allowed, message = rate_limiter.check_request()
    
    if not allowed:
        log.warning(f"Rate limit violation from {rate_limiter._get_client_ip()}: {message}")
        return Response(
            f"Rate limit exceeded. Please try again later.\n{message}",
            status=429,
            headers={
                'Retry-After': str(rate_limiter.ban_duration_minutes * 60),
                'Content-Type': 'text/plain'
            }
        )
    
    return None
