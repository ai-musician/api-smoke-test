#!/usr/bin/env python3
"""Tiny practice API for Claude_perf_smoke.py.

Run healthy:            python3 Claude_dummy_api.py
Run with a regression:  python3 Claude_dummy_api.py --slow
(--slow adds a 2s blocking delay to POST — simulates a blocking DB call
on the hot path, so the smoke test's POST budget blows and it exits 1.)
"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

SLOW = "--slow" in sys.argv
PORT = 8000


class Handler(BaseHTTPRequestHandler):
    def _ok(self, delay=0.0):
        time.sleep(delay)
        body = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._ok()

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self._ok(delay=2.0 if SLOW else 0.0)

    def log_message(self, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    mode = "SLOW (2s delay on POST)" if SLOW else "healthy"
    print(f"Dummy API on http://127.0.0.1:{PORT}  [{mode}]  — Ctrl+C to stop")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
