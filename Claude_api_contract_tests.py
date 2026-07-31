#!/usr/bin/env python3
"""API contract tests for the mock LLM server — pytest practice.

Run:  pytest Claude_api_contract_tests.py -v

The suite is self-contained: a session-scoped fixture boots the server as a
subprocess, polls /health until ready (never a blind sleep), and tears it
down at the end — the same pattern a CI job uses.

What "contract testing" means here (interview framing): the API's PROMISES —
status codes, error envelope shape, auth behavior, streaming framing — are
what clients program against. Perf tests catch "it got slow"; contract tests
catch "it got wrong". You need both gates on a PR.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

PORT = 8091  # own port: never collide with a manually-run server on 8090
BASE = f"http://localhost:{PORT}"
AUTH = {"Authorization": "Bearer sk-test"}
VALID_BODY = {"model": "smoke",
              "messages": [{"role": "user", "content": "ping"}]}


@pytest.fixture(scope="session")
def server():
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).parent / "Claude_llm_mock_server.py"),
         "--port", str(PORT)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):                      # readiness poll, max ~5s
            try:
                if httpx.get(f"{BASE}/health", timeout=0.5).status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.1)
        else:
            pytest.fail("mock server never became ready")
        yield BASE
    finally:
        proc.terminate()
        proc.wait(timeout=5)


# --- liveness ---------------------------------------------------------------

def test_health_returns_200_ok(server):
    r = httpx.get(f"{server}/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# --- auth: 401s must come back FAST and with a machine-readable envelope ----

@pytest.mark.parametrize("headers", [
    {},                                      # no header at all
    {"Authorization": "sk-test"},            # missing "Bearer " scheme
    # (fun fact found writing this: httpx refuses to SEND "Bearer " with a
    # trailing space — illegal header value — so the empty-token case is
    # exercised as a bare scheme with no token instead)
    {"Authorization": "Bearer"},             # scheme but no token
], ids=["absent", "wrong-scheme", "bare-scheme"])
def test_missing_or_malformed_auth_is_401(server, headers):
    r = httpx.post(f"{server}/v1/chat/completions",
                   headers=headers, json=VALID_BODY)
    assert r.status_code == 401
    assert r.json()["error"]["type"] == "authentication_error"


# --- request validation: 400 with a message that names the problem ----------

def test_non_json_body_is_400(server):
    r = httpx.post(f"{server}/v1/chat/completions", headers=AUTH,
                   content=b"not json{", timeout=5)
    assert r.status_code == 400
    assert "JSON" in r.json()["error"]["message"]


@pytest.mark.parametrize("missing", ["model", "messages"])
def test_missing_required_field_is_400_and_names_the_field(server, missing):
    body = {k: v for k, v in VALID_BODY.items() if k != missing}
    r = httpx.post(f"{server}/v1/chat/completions", headers=AUTH, json=body)
    assert r.status_code == 400
    assert missing in r.json()["error"]["message"]


def test_unknown_route_is_404(server):
    r = httpx.post(f"{server}/v1/embeddings", headers=AUTH, json=VALID_BODY)
    assert r.status_code == 404


# --- happy path: response SHAPE is the contract, not just the 200 -----------

def test_completion_response_shape(server):
    r = httpx.post(f"{server}/v1/chat/completions", headers=AUTH,
                   json=VALID_BODY, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["object"] == "chat.completion"
    assert data["model"] == VALID_BODY["model"]      # echoes requested model
    msg = data["choices"][0]["message"]
    assert msg["role"] == "assistant" and msg["content"]
    usage = data["usage"]
    assert usage["total_tokens"] == (usage["prompt_tokens"]
                                     + usage["completion_tokens"])


# --- streaming: SSE framing is part of the contract too ---------------------

def test_stream_is_well_formed_sse_and_terminates_with_done(server):
    chunks, saw_done = [], False
    with httpx.stream("POST", f"{server}/v1/chat/completions", headers=AUTH,
                      json={**VALID_BODY, "stream": True}, timeout=15) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        for line in r.iter_lines():
            if not line.startswith("data: "):
                continue
            if line == "data: [DONE]":
                saw_done = True
                break
            chunks.append(json.loads(line.removeprefix("data: ")))
    assert saw_done, "stream must terminate with data: [DONE]"
    assert len(chunks) > 1
    assert all(c["object"] == "chat.completion.chunk" for c in chunks)
    text = "".join(c["choices"][0]["delta"].get("content", "") for c in chunks)
    assert text.strip(), "concatenated deltas must form the completion text"


def test_stream_first_token_beats_full_response(server):
    """The point of streaming: TTFT << end-to-end. Measure both, assert it."""
    t0 = time.perf_counter()
    ttft = None
    with httpx.stream("POST", f"{server}/v1/chat/completions", headers=AUTH,
                      json={**VALID_BODY, "stream": True}, timeout=15) as r:
        for line in r.iter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                ttft = time.perf_counter() - t0
                break
    assert ttft is not None
    # Full generation is ~0.4s (32 tok × 8ms + 120ms prefill); the first
    # token must arrive well before that or streaming buys the user nothing.
    assert ttft < 0.3, f"TTFT {ttft:.2f}s — first token should beat generation"
