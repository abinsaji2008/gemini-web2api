import importlib.util
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# The upstream project is a single-file application.
UPSTREAM_REF = os.getenv("GEMINI_WEB2API_UPSTREAM_REF", "main")
UPSTREAM_URL = (
    f"https://raw.githubusercontent.com/Sophomoresty/gemini-web2api/"
    f"{UPSTREAM_REF}/gemini_web2api.py"
)
RUNTIME_FILE = Path("/tmp/gemini_web2api.py")

if not RUNTIME_FILE.exists() or RUNTIME_FILE.stat().st_size < 1000:
    urllib.request.urlretrieve(UPSTREAM_URL, RUNTIME_FILE)

spec = importlib.util.spec_from_file_location("gemini_web2api_upstream", RUNTIME_FILE)
upstream = importlib.util.module_from_spec(spec)
sys.modules["gemini_web2api_upstream"] = upstream
spec.loader.exec_module(upstream)

GeminiHandler = upstream.GeminiHandler
CONFIG = upstream.CONFIG

# Vercel requires a top-level handler inheriting from BaseHTTPRequestHandler.
class handler(BaseHTTPRequestHandler):
    pass

# Copy the complete upstream HTTP handler implementation.
for _name, _value in GeminiHandler.__dict__.items():
    if _name not in {"__dict__", "__weakref__"}:
        setattr(handler, _name, _value)

def _restore_route(self):
    parsed = urllib.parse.urlsplit(self.path)
    route_values = urllib.parse.parse_qs(
        parsed.query, keep_blank_values=True
    ).get("__route")

    if not route_values:
        return

    route = urllib.parse.unquote(route_values[0])
    if not route.startswith("/"):
        route = "/" + route

    real_query = [
        (k, v)
        for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if k != "__route"
    ]

    self.path = route
    if real_query:
        self.path += "?" + urllib.parse.urlencode(real_query)

_original_get = handler.do_GET
_original_post = handler.do_POST

def do_GET(self):
    _restore_route(self)
    return _original_get(self)

def do_POST(self):
    _restore_route(self)
    return _original_post(self)

handler.do_GET = do_GET
handler.do_POST = do_POST

# Optional Vercel environment configuration.
api_keys = os.getenv("GEMINI_API_KEYS", "").strip()
if api_keys:
    CONFIG["api_keys"] = [x.strip() for x in api_keys.split(",") if x.strip()]

cookie = os.getenv("GEMINI_COOKIE", "").strip()
if cookie:
    cookie_file = Path("/tmp/gemini-cookie.txt")
    cookie_file.write_text(cookie, encoding="utf-8")
    CONFIG["cookie_file"] = str(cookie_file)

for env_name, config_key in (
    ("GEMINI_AUTH_USER", "auth_user"),
    ("GEMINI_XSRF_TOKEN", "xsrf_token"),
    ("HTTPS_PROXY", "proxy"),
):
    value = os.getenv(env_name)
    if value:
        CONFIG[config_key] = value
