import time
import redis
import uuid

from django.conf import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)

WINDOW_US = 1_000_000  # 1 second in microseconds

lua_script_micro = """
-- KEYS[1] = Redis key
-- ARGV[1] = current timestamp (microseconds)
-- ARGV[2] = window size (microseconds)
-- ARGV[3] = max allowed requests

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_requests = tonumber(ARGV[3])

-- Calculate window start time
local window_start = now - window

-- Remove old entries outside the current window
redis.call("ZREMRANGEBYSCORE", key, "-inf", window_start)

-- Count current requests in the window
local count = redis.call("ZCARD", key)

-- Check if we've exceeded the limit
if count >= max_requests then
    -- Set a shorter expiration for throttled keys to ensure cleanup
    redis.call("PEXPIRE", key, math.ceil(window / 1000) + 100)
    return 0
end

-- Generate a unique member to avoid collisions
local unique_member = now .. ":" .. math.random(1000000, 9999999)

-- Add current request
redis.call("ZADD", key, now, unique_member)

-- Set expiration with some buffer time
redis.call("PEXPIRE", key, math.ceil(window / 1000) + 1000)

return 1
"""

rate_limiter_micro = r.register_script(lua_script_micro)

def allow_request(api_key: str, max_rps: int) -> bool:
    """
    Check if a request should be allowed based on rate limiting.
    
    Args:
        api_key: The API key to rate limit
        max_rps: Maximum requests per second allowed
        
    Returns:
        bool: True if request is allowed, False if rate limited
    """
    now_us = int(time.time() * 1_000_000)
    key = f"rps:{api_key}"

    allowed = rate_limiter_micro(keys=[key], args=[now_us, WINDOW_US, max_rps])
    return allowed
