import importlib.util
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

UPSTREAM_REF = os.getenv("GEMINI_WEB2API_UPSTREAM_REF", "main")
BASE_URL = f"https://raw.githubusercontent.com/Sophomoresty/gemini-web2api/{UPSTREAM_REF}"
CACHE_DIR = Path("/tmp/gemini-web2api")
RUNTIME_FILE = CACHE_DIR / "gemini_web2api.py"

def _load_upstream():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not RUNTIME_FILE.exists() or RUNTIME_FILE.stat().st_size < 1000:
        urllib.request.urlretrieve(
            f"{BASE_URL}/gemini_web2api.py",
            RUNTIME_FILE,
        )

    spec = importlib.util.spec_from_file_location(
        "gemini_web2api_upstream",
        RUNTIME_FILE,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load gemini_web2api.py")

    module = importlib.util.module_from_spec(spec)
    sys.modules["gemini_web2api_upstream"] = module
    spec.loader.exec_module(module)
    return module.GeminiHandler, module.CONFIG

GeminiHandler, CONFIG = _load_upstream()

# Vercel's Python detector requires a top-level handler inheriting directly
# from BaseHTTPRequestHandler.
class handler(BaseHTTPRequestHandler):
    pass

# Reuse the complete upstream HTTP handler implementation.
for _name, _value in GeminiHandler.__dict__.items():
    if _name not in {"__dict__", "__weakref__"}:
        setattr(handler, _name, _value)

def _normalize_path(self):
    original = self.path
    parsed = urllib.parse.urlsplit(original)
    path = parsed.path

    # Internal Vercel rewrite may prefix the public route with /api/index.py.
    prefix = "/api/index.py"
    if path == prefix:
        path = "/"
    elif path.startswith(prefix + "/"):
        path = path[len(prefix):]

    if not path:
        path = "/"

    # Accept a trailing slash on API routes.
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")

    # The upstream authorization code can inspect the original query string,
    # so perform authentication before replacing self.path.
    return path

_original_get = handler.do_GET
_original_post = handler.do_POST

def do_GET(self):
    path = _normalize_path(self)
    self.path = path
    return _original_get(self)

def do_POST(self):
    original = self.path
    path = _normalize_path(self)

    # Preserve query parameters while authorizing, because the upstream
    # handler supports ?key=<api-key> for Gemini-style requests.
    self.path = original
    if path.startswith("/v1") and not self._authorized():
        self.send_json({"error": {"message": "invalid api key"}}, 401)
        return

    self.path = path
    return _original_post(self)

handler.do_GET = do_GET
handler.do_POST = do_POST

# Optional runtime configuration through Vercel Environment Variables.
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
