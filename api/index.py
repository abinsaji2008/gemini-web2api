import importlib.util
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Load the real upstream single-file implementation.
UPSTREAM_REF = os.getenv("GEMINI_WEB2API_UPSTREAM_REF", "main")
CACHE_DIR = Path("/tmp/gemini-web2api")
RUNTIME_FILE = CACHE_DIR / "gemini_web2api.py"
UPSTREAM_URL = (
    f"https://raw.githubusercontent.com/Sophomoresty/gemini-web2api/"
    f"{UPSTREAM_REF}/gemini_web2api.py"
)

CACHE_DIR.mkdir(parents=True, exist_ok=True)
if not RUNTIME_FILE.exists() or RUNTIME_FILE.stat().st_size < 1000:
    urllib.request.urlretrieve(UPSTREAM_URL, RUNTIME_FILE)

spec = importlib.util.spec_from_file_location(
    "gemini_web2api_upstream",
    RUNTIME_FILE,
)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load upstream gemini_web2api.py")

upstream = importlib.util.module_from_spec(spec)
sys.modules["gemini_web2api_upstream"] = upstream
spec.loader.exec_module(upstream)

GeminiHandler = upstream.GeminiHandler
CONFIG = upstream.CONFIG

# Vercel's Python detector requires a top-level handler inheriting from
# BaseHTTPRequestHandler. For this deployment, chat completions are always
# returned as one complete JSON answer: the upstream SSE/token stream is not
# exposed to clients, even when they send "stream": true.
class handler(GeminiHandler):
    def handle_chat(self, body: bytes):
        import json

        try:
            request = json.loads(body)
            if isinstance(request, dict):
                request["stream"] = False
                body = json.dumps(request, ensure_ascii=False).encode("utf-8")
        except Exception:
            # Let the upstream handler return its normal JSON parsing error.
            pass

        return super().handle_chat(body)

# The upstream handler expects the original public URL in self.path.
# With a Vercel "routes" entry, the original request path is preserved.
# No rewrite-specific path manipulation is necessary.

api_keys = os.getenv("GEMINI_API_KEYS", "").strip()
if api_keys:
    CONFIG["api_keys"] = [k.strip() for k in api_keys.split(",") if k.strip()]

for env_name, config_key in (
    ("GEMINI_AUTH_USER", "auth_user"),
    ("GEMINI_XSRF_TOKEN", "xsrf_token"),
    ("HTTPS_PROXY", "proxy"),
):
    value = os.getenv(env_name)
    if value:
        CONFIG[config_key] = value

gemini_cookie = os.getenv("GEMINI_COOKIE", "").strip()
if gemini_cookie:
    cookie_path = Path("/tmp/gemini-web2api-cookie.txt")
    cookie_path.write_text(gemini_cookie, encoding="utf-8")
    CONFIG["cookie_file"] = str(cookie_path)

try:
    if os.getenv("GEMINI_TIMEOUT_SEC"):
        CONFIG["request_timeout_sec"] = int(os.environ["GEMINI_TIMEOUT_SEC"])
except ValueError:
    pass
