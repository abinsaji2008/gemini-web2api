import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path

from gemini_web2api.server import GeminiHandler
from gemini_web2api.config import CONFIG

# Vercel detects Python Functions by finding a top-level handler class that
# explicitly inherits BaseHTTPRequestHandler.
class handler(BaseHTTPRequestHandler):
    pass

# Reuse the complete upstream GeminiHandler implementation while keeping the
# explicit BaseHTTPRequestHandler inheritance that Vercel's detector expects.
for _name, _value in GeminiHandler.__dict__.items():
    if _name not in {"__dict__", "__weakref__"}:
        setattr(handler, _name, _value)

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
