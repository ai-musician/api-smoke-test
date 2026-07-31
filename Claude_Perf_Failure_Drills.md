# Perf Smoke Failure Drills — practice before Tuesday

Gemini's setup (`smoke_test.py` + `mock_server.py` + the GitHub Actions workflow) only ever showed you the **green** path. Interviews live on the red path: *"the check failed — what do you do?"* These drills make you fluent at reading failures and explaining what each one means in production.

Files:
- `Claude_broken_api.py` — server with 5 selectable, deterministic failure modes
- `Claude_smoke_test_v2.py` — improved smoke test (the "how would you make it better?" answer)
- Companions you already have: `Claude_perf_smoke.py`, `Claude_dummy_api.py`, `Claude_PR_Perf_Smoke_GitHub_Actions.md`

## How to run a drill

Terminal 1 (pick a mode), terminal 2 (run the test), then **read the output before looking at the answer below**:

```bash
python3 Claude_broken_api.py --mode slow      # terminal 1
python3 smoke_test.py                         # terminal 2 — exit code: echo $?
```

Stop the server (Ctrl+C) between drills. Everything is deterministic — you'll get the same output every run.

---

## Drill 1 — `--mode slow` (the classic regression)

**Expected output:**
```
ok   GET /health: p50=3ms p95=4ms (budget 200ms, n=30)
FAIL POST /v1/chat/completions: p50=2010ms p95=2015ms (budget 1500ms, n=30)
```

**What it simulates:** a synchronous DB/HTTP call landed on the async hot path, or an N+1 query. p50 ≈ p95 ≈ 2s — the *whole distribution* shifted, so this is deterministic code on every request, not an intermittent effect.

**Say in the interview:** "p50 and p95 moved together, so every request pays the cost — I'd diff the PR for new blocking calls on that endpoint's path, not look at infra."

## Drill 2 — `--mode errors` (latency is fine, correctness isn't)

**Expected output:**
```
ok   GET /health: p50=1ms p95=2ms (budget 200ms, n=30)
FAIL POST /v1/chat/completions: 11 request errors
```

**What it simulates:** bad deploy, dependency down, race condition. Note the trap: if you only gated on latency, this would pass — 500s are often *faster* than real responses. That's why the smoke gates on errors too.

**Spot-the-difference exercise:** run `Claude_smoke_test_v2.py` against the same server and it reports `10/30 errors` instead of 11 — v1 counts errors that happen during warm-up, v2 excludes them. Which is right? (Arguable — but v1 is *inconsistent*: it excludes warm-up latencies while counting warm-up errors. Consistency is the actual bug.)

**Say in the interview:** "A perf gate that ignores error rate can be gamed by failing fast. I always gate on both."

## Drill 3 — `--mode flaky` (why percentiles, never averages)

**Expected output:** both endpoints fail on p95 while p50 looks great:
```
FAIL GET /health: p50=3ms p95=3009ms (budget 200ms, n=30)
FAIL POST /v1/chat/completions: p50=60ms p95=3066ms (budget 1500ms, n=30)
```
(Both endpoints failing at once is itself a diagnostic clue — the +3s hits every 8th request *regardless of endpoint*, i.e. it's process-wide, like a GC pause, not endpoint code.)

**What it simulates:** GC pauses, lock contention, noisy CI neighbor — 1 in 8 requests takes +3s. The **average** here (~430ms) would look acceptable; the tail tells the truth. Also your talking point on *flaky CI*: if this were noise from the runner rather than the code, you'd see it across a week of green-run history — which is exactly why you keep run artifacts and tune budgets from history.

**Say in the interview:** "Averages hide multimodal distributions. One slow request in eight is invisible at p50 and screaming at p95."

## Drill 4 — `--mode slowhealth` (suspect the platform, not the endpoint)

**Expected output:**
```
FAIL GET /health: p50=410ms p95=412ms (budget 200ms, n=30)
ok   POST /v1/chat/completions: p50=60ms p95=62ms (budget 1500ms, n=30)
```

**What it simulates:** when even the trivial no-work endpoint is slow, the endpoint's own code is innocent — suspect the layer under it: blocked event loop, CPU throttling, swapping, container limits.

**Say in the interview:** "/health is my control group. If the control regresses, I look at the platform before the code."

## Drill 5 — `--mode hang` (why the client timeout exists)

⚠️ Each POST burns the full 10s client timeout — watch 2–3 requests fail, then Ctrl+C both terminals. Don't wait for the full run (~6 min).

**What it simulates:** deadlock or stuck upstream connection. Two layers of defense, and you should name both: the **client timeout** (10s in `smoke_test.py`) turns a hang into a countable error, and the workflow's **`timeout-minutes`** kills the job if even that fails. Without them, a hung server = a CI job that spins until GitHub's 6-hour limit.

---

## The "how would you improve it?" answer — `Claude_smoke_test_v2.py`

Run it against the healthy server to see the new output format:

```bash
python3 mock_server.py                          # terminal 1
python3 Claude_smoke_test_v2.py --json out.json # terminal 2
```

Six upgrades over Gemini's version, each with its *why* (the docstring in the file has the full wording):

1. **Readiness poll instead of `sleep 2`** — a blind sleep is either wasted time or a race on a slow runner. Poll `/health` until it answers.
2. **Error budget (5%) instead of zero-tolerance** — one network blip on a shared runner shouldn't block a merge; a real error rate should. Know the tradeoff you accepted: less sensitivity for less false-red fatigue.
3. **p99 alongside p50/p95** — with n=30 it's basically the max, but max is where deadlocks first show up.
4. **`--json` results file** — upload as a CI artifact → free latency trend over weeks → budgets tuned from history instead of guessed.
5. **`$GITHUB_STEP_SUMMARY` markdown table** — results on the run page, not buried in logs.
6. **Distinct exit codes** — `1` = perf regression, `2` = server never came up. "Your code is slow" and "the harness broke" should be distinguishable at a glance.

Workflow-level improvements to mention (some already in `Claude_PR_Perf_Smoke_GitHub_Actions.md`):
- `timeout-minutes: 10` on the job (hang protection)
- readiness poll in the workflow step, not `sleep 2`
- `actions/upload-artifact` for the JSON results
- `concurrency` + `cancel-in-progress` so force-pushes don't queue stale runs
- pip caching in `setup-python` (`cache: pip`)

## The one paragraph to internalize

> This is a smoke, not a load test. ~30 sequential requests, seconds on a shared runner, generous budgets — it exists to catch **order-of-magnitude** regressions at PR time: the blocking call, the N+1, the dependency that got 10x slower. It gates on **p95 and error rate**, never averages. Real perf work — throughput, concurrency scaling, saturation — happens on dedicated hardware with a real load suite. The smoke's job is to make the obvious mistake impossible to merge.
