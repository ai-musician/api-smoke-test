https://www.linkedin.com/jobs/view/inference-ml-api-sdet-at-cerebras-4436348819/
# Master Coding Practice List — Cerebras SDET (combined, deduped)

**Merged 2026-07-30 from 5 sources:** `Claude_Coding_Practice_List.md`, `Claude_New_Coding_Questions.md`, `Aug coding interview - Sheet1.pdf`, `cerebras-4436348819 - Sheet1.pdf` (candidate-report research), `cerebras-4436348819 - Sheet2.pdf` (Gemini nested-structure list). Duplicates appear once, in their highest-priority tier.

**Calibration:** LeetCode-medium, live HackerRank pad, ~15–20 min per problem in Python. A Cerebras QE candidate specifically reported a **2D array manipulation** problem (and ran out of time). Cerebras-tagged on aggregators: Flood Fill, Roman to Integer, Product of Array Except Self, Make String a Subsequence. Matrix multiplication comes up because of the hardware.

Legend: 🔴 = directly Cerebras-reported/tagged · 💰 = LeetCode premium · [HR] = HackerRank

---

## Tier 1 — 2D array / matrix (the confirmed Cerebras topic — do ALL)

- [x] 🔴 [48. Rotate Image](https://leetcode.com/problems/rotate-image/) — the classic in-place manipulation (reverse rows, then transpose)
- [x] 🔴 [54. Spiral Matrix](https://leetcode.com/problems/spiral-matrix/) — index discipline under pressure
- [x] 🔴 [73. Set Matrix Zeroes](https://leetcode.com/problems/set-matrix-zeroes/) — in-place, constant-space twist
- [x] [74. Search a 2D Matrix](https://leetcode.com/problems/search-a-2d-matrix/) — binary search on flattened indices
- [x] [240. Search a 2D Matrix II](https://leetcode.com/problems/search-a-2d-matrix-ii/) — staircase search from a corner
- [ ] [289. Game of Life](https://leetcode.com/problems/game-of-life/) — neighbor counting + in-place state encoding
- [ ] [498. Diagonal Traverse](https://leetcode.com/problems/diagonal-traverse/) — direction-flipping index walk
- [x] [36. Valid Sudoku](https://leetcode.com/problems/valid-sudoku/) — 2D + hashing; *validation* framing an SDET interviewer likes
- [ ] [HR] [2D Array — Hourglass Sum](https://www.hackerrank.com/challenges/2d-array/problem)
- [ ] [HR] [Matrix Layer Rotation](https://www.hackerrank.com/challenges/matrix-rotation-algo/problem)
- [ ] [HR] [Forming a Magic Square](https://www.hackerrank.com/challenges/magic-square-forming/problem)
- [ ] 🔴 **Naive matrix multiplication from scratch** (no LC number): write `matmul(A, B)`, state O(n³), verify against numpy with float tolerance, discuss how you'd parallelize/test it — reported in Cerebras loops because of the hardware

## Tier 2 — Grid BFS/DFS (Flood Fill was Cerebras-tagged)

- [ ] 🔴 [733. Flood Fill](https://leetcode.com/problems/flood-fill/)
- [x] [200. Number of Islands](https://leetcode.com/problems/number-of-islands/) — the only "graph" problem worth prepping
- [ ] [695. Max Area of Island](https://leetcode.com/problems/max-area-of-island/)
- [ ] [994. Rotting Oranges](https://leetcode.com/problems/rotting-oranges/) — multi-source BFS

## Tier 3 — Arrays, strings, hashmaps (Cerebras-tagged / most likely)

- [ ] 🔴 [238. Product of Array Except Self](https://leetcode.com/problems/product-of-array-except-self/)
- [ ] 🔴 [13. Roman to Integer](https://leetcode.com/problems/roman-to-integer/)
- [ ] 🔴 [2825. Make String a Subsequence Using Cyclic Increments](https://leetcode.com/problems/make-string-a-subsequence-using-cyclic-increments/)
- [x] [1. Two Sum](https://leetcode.com/problems/two-sum/) — hash-map reflex; know the "now make it O(n)" follow-up path
- [ ] [3. Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) — sliding window
- [ ] [49. Group Anagrams](https://leetcode.com/problems/group-anagrams/) — dict-of-lists with computed key
- [ ] [347. Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) — `Counter` + `heapq.nlargest`
- [ ] [692. Top K Frequent Words](https://leetcode.com/problems/top-k-frequent-words/) — the tie-break twist (count desc, name asc)
- [ ] [56. Merge Intervals](https://leetcode.com/problems/merge-intervals/) — sort-then-sweep
- [ ] [151. Reverse Words in a String](https://leetcode.com/problems/reverse-words-in-a-string/)
- [ ] [242. Valid Anagram](https://leetcode.com/problems/valid-anagram/)
- [ ] [26. Remove Duplicates from Sorted Array](https://leetcode.com/problems/remove-duplicates-from-sorted-array/) — in-place two-pointer
- [ ] [443. String Compression](https://leetcode.com/problems/string-compression/) — in-place two-pointer
- [ ] [HR] [Sherlock and Anagrams](https://www.hackerrank.com/challenges/sherlock-and-anagrams/problem)
- [ ] [HR] [Frequency Queries](https://www.hackerrank.com/challenges/frequency-queries/problem)
- [ ] [HR] [Array Manipulation](https://www.hackerrank.com/challenges/crush/problem)
- [ ] [HR] [Sparse Arrays](https://www.hackerrank.com/challenges/sparse-arrays/problem)

## Tier 4 — Nested structures / JSON recursion (the flatten-dict family)

- [ ] **Flatten a nested dict** `{"a":{"b":1}}` → `{"a.b":1}` — the API-tester favorite; ~8-line reference solution + asserts in `Claude_New_Coding_Questions.md`
- [ ] [341. Flatten Nested List Iterator](https://leetcode.com/problems/flatten-nested-list-iterator/) — closest free LC match; **do this one**
- [ ] 💰 [339. Nested List Weight Sum](https://leetcode.com/problems/nested-list-weight-sum/) — carry depth down the recursion
- [ ] [394. Decode String](https://leetcode.com/problems/decode-string/) — recursion over nested string structure
- [ ] [385. Mini Parser](https://leetcode.com/problems/mini-parser/) — parse a nested list from a string (inverse direction)
- [ ] [2625. Flatten Deeply Nested Array](https://leetcode.com/problems/flatten-deeply-nested-array/) — JS-track problem; solve the idea in Python locally
- [ ] [2628. JSON Deep Equal](https://leetcode.com/problems/json-deep-equal/) — JS-track; equivalent to "diff two JSON objects"
- [ ] [2633. Convert Object to JSON String](https://leetcode.com/problems/convert-object-to-json-string/) — JS-track; custom serialization via recursion
- [ ] [HR] [Nested Lists](https://www.hackerrank.com/challenges/nested-list/problem) — plus recursive-dictionary-search variant
- [ ] [Exponent (ex-Pramp) — Flatten a Dictionary](https://www.tryexponent.com/questions?search=flatten+a+dictionary) — the literal interview question
- [ ] [InterviewBit — Flatten a Dictionary](https://www.interviewbit.com/) — exact match to the dot-notation version
- [ ] [GeeksforGeeks — flatten nested dictionary](https://www.geeksforgeeks.org/python-convert-nested-dictionary-into-flattened-dictionary/) — solutions to compare against

### Variant ladder (blank editor, one rung per sitting, 10–15 min each)

1. Flatten nested dict, dots only, from blank file in <3 min (`{"a":{"b":1}}` → `{"a.b":1}`)
2. Flatten with lists: `{"a":[{"b":1}]}` → `{"a[0].b":1}` — state your bracket-vs-dot choice out loud
3. Flatten iteratively with an explicit stack (no recursion — survives 2000-deep nesting)
4. Unflatten (the inverse): `{"a.b":1}` → `{"a":{"b":1}}` — `split(".")` + `setdefault` walk
5. Round-trip test: `unflatten(flatten(x)) == x`, plus 4–5 asserts at the bottom of the pad

### Edge cases to name unprompted (the "poke" list)

- **Empty dict as value:** `{"a": {}}` — keep the key or drop it? (empty dict is falsy; recursing into it silently drops `"a"`)
- **Key collisions:** `{"a.b": 1, "a": {"b": 2}}` — both map to `"a.b"`, silent overwrite → flag as data loss
- **Non-string keys:** `{1: "x"}` vs `{"1": "x"}` — identical flat output, round-trip loses type info
- **Depth limit:** Python recursion caps ~1000 levels → RecursionError; iterative version is the fix

### Reference solutions (muscle memory)

```python
def flatten(d, parent=""):
    out = {}
    for k, v in d.items():
        key = f"{parent}.{k}" if parent else k
        if isinstance(v, dict) and v:          # empty dict is falsy -> kept as leaf
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out

def flatten_iter(d):                            # no recursion: survives any depth
    out, stack = {}, [("", d)]
    while stack:
        parent, cur = stack.pop()
        for k, v in cur.items():
            key = f"{parent}.{k}" if parent else k
            if isinstance(v, dict) and v:
                stack.append((key, v))
            else:
                out[key] = v
    return out

def unflatten(flat):
    out = {}
    for path, value in flat.items():
        parts = path.split(".")
        cur = out
        for p in parts[:-1]:                    # walk/create the folders
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = value                  # place the file
    return out

assert flatten({"a": {"b": 1}, "c": 2}) == {"a.b": 1, "c": 2}   # happy path
assert flatten({}) == {}                                        # empty input
assert flatten({"a": {}}) == {"a": {}}    # decide + defend: keep keys, no silent loss
assert flatten({"a": {"b": {"c": 1}}}) == {"a.b.c": 1}          # deep nesting
assert unflatten(flatten({"a": {"b": 1}})) == {"a": {"b": 1}}   # round-trip
```

### Verbal summary to rehearse (say while coding)

> "I walk the dict like folders on a computer, carrying the path as I go. Real values get written with their full path; empty dicts I keep as leaves so keys don't silently disappear. Every key touched once — O(n); recursion depth equals nesting depth."

## Tier 5 — Design / SDET-flavored (rate limiter, cache — on-theme for an inference API team)

- [ ] [146. LRU Cache](https://leetcode.com/problems/lru-cache/) — the senior-screen classic; `OrderedDict` or dict+DLL
- [ ] [20. Valid Parentheses](https://leetcode.com/problems/valid-parentheses/) — stack reflex
- [ ] [155. Min Stack](https://leetcode.com/problems/min-stack/)
- [ ] [981. Time Based Key-Value Store](https://leetcode.com/problems/time-based-key-value-store/)
- [ ] 💰 [362. Design Hit Counter](https://leetcode.com/problems/design-hit-counter/) — basically a rate limiter; free alternative below
- [ ] 💰 [359. Logger Rate Limiter](https://leetcode.com/problems/logger-rate-limiter/)
- [ ] 💰 [346. Moving Average from Data Stream](https://leetcode.com/problems/moving-average-from-data-stream/) — trivial with `deque`
- [ ] **Rate limiter from scratch**: `allow(client_id, ts) -> bool`, sliding window (`deque` per client) or token bucket
- [ ] **Retry with exponential backoff + jitter**: wrap a flaky function, max attempts, backoff cap (~10 lines)
- [ ] **Bounded-concurrency async fetcher**: N URLs, ≤K in flight (`asyncio.Semaphore` + `gather`) — resume says asyncio, be able to prove it from a blank file in <10 min
- [ ] **Producer/consumer** or "process N requests with retry logic"

## Tier 6 — Practical SDET prompts (no LC number — write from scratch)

- [ ] **Parse a log file**: count errors per service / per-endpoint error rates, top-N with tie-break (`defaultdict`, `Counter.most_common`)
- [ ] **Percentiles**: given (timestamp, latency_ms, status) records compute p50/p95/p99 + error rate — nearest-rank: `s[max(0, ceil(p/100*n)-1)]`
- [ ] **Diff two JSON objects** (added/removed/changed keys) — compare ignoring field order; floats with tolerance (directly relevant to comparing model outputs)
- [ ] **Validate/parse a version string, IP address, or bracket sequence** — `parse_version` + full pytest suite already done in `Claude_pytest_drill.py`
- [ ] **Dedupe and aggregate API response records**
- [ ] **"Here's a function — write test cases for it"**: enumerate out loud — happy, boundary, empty, invalid-type, duplicates, ordering, unicode, huge input, error-raising (`pytest.raises`, `@pytest.mark.parametrize`)

## Tier 7 — Warm-up easies (classic SDET screeners, ~30 min total)

- [x] [125. Valid Palindrome](https://leetcode.com/problems/valid-palindrome/)
- [ ] [98. Validate Binary Search Tree](https://leetcode.com/problems/validate-binary-search-tree/)
- [ ] [88. Merge Sorted Array](https://leetcode.com/problems/merge-sorted-array/)
- [ ] [387. First Unique Character in a String](https://leetcode.com/problems/first-unique-character-in-a-string/)
- [ ] [HR] [New Year Chaos](https://www.hackerrank.com/challenges/new-year-chaos/problem)

---

## Python fluency checklist (type these until automatic)

```python
from collections import defaultdict, Counter, deque
import heapq, math, re

Counter(words).most_common(k)
sorted(items, key=lambda x: (-x[1], x[0]))        # count desc, name asc
d = defaultdict(list); d[key].append(v)
heapq.nlargest(k, nums)
[[r[i] for r in matrix] for i in range(len(matrix[0]))]  # transpose
enumerate / zip / dict.get(k, default) / set ops
f-strings; str.split / strip / join; re.match for log lines
def percentile(vals, p):
    s = sorted(vals)
    return s[max(0, math.ceil(p/100*len(s)) - 1)]  # nearest-rank
```

**Gotchas that bite in a pad:** mutable default args (`def f(x, acc=[])`), integer division `//` vs `/`, shallow vs deep copy of 2D lists (`[[0]*n for _ in range(m)]`, never `[[0]*n]*m`), modifying a dict while iterating, `isinstance(True, int)` is `True` (the bool trap).

## Test-writing enumeration checklist (say OUT LOUD before typing tests)

1. happy path — 2. boundary — 3. duplicates — 4. empty/missing — 5. invalid type — 6. malformed value — 7. ordering — 8. error-raising (check the message too: `pytest.raises(ValueError, match=...)`) — 9. float precision (`pytest.approx`, never `==`)

Full worked example with `@pytest.mark.parametrize` + `ids=`: `Claude_pytest_drill.py` (34 passing tests over `parse_version` and `apply_discount`).

## What NOT to grind

Hard DP, advanced graphs, tries, segment trees — zero probability in an SDET HM screen. Every hour there is stolen from perf/ML Q&A prep.

## In-the-pad protocol (scored behavior, rehearse it)

1. Restate the problem + one clarifying question (empty? duplicates? sorted? size?).
2. State brute force → optimized approach + complexity **before typing**; get a nod.
3. Clean idiomatic Python, real variable names (`Counter`, `defaultdict`, `enumerate`, f-strings — reads as senior).
4. **"Let me test this"** — walk 2–3 edge cases against your own code, add asserts at the bottom. This is THE differentiating SDET signal.
5. Stuck 2+ min: think out loud, simplify. Watch the clock — if two problems in 45 min, ≤20 min on the first.
6. Practice in the HackerRank editor itself (no autocomplete) and its stdin/stdout format.

## Schedule to Tue 8/4 (compressed from the 10-day pacing)

- **Thu 7/30 + Fri 7/31 (30 min/day):** Tier 7 warm-ups fast, then 2 problems/day from Tier 1 (start 48, 54, 73), timed, bare editor.
- **Sat 8/1 (90 min):** log-parsing + percentile prompts (Tier 6), Merge Intervals, one more matrix + one grid-BFS (733 or 200); then rate limiter + async fetcher (Tier 5). Naive matmul once.
- **Sun 8/2 (30 min):** LRU cache + pytest-writing drill (`Claude_pytest_drill.py` from blank); one problem on hackerrank.com for I/O format; flatten-dict ladder rungs 1–2.
- **Mon 8/3:** nothing new. Re-type async fetcher, percentile function, and base flatten from blank. Stop.
