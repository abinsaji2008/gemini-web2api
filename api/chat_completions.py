import os
from http.server import BaseHTTPRequestHandler
from gemini_runtime import GeminiHandler, CONFIG

def _authorized(headers):
    keys = [x.strip() for x in os.getenv("GEMINI_API_KEYS", "").split(",") if x.strip()]
    if not keys:
        return True
    auth = headers.get("Authorization", "")
    return (auth.startswith("Bearer ") and auth[7:] in keys) or headers.get("x-api-key", "") in keys or headers.get("x-goog-api-key", "") in keys

class handler(BaseHTTPRequestHandler):
    def _read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length)

    def do_POST(self):
        if not _authorized(self.headers):
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":{"message":"invalid api key"}}')
            return

        body = self._read_body()

        # Use the upstream handler implementation with the exact route it expects.
        self.path = "/v1/chat/completions"

        # Copy upstream handler methods onto this Vercel handler instance.
        for name in ("send_json", "_start_sse", "_parse_body", "_authorized",
                     "_read_request_body", "_handle_chat"):
            method = getattr(GeminiHandler, name, None)
            if method:
                setattr(self, name, method.__get__(self, handler))

        # Upstream _handle_chat uses CONFIG directly; configure it from Vercel.
        keys = [x.strip() for x in os.getenv("GEMINI_API_KEYS", "").split(",") if x.strip()]
        if keys:
            CONFIG["api_keys"] = keys

        cookie = os.getenv("GEMINI_COOKIE", "").strip()
        if cookie:
            from pathlib import Path
            cookie_path = Path("/tmp/gemini-cookie.txt")
            cookie_path.write_text(cookie, encoding="utf-8")
            CONFIG["cookie_file"] = str(cookie_path)

        try:
            self._handle_chat(body)
        except Exception as exc:
            self.send_json({"error": {"message": str(exc)}}, 500)
