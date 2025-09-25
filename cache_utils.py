# cache_utils.py
from functools import lru_cache
import hashlib
import json
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def load_signals_cached(file_path="knowledge_base.json"):
    """Cache the signals data to avoid repeated file reads"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_query_hash(query, signals_count):
    """Create hash for caching based on query and data state"""
    return hashlib.md5(f"{query}_{signals_count}".encode()).hexdigest()

# Cache for API responses (optional enhancement)
api_cache = {}
CACHE_DURATION = timedelta(hours=1)

def get_cached_api_response(cache_key):
    """Get cached API response if still valid"""
    if cache_key in api_cache:
        data, timestamp = api_cache[cache_key]
        if datetime.now() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cached_api_response(cache_key, data):
    """Cache API response with timestamp"""
    api_cache[cache_key] = (data, datetime.now())