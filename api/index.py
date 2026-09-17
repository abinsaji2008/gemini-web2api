import os
import sys
import tempfile
from pathlib import Path

# Ensure the repository root is importable when Vercel invokes this function.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gemini_web2api.server import GeminiHandler
from gemini_web2api.config import CONFIG

# Vercel's Python runtime detects a top-level handler class that inherits from
# BaseHTTPRequestHandler.
class handler(GeminiHandler):
    pass

# Configure the upstream project from Vercel Environment Variables.
api_keys = os.getenv("GEMINI_API_KEYS", "")
if api_keys.strip():
    CONFIG["api_keys"] = [k.strip() for k in api_keys.split(",") if k.strip()]

for env_name, config_key in (
    ("GEMINI_AUTH_USER", "auth_user"),
    ("GEMINI_XSRF_TOKEN", "xsrf_token"),
    ("HTTPS_PROXY", "proxy"),
):
    value = os.getenv(env_name)
    if value:
        CONFIG[config_key] = value

# Vercel has an ephemeral writable /tmp directory, so an authenticated Gemini
# cookie supplied as an Environment Variable can be exposed to the upstream
# package through its existing cookie-file configuration without committing it
# to GitHub.
gemini_cookie = os.getenv("GEMINI_COOKIE", "").strip()
if gemini_cookie:
    cookie_path = Path(tempfile.gettempdir()) / "gemini-web2api-cookie.txt"
    try:
        cookie_path.write_text(gemini_cookie, encoding="utf-8")
        CONFIG["cookie_file"] = str(cookie_path)
    except OSError:
        pass
elif os.getenv("GEMINI_COOKIE_FILE"):
    # Optional compatibility path for a real file supplied by the runtime.
    CONFIG["cookie_file"] = os.environ["GEMINI_COOKIE_FILE"]

try:
    if os.getenv("GEMINI_TIMEOUT_SEC"):
        CONFIG["request_timeout_sec"] = int(os.environ["GEMINI_TIMEOUT_SEC"])
except ValueError:
    pass
