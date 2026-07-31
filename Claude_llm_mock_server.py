#!/usr/bin/env python3
"""Mock LLM inference server — the system under test for load + API drills.

Simulates an OpenAI-compatible inference endpoint with the three behaviors
that matter for performance testing an LLM API:

  1. CAPACITY MODEL — a semaphore of --slots concurrent "inference slots"
     (think: batch slots on the accelerator). Requests beyond capacity
     QUEUE. This is what creates a realistic saturation knee: throughput
     plateaus at slots/service_time while latency climbs with queue depth.
  2. STREAMING (SSE) — with "stream": true, tokens arrive as
     `data: {...}` chunks. Lets you measure TTFT (time to first token)
     and tokens/sec — the two numbers Cerebras markets on.
  3. REAL API CONTRACT — bearer auth (401), JSON validation (400),
     unknown routes (404) — so the pytest contract suite has teeth.

Timing model (defaults): TTFT 120ms ("prefill"), then 32 tokens at 8ms
each (~125 tok/s generation). /health does NOT take a slot — a liveness
probe must never queue behind inference traffic (say that in the interview).

Run:  python3 Claude_llm_mock_server.py            # port 8090, 8 slots
      python3 Claude_llm_mock_server.py --slots 4  # knee at lower rps
"""
import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TTFT_MS = 120     # simulated prefill time before the first token
TOKEN_MS = 8      # inter-token generation time (~125 tok/s)
TOKENS = 32       # tokens generated per completion

work_slots = None  # set in main() from --slots


class LLMMock(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep load-test output readable
        pass

    def _json(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code, etype, msg):
        # OpenAI-style error envelope
        self._json(code, {"error": {"type": etype, "message": msg}})

    def do_GET(self):
        if self.path == "/health":
            # No slot taken: liveness must not queue behind inference.
            return self._json(200, {"status": "ok"})
        self._error(404, "invalid_request_error", f"unknown route {self.path}")

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            return self._error(404, "invalid_request_error",
                               f"unknown route {self.path}")

        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or not auth.removeprefix("Bearer ").strip():
            return self._error(401, "authentication_error",
                               "missing or malformed bearer token")

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            return self._error(400, "invalid_request_error",
                               "request body is not valid JSON")
        for field in ("model", "messages"):
            if field not in body:
                return self._error(400, "invalid_request_error",
                                   f"missing required field: {field}")

        with work_slots:               # queue here when saturated
            time.sleep(TTFT_MS / 1000) # "prefill"
            if body.get("stream"):
                self._stream_tokens(body)
            else:
                time.sleep(TOKENS * TOKEN_MS / 1000)  # "generation"
                self._json(200, {
                    "id": "chatcmpl-mock", "object": "chat.completion",
                    "model": body["model"],
                    "choices": [{"index": 0, "finish_reason": "stop",
                                 "message": {"role": "assistant",
                                             "content": "tok " * TOKENS}}],
                    "usage": {"prompt_tokens": 8,
                              "completion_tokens": TOKENS,
                              "total_tokens": 8 + TOKENS},
                })

    def _stream_tokens(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        for i in range(TOKENS):
            chunk = {"id": "chatcmpl-mock", "object": "chat.completion.chunk",
                     "model": body["model"],
                     "choices": [{"index": 0,
                                  "delta": {"content": f"tok{i} "}}]}
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode())
            self.wfile.flush()         # first token leaves NOW -> real TTFT
            time.sleep(TOKEN_MS / 1000)
        self.wfile.write(b"data: [DONE]\n\n")


def main():
    global work_slots
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8090)
    ap.add_argument("--slots", type=int, default=8,
                    help="concurrent inference slots (capacity model)")
    args = ap.parse_args()
    work_slots = threading.Semaphore(args.slots)
    service_time = (TTFT_MS + TOKENS * TOKEN_MS) / 1000
    print(f"Mock LLM server on http://localhost:{args.port} — "
          f"{args.slots} slots, service time ~{service_time:.2f}s/req "
          f"-> saturation at ~{args.slots / service_time:.0f} rps")
    ThreadingHTTPServer(("localhost", args.port), LLMMock).serve_forever()


if __name__ == "__main__":
    main()
