# API Testing Q&A — Cerebras HM Screen

The team owns quality for an **OpenAI-compatible inference API**, so expect API testing questions to be concrete: status codes, error semantics, retries, rate limits, streaming. Your edge: you've tested APIs *behind an NGINX gateway* (Callhome) and validated RBAC/auth across UI and API at Netskope — use both.

---

## Section A — Status codes (know these cold)

### Q1. "A customer reports the API returned 500. What does that tell you, and what do you do?"

> "A 500 means the *server* hit an unhandled failure — the request may have been perfectly valid. First thing I establish is **where the 500 came from**: from testing behind an NGINX gateway I know a 500 can be minted by the app, the gateway itself, or anything between. So:
> 1. **Correlate** — grab the request ID from the response/headers and find it in server logs and traces. If there's no request ID in error responses, that's my first bug report: unoperable errors are a quality gap in themselves.
> 2. **Classify** — is it deterministic (same request always 500s → likely a code path bug, e.g., an unhandled input shape) or intermittent (→ infra: pod restart, dependency timeout misreported as 500, race)?
> 3. **Reproduce minimally** — shrink the failing request to the smallest payload that still 500s.
> 4. **Check the contract** — even when the server must fail, a 500 is often the *wrong* code: bad user input should be 400/422, overload should be 503, dependency timeout 504. A 500 for a predictable condition means missing validation, and clients can't do the right thing (retry vs. fix request) if we misclassify. I treat 'correct error code' as a testable requirement, not a nicety.
> 5. Also: **500 bodies must never leak internals** — stack traces, file paths, internal hostnames. I've tested that explicitly in security-sensitive releases (FedRAMP)."

### Q2. Status code table — meaning, when it's correct, and how you'd test it

| Code | Meaning | Correct when | Test angle |
|---|---|---|---|
| **200** | OK | Successful sync request | Also assert body/schema — 200 with an error body is a classic API bug. Streaming: 200 arrives *before* generation succeeds (see Q10). |
| **201** | Created | Resource created (POST) | Response includes location/ID of new resource. |
| **204** | No Content | Success, nothing to return (DELETE) | Body is actually empty. |
| **400** | Bad Request | Malformed/invalid input | Every documented validation rule has a negative test: bad JSON, wrong types, out-of-range params (`temperature: 5`), unknown fields. |
| **401** | Unauthorized | Missing/invalid/expired **authentication** | No key, wrong key, expired key, revoked key, malformed header. |
| **403** | Forbidden | Authenticated but not **authorized** | Valid key without permission — e.g., a model/org the key can't access. The 401-vs-403 distinction is a favorite interview probe: *401 = who are you? 403 = I know who you are; you can't do this.* My Netskope RBAC testing was exactly this matrix. |
| **404** | Not Found | Resource doesn't exist | Nonexistent model name, wrong endpoint path. Security nuance: sometimes 404 is deliberately returned instead of 403 to avoid confirming a resource exists. |
| **405** | Method Not Allowed | Wrong HTTP verb | GET on a POST-only endpoint. |
| **408** | Request Timeout | Server gave up waiting on a slow *client* | Slow-send tests (my Slowloris case). |
| **409** | Conflict | State conflict (duplicate create, version clash) | Concurrent modification tests. |
| **413** | Payload Too Large | Body over limit | Request exactly at, and just over, the documented limit — boundary testing. For LLMs: giant prompt bodies. |
| **422** | Unprocessable Entity | Syntactically valid, semantically wrong | Well-formed JSON that violates business rules. Teams vary on 400 vs 422 — what matters is the API is *consistent and documented*. |
| **429** | Too Many Requests | Rate limit exceeded | See Q6 — headers, recovery, fairness. |
| **500** | Internal Server Error | Unhandled server failure | Should be rare and *always* a bug or misclassification. No internals in body. |
| **502** | Bad Gateway | Proxy got an invalid/failed response from upstream | Kill the backend while the gateway lives — my Callhome failover drill. |
| **503** | Service Unavailable | Overloaded / no capacity / maintenance | Should carry `Retry-After` when possible. For inference: queue-full behavior under load spikes. |
| **504** | Gateway Timeout | Upstream too slow for the proxy | Slow backend + gateway timeout config. Long LLM generations make this a *real* config-sensitivity area. |

### Q3. "Why does the 502 / 503 / 504 distinction matter?"

> "They tell the client — and the on-call engineer — three different stories. **502**: the backend returned garbage or dropped the connection (backend crashed or is misbehaving). **503**: the service knows it can't take the request (overload, deploy, no healthy upstreams) — politely retryable, ideally with `Retry-After`. **504**: the backend is alive but too slow for the gateway's timeout budget. In my Callhome failover testing, the difference between 'node kill produces a brief blip of 502s' and 'traffic reroutes with zero client-visible errors' was exactly the pass/fail line. And for LLM inference, 504 is special: generations legitimately run for minutes, so gateway timeout budgets need to be tested against the *longest legal* generation, streaming and non-streaming."

---

## Section B — Core API testing methodology

### Q4. "How do you approach testing a new API endpoint end-to-end?"

> "Layers, in order:
> 1. **Contract/schema** — response structure matches the spec for success *and* error cases; unknown fields, types, nullability. Ideally automated from an OpenAPI spec so drift is caught mechanically.
> 2. **Happy paths** — representative valid inputs across the parameter space.
> 3. **Negative/boundary** — every parameter at min, max, just-outside, wrong type, missing, null, empty; malformed JSON; wrong content-type; oversized payloads.
> 4. **Auth matrix** — no auth, bad auth, expired auth, valid-but-unauthorized (401 vs 403), cross-tenant access attempts.
> 5. **Idempotency & state** — repeated calls, concurrent calls, out-of-order calls.
> 6. **Failure injection** — dependency down/slow → verify the *right* error code and no hangs.
> 7. **Non-functional** — latency envelope, rate-limit behavior, and backward compatibility with previous API versions.
> The negative and error-path layers are where senior SDETs earn their pay — happy paths are what devs already checked."

### Q5. "How do you test authentication and authorization on an API?"

> "At Netskope I did this for FedRAMP releases, so I think of it as a **role × operation matrix**: for every role/permission level, and every operation, assert both the allow *and* the deny — positive and negative access. Key details:
> - Deny must be tested **at the API layer directly**, not just through the UI — UIs hide buttons, attackers use curl.
> - Verify 401 vs 403 semantics are consistent.
> - Token/key lifecycle: expired, revoked, rotated keys; sessions invalidated on permission change.
> - **Audit logging as part of the auth contract** — every security-sensitive operation (auth events, permission changes) must produce an audit record; I tested the logs, not just the responses.
> - Cross-tenant isolation: authenticated-as-tenant-A must never read tenant B — the single most catastrophic API bug class for a multi-tenant inference cloud."

### Q6. "How do you test rate limiting?"

> "Four dimensions:
> 1. **Enforcement accuracy** — drive requests at just-under, at, and over the limit; verify allowed counts match the policy (and know whether it's a fixed window, sliding window, or token bucket — burst behavior differs).
> 2. **Response quality** — 429 with informative headers (`Retry-After`, remaining-quota headers) so well-behaved clients can back off; for LLM APIs limits are often *token-based* not just request-based, so test both meters.
> 3. **Recovery** — after backing off, clients get capacity back on schedule; no lingering penalty.
> 4. **Isolation/fairness** — one tenant hammering the API must not consume another tenant's quota or degrade their latency. My asyncio load-CLI is exactly the tool for this: precise offered rates, concurrent multi-key traffic, and per-key result accounting."

### Q7. "What is idempotency and how do you test it?"

> "An idempotent operation gives the same end state no matter how many times it's applied — GET/PUT/DELETE should be idempotent by contract, POST usually isn't unless the API supports idempotency keys. It matters because **retries are how distributed clients survive**, and retrying a non-idempotent POST double-charges or double-creates. Tests: replay the same request (with the same idempotency key if supported) and assert single side effect; kill the connection mid-response and retry — the classic 'timeout after server committed' case; concurrent duplicates racing each other."

### Q8. "How do you test retry/timeout behavior from the client side?"

> "I test both directions of the contract. **Server side**: which errors are marked retryable (503/429 with Retry-After) vs. not (400) — misclassification teaches clients to retry hopeless requests or give up on transient ones. **Client/SDK side**: exponential backoff with jitter actually happens (no thundering herd), retry budgets are bounded, and — critical for inference — **non-idempotent generation requests aren't blindly retried after a timeout**, or you bill the customer twice for one answer. I use fault injection (drop, delay, reset connections at the proxy) to drive these paths deterministically rather than waiting for them to happen."

### Q9. "How do you test API backward compatibility across versions?"

> "The contract with existing customers is: **additive changes only** — new optional fields OK; removing/renaming fields, changing types, tightening validation, or changing error codes are breaking. My approach: a versioned contract-test suite pinned to the *previous* release's schema, run against every new build — if yesterday's assertions fail today, that's a breaking change, flagged before customers find it. Plus: old SDK versions against new server in the compat matrix, and deprecation tested as its own feature (warnings, sunset headers, documented timelines). This is pure 'customer trust' territory — exactly this team's charter."

---

## Section C — LLM/inference API specifics (the job)

### Q10. "How does error handling change for a streaming (SSE) endpoint?"

> "This is the trap question — **status codes stop working once the stream starts**. The server sends `200 OK` and begins streaming; if generation fails at token 500, it can't change the status code retroactively. So the error contract moves *into the stream*: a well-formed error event, then a clean termination — and clients must be tested against it. My test list:
> - Error mid-stream → error event received, stream terminates cleanly, partial content clearly bounded.
> - Server dies mid-stream → client sees connection drop, not a silent 'complete-looking' truncation. **Silent truncation is the worst failure mode** — the response looks done but isn't; I'd test that a terminal 'done' event is *always* present in success so its absence is detectable.
> - Client disconnects mid-stream → server stops generating and releases capacity (resource-leak test, my Slowloris instinct in reverse).
> - Every event parses; usage/accounting in the final event matches tokens actually streamed."

### Q11. "What's specific about testing an OpenAI-compatible API?"

> "Compatibility *is* the feature — customers point existing OpenAI SDK code at the endpoint and expect it to just work. So the test target is not 'our spec,' it's **behavioral parity with the reference**: field names/shapes in success and error responses, streaming chunk format, finish_reason semantics, tool/function-call payloads, token usage reporting. I'd maintain a conformance suite that runs the *official OpenAI client SDKs* (Python/JS, multiple versions) against our endpoint — because customers use the SDK, not raw HTTP, and SDKs are strict about shapes in surprising places. Every divergence is either a documented known-gap or a bug."

### Q12. "Which parameters of a chat/completions endpoint deserve the most testing attention?"

> "The ones with semantic contracts, boundaries, or interactions:
> - **max_tokens** — exact enforcement; finish_reason = 'length' when hit; interaction with context limit.
> - **Context length** — prompt at the model's limit, just over (must be a clean 400 with a helpful message, not a 500), and prompt+max_tokens exceeding the window together.
> - **temperature/top_p** — range validation, and temperature=0 determinism if the platform promises it.
> - **stop sequences** — honored mid-generation, multi-sequence, sequence spanning token boundaries.
> - **Structured output / JSON mode** — output always parses; schema conformance under adversarial prompts.
> - **Tool calling** — valid tool schemas produce well-formed calls; malformed tool definitions rejected with 400, not model confusion.
> - **n, streaming flag, logprobs** — each multiplies the response-shape matrix.
> Boundary + interaction testing here, because single-parameter happy paths are the easy 20%."

### Q13. "The API returns 200 but customers say responses got 'worse.' Not a status code problem — what do you do?"

> "That's the gap between API correctness and **model quality**, and it's why this team exists. A 200 with degraded output is invisible to traditional API testing. My answer is the methodology I built for my RAG assistant: **golden datasets with scored evaluation and statistical thresholds** — response quality tracked as distributions across a versioned eval set, compared release-over-release, so 'worse' becomes a measurable regression instead of vibes. Then wire that into the release gate exactly like a functional test. Plus production-side: sampled live-traffic evals and customer-feedback loops feeding a triage queue — I built precisely that feedback→known-gaps pipeline for my assistant."

---

## Section D — Automation craft

### Q14. "How would you structure an API test framework from scratch?"

> "Python: **pytest + httpx** (async, so streaming and concurrency tests are first-class). Structure:
> - A thin typed **client layer** wrapping the API (one place to handle auth, retries-off-by-default-in-tests, request IDs) — tests read as intent, not HTTP plumbing.
> - **Fixtures** for auth contexts (per-role keys), test tenants, and environment config — same suite runs against dev/staging/prod-canary by config, no code change.
> - **Schema validation** as assertions (pydantic models mirroring the contract) so every test implicitly checks the contract.
> - Markers/tiers: smoke (minutes, every PR) / full regression (release gate) / destructive-fault-injection (dedicated env only).
> - Every failure artifact captured: request, response, request ID, timing — a failing API test should be a ready-to-file bug report.
> This is how I built the VPE E2E framework at Netskope, and the 'built from the ground up' line in this JD is describing that work."

### Q15. "What's a subtle API bug you've caught that a naive test suite would miss?"

Pick and rehearse one real story. Good shapes from your background:
> - An **error-path bug**: correct behavior on success but wrong code/shape on failure (e.g., 500 where a 400 belonged, or an error response missing fields the SDK required).
> - A **state/ordering bug**: passed in isolation, failed when operations ran concurrently or out of order (upgrade/rollback sequencing from your VPE migration testing).
> - An **audit-gap bug**: operation succeeded but the required audit record was missing/wrong — invisible unless logs are part of the contract (your FedRAMP work).
Have one with specific details — he will drill into whichever you offer.

---

## Rapid-fire one-liners (30 seconds each, have them loaded)

- **PUT vs PATCH vs POST**: PUT replaces (idempotent), PATCH partially updates, POST creates/acts (not idempotent by default).
- **401 vs 403**: authentication vs authorization — "who are you" vs "you can't do that."
- **Why test error responses as strictly as success?** Clients branch on them; a wrong error code causes wrong client behavior (bad retries, bad UX), and error paths are where leaks and hangs live.
- **Contract testing vs E2E**: contract tests catch drift cheaply per-service; E2E validates the composed system. You need both; contract-first keeps E2E suites small.
- **How many 9s of API success is 'good'?** Depends on the SLO the business signed — my Callhome SLO was 99.9% under load; the point is it's an explicit, tested number, not a feeling.
