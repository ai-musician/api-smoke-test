# ML / Model Quality Q&A — Cerebras HM Screen

**Calibration:** Sanjeev is a career *systems validation* engineer, not an ML researcher. He will not quiz you on backprop or transformer math. He WILL probe whether you can **test a system whose output is probabilistic** — the JD's own words: "evaluating accuracy, fairness, and performance at scale" and "rigorous evaluation methodologies." Your RAG project is your proof; this file arms you to discuss it in industry-standard vocabulary.

Depth rule: know Section B at *conversational* level (one crisp paragraph each), Sections C–D at *deep* level (that's the job), Section E at *awareness* level.

---

## Section B — LLM fundamentals an SDET must speak fluently

### Q1. "Why can't you test an LLM like normal software?"

> "Three reasons: **outputs are probabilistic** — the same input can legitimately produce different valid answers, so exact-match assertions break; **correctness is graded, not binary** — a response can be 80% right; and **the input space is unbounded natural language** — no equivalence-class partitioning covers it. So testing shifts from 'assert equals' to **measurement**: score outputs against references or rubrics, aggregate over a dataset, compare distributions against a baseline, gate on statistical thresholds. That's exactly the shift I made building my RAG test suite — score distributions and per-cohort thresholds instead of deterministic pass/fail."

### Q2. "Does temperature=0 make outputs deterministic? Can you rely on that for testing?"

> "Temperature=0 means greedy decoding — always pick the highest-probability token — so it *mostly* stabilizes output, and I use it to reduce variance in tests. But I don't build a strategy on it: floating-point non-associativity means batching, kernel differences, or hardware changes can flip near-tie tokens, and one flipped token early diverges the whole continuation. Also, testing only at temperature=0 tests a configuration customers mostly don't use. So: greedy for cheap smoke checks, distribution-based scoring for real quality gates."

### Q3. Rapid-fire concepts (one line each, be able to expand)

- **Token**: the model's unit of text (~4 chars English avg); billing, limits, and speed are all per-token.
- **Context window**: max tokens (prompt + generation) the model can attend to; boundary-test target.
- **temperature / top_p**: sampling randomness controls — temperature reshapes the distribution, top_p truncates its tail.
- **Prefill vs decode**: prompt processed in parallel (drives TTFT), then tokens generated one-by-one (drives tokens/sec).
- **KV cache**: stored attention state so each new token doesn't recompute the whole prompt; why long contexts eat memory.
- **Quantization / precision (FP16→FP8 etc.)**: smaller weights → faster/cheaper, with possible quality loss — *a first-class test target on new hardware* (see Q8).
- **Logprobs**: per-token probabilities the API can return — a testing power tool (see Q9).
- **Hallucination**: fluent, confident, wrong — the failure mode benchmarks under-measure and customers over-experience.

---

## Section C — Evaluation methodology (the heart of the role)

### Q4. "How would you evaluate whether a model deployment is 'good'?"

> "Layered, from cheap to expensive:
> 1. **Golden datasets** — versioned prompt sets with references, scored automatically. Exact/regex match where the task permits (math, code, extraction), semantic similarity or rubric scoring where it doesn't.
> 2. **Industry benchmarks** — MMLU-class knowledge suites, GSM8K-class math, HumanEval-class code (pass@k has the huge advantage of *executable* ground truth), instruction-following suites. These give comparability across models and releases — and the JD explicitly wants contributions here.
> 3. **LLM-as-judge** — a strong model grades outputs against a rubric; scales grading of open-ended responses. But the judge is itself a component under test: I'd calibrate it against a human-labeled sample, watch for known judge biases — position bias, verbosity bias, self-preference — and re-validate the judge whenever it changes.
> 4. **Human eval** — small, expensive, the ground truth that anchors the automated layers.
> 5. **Capability-specific suites** — tool calling, structured output/JSON validity, long-context retrieval (needle-in-haystack), multilingual, safety refusals.
> The engineering is in making this a **pipeline with baselines and gates**, not a one-off study — every release scored, compared, and blocked on regression."

### Q5. "How do you detect a quality regression between two model builds when outputs vary run to run?"

> "Treat it as a statistics problem, which is what I did on my RAG gate:
> - Score both builds on the same versioned eval set, **multiple sampled runs** if temperature > 0.
> - Compare **distributions, not single numbers** — mean shift plus tail behavior; a regression that only hurts the worst 5% of cases still hurts real users.
> - **Per-cohort thresholds** — slice by task type, length, language, difficulty. My RAG suite gated per-cohort because an aggregate can stay flat while one slice collapses.
> - Know your **noise band**: run build-vs-itself to measure eval variance first; only flag deltas that clear it. Otherwise the gate cries wolf and gets ignored — a flaky quality gate is as useless as a flaky unit test.
> - For gray-zone deltas: paired per-item comparison (which items flipped from pass to fail?) beats aggregate scores — it also hands engineering a repro list, not just a number."

### Q6. "What are the pitfalls of public benchmarks?"

> "- **Contamination** — the benchmark leaked into training data; scores measure memorization. Mitigate with held-out/private sets and perturbed variants (reworded questions, shuffled choices).
> - **Saturation** — frontier models cluster near the ceiling, so the benchmark stops discriminating.
> - **Overfitting-to-the-metric** — optimizing MMLU is not optimizing usefulness; Goodhart's law.
> - **Format sensitivity** — scores swing on prompt template, few-shot count, answer-extraction regex; two labs report different numbers for the same model. So for release testing I care less about the absolute score and more about **delta under identical harness conditions** — same prompts, same extraction, same sampling — which is also why owning our own eval harness matters more than quoting leaderboards."

### Q7. "Your API tests pass, latency is fine, but a customer says the model 'got dumber' after a release. Walk me through it."

> "First, believe them — perceived regressions are often real but narrow.
> 1. **Get specifics**: example prompts, expected vs. actual, which endpoint/model/params. Anecdotes → repro set.
> 2. **Check what actually changed**: model weights? serving stack? quantization/precision? default sampling params? prompt template/system prompt handling? Tokenizer version? Several 'model got dumber' incidents in the industry have been serving-stack or template bugs, not weights.
> 3. **Run the eval battery on both versions** with the customer's case type added as a cohort — does the regression reproduce under controlled conditions?
> 4. **Segment**: all traffic or just long contexts / specific language / tool-calling paths? (Long-context degradation is a classic silent-regression corner.)
> 5. Fix, then **fold the repro set into the permanent golden dataset** — the gate grows a new cohort so this class of regression can't ship silently again. Same closed-loop I built for my RAG assistant: user downvotes became a Knowledge Gaps queue became test cases."

---

## Section D — Cerebras-specific: validating models on new hardware

### Q8. "Cerebras ports models to wafer-scale hardware. How would you validate our deployment produces 'the same model' as the reference?"

*(High-probability question — it is arguably the team's core problem.)*

> "Equivalence testing across implementations, in tiers:
> 1. **Numerical tier**: compare **logprobs/logits** on a fixed prompt set against the reference implementation — token-level probability deltas catch subtle numerical drift long before it's visible in text. Perplexity on a held-out corpus as an aggregate check.
> 2. **Greedy-decode tier**: temperature=0 outputs on a large prompt set; measure token-level divergence rate and *where* divergence starts. Exact match everywhere is not achievable across hardware/precision — the question is whether divergences are within the noise band that precision differences legitimately cause.
> 3. **Quality tier**: full eval battery (benchmarks + golden sets) on both; assert score deltas within tolerance. This is the tier that answers 'does any numerical difference *matter*.'
> 4. **Behavioral tier**: capability spot-checks — tool calls, JSON mode, stop sequences, long-context retrieval — because a numerically-close model can still break a *contract* if the serving layer differs.
> The tolerance policy per tier is a product decision I'd drive with the ML systems team — my job is making the deltas visible, attributable, and gated."

### Q9. "How would you use logprobs in testing?"

> "Logprobs turn a text API into a measurable instrument:
> - **Implementation equivalence** (Q8) — compare distributions across hardware/precision/build.
> - **Sensitive regression detection** — a build change that shifts token probabilities shows in logprobs before it flips visible outputs.
> - **Calibration checks** — on multiple-choice golden sets, does probability mass track correctness?
> - **Sampling-parameter validation** — verify temperature/top_p actually reshape the distribution as specified; a serving bug that ignores temperature is directly detectable.
> It's the closest thing this domain has to a scope probe on a hardware board — which is a metaphor a systems-validation Director will appreciate."

### Q10. "Does quantization/precision reduction affect quality, and how do you test for it?"

> "It can — the loss is usually small and uneven: aggregate benchmarks barely move while specific capabilities (math, code, low-resource languages, long-context recall) degrade first. So I'd test a precision change like a model change: full eval battery, **per-cohort** deltas with the sensitive cohorts weighted, logprob-divergence analysis, and paired item-level diffs to find which prompts flipped. The trap is validating on aggregate MMLU, seeing -0.2%, shipping — and having quietly broken code generation for a key customer."

---

## Section E — Fairness & safety (awareness level; JD says "accuracy, fairness")

### Q11. "How would you test a model for fairness/bias?"

> "Structured, not vibes:
> - **Counterfactual/template testing** — same prompt with demographic terms swapped; score whether quality, sentiment, or refusal rate shifts. It's equivalence-class testing where the classes are demographic variations — a familiar QA pattern applied to a new property.
> - **Benchmark suites** — established bias benchmarks (BBQ-class QA bias sets, toxicity suites like RealToxicityPrompts) folded into the recurring eval battery, not run once.
> - **Refusal-behavior testing both directions** — harmful requests refused, benign requests *not* over-refused (over-refusal is also a quality regression customers feel).
> - **Slice reporting** — fairness metrics reported per release next to accuracy, so drift is visible.
> I'd be honest with him that this is the area I've read more than practiced — then pivot: the *machinery* (cohort-sliced eval pipelines with gates) is identical to what I've built; fairness is another cohort dimension and metric plugged into it."

---

## Your RAG story, retold in eval vocabulary (rehearse this mapping)

| What you built | Industry term he'll recognize |
|---|---|
| Automated suite validating retrieval/ranking via score distributions | **Offline eval pipeline with statistical quality gates** |
| Per-cohort thresholds | **Sliced/cohort-based evaluation** |
| Pre-release regression gate | **Eval-gated releases / model release regression testing** |
| Confidence-threshold abstention for hallucination | **Selective answering / calibrated abstention** |
| Downvotes → Knowledge Gaps queue → fixes | **Production feedback loop; eval set grown from field failures** |
| Admin UI exposing raw/weighted cosine scores + citations | **Eval observability / traceable retrieval scoring** |
| Embedding-model selection (Titan v2), chunking, ranking tuning | **Retrieval eval & ablation** |

One-liner to land it: *"I didn't have an eval team to hand me methodology — I derived distribution-based gating from first principles because deterministic asserts were lying to me. Cerebras is where I'd get to do that with real scale and rigor."*

---

## Honesty boundaries (he will respect these; bluffing kills the interview)

- Haven't run MMLU/GSM8K harnesses hands-on? Say so, then: "the gating statistics are the same ones I built; the harness is learnable in a week."
- Don't claim training experience — your lane is **inference-side quality**, which is the job.
- Don't overstate the RAG system's scale; its value is the *methodology*, not the QPS.
- If he goes deeper than you know (speculative decoding internals, MoE routing): "I know the concept at the level of its testing implications — here's how I'd test around it — but I won't pretend to know the internals."
