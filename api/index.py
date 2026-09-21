import os
from pathlib import Path

# Import the actual handler from the repository's package-based server.
from gemini_web2api.server import GeminiHandler

# Export the handler as a plain module-level variable so Vercel's Python
# runtime can detect it without needing to infer a subclass.
handler = GeminiHandler

# Optional runtime configuration through Vercel Environment Variables.
from gemini_web2api.config import CONFIG

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
