#!/usr/bin/env python3
"""Perf smoke v2 — the "how would you improve it?" answer, as working code.

Improvements over smoke_test.py (each is an interview talking point):

  1. READINESS POLL instead of a blind `sleep 2` — polls /health until the
     server answers. A blind sleep is either wasted time or a race.
  2. ERROR BUDGET instead of zero-tolerance — one blip on a shared CI
     runner shouldn't block a merge; a >5% error rate should. Tradeoff:
     you accept tiny real regressions to kill flaky-red-check fatigue.
  3. p99 next to p50/p95 — with n=30, p99 is basically the max; still worth
     printing because "max" is where deadlocks and GC pauses first appear.
  4. JSON RESULTS FILE (--json) — upload as a CI artifact and you get a
     latency trend over weeks of runs for free; that history is how you
     tune the budgets instead of guessing them.
  5. GITHUB STEP SUMMARY — writes a markdown table to $GITHUB_STEP_SUMMARY
     so results show on the run page without digging through logs.
  6. DISTINCT EXIT CODES — 1 = perf/error budget failed, 2 = server never
     came up. CI can tell "your code is slow" from "the harness is broken".
"""
import argparse
import asyncio
import json
import math
import os
import sys
import time

import httpx

ENDPOINTS = [
    # (method, path, json_body, p95_budget_ms)
    ("GET",  "/health", None, 200),
    ("POST", "/v1/chat/completions",
     {"model": "smoke", "messages": [{"role": "user", "content": "ping"}],
      "max_tokens": 8},
     1500),
]

WARMUP = 5
SAMPLES = 30
ERROR_BUDGET = 0.05   # fail only if >5% of measured requests error
TIMEOUT_S = 10.0


def percentile(vals, p):
    s = sorted(vals)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)]  # nearest-rank


async def wait_ready(client, attempts=15):
    """Poll /health until the server responds — replaces a blind sleep."""
    for _ in range(attempts):
        try:
            r = await client.get("/health", timeout=2.0)
            if r.status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        await asyncio.sleep(1)
    return False


async def measure(client, method, path, body):
    latencies, errors = [], 0
    for i in range(WARMUP + SAMPLES):
        t0 = time.perf_counter()
        try:
            r = await client.request(method, path, json=body)
            r.raise_for_status()
        except httpx.HTTPError:
            if i >= WARMUP:
                errors += 1
            continue
        if i >= WARMUP:
            latencies.append((time.perf_counter() - t0) * 1000)
    return latencies, errors


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url",
                    default=os.getenv("TARGET_URL", "http://localhost:8080"))
    ap.add_argument("--json", metavar="FILE",
                    help="also write results as JSON (CI artifact / trending)")
    args = ap.parse_args()

    results, failures = [], []
    async with httpx.AsyncClient(base_url=args.base_url,
                                 timeout=TIMEOUT_S) as client:
        if not await wait_ready(client):
            print(f"FATAL: server at {args.base_url} never became ready")
            sys.exit(2)   # harness problem, not a perf regression

        for method, path, body, budget_ms in ENDPOINTS:
            latencies, errors = await measure(client, method, path, body)
            error_rate = errors / SAMPLES
            row = {"endpoint": f"{method} {path}", "budget_ms": budget_ms,
                   "errors": errors, "error_rate": round(error_rate, 3)}

            if error_rate > ERROR_BUDGET:
                row.update(p50=None, p95=None, p99=None, status="FAIL")
                failures.append(f"{method} {path}: error rate "
                                f"{error_rate:.0%} > {ERROR_BUDGET:.0%} budget")
                print(f"FAIL {method} {path}: {errors}/{SAMPLES} errors "
                      f"({error_rate:.0%} > {ERROR_BUDGET:.0%} budget)")
            else:
                p50 = percentile(latencies, 50)
                p95 = percentile(latencies, 95)
                p99 = percentile(latencies, 99)
                ok = p95 <= budget_ms
                row.update(p50=round(p50), p95=round(p95), p99=round(p99),
                           status="ok" if ok else "FAIL")
                print(f"{'ok  ' if ok else 'FAIL'} {method} {path}: "
                      f"p50={p50:.0f}ms p95={p95:.0f}ms p99={p99:.0f}ms "
                      f"(budget {budget_ms}ms, n={len(latencies)}, "
                      f"errors={errors})")
                if not ok:
                    failures.append(f"{method} {path}: p95 {p95:.0f}ms "
                                    f"> budget {budget_ms}ms")
            results.append(row)

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"timestamp": time.time(), "base_url": args.base_url,
                       "results": results}, f, indent=2)

    # Surface results on the GitHub Actions run page, not buried in logs
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a") as f:
            f.write("## Perf smoke results\n\n"
                    "| Endpoint | p50 | p95 | p99 | Budget | Errors | Status |\n"
                    "|---|---|---|---|---|---|---|\n")
            ms = lambda v: f"{v}ms" if v is not None else "—"
            for r in results:
                f.write(f"| {r['endpoint']} | {ms(r['p50'])} | {ms(r['p95'])} | "
                        f"{ms(r['p99'])} | {r['budget_ms']}ms | "
                        f"{r['errors']} | {r['status']} |\n")

    if failures:
        print(f"\nPerf smoke FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nPerf smoke passed.")


if __name__ == "__main__":
    asyncio.run(main())
