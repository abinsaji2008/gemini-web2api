import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

UPSTREAM_REF = os.getenv("GEMINI_WEB2API_UPSTREAM_REF", "main")
BASE_URL = f"https://raw.githubusercontent.com/Sophomoresty/gemini-web2api/{UPSTREAM_REF}"
CACHE_DIR = Path("/tmp/gemini-web2api")

FILES = {
    "gemini_web2api.py": CACHE_DIR / "gemini_web2api.py",
}

def _load_upstream():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    destination = FILES["gemini_web2api.py"]
    if not destination.exists() or destination.stat().st_size < 1000:
        urllib.request.urlretrieve(
            f"{BASE_URL}/gemini_web2api.py",
            destination,
        )

    spec = importlib.util.spec_from_file_location(
        "gemini_web2api_upstream",
        destination,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load gemini_web2api.py")

    module = importlib.util.module_from_spec(spec)
    sys.modules["gemini_web2api_upstream"] = module
    spec.loader.exec_module(module)
    return module.GeminiHandler, module.CONFIG

import importlib.util
GeminiHandler, CONFIG = _load_upstream()

# Vercel's Python detector requires a top-level handler inheriting from
# BaseHTTPRequestHandler.
class handler(BaseHTTPRequestHandler):
    pass

for _name, _value in GeminiHandler.__dict__.items():
    if _name not in {"__dict__", "__weakref__"}:
        setattr(handler, _name, _value)

def _normalize_rewritten_path(self):
    # With the explicit Vercel rewrites, the upstream handler can receive
    # /api/index.py/<original-path>. Restore the public path before dispatch.
    prefix = "/api/index.py"
    path = self.path

    if path == prefix or path == prefix + "/":
        self.path = "/"
        return

    if path.startswith(prefix + "/"):
        self.path = path[len(prefix):]
        return

    # Keep direct /api/index.py query requests usable as well.
    parsed = urllib.parse.urlsplit(path)
    if parsed.path == prefix:
        self.path = "/" + (
            "?" + parsed.query if parsed.query else ""
        )

_original_get = handler.do_GET
_original_post = handler.do_POST

def do_GET(self):
    _normalize_rewritten_path(self)
    return _original_get(self)

def do_POST(self):
    _normalize_rewritten_path(self)
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
