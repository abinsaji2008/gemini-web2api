from http.server import BaseHTTPRequestHandler

from gemini_runtime import MODELS, CONFIG, __version__

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"

        if path == "/":
            body = {
                "status": "ok",
                "version": __version__,
                "models": list(MODELS.keys()),
            }
            import json
            raw = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error":"not found"}')
