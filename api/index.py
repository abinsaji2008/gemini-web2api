import importlib.util
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

# This repository is intentionally small, so Vercel does not need to build the
# upstream project as a Git dependency. The upstream project is pinned to a
# known commit and loaded into /tmp on a cold start.
UPSTREAM_REF = os.getenv(
    "GEMINI_WEB2API_UPSTREAM_REF",
    "2bb988bfcbb82a7fab5d2c99aa5560ff40d64f7e",
)
UPSTREAM_URL = (
    "https://raw.githubusercontent.com/Sophomoresty/gemini-web2api/"
    f"{UPSTREAM_REF}/gemini_web2api.py"
)
BOOTSTRAP_DIR = Path(tempfile.gettempdir()) / "gemini-web2api"
UPSTREAM_FILE = BOOTSTRAP_DIR / "gemini_web2api_upstream.py"


def _load_upstream():
    BOOTSTRAP_DIR.mkdir(parents=True, exist_ok=True)
    if not UPSTREAM_FILE.exists() or UPSTREAM_FILE.stat().st_size < 1000:
        try:
            urllib.request.urlretrieve(UPSTREAM_URL, UPSTREAM_FILE)
        except Exception as exc:
            raise RuntimeError(
                "Unable to load the pinned gemini-web2api runtime from GitHub: "
                f"{exc}"
            ) from exc

    spec = importlib.util.spec_from_file_location(
        "gemini_web2api_upstream", UPSTREAM_FILE
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to create the gemini-web2api runtime module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_upstream = _load_upstream()
GeminiHandler = _upstream.GeminiHandler
CONFIG = _upstream.CONFIG

# Vercel's Python runtime recognizes a top-level BaseHTTPRequestHandler subclass.
class handler(GeminiHandler):
    pass


# Optional protection for clients using this API as an OpenAI-compatible backend.
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

# Vercel gives functions an ephemeral writable /tmp directory. Accept the
# browser cookie directly as a secret Environment Variable without committing it.
gemini_cookie = os.getenv("GEMINI_COOKIE", "").strip()
if gemini_cookie:
    cookie_path = Path(tempfile.gettempdir()) / "gemini-web2api-cookie.txt"
    try:
        cookie_path.write_text(gemini_cookie, encoding="utf-8")
        CONFIG["cookie_file"] = str(cookie_path)
    except OSError:
        pass
elif os.getenv("GEMINI_COOKIE_FILE"):
    CONFIG["cookie_file"] = os.environ["GEMINI_COOKIE_FILE"]

try:
    if os.getenv("GEMINI_TIMEOUT_SEC"):
        CONFIG["request_timeout_sec"] = int(os.environ["GEMINI_TIMEOUT_SEC"])
except ValueError:
    pass
