# Performance Testing Q&A — Cerebras HM Screen (Sanjeev Gadgil)

Why this matters: Sanjeev **built in-house performance testing tools at Pavilion Data** and his stated focus is "performance, reliability, and scalability." Expect at least one deep perf thread. Your two anchors: the **Callhome Gateway perf project** (real SLOs, 16 test cases) and the **asyncio load-testing CLI**.

Answers are written in your voice, ready to rehearse. Don't memorize word-for-word — memorize the bullet skeletons.

---

## Section A — Your own perf work (he'll dig here first)

### Q1. "Walk me through a performance test you designed end-to-end."

**Use the Callhome Gateway project.**

> "I owned performance testing for our NGINX-based Callhome Gateway — the front door for device traffic. I started from SLOs, not tools: **500 req/s per node with <20ms added gateway latency, 99.9% success rate, CPU under 70%** at target load. From there I designed ~16 test cases in layers:
> - **Baseline** — minimal health-check requests to isolate the gateway's own overhead from backend cost.
> - **Security overhead** — TLS and mTLS handshake cost, new-session vs. resumed-session, because handshakes are CPU-expensive and that's where auth features silently eat capacity.
> - **Session paths** — first-time authentication vs. cookie-reuse path, since real traffic is a mix.
> - **Large payloads** — 20 concurrent multi-GB uploads to test disk buffering and exhaustion, not just CPU.
> - **Soak** — 8-hour realistic traffic mix to catch memory leaks and slow degradation that a 10-minute run never shows.
> - **Failure injection** — kill a node under load and verify failover with no user-visible errors.
> - **Slow-client abuse** — Slowloris-style slow senders tying up worker connections.
>
> Two design details I'm proud of: I **injected random noise into request payloads** so caching couldn't fake the results, and I scoped the test explicitly — backend service failures didn't count against the gateway, so the results were attributable."

If he asks what you found: "The soak and profiling pointed to the gateway re-reading a config file from disk per request instead of caching it — a classic 'invisible at low load, dominant at high load' inefficiency."

---

### Q2. "Tell me about the load-testing tool you built. Why build instead of using Locust/k6/JMeter?"

> "I built an async HTTP load-testing CLI in Python on asyncio. Design: a single event loop drives thousands of in-flight requests with a **semaphore bounding concurrency**, a shared connection pool, and per-request timing recorded into histograms so I can report accurate percentiles, not averages. It supports four load profiles — **constant, ramp, spike, soak** — because each answers a different question. Output is CI-friendly: latency and error-rate **thresholds as pass/fail exit codes**, so perf runs gate merges like any other test.
>
> Why build: our cases needed things off-the-shelf tools made painful — mTLS with our cert workflows, custom payload generation with cache-busting noise, and tight CI integration with our thresholds. A focused ~1-2k-line tool we fully understood beat configuring a general framework we'd fight. I'd still reach for k6 or Locust when the standard model fits — building was a deliberate trade-off, not a default."

**Be ready for the follow-up: "How do you know your load generator isn't the bottleneck?"**
> "I validate the harness before trusting the numbers: monitor generator-side CPU, socket counts, and event-loop lag; scale generators horizontally and check the target's throughput scales with offered load; and run generator-to-generator (or against a trivial echo server) to establish the harness's own ceiling and latency floor. If the client is saturating, the server numbers are fiction."

---

### Q3. "How do you make performance tests reliable enough to gate a release in CI?"

> - **Dedicated, controlled environment** — we ran in an isolated perf environment (perf01), never shared infra; noisy neighbors destroy repeatability.
> - **Warm-up excluded** — discard the first N seconds (connection pools, JIT, caches filling) before measuring.
> - **Thresholds with headroom** — gate on p95/p99 and error rate with margin over the SLO, so normal variance doesn't flap the gate.
> - **Multiple runs / trend tracking** — a single bad run alerts; a trend across runs blocks. I compared each release's results against the stored baseline, not against an absolute number alone.
> - **Fixed workload definition** — same request mix, payload sizes, and concurrency profile versioned with the test code, so a regression means the *system* changed, not the test."

---

### Q4. "How did you prevent the system under test from cheating?"

> "Caching is the classic cheat. My load generator injected random noise into payloads so no two requests were identical — otherwise the gateway or anything behind it could serve memoized responses and I'd be benchmarking a cache. The general principle: **know every layer that could short-circuit the work** — CDN, proxy cache, connection reuse, DB query cache — and decide deliberately whether each is in-scope or defeated. This maps directly to LLM inference: prompt caching and KV-cache reuse can make a benchmark look 10x better than cold reality, so you control prompt uniqueness the same way."

*(That last sentence is a bridge he'll love — it shows you already think in their domain.)*

---

## Section B — Fundamentals (warm-up probes)

### Q5. "Why percentiles instead of average latency?"

> "Averages hide the users you're hurting. Latency distributions are long-tailed — a great mean can coexist with a p99 of several seconds, and at scale p99 is not rare: a user session making 100 API calls hits the p99 about 63% of the time. So I report p50 for typical experience, p95/p99 for tail, and max/error-rate for pathology. I also never average percentiles across runs or nodes — you have to merge the raw histograms."

### Q6. "What's the relationship between throughput and latency?"

> "Latency stays roughly flat while the system has headroom, then rises sharply as you approach saturation — the hockey-stick 'knee.' Queueing theory drives it: as utilization approaches 100%, queue time explodes. Little's Law (**concurrency = throughput × latency**) ties the three together and is how I sanity-check results — if my numbers don't satisfy it, the harness is broken. Practically, I find the knee with a ramp test and recommend operating at the point where p99 is still within SLO, not at max throughput."

### Q7. "Open-loop vs. closed-loop load generation? Coordinated omission?"

> "**Closed-loop**: N virtual users each wait for a response before sending the next request — arrival rate self-throttles when the server slows down. **Open-loop**: requests arrive on a fixed schedule regardless of responses — like real independent users. Closed-loop testing under-reports badly during slowdowns: when the server stalls, a closed-loop client politely stops sending, so the stall barely appears in the data. That's **coordinated omission**. Mitigations: open-loop or hybrid generation, or correct recorded latencies against the intended send schedule (the HdrHistogram approach). My CLI's semaphore model is closed-loop at the concurrency cap, so for rate-driven tests I schedule sends by target rate and measure from *intended* send time."

*(Knowing coordinated omission by name is a strong senior signal with a perf-tools builder.)*

### Q8. "What do constant, ramp, spike, and soak profiles each tell you?"

> "- **Constant**: steady-state behavior at a known operating point — SLO validation.
> - **Ramp**: find the knee and max sustainable throughput; watch where p99 leaves the envelope.
> - **Spike**: elasticity and recovery — does the system shed, queue, or collapse when traffic jumps 5–10x in seconds, and how fast does it return to baseline?
> - **Soak**: hours at realistic load — memory leaks, fd/socket leaks, disk fill, degradation that only time reveals. My 8-hour Callhome soak was where the config-file-reread inefficiency and slow-degradation risks showed up."

### Q9. "How do you separate client, network, and server latency?"

> "Measure at multiple points and subtract. Client-side total minus server-processing time (from server logs/metrics or a `Server-Timing` header) gives network plus queueing. TCP/TLS handshake time is separable from time-to-first-byte on the client. In the Callhome work I explicitly measured 'added gateway latency' — request time through the gateway minus the backend's own response time — so the 20ms SLO was attributable to the component I was testing. Rule: never report a latency number without knowing which segments it includes."

---

## Section C — LLM inference performance (the job itself)

### Q10. "What metrics matter for an LLM inference API?"

> "Different metrics for different phases of a generation:
> - **TTFT (time to first token)** — dominates perceived responsiveness, especially chat UX; driven by queueing plus prefill (prompt processing) cost, so it scales with input length.
> - **Inter-token latency / TPOT** — the steady drip rate after the first token; drives how fast text streams.
> - **Output tokens/sec per request** — the user-visible generation speed (Cerebras's headline strength).
> - **End-to-end latency** — TTFT + output_tokens × ITL; what a non-streaming caller sees.
> - **System throughput** — total tokens/sec across all concurrent requests; the cost/capacity metric, and it trades off against per-request latency via batching.
> - Plus **error/timeout rate, queue depth, and tail percentiles of all of the above**. I'd also track *goodput* — throughput of requests that met SLO — because raw throughput with blown latencies isn't useful capacity."

### Q11. "How would you load test a streaming (SSE) endpoint?"

> "The unit of measurement changes: one request is now a stream of events. My harness records **timestamps per token event**, not one duration per request — TTFT is first-event minus send time, ITL is the gap distribution, and I watch for **mid-stream stalls** (a p99 inter-token gap matters as much as p99 TTFT). Implementation-wise, that's exactly what asyncio is good at — thousands of concurrent open streams, each an async iterator over the SSE connection, cheap because they're mostly idle-waiting. I'd also validate stream *correctness under load*: events well-formed, terminal event always sent, connections closed properly — perf tests double as protocol-robustness tests."

### Q12. "Why does batching create a throughput/latency trade-off in LLM serving?"

> "The accelerator is most efficient processing many sequences at once, so servers use continuous batching — new requests join the in-flight batch each step. Bigger effective batches raise total tokens/sec but each request shares compute per step, so ITL rises, and admission under load raises TTFT via queueing. So there's a frontier: throughput vs. per-request latency. A perf strategy has to characterize the whole frontier — latency at several concurrency levels — not a single point. A benchmark at concurrency=1 flatters latency; one at max batch flatters throughput; honest reporting shows the curve."

### Q13. "What makes benchmarking LLM APIs uniquely tricky?"

> "It's the least deterministic perf target I can think of:
> - **Variable output length** — latency depends on how many tokens the model *decides* to generate; you control it with max_tokens, forced-length prompts, or normalize to per-token metrics.
> - **Tokenizer differences** — 'tokens/sec' isn't comparable across model families unless you normalize; same text, different token counts.
> - **Prompt/KV caching** — repeated prompts can be served largely from cache; unique-prefix prompts or cache controls needed, same cache-busting principle as my Callhome noise injection.
> - **Prefill vs. decode sensitivity** — TTFT scales with input length, so the input-length distribution must mirror production, not just 'short prompt' tests.
> - **Warm-up and model loading** — first requests after deploy hit cold paths.
> - **Rate limits and shared capacity** — on a live service, other tenants' load is invisible variance; you need dedicated capacity or many runs across time windows."

### Q14. "Design a performance regression strategy for our model releases."

> "Layered, mirroring what I did for release sign-off at Netskope:
> 1. **A versioned workload suite** — fixed prompt sets stratified by input length and output length, plus streaming and tool-call variants, checked into the repo so runs are comparable across releases.
> 2. **Per-release baseline comparison** — for each model/hardware config, store TTFT/ITL/throughput distributions; gate on statistical regression vs. baseline (e.g., p99 TTFT worsened beyond noise band), not absolute numbers alone.
> 3. **Concurrency sweep** — measure at several load levels to catch regressions that only appear near saturation, like a batching or scheduler change.
> 4. **Soak on release candidates** — hours-long realistic mix to catch leaks and degradation before production.
> 5. **Canary in production** — small traffic slice with the same metrics dashboards, automatic rollback thresholds.
> 6. **Attribution discipline** — separate model changes from serving-stack changes from hardware changes by testing them independently when possible, so a regression has an owner within an hour, not a week."

### Q15. "How would you fairly validate a claim like '10x faster than GPU clouds'?"

> "Define the claim precisely first — 10x on *what metric* (output tokens/sec per request is the usual one), *which model*, *what input/output lengths*, *what concurrency*. Then: same model and quantization on both sides, matched sampling settings, unique prompts to defeat caching, measure from the same client region, many runs across time-of-day to absorb the other side's multi-tenant variance, and report full distributions with the methodology published. The credibility of a public benchmark is a quality deliverable in itself — it's the kind of thing this team would own, and sloppy methodology there is a customer-trust bug."

---

## Section D — Debugging performance problems

### Q16. "API latency regressed 20% after a release. Walk me through your investigation."

> "1. **Scope it**: which percentile moved — p50 (everything slower: systemic) or just p99 (tail: contention, GC, one bad node)? Which endpoints/models/regions? All traffic or a slice?
> 2. **Check the boring things first**: config diffs, resource limits, replica counts, node types — my on-call experience says deployment/environment causes outnumber code causes.
> 3. **Diff the release**: what actually shipped — code, model version, serving params (batch size, scheduler), infra changes. Bisect if the delta is large; A/B old vs. new build in the perf environment to confirm reproducibility outside production.
> 4. **Segment the latency**: queue time vs. prefill vs. decode (or gateway vs. backend) from internal metrics — the segment that grew tells you the layer.
> 5. **Profile that layer**, fix, then **add the regression to the CI perf gate** so it can't ship silently again. The fix isn't done until the detection gap is closed — that's the difference between fixing a bug and fixing the process."

### Q17. "p50 is fine but p99 is terrible. What do you look for?"

> "Tail-only pain means *most* requests are fine and something intermittent or unevenly distributed is hurting a few:
> - **Queueing spikes** — bursty arrivals briefly exceeding capacity.
> - **One bad replica/node** — a single slow pod poisons the tail while barely moving the median; check per-instance percentiles.
> - **GC or periodic background work** — compaction, log rotation, cron; correlate tail events with time.
> - **Cold paths** — cache misses, cold model shards, connection re-establishment.
> - **Request heterogeneity** — for LLMs, the long-input or long-output requests may *be* the p99; segment latency by request size before assuming pathology.
> - **Retries/timeouts stacking** — a retry storm shows up as tail latency plus elevated backend load.
> First move is always: is the tail uniform across instances and request types, or concentrated? That one cut usually points at the cause."

### Q18. "Tell me about a performance issue you actually found."

> "Two I'd offer:
> 1. The Callhome gateway **re-reading a config file from disk on every request** — invisible in functional tests, found through soak testing plus profiling under load; the signature was CPU and iowait growing faster than request rate.
> 2. From the Slowloris test case: **slow clients exhausting worker connections** — the gateway looked healthy on CPU but new connections queued because workers were parked on byte-at-a-time senders. Fix direction was timeouts and per-client limits. Lesson I carry: capacity isn't one number — you can be starved on connections while idle on CPU, so perf test design has to attack each resource axis separately (CPU, memory, disk, fds, connection slots)."

---

## Bridges to drop during any perf answer

- "Same cache-busting principle applies to prompt caching in LLM benchmarks" — connects your past to their present.
- "I gate perf in CI with thresholds, so regressions block merge like functional failures" — quality-culture signal, JD keyword.
- "I report distributions, never averages" — perf-craft signal a tools-builder will recognize.
- "Percentiles can't be averaged" — small, senior, memorable.

## Red flags to avoid

- Don't quote tokens/sec numbers for Cerebras from memory — say "I'd measure rather than quote."
- Don't claim vLLM/serving-stack internals expertise you don't have; frame batching knowledge as "conceptual understanding I'd validate against your stack."
- If asked about a tool you haven't used (k6, Locust, JMeter): one honest sentence, then pivot to the concepts, which transfer.
