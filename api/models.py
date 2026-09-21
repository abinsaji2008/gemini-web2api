from http.server import BaseHTTPRequestHandler
from gemini_runtime import MODELS
import json
import os

def _authorized(headers):
    keys = [x.strip() for x in os.getenv("GEMINI_API_KEYS", "").split(",") if x.strip()]
    if not keys:
        return True
    auth = headers.get("Authorization", "")
    return auth.startswith("Bearer ") and auth[7:] in keys or headers.get("x-api-key", "") in keys or headers.get("x-goog-api-key", "") in keys

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if not _authorized(self.headers):
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":{"message":"invalid api key"}}')
            return

        body = {
            "object": "list",
            "data": [
                {
                    "id": name,
                    "object": "model",
                    "created": 1700000000,
                    "owned_by": "google",
                    "description": cfg["desc"],
                }
                for name, cfg in MODELS.items()
            ],
        }
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
