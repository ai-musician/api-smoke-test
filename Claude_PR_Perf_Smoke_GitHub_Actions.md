# PR Perf Smoke Test — GitHub Actions Setup

Companion to `Claude_perf_smoke.py` (verified working: passes against a healthy API, exit 1 when an endpoint blows its budget). The goal: **every PR that touches API code gets a red check if it introduced an order-of-magnitude latency regression** — a blocking DB call on a hot path, an N+1 query, a dependency that got 10x slower.

## The workflow — `.github/workflows/perf-smoke.yml`

```yaml
name: perf-smoke

on:
  pull_request:
    paths:                      # only run when API code could have changed
      - "api/**"
      - "src/**"
      - "requirements*.txt"

jobs:
  perf-smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 10         # a hung server must fail the check, not hang CI

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt httpx

      - name: Start the API under test
        run: |
          uvicorn app.main:app --port 8000 &
          # wait for readiness — polling beats a blind sleep
          for i in $(seq 1 30); do
            curl -sf http://localhost:8000/health && exit 0
            sleep 1
          done
          echo "API never became healthy" && exit 1

      - name: Run perf smoke
        run: python tests/perf_smoke.py --base-url http://localhost:8000
        # non-zero exit -> red check -> merge blocked (with branch protection)
```

Then in **Settings → Branches → branch protection rule for `main`** add `perf-smoke` to required status checks — that's what turns "a script that exits 1" into "a merge that can't happen."

## Step-by-step, as you'd narrate it in the interview

1. **Trigger on `pull_request` with a `paths` filter** — perf smoke runs only when API code, source, or dependencies changed. No wasted CI minutes on README PRs.
2. **Boot the real service in the job** — same process as production (`uvicorn app.main:app`), then **poll `/health` for readiness** instead of sleeping; a blind `sleep 10` is either wasteful or flaky.
3. **Warm up, then measure** — first 5 requests discarded (connection pool, caches). Then ~30 sequential requests per endpoint, computing p50/p95 with nearest-rank.
4. **Gate on p95 vs. per-endpoint budgets with generous headroom** — shared CI runners are noisy neighbors, so budgets are set to catch 5–10x blowups, not 10% drifts. Tune budgets from a week of green-run history.
5. **Exit code is the gate** — script exits 1 → step fails → required status check goes red → merge blocked. Perf regressions block merge exactly like failing unit tests.

## The senior framing (say this part — it's what separates you)

- **"This is a smoke, not a load test."** Scope honesty: on shared runners you can't measure 10% regressions — that's the job of the full perf suite (ramp/soak, dedicated environment, baseline distributions). The smoke exists so an *obvious* mistake never survives to the expensive stage. Two layers, two purposes.
- **"Sequential on purpose."** We're measuring hot-path per-request latency, not throughput. Concurrency here would only add scheduler noise to a noisy runner.
- **"Percentiles, never averages"** — even at n=30, one 2-second outlier hides in a mean but shows in p95.
- **Upgrade path if asked "how would you make it stronger?"**: (1) store each main-branch run's results as an artifact and compare PR vs. main *on the same runner class* — relative comparison absorbs runner noise better than absolute budgets; (2) for LLM APIs, measure TTFT with a streaming request instead of total time; (3) nightly full perf suite on dedicated hardware with distribution-vs-baseline gates — the CI smoke is the tripwire, not the instrument.

## Local demo commands (what was verified)

```bash
# healthy server → all green, exit 0
python Claude_perf_smoke.py --base-url http://127.0.0.1:8123
# ok   GET /health: p50=1ms p95=1ms (budget 200ms, n=30)
# ok   POST /v1/chat/completions: p50=1ms p95=1ms (budget 1500ms, n=30)

# server with a 2s blocking call added to the POST hot path → exit 1
python Claude_perf_smoke.py --base-url http://127.0.0.1:8124
# ok   GET /health: p50=1ms p95=1ms (budget 200ms, n=30)
# FAIL POST /v1/chat/completions: p50=2008ms p95=2011ms (budget 1500ms, n=30)
```
