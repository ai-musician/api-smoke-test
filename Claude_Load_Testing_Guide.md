# Load Testing, LLM API Testing & CI/CD — the complete drill set

The layer *above* the PR smoke test. Sanjeev's org builds "the world's fastest feature-rich inference service" — this drill set gives you hands-on fluency in exactly the numbers his team lives on: **saturation capacity, TTFT, tokens/sec**, plus the API contract and CI/CD story around them.

Files (all verified working — the outputs below are real runs):
- `Claude_llm_mock_server.py` — OpenAI-compatible mock inference server: 8 "inference slots" (capacity model → real saturation knee), SSE streaming, bearer auth, validation errors
- `Claude_load_test.py` — async closed-loop load generator: `fixed` / `sweep` / `stream` modes
- `Claude_api_contract_tests.py` — 11 pytest contract tests, self-contained (fixture boots the server)
- Below this layer: `smoke_test.py` (+ v2) for PR gating, `Claude_Perf_Failure_Drills.md` for failure reading

## The test pyramid you can now describe end-to-end

| Layer | Tool here | Question it answers | Where it runs |
|---|---|---|---|
| Contract | pytest suite | Is the API **wrong**? (codes, shapes, SSE framing) | every PR, seconds |
| Perf smoke | `smoke_test.py` | Did latency get **obviously** worse? (p95 vs budget) | every PR, seconds |
| Load | `Claude_load_test.py` | **How much** traffic before degradation? Where's the knee? | nightly/pre-release, dedicated hw |

## Drill A — capacity & the saturation knee

```bash
python3 Claude_llm_mock_server.py        # terminal 1 — prints its own math:
# 8 slots, service time ~0.38s/req -> saturation at ~21 rps
python3 Claude_load_test.py --mode sweep # terminal 2
```

Real output:
```
   c      rps    p50ms    p95ms    p99ms  err
   1      2.6      389      394      394    0
   2      5.1      390      392      392    0
   4     10.2      392      398      403    0
   8     20.0      400      411      414    0
  16     20.8      764      781     1137    0  <- knee
  32     20.7     1528     1549     2677    0
```

**Read it aloud until it's second nature:** throughput doubles with concurrency (2.6 → 5.1 → 10.2 → 20.0) while latency stays flat — the server has free slots. At c=8 every slot is busy: past that, rps is **pinned at ~20** and extra concurrency only buys queueing (p50 goes 400 → 764 → 1528ms — note it doubles with c, exactly queue math). **Capacity = the rps at the knee.** A latency SLO without a stated load is meaningless; the drill makes that visceral.

Practice: rerun with `--slots 4` on the server and *predict* the new knee before looking (~10.5 rps).

## Drill B — Little's law as a harness sanity check

```bash
python3 Claude_load_test.py --duration 10     # fixed mode, 8 workers
#   throughput: 20.0 rps   (n=120, errors=0)
#   latency:    p50=400ms p95=408ms p99=412ms
#   Little's law check: rps × mean latency = 8.0 ≈ 8 workers
```

L = λW (in-flight = throughput × latency). In a closed loop with N workers this must equal N — if it doesn't, your **harness** is broken (workers stalled, event loop blocked). Interviewers love hearing you validate the measuring instrument, not just the system.

**Closed vs open loop — know this cold:** closed loop (used here) = each worker waits for a response before sending again, so a slow server *reduces your offered load* — it self-throttles and understates user pain. Open loop = fixed arrival rate no matter what, which is how real traffic behaves and what exposes **coordinated omission** (the classic benchmark sin: your load generator politely waits out the server's stalls, then reports great latency for the requests it *didn't* send during them).

## Drill C — TTFT and tokens/sec (the Cerebras numbers)

```bash
python3 Claude_load_test.py --mode stream
#   TTFT:       p50=132ms p95=139ms (n=12, errors=0)
#   tokens/sec: p50=100 p5=97   (tok/s is a rate: the LOW tail is the bad tail)
```

- **TTFT** (time to first token) = queueing + prefill. It's what the user *feels* as responsiveness. Measured from the SSE stream itself: timestamp of the first `data:` chunk.
- **tokens/sec** = generation rate after the first token, `(n_tokens − 1) / (t_last − t_first)`. Note the fencepost: the first token *starts* the clock, it doesn't count toward the rate.
- End-to-end latency is the wrong headline for LLMs: a 4s response with 100ms TTFT feels fast; a 2s response with 2s TTFT feels broken.
- For a rate, **the low percentile is the bad tail** — report p5 tok/s, not p95.
- The throughput-vs-latency tension has an inference-specific face: **bigger batches raise total tokens/sec but hurt per-request TTFT**. Capacity planning for inference = choosing where on that curve to run. (This is Sanjeev's team's daily tradeoff — great question territory for them.)

## Drill D — API contract testing with pytest

```bash
pytest Claude_api_contract_tests.py -v     # 11 tests, ~1.2s
```

What to internalize per test group (read the file — it's commented for this):
- **Fixture boots the server subprocess and polls `/health`** — never a blind sleep; same pattern as the CI workflow. Session-scoped: one server for all tests.
- **Auth 401s** are parametrized over three ways to get auth wrong (absent / wrong scheme / bare scheme) — enumerate failure modes, don't just test the happy path. Bonus war story from writing this: httpx refuses to even *send* `"Bearer "` with a trailing space (illegal header value) — a reminder that clients enforce contracts too.
- **400s must name the offending field** — error *messages* are part of the contract; clients debug with them.
- **Response shape over status code** — a 200 with a missing `usage` block is still a broken API. Also asserts internal consistency (`total = prompt + completion`).
- **SSE framing is contract**: `text/event-stream` content type, every chunk parses as JSON, deltas concatenate to the full text, stream terminates with `data: [DONE]`. Streaming bugs (missing DONE, truncated chunks) are exactly what an inference-quality team gates on.
- **`/health` takes no inference slot** in the server — liveness probes must never queue behind traffic, or your orchestrator kills healthy-but-busy pods. Small detail, senior-sounding point.

## CI/CD — how the layers wire in

You already have the PR lane live (repo `ai-musician/music-api-smoke-test`, workflow green): contract + smoke on every push/PR, results as a PR comment. The load lane is **not** a PR gate — it's too slow and too noisy for shared runners. It runs on a schedule against dedicated hardware:

```yaml
name: nightly-load
on:
  schedule:
    - cron: "0 8 * * *"        # nightly; UTC
  workflow_dispatch:            # always keep a manual trigger
jobs:
  load:
    runs-on: [self-hosted, perf]   # dedicated box — never shared runners
    timeout-minutes: 30
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with: { python-version: "3.12", cache: pip }
      - run: pip install httpx pytest
      - run: pytest Claude_api_contract_tests.py     # contract first: no point loading a broken API
      - run: python Claude_llm_mock_server.py &      # real deployment URL in prod
      - run: python Claude_load_test.py --mode sweep --duration 30 | tee load_results.txt
      - uses: actions/upload-artifact@v4             # history -> trend -> tuned budgets
        with: { name: load-${{ github.run_id }}, path: load_results.txt }
```

The gating philosophy in one line: **PRs gate on cheap, deterministic checks (contract + smoke); capacity regressions are caught nightly by trend, on hardware you control.** Comparing tonight's knee to last week's knee is the regression signal — a single absolute threshold on a load test is how you get either false reds or a slowly boiling frog.

## Rapid-fire vocabulary check (cover the right column)

| Term | One-liner |
|---|---|
| Saturation knee | Where throughput flattens; past it, concurrency only buys queueing latency |
| Little's law | in-flight = throughput × latency; validates the harness in closed loop |
| Closed vs open loop | Workers wait vs fixed arrival rate; closed self-throttles and hides pain |
| Coordinated omission | Load gen skips sending during stalls, then reports flattering latency |
| TTFT | Queue + prefill; the responsiveness the user feels; from first SSE chunk |
| tokens/sec | Generation rate after first token; report the LOW tail (p5) |
| Batching tradeoff | Bigger batches: total tok/s up, per-request TTFT down worse |
| Contract test | Gates "the API got wrong"; perf gates "the API got slow" — need both |
| Warm-up exclusion | First requests pay connection/cache/JIT costs; measure steady state |
| Percentiles not averages | Averages hide multimodal tails; users live at p95 |
