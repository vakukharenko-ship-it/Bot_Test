import asyncio
import time
from config import CACHE_TTL_SECONDS

_cache = {}
_cache_timestamps = {}
_cache_lock = asyncio.Lock()

async def get_from_cache(key):
    async with _cache_lock:
        if key in _cache:
            timestamp = _cache_timestamps.get(key)
            if timestamp and (time.time() - timestamp) < CACHE_TTL_SECONDS:
                return _cache[key]
    return None

async def save_to_cache(key, value):
    async with _cache_lock:
        _cache[key] = value
        _cache_timestamps[key] = time.time()