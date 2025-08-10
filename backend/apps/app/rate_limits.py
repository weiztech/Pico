import time
import redis

from django.conf import settings

r = redis.Redis(host=settings.REDIS_HOST, port=6379, db=0)

MAX_RPS = 10
WINDOW_US = 1_000_000  # 1 second in microseconds

lua_script_micro = """
-- KEYS[1] = Redis key
-- ARGV[1] = current timestamp (microseconds)
-- ARGV[2] = window size (microseconds)
-- ARGV[3] = max allowed requests

-- Remove timestamps outside the window
redis.call("ZREMRANGEBYSCORE", KEYS[1], 0, ARGV[1] - ARGV[2])

-- Count how many remain
local count = redis.call("ZCARD", KEYS[1])
if count >= tonumber(ARGV[3]) then
    return 0
end

-- Add current timestamp
redis.call("ZADD", KEYS[1], ARGV[1], ARGV[1])

-- Expire key slightly longer than window
redis.call("PEXPIRE", KEYS[1], math.floor((ARGV[2] / 1000) + 1000))

return 1
"""

rate_limiter_micro = r.register_script(lua_script_micro)

def allow_request(api_key: str) -> bool:
    now_us = int(time.time() * 1_000_000)
    key = f"rps:{api_key}"
    allowed = rate_limiter_micro(keys=[key], args=[now_us, WINDOW_US, MAX_RPS])
    return allowed == 1
