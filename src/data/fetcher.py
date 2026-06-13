"""HTTP fetcher with JSON file cache to avoid hammering APIs."""

import json
import os
import time
import requests
from config import Config


def _cache_path(key: str) -> str:
    os.makedirs(Config.CACHE_DIR, exist_ok=True)
    safe = key.replace("/", "_").replace("?", "_").replace("&", "_").replace("=", "_")
    return os.path.join(Config.CACHE_DIR, safe + ".json")


def _load_cache(key: str):
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    if time.time() - os.path.getmtime(path) > Config.CACHE_TTL:
        return None
    with open(path) as f:
        return json.load(f)


def _save_cache(key: str, data) -> None:
    with open(_cache_path(key), "w") as f:
        json.dump(data, f)


def fetch(url: str, headers: dict = None, params: dict = None, cache_key: str = None) -> dict:
    key = cache_key or url + str(params)
    cached = _load_cache(key)
    if cached is not None:
        return cached

    resp = requests.get(url, headers=headers or {}, params=params or {}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    _save_cache(key, data)
    return data
