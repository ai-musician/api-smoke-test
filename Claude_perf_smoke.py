#!/usr/bin/env python3
"""PR perf smoke test — fail fast on OBVIOUS latency/error regressions.

Philosophy (say this in the interview):
  - This is a SMOKE, not a load test: ~30 sequential requests per endpoint,
    runs in seconds on a shared CI runner. It exists to catch 5–10x
    regressions (a blocking DB call on a hot path, an N+1 query, a
    dependency that got slow) — NOT 10% drifts. Real perf runs happen
    on dedicated hardware with the full load suite.
  - Budgets have generous headroom because CI runners are noisy neighbors.
  - Warm-up requests are excluded (connection pool, caches, JIT).
  - Report percentiles, never averages; exit code gates the merge.
"""
import argparse
import asyncio
import math
import sys
import time

import httpx

# Per-endpoint latency budgets (ms). Generous: catch order-of-magnitude
# problems, not variance. Tune from a week of green-run history.
ENDPOINTS = [
    # (method, path, json_body, p95_budget_ms)
    ("GET",  "/health", None, 200),
    ("POST", "/v1/chat/completions",
     {"model": "smoke", "messages": [{"role": "user", "content": "ping"}],
      "max_tokens": 8},
     1500),
]

WARMUP = 5      # requests discarded before measuring
SAMPLES = 30    # measured requests per endpoint


def percentile(vals, p):
    s = sorted(vals)
    return s[max(0, math.ceil(p / 100 * len(s)) - 1)]  # nearest-rank


async def measure(client, method, path, body):
    """Sequential requests: we're measuring per-request hot-path latency,
    not throughput, so concurrency would only add scheduling noise."""
    latencies, errors = [], 0
    for i in range(WARMUP + SAMPLES):
        t0 = time.perf_counter()
        try:
            r = await client.request(method, path, json=body)
            r.raise_for_status()
        except httpx.HTTPError:
            errors += 1
            continue
        elapsed_ms = (time.perf_counter() - t0) * 1000
        if i >= WARMUP:
            latencies.append(elapsed_ms)
    return latencies, errors


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    args = ap.parse_args()

    failures = []
    async with httpx.AsyncClient(base_url=args.base_url, timeout=10.0) as client:
        for method, path, body, budget_ms in ENDPOINTS:
            latencies, errors = await measure(client, method, path, body)
            if errors:
                failures.append(f"{method} {path}: {errors} errors")
                print(f"FAIL {method} {path}: {errors} request errors")
                continue
            p50 = percentile(latencies, 50)
            p95 = percentile(latencies, 95)
            status = "ok  " if p95 <= budget_ms else "FAIL"
            print(f"{status} {method} {path}: "
                  f"p50={p50:.0f}ms p95={p95:.0f}ms (budget {budget_ms}ms, n={len(latencies)})")
            if p95 > budget_ms:
                failures.append(f"{method} {path}: p95 {p95:.0f}ms > budget {budget_ms}ms")

    if failures:
        print(f"\nPerf smoke FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)   # non-zero exit = red check on the PR
    print("\nPerf smoke passed.")


if __name__ == "__main__":
    asyncio.run(main())
