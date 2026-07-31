# Session Context Prompt — Cerebras Interview Prep (saved 2026-07-30)

**Purpose:** If a Claude Code session is closed, paste or reference this file in a new session to restore full context. (Claude's persistent memory for this project folder also records the key facts automatically.)

---

## Who / what / when

- **Jean** — Sr. SDET at Netskope, interviewing for **Senior Software Engineer in Test, ML API Quality** at Cerebras.
- **HM screen: Tuesday 2026-08-04, 45 min, Microsoft Teams + HackerRank pad**, with **Sanjeev Gadgil** (Director, Inference Service Quality — career validation engineer: AMD SeaMicro → ChargePoint → Pavilion Data perf tools → Cerebras, 5 promotions).
- Jean's differentiators: solo-built RAG assistant (Claude + Pinecone) with statistical regression-gate test methodology; asyncio load-testing CLI; Callhome Gateway perf project (500 rps/node, <20ms, 99.9%, 16 TCs); K8s on-call/release ownership at Netskope.

## File convention (IMPORTANT)

**Every file Claude generates must be named with a `Claude_` prefix** — Jean uses multiple AI tools and identifies the source by prefix (`ChatGPT_*`, `Gemini_*` files exist in the same folder). All Claude prep files were renamed to this convention on 7/30.

## The two MASTER files (everything merged, checkbox format — Jean loves this design)

1. **`Claude_Master_Coding_Practice_List.md`** — coding prep for the pad. 7 priority tiers, checkboxes, clickable links. Merged+deduped from 5 sources: the two older Claude lists + 3 PDFs from `~/Downloads` ("Aug coding interview - Sheet1.pdf", "cerebras-4436348819 - Sheet1/Sheet2.pdf"). Markers: 🔴 Cerebras-reported (2D matrix, Flood Fill, matmul-from-scratch), 💰 LC premium, [HR] HackerRank. Includes the full flatten-dict deep-dive (variant ladder, edge-case "poke" list, verified reference solutions for flatten / flatten_iter / unflatten, verbal summary), Python fluency checklist, pytest 9-category enumeration checklist, and schedule to 8/4.
2. **`Claude_Master_Interview_QA_List.md`** — everything spoken. Merged from HM prep plan + Performance Testing Q&A + API Testing Q&A. 16 sections: verbatim 90-sec pitch, 3 STAR pillars, gap pre-empts, full question bank with bullet skeletons (⭐ highest probability, 🎯 maps to Sanjeev's own background), perf fundamentals (percentiles, Little's Law, coordinated omission), LLM inference metrics (TTFT/ITL/goodput), API status codes + methodology, SSE streaming traps, rapid-fire one-liners, verbatim bridges, red flags, 5 questions for Sanjeev (incl. 750MW + hardware-black-box variant), screen-share play (NEVER demo the Netskope bot; sanitized diagram, ask-first, 2-min time-box), Mon 8/3 logistics checklist, 45-min shape.

## Supporting files (kept as backups / detail)

- `Claude_HM_Screen_Prep_Plan_Sanjeev_Gadgil.md`, `Claude_Performance_Testing_QA.md`, `Claude_API_Testing_QA.md` — full scripted answers the QA master's skeletons reference (as *Perf Q#* / *API Q#*).
- `Claude_ML_Evaluation_QA.md` — **NOT yet merged into the QA master** (offered; pending Jean's decision).
- `Claude_pytest_drill.py` — parse_version + apply_discount with 34 passing tests; the test-writing drill (run via a venv — Homebrew Python blocks global pip, PEP 668).
- `Claude_New_Coding_Questions.md`, `Claude_Coding_Practice_List.md` — superseded by the coding master, kept.

## Where things stand / possible next steps

- Both masters are complete and self-contained; all old-file content migrated in full.
- **Offered, not yet done:** (1) timed mock interview — Cerebras-flavored coding prompt or firing ⭐ questions with critique; (2) merging ML eval Q&A into the QA master as new sections.
- Remaining schedule: Thu-Fri 30 min/day Tier 1 matrix + warm-ups · Sat 90 min log-parsing/percentiles/rate-limiter/async-fetcher + matmul · Sun LRU + pytest drill + flatten ladder · Mon logistics only, no new material.
