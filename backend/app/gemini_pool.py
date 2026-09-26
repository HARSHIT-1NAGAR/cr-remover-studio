"""
Gemini Multi-Key Pool & Failover Manager for CR Remover Studio.

Features:
- Multi-API-Key Pooling: Rotates across multiple Google Gemini API keys.
- Automatic Failover: When a key encounters a 429 (ResourceExhausted / Rate Limit)
  or quota exhaustion, it puts that key into temporary cooldown, logs the rotation,
  and seamlessly retries the request using the next available key in the pool.
- Multi-Model Fallbacks: Automatically tries gemini-2.0-flash, gemini-1.5-flash,
  gemini-2.0-flash-lite, and gemini-1.5-pro.
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
from pathlib import Path
import google.generativeai as genai
from app.config import STORAGE_DIR

POOL_STORAGE_FILE = STORAGE_DIR / "gemini_keys.json"

# Models to attempt in order of speed and capability
PREFERRED_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-pro",
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
        # Replace common separators with newline
        cleaned = raw.replace(",", "\n").replace(";", "\n").replace("|", "\n")
        for line in cleaned.splitlines():
            line = line.strip().strip("'\"`")
            if line:
                for chunk in line.split():
                    chunk = chunk.strip().strip("'\"`")
                    if chunk and len(chunk) >= 8:
                        tokens.append(chunk)

    # Deduplicate preserving order
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

    def mark_rate_limited(self, error: str, cooldown_seconds: int = 60):
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
    Thread-safe Gemini API Key Pool with automatic rotation and failover.
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
        # 1. Load from storage JSON file
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

        # 2. Load from environment variables
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
            # Keep existing health stats if key already exists
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
        """
        Gathers and orders candidate keys for an API call.
        Prioritizes:
        1. Explicit request keys (if any)
        2. Pool keys that are currently active/healthy
        3. Rate-limited keys whose cooldown expired
        4. Rate-limited keys (as last resort)
        """
        # Register any transient keys passed in request
        if request_keys:
            self.register_keys(request_keys, persist=False)

        candidates = []
        with self._lock:
            # Active and ready keys
            ready_keys = [k for k, h in self._keys_map.items() if h.is_available()]
            # Rate-limited keys (in case everything is limited, try youngest cooldown)
            limited_keys = [k for k, h in self._keys_map.items() if h.status == "rate_limited" and not h.is_available()]
            limited_keys.sort(key=lambda k: self._keys_map[k].cooldown_until)

            # Round-robin shift for load balancing
            if ready_keys:
                idx = self._round_robin_idx % len(ready_keys)
                self._round_robin_idx += 1
                ready_keys = ready_keys[idx:] + ready_keys[:idx]

            candidates = ready_keys + limited_keys

        # If user passed explicit request keys, place them first
        if request_keys:
            req_list = parse_raw_keys(request_keys)
            # Reorder so request keys come first if available
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

    def generate_content(
        self,
        prompt: str,
        api_keys: Union[str, List[str], None] = None,
        model_names: Optional[List[str]] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Executes a Gemini prompt with automatic multi-key rotation and multi-model failover.
        """
        candidates = self.get_candidate_keys(api_keys)
        if not candidates:
            raise ValueError("No Gemini API keys configured in pool or request.")

        models_to_try = model_names or PREFERRED_MODELS
        last_error = None

        for key_idx, key in enumerate(candidates):
            health = self._keys_map.get(key)
            masked = health.masked if health else mask_key(key)

            # Configure genai with this candidate key
            try:
                genai.configure(api_key=key)
            except Exception as e:
                if health:
                    health.mark_invalid(str(e))
                continue

            # Try models for this key
            for model_name in models_to_try:
                try:
                    start_t = time.time()
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        generation_config={"temperature": temperature}
                    )
                    response = model.generate_content(prompt)
                    latency = int((time.time() - start_t) * 1000)

                    if response and response.text:
                        if health:
                            health.mark_success(latency_ms=latency)
                        # Success!
                        return response.text.strip()
                    else:
                        raise ValueError("Empty response text received from Gemini API.")

                except Exception as err:
                    err_str = str(err)
                    last_error = err

                    # Detect Rate Limit / Quota Exceeded (429, ResourceExhausted)
                    is_rate_limit = (
                        "429" in err_str
                        or "ResourceExhausted" in err_str
                        or "QuotaExceeded" in err_str
                        or "rate limit" in err_str.lower()
                        or "quota" in err_str.lower()
                    )

                    # Detect Invalid API Key
                    is_invalid_key = (
                        "API_KEY_INVALID" in err_str
                        or "API key not valid" in err_str
                        or "PERMISSION_DENIED" in err_str
                    )

                    if is_rate_limit:
                        print(f"[GeminiPool] ⚠️ Key {masked} rate limited / quota exhausted ({model_name}). Rotating to next key in pool...")
                        if health:
                            health.mark_rate_limited(err_str, cooldown_seconds=60)
                        # Break out of model loop and switch to the next candidate key immediately!
                        break

                    elif is_invalid_key:
                        print(f"[GeminiPool] ❌ Key {masked} is invalid. Marking invalid and switching to next key...")
                        if health:
                            health.mark_invalid(err_str)
                        break

                    else:
                        # Model not found or transient error -> try next model for this key first
                        print(f"[GeminiPool] ⚠️ Key {masked} with {model_name} failed: {err_str[:120]}. Trying fallback model...")
                        continue

            # If we reached here, this key failed all models, so proceed to next key in candidate list

        # If all candidate keys failed
        raise RuntimeError(f"All {len(candidates)} Gemini API key(s) exhausted or failed. Last error: {last_error}")

    def generate_json(
        self,
        prompt: str,
        api_keys: Union[str, List[str], None] = None,
        model_names: Optional[List[str]] = None,
        fallback: Optional[Any] = None,
        temperature: float = 0.5,
    ) -> Any:
        """
        Executes a Gemini prompt, cleans markdown fences, and parses valid JSON.
        Returns fallback if parsing or generation fails.
        """
        try:
            raw_text = self.generate_content(
                prompt=prompt,
                api_keys=api_keys,
                model_names=model_names,
                temperature=temperature,
            )

            # Strip Markdown ```json ... ``` fences
            cleaned = raw_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            # Attempt direct json parse
            try:
                return json.loads(cleaned)
            except Exception:
                pass

            # Regex search for JSON object {...} or list [...]
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
        """Tests a single key with a minimal ping."""
        k = key.strip()
        masked = mask_key(k)
        start_t = time.time()
        try:
            def _call():
                genai.configure(api_key=k)
                model = genai.GenerativeModel("gemini-1.5-flash")
                res = model.generate_content("Reply with the word 'OK'.")
                return res.text

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
            is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "ResourceExhausted" in err_str
            is_invalid = "API_KEY_INVALID" in err_str or "not valid" in err_str.lower()

            status = "rate_limited" if is_rate_limit else ("invalid" if is_invalid else "error")
            with self._lock:
                h = self._keys_map.get(k)
                if h:
                    if is_rate_limit:
                        h.mark_rate_limited(err_str)
                    elif is_invalid:
                        h.mark_invalid(err_str)
                    else:
                        h.mark_error(err_str)

            return {
                "key": k,
                "masked": masked,
                "status": status,
                "valid": False,
                "latency_ms": None,
                "message": err_str[:120],
            }

    async def test_all_keys(self, raw_keys: Union[str, List[str], None] = None) -> List[Dict[str, Any]]:
        """Tests all keys concurrently and returns test reports."""
        target_keys = parse_raw_keys(raw_keys) if raw_keys else list(self._keys_map.keys())
        if not target_keys:
            return []

        tasks = [self.test_single_key(k) for k in target_keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        output = []
        for r, k in zip(results, target_keys):
            if isinstance(r, dict):
                output.append(r)
            else:
                output.append({
                    "key": k,
                    "masked": mask_key(k),
                    "status": "error",
                    "valid": False,
                    "latency_ms": None,
                    "message": str(r)[:120],
                })
        return output


# Global Singleton Instance
gemini_pool = GeminiKeyPool()
