"""
Gemini Multi-Key Pool & High-Speed Failover Manager for CR Remover Studio.

Features:
- Direct High-Speed REST Client: Ultra-fast generation (<3s) without SDK overhead.
- Multi-API-Key Pooling: Rotates across multiple Google Gemini API keys.
- Automatic Failover: When a key encounters a 429 (ResourceExhausted / Rate Limit)
  or quota exhaustion, it puts that key into temporary cooldown, logs the rotation,
  and seamlessly retries the request using the next available key in the pool.
- Multi-Model Fallbacks: Automatically tries gemini-3-flash-preview, gemini-3.5-flash,
  gemini-3.1-flash-lite, and gemini-flash-latest.
- Multi-Source Loading: Reads keys from runtime parameters, storage/gemini_keys.json,
  and environment variables (GEMINI_API_KEYS, GEMINI_API_KEY).
- Live Health Testing & Latency Benchmarking for each key.
"""

from typing import List, Dict, Any, Optional, Union
import os
import re
import json
import time
import asyncio
import threading
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from app.config import STORAGE_DIR

POOL_STORAGE_FILE = STORAGE_DIR / "gemini_keys.json"

# Models to attempt in order of speed, capability, and availability
PREFERRED_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.7-flash",
]


def mask_key(key: str) -> str:
    """Masks an API key for safe logging and UI display (e.g. AIzaSy...9xK2)."""
    k = (key or "").strip()
    if not k:
        return "EMPTY"
    if len(k) <= 10:
        return k[:3] + "..." + k[-2:]
    return k[:8] + "..." + k[-4:]


def parse_raw_keys(raw: Union[str, List[str], None]) -> List[str]:
    """
    Parses a string or list of keys, handling commas, newlines, semicolons,
    spaces, quotes, and duplicates.
    """
    if not raw:
        return []
    
    tokens = []
    if isinstance(raw, list):
        for item in raw:
            tokens.extend(parse_raw_keys(item))
    elif isinstance(raw, str):
        cleaned = raw.replace(",", "\n").replace(";", "\n").replace("|", "\n")
        for line in cleaned.splitlines():
            line = line.strip().strip("'\"`")
            if line:
                for chunk in line.split():
                    chunk = chunk.strip().strip("'\"`")
                    if chunk and len(chunk) >= 8:
                        tokens.append(chunk)

    seen = set()
    result = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


class KeyHealth:
    def __init__(self, key: str):
        self.key = key
        self.masked = mask_key(key)
        self.status = "active"  # "active", "rate_limited", "invalid", "error"
        self.cooldown_until: float = 0.0
        self.success_count: int = 0
        self.fail_count: int = 0
        self.last_error: str = ""
        self.last_used: float = 0.0
        self.last_latency_ms: Optional[int] = None

    def is_available(self) -> bool:
        """Returns True if the key is not invalid and cooldown has expired."""
        if self.status == "invalid":
            return False
        if self.status == "rate_limited":
            if time.time() >= self.cooldown_until:
                self.status = "active"
                return True
            return False
        return True

    def mark_success(self, latency_ms: Optional[int] = None):
        self.status = "active"
        self.cooldown_until = 0.0
        self.success_count += 1
        self.last_used = time.time()
        if latency_ms is not None:
            self.last_latency_ms = latency_ms

    def mark_rate_limited(self, error: str, cooldown_seconds: int = 45):
        self.status = "rate_limited"
        self.cooldown_until = time.time() + cooldown_seconds
        self.fail_count += 1
        self.last_error = error
        self.last_used = time.time()

    def mark_invalid(self, error: str):
        self.status = "invalid"
        self.fail_count += 1
        self.last_error = error
        self.last_used = time.time()

    def mark_error(self, error: str):
        self.status = "error"
        self.fail_count += 1
        self.last_error = error
        self.last_used = time.time()

    def to_dict(self) -> Dict[str, Any]:
        cooldown_remaining = max(0, int(self.cooldown_until - time.time()))
        return {
            "key": self.key,
            "masked": self.masked,
            "status": self.status,
            "cooldown_remaining_sec": cooldown_remaining,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "last_error": self.last_error,
            "last_used": self.last_used,
            "last_latency_ms": self.last_latency_ms,
        }


class GeminiKeyPool:
    """
    Thread-safe Gemini API Key Pool with direct REST calls, automatic rotation, and failover.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GeminiKeyPool, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._keys_map: Dict[str, KeyHealth] = {}
        self._round_robin_idx = 0
        self._load_initial_keys()
        self._initialized = True

    def _load_initial_keys(self):
        """Loads keys from storage and environment variables."""
        if POOL_STORAGE_FILE.exists():
            try:
                with open(POOL_STORAGE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    keys = data.get("keys", []) if isinstance(data, dict) else data
                    for k in parse_raw_keys(keys):
                        if k not in self._keys_map:
                            self._keys_map[k] = KeyHealth(k)
            except Exception as e:
                print(f"[GeminiPool] Error reading {POOL_STORAGE_FILE}: {e}")

        env_keys_raw = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
        for k in parse_raw_keys(env_keys_raw):
            if k not in self._keys_map:
                self._keys_map[k] = KeyHealth(k)

        print(f"[GeminiPool] Initialized pool with {len(self._keys_map)} Gemini API key(s).")

    def register_keys(self, raw: Union[str, List[str], None], persist: bool = False) -> List[str]:
        """Registers new keys into the pool."""
        parsed = parse_raw_keys(raw)
        with self._lock:
            for k in parsed:
                if k not in self._keys_map:
                    self._keys_map[k] = KeyHealth(k)
            if persist:
                self._save_to_disk()
        return parsed

    def set_keys(self, raw: Union[str, List[str], None], persist: bool = True) -> List[str]:
        """Replaces the persistent pool with the provided keys."""
        parsed = parse_raw_keys(raw)
        with self._lock:
            new_map = {}
            for k in parsed:
                new_map[k] = self._keys_map.get(k, KeyHealth(k))
            self._keys_map = new_map
            if persist:
                self._save_to_disk()
        return parsed

    def remove_key(self, key_or_masked: str) -> bool:
        """Removes a key by exact value or masked string."""
        with self._lock:
            target_key = None
            for k, h in self._keys_map.items():
                if k == key_or_masked or h.masked == key_or_masked:
                    target_key = k
                    break
            if target_key and target_key in self._keys_map:
                del self._keys_map[target_key]
                self._save_to_disk()
                return True
        return False

    def _save_to_disk(self):
        """Persists current pool keys to storage."""
        try:
            STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            keys_list = list(self._keys_map.keys())
            with open(POOL_STORAGE_FILE, "w", encoding="utf-8") as f:
                json.dump({"keys": keys_list, "updated_at": time.time()}, f, indent=2)
        except Exception as e:
            print(f"[GeminiPool] Error saving keys to disk: {e}")

    def get_candidate_keys(self, request_keys: Union[str, List[str], None] = None) -> List[str]:
        """Gathers and orders candidate keys prioritizing healthy ones."""
        if request_keys:
            self.register_keys(request_keys, persist=False)

        with self._lock:
            ready_keys = [k for k, h in self._keys_map.items() if h.is_available()]
            limited_keys = [k for k, h in self._keys_map.items() if h.status == "rate_limited" and not h.is_available()]
            limited_keys.sort(key=lambda k: self._keys_map[k].cooldown_until)

            if ready_keys:
                idx = self._round_robin_idx % len(ready_keys)
                self._round_robin_idx += 1
                ready_keys = ready_keys[idx:] + ready_keys[:idx]

            candidates = ready_keys + limited_keys

        if request_keys:
            req_list = parse_raw_keys(request_keys)
            explicit_candidates = [k for k in req_list if k in candidates]
            other_candidates = [k for k in candidates if k not in req_list]
            candidates = explicit_candidates + other_candidates

        return candidates

    def get_status(self) -> Dict[str, Any]:
        """Returns detailed health status of all keys in the pool."""
        with self._lock:
            key_list = [h.to_dict() for h in self._keys_map.values()]
            total = len(key_list)
            active = sum(1 for h in self._keys_map.values() if h.is_available())
            rate_limited = sum(1 for h in self._keys_map.values() if h.status == "rate_limited" and not h.is_available())
            invalid = sum(1 for h in self._keys_map.values() if h.status == "invalid")
            return {
                "total_keys": total,
                "active_keys": active,
                "rate_limited_keys": rate_limited,
                "invalid_keys": invalid,
                "keys": key_list,
            }

    def _execute_http_request(
        self,
        api_key: str,
        model_name: str,
        prompt: str,
        temperature: float = 0.7,
        json_mode: bool = False
    ) -> str:
        """Direct HTTP call to Gemini REST endpoint with clean JSON/text extraction."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        gen_config: Dict[str, Any] = {"temperature": temperature}
        if json_mode:
            gen_config["responseMimeType"] = "application/json"

        body = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": gen_config
        }
        
        payload_bytes = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "CR-Remover-Studio/2.0"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=25) as response:
            resp_bytes = response.read()
            resp_json = json.loads(resp_bytes.decode("utf-8"))
            
            candidates = resp_json.get("candidates", [])
            if not candidates:
                raise ValueError("No candidate response returned by Gemini API.")
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                raise ValueError("Empty response parts returned by Gemini API.")
            
            return parts[0].get("text", "").strip()

    def generate_content(
        self,
        prompt: str,
        api_keys: Union[str, List[str], None] = None,
        model_names: Optional[List[str]] = None,
        temperature: float = 0.7,
        json_mode: bool = False
    ) -> str:
        """
        Executes a Gemini prompt with direct REST calls, multi-key rotation and multi-model failover.
        """
        candidates = self.get_candidate_keys(api_keys)
        if not candidates:
            raise ValueError("No Gemini API keys configured in pool or request.")

        models_to_try = model_names or PREFERRED_MODELS
        last_error = None

        for key_idx, key in enumerate(candidates):
            health = self._keys_map.get(key)
            masked = health.masked if health else mask_key(key)

            for model_name in models_to_try:
                start_t = time.time()
                try:
                    text_out = self._execute_http_request(
                        api_key=key,
                        model_name=model_name,
                        prompt=prompt,
                        temperature=temperature,
                        json_mode=json_mode
                    )
                    latency = int((time.time() - start_t) * 1000)

                    if text_out:
                        if health:
                            health.mark_success(latency_ms=latency)
                        return text_out
                    else:
                        raise ValueError("Empty response text received.")

                except urllib.error.HTTPError as http_err:
                    err_code = http_err.code
                    err_body = ""
                    try:
                        err_body = http_err.read().decode("utf-8")
                    except Exception:
                        pass
                    last_error = f"HTTP {err_code}: {err_body[:200]}"

                    if err_code == 429:
                        print(f"[GeminiPool] ⚠️ Key {masked} rate limited / quota exhausted ({model_name}). Rotating to next key in pool...")
                        if health:
                            health.mark_rate_limited(last_error, cooldown_seconds=45)
                        break # Switch to next key immediately!

                    elif err_code in (400, 403) and ("API_KEY_INVALID" in err_body or "API key not valid" in err_body):
                        print(f"[GeminiPool] ❌ Key {masked} is invalid. Marking invalid...")
                        if health:
                            health.mark_invalid(last_error)
                        break

                    elif err_code == 404:
                        # Model not available -> try next model for this key
                        continue

                    else:
                        print(f"[GeminiPool] ⚠️ Key {masked} with {model_name} HTTP {err_code}: {err_body[:100]}. Trying next model...")
                        continue

                except Exception as err:
                    last_error = str(err)
                    print(f"[GeminiPool] ⚠️ Key {masked} with {model_name} error: {last_error[:100]}. Trying next...")
                    continue

        raise RuntimeError(f"All {len(candidates)} Gemini API key(s) exhausted or failed. Last error: {last_error}")

    def generate_json(
        self,
        prompt: str,
        api_keys: Union[str, List[str], None] = None,
        model_names: Optional[List[str]] = None,
        fallback: Optional[Any] = None,
        temperature: float = 0.6,
    ) -> Any:
        """
        Executes a Gemini prompt with JSON mode enabled, strips markdown, and parses valid JSON.
        """
        try:
            raw_text = self.generate_content(
                prompt=prompt,
                api_keys=api_keys,
                model_names=model_names,
                temperature=temperature,
                json_mode=True
            )

            cleaned = raw_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            try:
                return json.loads(cleaned)
            except Exception:
                pass

            match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', cleaned)
            if match:
                return json.loads(match.group(1))

            raise ValueError("No valid JSON found in model output.")

        except Exception as e:
            print(f"[GeminiPool] JSON generation error: {e}")
            if fallback is not None:
                return fallback
            raise e

    async def test_single_key(self, key: str) -> Dict[str, Any]:
        """Tests a single key with a minimal ping using direct REST call."""
        k = key.strip()
        masked = mask_key(k)
        start_t = time.time()
        try:
            def _call():
                return self._execute_http_request(
                    api_key=k,
                    model_name="gemini-3-flash-preview",
                    prompt="Reply with the word OK."
                )

            text = await asyncio.to_thread(_call)
            latency = int((time.time() - start_t) * 1000)
            
            with self._lock:
                h = self._keys_map.get(k)
                if h:
                    h.mark_success(latency_ms=latency)

            return {
                "key": k,
                "masked": masked,
                "status": "active",
                "valid": True,
                "latency_ms": latency,
                "message": f"Verified ({latency}ms)",
            }
        except Exception as err:
            err_str = str(err)
            with self._lock:
                h = self._keys_map.get(k)
                if h:
                    if "429" in err_str:
                        h.mark_rate_limited(err_str)
                    elif "API_KEY" in err_str or "400" in err_str or "403" in err_str:
                        h.mark_invalid(err_str)
                    else:
                        h.mark_error(err_str)

            return {
                "key": k,
                "masked": masked,
                "status": "error",
                "valid": False,
                "latency_ms": None,
                "message": f"Failed: {err_str[:80]}",
            }


# Singleton instance
gemini_pool = GeminiKeyPool()
