#!/usr/bin/env python3
"""Async load generator for the mock LLM server — a LOAD test, not a smoke.

Where smoke_test.py asks "did one request get obviously slower?", this asks
the load-testing questions: "how much traffic before latency degrades, and
what does saturation look like?" Concepts baked in (each is interview vocab):

  CLOSED LOOP: N workers, each waits for a response before sending the next
    request. Offered load adapts to the server — simple, but it HIDES
    queueing pain (a slow server slows your workers, so you offer less).
    Open-loop (fixed arrival rate regardless of responses) is what exposes
    coordinated omission; know the distinction and name it.
  LITTLE'S LAW: L = λW (in-flight = throughput × latency). In a closed loop
    with N workers, N ≈ rps × mean_latency always holds — printed after each
    run so you can sanity-check the harness itself.
  SATURATION KNEE (sweep mode): as concurrency doubles, throughput doubles —
    until the server's slots are full. Past the knee, throughput is FLAT and
    added concurrency only buys queueing latency. Capacity = where the knee is.
  TTFT & TOKENS/SEC (stream mode): for LLM inference, end-to-end latency is
    the wrong headline number. Users feel TTFT (prefill + queue) and
    tokens/sec (generation rate). Measured from the SSE stream itself.

Run (server first: python3 Claude_llm_mock_server.py):
  python3 Claude_load_test.py                          # fixed: 8 workers, 10s
  python3 Claude_load_test.py --mode sweep             # find the knee
  python3 Claude_load_test.py --mode stream            # TTFT + tok/s
"""
import argparse
import asyncio
import json
import math
import sys
import time

import httpx

BODY = {"model": "smoke", "stream": False,
        "messages": [{"role": "user", "content": "ping"}]}
HEADERS = {"Authorization": "Bearer sk-test"}


def pct(vals, p):
    s = sorted(vals)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)] if s else float("nan")


async def closed_loop_worker(client, stop_at, lats, errs):
    """One closed-loop user: request, wait for response, repeat."""
    while time.monotonic() < stop_at:
        t0 = time.perf_counter()
        try:
            r = await client.post("/v1/chat/completions", json=BODY)
            r.raise_for_status()
            lats.append((time.perf_counter() - t0) * 1000)
        except httpx.HTTPError:
            errs.append(1)


async def run_stage(client, concurrency, duration):
    lats, errs = [], []
    stop_at = time.monotonic() + duration
    t0 = time.monotonic()
    await asyncio.gather(*[closed_loop_worker(client, stop_at, lats, errs)
                           for _ in range(concurrency)])
    wall = time.monotonic() - t0
    return {"c": concurrency, "rps": len(lats) / wall,
            "p50": pct(lats, 50), "p95": pct(lats, 95), "p99": pct(lats, 99),
            "mean": sum(lats) / len(lats) if lats else float("nan"),
            "n": len(lats), "errors": len(errs)}


async def mode_fixed(client, args):
    print(f"Closed-loop: {args.concurrency} workers for {args.duration}s ...")
    r = await run_stage(client, args.concurrency, args.duration)
    print(f"  throughput: {r['rps']:.1f} rps   (n={r['n']}, errors={r['errors']})")
    print(f"  latency:    p50={r['p50']:.0f}ms p95={r['p95']:.0f}ms "
          f"p99={r['p99']:.0f}ms")
    inflight = r["rps"] * r["mean"] / 1000
    print(f"  Little's law check: rps × mean latency = {inflight:.1f} "
          f"≈ {args.concurrency} workers (harness sanity)")
    return r["errors"] == 0


async def mode_sweep(client, args):
    print(f"Concurrency sweep, {args.duration}s per stage — watch for the knee:")
    print(f"  {'c':>4} {'rps':>8} {'p50ms':>8} {'p95ms':>8} {'p99ms':>8} {'err':>4}")
    prev_rps = None
    for c in [1, 2, 4, 8, 16, 32]:
        r = await run_stage(client, c, args.duration)
        note = ""
        if prev_rps and r["rps"] < prev_rps * 1.3:
            note = "  <- knee: throughput flat, latency now buys nothing"
        print(f"  {r['c']:>4} {r['rps']:>8.1f} {r['p50']:>8.0f} "
              f"{r['p95']:>8.0f} {r['p99']:>8.0f} {r['errors']:>4}{note}")
        prev_rps = r["rps"]
    print("\nReading it: capacity is the rps where the curve flattens; past it,"
          "\nextra concurrency only grows the queue (p95 climbs, rps doesn't).")
    return True


async def stream_once(client, ttfts, tps_list, errs):
    """One streaming request: TTFT = first SSE data line; tok/s from the rest."""
    t0 = time.perf_counter()
    t_first, n_tokens = None, 0
    try:
        async with client.stream("POST", "/v1/chat/completions",
                                 json={**BODY, "stream": True}) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                if line == "data: [DONE]":
                    break
                if t_first is None:
                    t_first = time.perf_counter()
                n_tokens += 1
        t_end = time.perf_counter()
        if t_first and n_tokens > 1:
            ttfts.append((t_first - t0) * 1000)
            tps_list.append((n_tokens - 1) / (t_end - t_first))
    except httpx.HTTPError:
        errs.append(1)


async def mode_stream(client, args):
    print(f"Streaming: {args.concurrency} workers × {args.requests} requests each ...")
    ttfts, tps_list, errs = [], [], []

    async def worker():
        for _ in range(args.requests):
            await stream_once(client, ttfts, tps_list, errs)

    await asyncio.gather(*[worker() for _ in range(args.concurrency)])
    if not ttfts:
        print("  no successful streams"); return False
    print(f"  TTFT:       p50={pct(ttfts, 50):.0f}ms p95={pct(ttfts, 95):.0f}ms "
          f"(n={len(ttfts)}, errors={len(errs)})")
    print(f"  tokens/sec: p50={pct(tps_list, 50):.0f} p5={pct(tps_list, 5):.0f}"
          f"  (tok/s is a rate: the LOW tail is the bad tail, so report p5)")
    print("  Why not just end-to-end latency? A 4s response with 100ms TTFT"
          "\n  feels fast; a 2s response with 2s TTFT feels broken.")
    return len(errs) == 0


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8090")
    ap.add_argument("--mode", default="fixed",
                    choices=["fixed", "sweep", "stream"])
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--duration", type=float, default=10.0,
                    help="seconds per stage (fixed/sweep)")
    ap.add_argument("--requests", type=int, default=5,
                    help="requests per worker (stream mode)")
    args = ap.parse_args()

    async with httpx.AsyncClient(base_url=args.base_url, headers=HEADERS,
                                 timeout=30.0) as client:
        try:
            r = await client.get("/health", timeout=2.0)
            r.raise_for_status()
        except httpx.HTTPError:
            print(f"FATAL: no server at {args.base_url} "
                  f"(start Claude_llm_mock_server.py first)")
            sys.exit(2)
        ok = await {"fixed": mode_fixed, "sweep": mode_sweep,
                    "stream": mode_stream}[args.mode](client, args)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
