import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler
from pathlib import Path

UPSTREAM_REF = os.getenv("GEMINI_WEB2API_UPSTREAM_REF", "main")
BASE_URL = f"https://raw.githubusercontent.com/Sophomoresty/gemini-web2api/{UPSTREAM_REF}"
CACHE_DIR = Path("/tmp/gemini-web2api")

FILES = {
    "gemini_web2api/__init__.py": CACHE_DIR / "gemini_web2api" / "__init__.py",
    "gemini_web2api/config.py": CACHE_DIR / "gemini_web2api" / "config.py",
    "gemini_web2api/models.py": CACHE_DIR / "gemini_web2api" / "models.py",
    "gemini_web2api/gemini.py": CACHE_DIR / "gemini_web2api" / "gemini.py",
    "gemini_web2api/tools.py": CACHE_DIR / "gemini_web2api" / "tools.py",
    "gemini_web2api/multimodal.py": CACHE_DIR / "gemini_web2api" / "multimodal.py",
    "gemini_web2api/server.py": CACHE_DIR / "gemini_web2api" / "server.py",
}

def _load_upstream():
    package_dir = CACHE_DIR / "gemini_web2api"
    package_dir.mkdir(parents=True, exist_ok=True)

    for relative, destination in FILES.items():
        if not destination.exists() or destination.stat().st_size < 100:
            urllib.request.urlretrieve(f"{BASE_URL}/{relative}", destination)

    sys.path.insert(0, str(CACHE_DIR))
    import gemini_web2api.server as server
    import gemini_web2api.config as config
    return server.GeminiHandler, config.CONFIG

# Import here so the Vercel builder can resolve the dependency as part of the
# module graph. Runtime files are fetched on cold start into /tmp.
import urllib.request
GeminiHandler, CONFIG = _load_upstream()

# Vercel's Python detector requires a top-level handler inheriting directly
# from BaseHTTPRequestHandler.
class handler(BaseHTTPRequestHandler):
    pass

for _name, _value in GeminiHandler.__dict__.items():
    if _name not in {"__dict__", "__weakref__"}:
        setattr(handler, _name, _value)

# Vercel internal rewrites can expose the rewritten destination as self.path.
# Restore the original request path captured by vercel.json.
_original_path = handler.path if hasattr(handler, "path") else ""
_parsed = urllib.parse.urlsplit(_original_path)
_route = urllib.parse.parse_qs(_parsed.query).get("__route", [None])[0]
if _route is not None:
    # Preserve any real query parameters while removing the routing marker.
    _route_path = "/" + urllib.parse.unquote(_route).lstrip("/")
    _query_pairs = urllib.parse.parse_qsl(_parsed.query, keep_blank_values=True)
    _query_pairs = [(k, v) for k, v in _query_pairs if k != "__route"]
    handler.path = _route_path + (
        "?" + urllib.parse.urlencode(_query_pairs) if _query_pairs else ""
    )

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
