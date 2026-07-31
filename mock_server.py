# mock_server.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time

class MockAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            # 1. Read the incoming POST request body length
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                _ = self.rfile.read(content_length)  # Read the body bytes
            
            # 2. Simulate a slight latency (50ms) for AI inference
            time.sleep(0.05)
            
            # 3. Return a successful 200 OK response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response_body = {"choices": [{"message": {"content": "pong"}}]}
            self.wfile.write(json.dumps(response_body).encode())
        else:
            self.send_response(404)
            self.end_headers()

    # Suppress verbose terminal log lines for clean output
    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    print("Starting mock API server on http://localhost:8080...")
    server = HTTPServer(("localhost", 8080), MockAPI)
    server.serve_forever()
