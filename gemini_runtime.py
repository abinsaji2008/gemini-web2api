import importlib.util
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

UPSTREAM_REF = os.getenv("GEMINI_WEB2API_UPSTREAM_REF", "main")
RUNTIME_FILE = Path(tempfile.gettempdir()) / "gemini_web2api.py"
UPSTREAM_URL = f"https://raw.githubusercontent.com/Sophomoresty/gemini-web2api/{UPSTREAM_REF}/gemini_web2api.py"

if not RUNTIME_FILE.exists() or RUNTIME_FILE.stat().st_size < 1000:
    urllib.request.urlretrieve(UPSTREAM_URL, RUNTIME_FILE)

spec = importlib.util.spec_from_file_location("gemini_web2api_upstream", RUNTIME_FILE)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load gemini_web2api.py")

upstream = importlib.util.module_from_spec(spec)
sys.modules["gemini_web2api_upstream"] = upstream
spec.loader.exec_module(upstream)

GeminiHandler = upstream.GeminiHandler
CONFIG = upstream.CONFIG
MODELS = upstream.MODELS
__version__ = upstream.__version__
