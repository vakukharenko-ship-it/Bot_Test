import asyncio
import time
import aiohttp
from config import API_TIMEOUT, API_RETRY_ATTEMPTS, API_RETRY_DELAY, RATE_LIMIT_REQUESTS_PER_SECOND
from utils.logger import write_log

_http_session = None
_rate_limiter = None

class RateLimiter:
    def __init__(self, rate=RATE_LIMIT_REQUESTS_PER_SECOND):
        self.rate = rate
        self.lock = asyncio.Lock()
        self.last_request_time = 0

    async def acquire(self):
        async with self.lock:
            now = time.time()
            wait_time = (1.0 / self.rate) - (now - self.last_request_time)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_request_time = time.time()

async def init_http_session():
    global _http_session, _rate_limiter
    _rate_limiter = RateLimiter()
    timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
    connector = aiohttp.TCPConnector(
        limit=50,
        limit_per_host=10,
        ttl_dns_cache=300
    )
    _http_session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    write_log("✅ HTTP-сессия инициализирована")

async def close_http_session():
    global _http_session
    if _http_session:
        await _http_session.close()
        write_log("🔒 HTTP-сессия закрыта")

async def api_request_with_retry(url, headers, payload=None, method='POST'):
    global _http_session, _rate_limiter
    for attempt in range(API_RETRY_ATTEMPTS):
        try:
            await _rate_limiter.acquire()
            if method == 'POST':
                async with _http_session.post(url, headers=headers, json=payload) as resp:
                    if resp.status == 429:
                        wait_time = API_RETRY_DELAY * (2 ** attempt)
                        write_log(f"⚠️ Rate limit, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    resp.raise_for_status()
                    return await resp.json()
            else:
                async with _http_session.get(url, headers=headers, params=payload) as resp:
                    if resp.status == 429:
                        wait_time = API_RETRY_DELAY * (2 ** attempt)
                        write_log(f"⚠️ Rate limit, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    resp.raise_for_status()
                    return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == API_RETRY_ATTEMPTS - 1:
                write_log(f"❌ Request failed after {API_RETRY_ATTEMPTS} attempts: {e}")
                raise
            write_log(f"⚠️ Request failed (attempt {attempt+1}/{API_RETRY_ATTEMPTS}): {e}")
            await asyncio.sleep(API_RETRY_DELAY * (attempt + 1))
    raise Exception("API request failed after retries")
