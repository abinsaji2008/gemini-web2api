import os
import sys
from pathlib import Path

# Ensure the repository root is importable when Vercel invokes this function.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gemini_web2api.server import GeminiHandler
from gemini_web2api.config import CONFIG

# Vercel's Python runtime detects a top-level handler class that inherits from
# BaseHTTPRequestHandler. The upstream server already implements that class,
# so we expose a tiny subclass under the required entrypoint name.
class handler(GeminiHandler):
    pass

# Configure the upstream project from Vercel environment variables.
api_keys = os.getenv("GEMINI_API_KEYS", "")
if api_keys.strip():
    CONFIG["api_keys"] = [k.strip() for k in api_keys.split(",") if k.strip()]

for env_name, config_key in (
    ("GEMINI_AUTH_USER", "auth_user"),
    ("GEMINI_XSRF_TOKEN", "xsrf_token"),
    ("GEMINI_COOKIE_FILE", "cookie_file"),
    ("HTTPS_PROXY", "proxy"),
):
    value = os.getenv(env_name)
    if value:
        CONFIG[config_key] = value

try:
    if os.getenv("GEMINI_TIMEOUT_SEC"):
        CONFIG["request_timeout_sec"] = int(os.environ["GEMINI_TIMEOUT_SEC"])
except ValueError:
    pass
