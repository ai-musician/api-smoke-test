#!/usr/bin/env python3
"""Broken-on-purpose API server — practice READING perf smoke failures.

Each mode simulates a real class of production regression. Run one mode in
terminal 1, then run the smoke test in terminal 2 and read the output:

    python3 Claude_broken_api.py --mode slow
    python3 smoke_test.py                     # or Claude_smoke_test_v2.py

Modes (all deterministic, so the output is reproducible):
  slow        POST sleeps 2s every time.
              Real-world: a synchronous DB/HTTP call landed on the async
              hot path, or an N+1 query. p95 blows the budget cleanly.
  errors      Every 3rd POST returns 500.
              Real-world: bad deploy, dependency down, race under load.
              Latency looks fine — the ERROR count is what fails the check.
  flaky       Every 8th request (any endpoint) takes +3s.
              Real-world: GC pauses, lock contention, noisy CI neighbor.
              p50 stays great; only the TAIL (p95) catches it. This is
              exactly why the smoke reports percentiles, never averages.
  slowhealth  GET /health takes 400ms (POST is normal).
              Real-world: when even the trivial endpoint is slow, suspect
              the platform — blocked event loop, CPU throttling, swap —
              not the endpoint's own code.
  hang        POST never responds within the client's 10s timeout.
              Real-world: deadlock, stuck upstream connection. The client
              timeout is what saves CI from hanging forever. NOTE: each
              request burns the full 10s — watch 2-3 fail, then Ctrl+C.
"""
import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8080


class BrokenAPI(BaseHTTPRequestHandler):
    mode = "slow"
    counter = 0  # deterministic failure injection, not random

    def _tick(self):
        BrokenAPI.counter += 1
        return BrokenAPI.counter

    def _flaky_delay(self):
        if self.mode == "flaky" and self._tick() % 8 == 0:
            time.sleep(3.0)

    def _send_json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path != "/health":
            return self._send_json(404, {"error": "not found"})
        self._flaky_delay()
        if self.mode == "slowhealth":
            time.sleep(0.4)
        self._send_json(200, {"status": "ok"})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            return self._send_json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        if length:
            self.rfile.read(length)

        self._flaky_delay()
        if self.mode == "slow":
            time.sleep(2.0)
        elif self.mode == "hang":
            time.sleep(12.0)  # longer than the smoke test's 10s timeout
        elif self.mode == "errors" and self._tick() % 3 == 0:
            return self._send_json(500, {"error": "internal server error"})
        else:
            time.sleep(0.05)  # normal "inference" latency, same as mock_server

        self._send_json(200, {
            "id": "chatcmpl-broken",
            "choices": [{"message": {"role": "assistant", "content": "pong"}}],
        })


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="slow",
                    choices=["slow", "errors", "flaky", "slowhealth", "hang"])
    args = ap.parse_args()
    BrokenAPI.mode = args.mode
    print(f"Broken API on http://localhost:{PORT} — mode: {args.mode}")
    HTTPServer(("localhost", PORT), BrokenAPI).serve_forever()


if __name__ == "__main__":
    main()
