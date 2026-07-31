https://www.linkedin.com/jobs/view/inference-ml-api-sdet-at-cerebras-4436348819/
# Master Interview Q&A List — Cerebras HM Screen (combined, checkbox edition)

**Merged 2026-07-30 from 3 sources:** `Claude_HM_Screen_Prep_Plan_Sanjeev_Gadgil.md` (behavioral/pitch), `Claude_Performance_Testing_QA.md`, `Claude_API_Testing_QA.md`. Each item = one question with its **bullet skeleton** — rehearse until you can expand each skeleton to 60–90 seconds aloud. Full scripted answers stay in the source files (referenced as *Perf Q#* / *API Q#*).

**Interview:** Tue Aug 4 · 45 min · Teams + HackerRank pad · **Sanjeev Gadgil**, Director, Inference Service Quality — career validation engineer (AMD SeaMicro → ChargePoint QA-lab-from-scratch → Pavilion perf tools → Cerebras, 5 promotions). He built perf tools and simulators himself: expect deep follow-ups, respect for hands-on stories, zero patience for hand-waving.

**Golden rule for the screen:** every answer should quietly signal one of: **ownership, hands-on depth, or judgment under ambiguity**. Those are the three things a validation-engineer-turned-director filters for.

Legend: ⭐ = highest probability · 🎯 = maps directly to Sanjeev's own background

---

## 1. Pitch & positioning (rehearse first)

### The 90-second pitch (say it aloud until fluid, not memorized-stiff)

- [ ] > "I've spent 6 years at Netskope as a Senior SDET owning quality for a distributed, Kubernetes-based security platform — release sign-off, on-call triage, compliance validation, and building E2E automation and test environments from scratch. In the last two years I went deep on GenAI: I solo-built a production RAG assistant on Claude and Pinecone, and — the part most relevant to you — I had to invent the testing methodology for it, because probabilistic systems break deterministic pass/fail testing. I built a regression gate based on score distributions and per-cohort thresholds. I also built an async load-testing CLI for latency/reliability validation. Cerebras is the place where those two threads — large-scale distributed systems quality and ML/LLM evaluation — come together, on the fastest inference stack in the industry."

### The three proof pillars (rehearse a 2–3 min STAR story for each)

- [ ] **Pillar 1 — Testing non-deterministic ML systems** ⭐ — the RAG test suite: score distributions, per-cohort thresholds, pre-release regression gate, confidence-threshold abstention for hallucination. *This is THE story. Maps directly to "evaluating accuracy at scale" and "rigorous evaluation methodologies."*
- [ ] **Pillar 2 — Distributed-systems debugging & release ownership** — K8s on-call triage (crash loops, Ceph instability, PVC failures), classifying product vs. deploy vs. environment, release sign-off with risk-based judgment. *Maps to "debugging complex issues across distributed, scaled-out deployments" and "risk-based testing priorities."*
- [ ] **Pillar 3 — Building frameworks/tools from the ground up** 🎯 — VPE E2E automation, high-fidelity customer-mirroring environments, the asyncio load-test CLI with constant/ramp/spike/soak profiles and CI pass/fail thresholds. *Maps to "design and build reusable test frameworks from the ground up" — and to Sanjeev's own Pavilion perf-tooling background.*
  - **Concrete CI-gating example (be able to whiteboard or code it live):** a PR perf smoke test — every PR touching API code boots the real service in GitHub Actions, polls `/health` for readiness, sends ~30 sequential requests per endpoint after 5 warm-ups, gates **p95 against per-endpoint budgets with generous headroom**, and exits non-zero → red required check → merge blocked. Catches order-of-magnitude mistakes (blocking DB call on a hot path, dependency gone 10x slower) before they reach the expensive stage. Key framing: **"this is a smoke, not a load test"** — shared runners can't measure 10% drift; the full ramp/soak suite on dedicated hardware does that nightly. Two layers, two purposes. Upgrade path if probed: PR-vs-main relative comparison via stored artifacts (absorbs runner noise), TTFT via streaming request for LLM APIs. Working code + workflow YAML: `Claude_perf_smoke.py` + `Claude_PR_Perf_Smoke_GitHub_Actions.md` (both verified: green on healthy API, exit 1 on a simulated 2s hot-path regression).

### Gaps to pre-empt (don't wait to be caught)

- [ ] **No direct LLM inference-serving test experience at scale.** Counter: you've tested the two halves separately (distributed infra quality + LLM evaluation) and built LLM eval methodology solo with zero playbook — which is exactly the situation on a fast-scaling team.
- [ ] **Mentorship is a JD requirement** — prepare one concrete example: onboarding/mentoring junior SDETs, driving methodology adoption, or a cross-team quality initiative you led.
- [ ] **Hardware familiarity is preferred-only.** Know the one-liner: wafer-scale engine, all model weights in on-chip SRAM → no memory-bandwidth bottleneck → extreme tokens/sec. **Don't fake depth.**

## 2. Behavioral questions

- [ ] ⭐ **"Why Cerebras? Why quality engineering rather than dev?"** — own the quality identity confidently; he did (career validation engineer by choice). Full answer, three reasons escalating (~60–75 sec):
  > "**First, the technical problem**: you're serving frontier models faster than anyone, on hardware nobody else has, behind an OpenAI-compatible contract customers just expect to work — correctness, model quality, and extreme performance collide in one API surface; the most interesting quality problem in the industry right now.
  > **Second, it's where my two threads converge**: six years of distributed-systems quality at Netskope, two years building LLM eval methodology from scratch. Most roles use one thread or the other — testing an inference API is the one job that needs both: distributed-systems testing where the payload is a model.
  > **Third — the real one — stakes and timing**: with the OpenAI partnership, your release confidence is load-bearing for a big part of the industry, and the methodology for testing systems like this is still being invented. I'd rather help write that playbook than inherit a finished one — that's what I had to do solo for my RAG project, and I want to do it on a team that lives it."
  - *Companion ("why QE rather than dev?")*: "I've built product code — the RAG assistant is proof I can. But what I love is the moment a system becomes *trustworthy* — designing the test that catches the failure nobody imagined. I chose quality the way you choose a craft, not as a waiting room for a dev role."
  - *Avoid:* leading with speed/valuation hype; citing learning/career growth as the driver (give, not get).
- [ ] **"Shipping under deadline when quality was at risk"** — release sign-off story: how you framed risk to leadership, blast radius × likelihood, what shipped/held.
- [ ] **"Cross-functional quality initiative you drove"** — OPS/Engineering/WebUI/Proxy partnership, or AI reporting-tool adoption.
- [ ] **"How have you mentored junior engineers?"** — the prepared story from §1.
- [ ] **"Hardest bug you've root-caused in a distributed system"** 🎯 — pick the K8s/Ceph story you remember deepest: symptom → hypotheses → evidence narrowing (events, logs, node health, PVC state) → root cause → **systemic fix, not just the patch**. He WILL probe details.
- [ ] **Ownership/ambiguity probes** (hypergrowth culture): have one "priorities shifted mid-release and I re-planned" example.
- [ ] **"Why do you want to change jobs?"** — pull, not push (~45 sec):
  > "It's a pull, not a push — I've had six good years at Netskope: grew from owning test areas to owning release sign-off, built the E2E framework and test environments from scratch, and in the last two years built a production RAG assistant with its own evaluation methodology. That project changed what I want to do full-time: ML quality. But at Netskope that's structurally a side thread — the core product is network security. My best work now comes from a team whose *entire charter* is ML API quality, at the hardest scale available. If Netskope had this team, I'd be applying internally."
  - *Never mention:* comp, boredom, managers, layoffs. If probed: "that wasn't a factor — the pull was the problem space."
- [ ] **"What should your current company improve?"** — only criticize what you personally attacked (~45 sec):
  > "A real one, because I worked on it. Netskope's ML team does rigorous model validation with their own eval datasets — that part is solid. The gap is that model quality and product quality live in two separate worlds: the ML team tests the model, the QA org tests the feature around it deterministically, but at release sign-off nothing connects them — the model's eval results aren't part of the quality gate, and QA doesn't share golden datasets or statistical thresholds for the feature's end-to-end AI behavior. So an AI-backed feature can pass QA while its output quality regresses, and no gate catches it. I bridged that for my own project — built the eval methodology directly into the release gate — but that bridge exists because I built it, not because it's the org's standard. What I'd improve: treat AI quality as one discipline spanning ML and QA, not two silos. And it's part of why this role appeals — your team is exactly that idea made into a charter: model quality and API quality under one owner."
  - *Backup if pushed for more* (give ONE, then stop): "perf testing owned per-team rather than as a central practice — I'd centralize the tooling."
  - *Rule for both:* warm about Netskope throughout; one critique wrapped in respect; criticism of methodology, never of people.

## 3. Test strategy & design ⭐ (highest-probability technical thread)

- [ ] ⭐ **"Design a test strategy for a new model launch on our inference API"** — layer it: contract/schema conformance → functional (streaming, tool calls, long context, edge tokens) → quality evals vs. golden baselines w/ statistical thresholds → perf (TTFT, tokens/sec, p99 under concurrency) → chaos/failover multi-region → canary + prod monitoring. Say "coverage vs. risk trade-off" explicitly.
- [ ] ⭐ **"How do you test something non-deterministic?"** — RAG regression-gate story: distributions not point assertions, cohort thresholds, temperature=0 where possible but don't rely on it, semantic-similarity scoring, LLM-as-judge with calibration.
- [ ] **"How do you decide what NOT to test?"** — risk-based prioritization from release sign-off: blast radius × likelihood.
- [ ] **"200 OK but customers say responses got 'worse'"** (*API Q13*) — the gap between API correctness and model quality = why this team exists. Golden datasets, scored evals as distributions, release-over-release comparison, wired into the gate; plus sampled live-traffic evals + feedback→known-gaps pipeline (you built exactly this).

### Possible HackerRank live coding (be ready even if it ends up talk-only)

- [ ] Expect **practical SDET Python, not LeetCode-hard**: parse/aggregate a log file or JSON API responses · compute latency percentiles from a stream of records · rate-limiter or retry-with-backoff logic · write a small test class for a given function · async requests with bounded concurrency (`asyncio.Semaphore`).
- [ ] Practice typing clean Python **in a bare pad**: dataclasses, collections (`defaultdict`/`Counter`), sorting with keys, generator-based streaming, pytest-style structure, **edge cases stated out loud**.
- [ ] Full problem list, reference solutions, and drills: `Claude_Master_Coding_Practice_List.md` (Tiers 5–6 are exactly these prompts) + `Claude_pytest_drill.py`.

## 4. Performance testing — your own work (he digs here first 🎯)

- [ ] ⭐ **"Walk me through a perf test you designed end-to-end"** (*Perf Q1*) — Callhome Gateway: started from SLOs not tools (**500 rps/node, <20ms added latency, 99.9% success, CPU<70%**) → layered 16 TCs: baseline / TLS-mTLS handshake cost / session paths / multi-GB uploads / 8-hr soak / node-kill failover / Slowloris. Pride details: **cache-busting noise injection** + explicit scoping (backend failures don't count against gateway).
- [ ] **"What did you find?"** — config file re-read from disk per request; invisible at low load, dominant at high load; found via soak + profiling (CPU/iowait growing faster than request rate).
- [ ] 🎯 **"Why build your own load tool instead of Locust/k6/JMeter?"** (*Perf Q2*) — asyncio, semaphore-bounded concurrency, histograms → real percentiles, 4 profiles, CI pass/fail exit codes. Why build: mTLS cert workflows + cache-busting payloads + CI thresholds made off-the-shelf painful; "deliberate trade-off, not a default — I'd still reach for k6 when the standard model fits."
- [ ] **Follow-up: "How do you know the load generator isn't the bottleneck?"** — monitor generator CPU/sockets/event-loop lag; scale generators horizontally and check target scales with offered load; echo-server run to find the harness's own ceiling. "If the client saturates, the server numbers are fiction."
- [ ] **"How do perf tests reliably gate CI?"** (*Perf Q3*) — dedicated isolated env; warm-up excluded; thresholds with headroom over SLO; trend-vs-baseline not absolute numbers; versioned fixed workload.
- [ ] **"How did you stop the system cheating?"** (*Perf Q4*) — payload noise defeats caching; know every short-circuit layer (CDN, proxy cache, DB cache) and decide in/out deliberately. **Bridge: "same principle as prompt/KV caching in LLM benchmarks."**

## 5. Performance fundamentals (warm-up probes)

- [ ] **"Why percentiles, not averages?"** (*Perf Q5*) — averages hide the hurt users; 100-call session hits p99 ~63% of the time; report p50/p95/p99 + max/error rate; **"percentiles can't be averaged — merge raw histograms."**
- [ ] **"Throughput vs. latency relationship?"** (*Perf Q6*) — flat while headroom, hockey-stick at the knee (queueing theory); **Little's Law: concurrency = throughput × latency** — used to sanity-check the harness; operate where p99 still meets SLO, not at max throughput.
- [ ] **"Open vs. closed-loop? Coordinated omission?"** (*Perf Q7*) — closed-loop self-throttles when server stalls → under-reports; open-loop = fixed arrival schedule; mitigate via open/hybrid or measuring from *intended* send time (HdrHistogram). *Knowing this by name is a senior signal to a perf-tools builder.*
- [ ] **"What does each load profile tell you?"** (*Perf Q8*) — constant = SLO validation; ramp = find the knee; spike = elasticity + recovery time; soak = leaks/degradation only time reveals.
- [ ] **"How do you separate client/network/server latency?"** (*Perf Q9*) — measure at multiple points and subtract; Server-Timing; "added gateway latency" = through-gateway minus backend time. "Never report a latency number without knowing which segments it includes."

## 6. LLM inference performance (the job itself)

- [ ] ⭐ **"What metrics matter for an LLM inference API?"** (*Perf Q10*) — **TTFT** (queueing+prefill, scales w/ input length) · **ITL/TPOT** · **output tokens/sec per request** (the Cerebras headline) · e2e = TTFT + n×ITL · **system throughput** (trades vs. per-request latency via batching) · tails/error rate/queue depth · **goodput** (throughput that met SLO).
- [ ] **"Load test a streaming SSE endpoint?"** (*Perf Q11*) — unit of measurement changes: timestamp per token event; TTFT + ITL distribution + **mid-stream stall p99**; asyncio = thousands of idle-waiting streams; perf tests double as protocol-robustness tests (terminal event always present).
- [ ] **"Why does batching create the throughput/latency trade-off?"** (*Perf Q12*) — continuous batching: bigger batches → more total tokens/sec but higher ITL and TTFT; characterize the **frontier** at several concurrency levels; "concurrency=1 flatters latency, max-batch flatters throughput — honest reporting shows the curve."
- [ ] **"What makes benchmarking LLM APIs tricky?"** (*Perf Q13*) — variable output length; tokenizer differences (tokens/sec not comparable across families); prompt/KV caching (cache-bust!); prefill sensitivity → input-length distribution must mirror prod; cold-start; multi-tenant variance.
- [ ] **"Design a perf regression strategy for model releases"** (*Perf Q14*) — versioned workload suite (stratified prompt sets + streaming/tool variants) → per-release baseline distributions, statistical gate → concurrency sweep → RC soak → prod canary w/ auto-rollback → **attribution discipline** (model vs. serving stack vs. hardware tested independently).
- [ ] **"Fairly validate '10x faster than GPU clouds'?"** (*Perf Q15*) — define metric/model/lengths/concurrency; same quantization + sampling both sides; unique prompts; same client region; many runs across time; publish full distributions + methodology. "A public benchmark's credibility is itself a quality deliverable."

## 7. Debugging performance problems

- [ ] ⭐ **"Latency regressed 20% after a release — investigate"** (*Perf Q16*) — 1) scope: which percentile (p50=systemic, p99=tail), which endpoints/models/regions; 2) boring things first (config, limits, replicas — deploy causes outnumber code causes); 3) diff the release, A/B old-vs-new in perf env; 4) segment latency (queue/prefill/decode) — the segment that grew names the layer; 5) profile, fix, **add to CI gate: "the fix isn't done until the detection gap is closed."**
- [ ] **"p50 fine, p99 terrible — what do you look for?"** (*Perf Q17*) — queueing bursts; one bad replica (check per-instance percentiles); GC/periodic work; cold paths; **request heterogeneity — long-input/long-output requests may BE the p99**; retry storms. First cut: is the tail uniform across instances and request types, or concentrated?
- [ ] **"A perf issue you actually found"** (*Perf Q18*) — config-reread (soak+profiling) or Slowloris worker starvation (healthy CPU, starved connection slots). Lesson: "capacity isn't one number — test each resource axis separately: CPU, memory, disk, fds, connection slots."

## 8. API testing — status codes & error semantics

- [ ] ⭐ **"Customer reports a 500 — what does it tell you, what do you do?"** (*API Q1*) — where minted (app vs. gateway vs. between)? → correlate by request ID (no request ID in errors = first bug report) → deterministic vs. intermittent → minimal repro → **is 500 even the right code?** (bad input=400/422, overload=503, dependency timeout=504 — misclassification breaks client retry logic) → bodies never leak internals (FedRAMP experience).
- [ ] **Status codes cold** (*API Q2 table*): 200 (assert body too — "200 with error body" is a classic bug) · 201+location · 204 empty · 400 malformed · **401 vs 403 = authentication vs authorization — "who are you?" vs "you can't do that"** · 404 (sometimes deliberate instead of 403) · 405 · 408 slow client · 409 conflict · 413 boundary-test the limit · 422 semantically wrong (consistency > which one) · 429 + headers · 500 always-a-bug · 502 upstream garbage · 503 + Retry-After · 504 upstream too slow.
- [ ] **"Why does 502/503/504 distinction matter?"** (*API Q3*) — three different stories for client and on-call: backend crashed / service knows it can't take it (politely retryable) / backend alive but over timeout budget. **LLM angle: generations run minutes → gateway timeout budget must be tested against the longest legal generation.**

## 9. API testing — methodology

- [ ] **"Test a new endpoint end-to-end"** (*API Q4*) — contract/schema (incl. error shapes) → happy paths → negative/boundary (min/max/just-outside/wrong type/missing/null/oversized) → auth matrix → idempotency & concurrency → failure injection → non-functional (latency, rate limits, backward compat). "Negative and error paths are where senior SDETs earn their pay."
- [ ] **"Test authN/authZ?"** (*API Q5*) — **role × operation matrix, assert allow AND deny**; deny tested at API layer directly (UIs hide buttons, attackers use curl); token lifecycle (expired/revoked/rotated); **audit logging as part of the auth contract**; cross-tenant isolation = the most catastrophic bug class for a multi-tenant inference cloud.
- [ ] **"Test rate limiting?"** (*API Q6*) — enforcement accuracy (under/at/over; window vs. bucket burst behavior) · response quality (429 + Retry-After/quota headers; **LLM limits are token-based too — test both meters**) · recovery on schedule · tenant isolation/fairness. "My asyncio CLI is exactly the tool: precise offered rates, multi-key traffic, per-key accounting."
- [ ] **"Idempotency — what and how?"** (*API Q7*) — same end state however many times applied; retries are how distributed clients survive; test: replay w/ idempotency key → single side effect; kill connection mid-response and retry (timeout-after-commit case); concurrent duplicates racing.
- [ ] **"Test retry/timeout behavior?"** (*API Q8*) — both directions: server marks retryable correctly (503/429 vs 400); client does backoff+jitter, bounded budgets; **non-idempotent generation requests must not blind-retry after timeout → double-billing**. Drive with fault injection at the proxy, not by waiting.
- [ ] **"Backward compatibility across versions?"** (*API Q9*) — additive-only contract; suite pinned to *previous* release's schema runs against every new build; old SDKs × new server matrix; deprecation tested as a feature (warnings, sunset headers). "Pure customer-trust territory — this team's charter."

## 10. LLM/inference API specifics

- [ ] ⭐ **"How does error handling change for streaming SSE?"** (*API Q10*) — the trap: **status codes stop working once the stream starts** (200 sent before generation succeeds) → error contract moves into the stream: error event + clean termination; **silent truncation is the worst failure mode** → terminal 'done' event must ALWAYS be present so absence is detectable; client-disconnect → server releases capacity; usage in final event matches tokens streamed.
- [ ] **"What's specific about OpenAI-compatible?"** (*API Q11*) — compatibility IS the feature; target is behavioral parity, not "our spec": field shapes, streaming chunk format, finish_reason, tool-call payloads, usage reporting; **run the official OpenAI SDKs (Python/JS, multiple versions) as a conformance suite** — customers use SDKs, and SDKs are strict in surprising places.
- [ ] **"Which chat/completions params deserve the most testing?"** (*API Q12*) — max_tokens (finish_reason='length', interaction w/ context limit) · context length at/over limit (clean 400, never 500) · temperature/top_p (range + t=0 determinism if promised) · stop sequences (mid-generation, spanning token boundaries) · JSON mode (always parses, adversarial prompts) · tool calling (malformed defs → 400, not model confusion) · n/stream/logprobs multiply the matrix.
- [ ] **"Structure an API test framework from scratch"** (*API Q14*) — pytest + httpx (async → streaming first-class); thin typed client layer; fixtures for auth contexts/tenants/env; pydantic schema assertions; smoke/regression/destructive tiers; every failure = ready-to-file bug report (request, response, request ID, timing). "This is the VPE framework story — the JD's 'from the ground up' line."
- [ ] **"A subtle API bug a naive suite would miss"** (*API Q15*) — have ONE rehearsed with real detail: error-path bug (wrong code/shape on failure), state/ordering bug (passed alone, failed concurrent — VPE upgrade/rollback), or audit-gap bug (success but missing audit record — FedRAMP). He will drill into whichever you offer.

## 11. Rapid-fire one-liners (30 sec each, loaded)

- [ ] **PUT vs PATCH vs POST** — replace (idempotent) / partial update / create-act (not idempotent by default).
- [ ] **401 vs 403** — authentication vs authorization.
- [ ] **Why test error responses as strictly as success?** — clients branch on them; wrong code → wrong client behavior; error paths are where leaks and hangs live.
- [ ] **Contract vs E2E** — contract catches drift cheaply per-service; E2E validates the composition; contract-first keeps E2E small.
- [ ] **How many 9s is 'good'?** — whatever SLO the business signed (Callhome: 99.9% under load); an explicit tested number, not a feeling.
- [ ] **Little's Law** — concurrency = throughput × latency.
- [ ] **Percentiles can't be averaged** — merge raw histograms.

## 12. Bridges to drop (memorize verbatim)

- [ ] "Same cache-busting principle applies to prompt caching in LLM benchmarks."
- [ ] "I gate perf in CI with thresholds, so regressions block merge like functional failures."
- [ ] "I report distributions, never averages."
- [ ] "The fix isn't done until the detection gap is closed."

## 13. Red flags to avoid

- [ ] Don't quote Cerebras tokens/sec numbers from memory — "I'd measure rather than quote."
- [ ] Don't claim vLLM/serving-stack internals depth — "conceptual understanding I'd validate against your stack."
- [ ] Unused tool (k6/Locust/JMeter)? One honest sentence, then pivot to concepts.
- [ ] Don't treat SDET as a stepping stone to dev — own the quality identity.

## 14. Your questions for Sanjeev (pick 3)

- [ ] "The OpenAI 750MW partnership massively raises the stakes on release confidence. How is the quality org's charter changing to match that scale?"
- [ ] "How does the team baseline model quality today — golden datasets, public benchmarks, LLM-as-judge — and where does that methodology break down at your release velocity?"
- [ ] "You've built QA infrastructure from scratch at ChargePoint, Pavilion, and here — what separates the SDETs who thrive on this team from the ones who don't?"
  - *Bonus variant:* "Your validation background has always spanned hardware and software — how much does an ML API Quality engineer here need to reason about the wafer-scale hardware underneath, versus treating it as a black box?"
- [ ] "What's the biggest quality gap on the ML API surface right now that this hire should attack in the first 90 days?"
- [ ] "How do pre-deployment validation and production monitoring split responsibility on your team?"

## 15. Logistics checklist (Mon 8/3)

- [ ] **Do NOT live-demo the Netskope bot** (their internal prod system — showing it would undercut the customer-trust message). Instead: sanitized one-page architecture diagram, open and one Alt-Tab away.
- [ ] **Ask before sharing, and time-box it:** "I have a one-page architecture diagram of the RAG system I mentioned — happy to share my screen for two minutes if useful." Deploy it only when the conversation is already on the project (his follow-up to your pitch, or "tell me about something you built"). **Never open with it, never force it**, and if he says "just describe it," describe it — **the diagram is a prop, not the act.**
- [ ] Teams: camera/mic/screen-share tested; share a *window*, not desktop; DND on, Slack/email/Netskope apps closed.
- [ ] HackerRank: log in early, try a sample pad (editor + shortcuts), popup blockers off.
- [ ] Second monitor or rehearsed split-screen; notes off-screen with the 3 pillar keywords; water.
- [ ] 30 min before: reread pitch + question list once.

## 16. Expected 45-min shape

0–5 intros · 5–12 **pitch + one pillar story** · 12–30 technical deep-dive (test strategy / debugging / possible pad exercise) · 30–40 behavioral · 40–45 your questions.
