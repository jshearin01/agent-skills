---
name: ai-slop-detector
description: >
  Detect and remediate AI-generated slop in copywriting/text, frontend UI/design, React
  components, and backend/architecture code. Use this skill whenever reviewing code before
  shipping, auditing AI-generated content, doing code reviews, evaluating copywriting, or
  when asked to improve text/UI/code that looks or feels AI-generated. Trigger on phrases
  like: does this look AI-generated, clean up this copy, this looks like AI slop, review
  this code for quality, make this less AI, improve this UI, audit for vibe coding
  anti-patterns, this copy sounds robotic, or any request to review or improve AI-assisted
  output across text, UI, or code.
---

# AI Slop Detector & Remediator

A comprehensive skill for detecting AI-generated "slop" across four domains — **copywriting/text**, **UI/design**, **React/frontend code**, and **backend/architecture** — and providing actionable, prescriptive fixes with before/after examples.

## Quick Reference: Domain Index

| Domain | Reference File | Key Slop Signals |
|--------|---------------|-----------------|
| Copywriting / Text | [references/text-slop.md](references/text-slop.md) | Buzzwords, passive voice, structure tells |
| UI / Design | [references/ui-slop.md](references/ui-slop.md) | Purple gradients, Inter font, 3-card grids |
| React / Frontend Code | [references/code-slop.md](references/code-slop.md) | God components, useEffect abuse, no error handling |
| Backend / Architecture | [references/code-slop.md](references/code-slop.md) | N+1 queries, hardcoded secrets, no layer separation |

**Always load the relevant reference file(s) before diagnosing or fixing.**

---

## Workflow

### Step 1 — Identify Domain(s)
Determine what's being reviewed: text, UI/CSS/HTML, React, backend, or a mix.

### Step 2 — Load Reference File
Read the appropriate reference `.md` file(s). For cross-domain reviews, load all relevant ones.

### Step 3 — Scan & Flag
Work through the content systematically. For each slop signal:
- Name the specific pattern (use the pattern names from the reference files)
- Quote or point to the exact location
- Severity: 🔴 Critical (ships broken/insecure/embarrassing) / 🟡 Medium (hurts quality/trust) / 🟢 Minor (polish/style)

### Step 4 — Remediate
For each flagged issue provide:
1. **Why it's slop** — one-sentence explanation
2. **Before** — the problematic excerpt (quoted or referenced)
3. **After** — a concrete rewrite or fix
4. **Principle** — the rule being violated

### Step 5 — Summary Report
End every audit with:
- **Slop density**: Low / Medium / High / Severe
- **Top 3 highest-impact fixes** (prioritized by severity then effort)
- **Full checklist** of all issues found, ordered by severity

---

## Universal Slop Signals (All Domains)

These appear across text, code comments, and UI copy alike:

- **Over-hedging**: "It's worth noting...", "It's important to understand...", "Please note..."
- **Fake depth**: Claims complexity/nuance/comprehensiveness without demonstrating it
- **Structural uniformity**: Every section identical in length/format — AI loves symmetry, humans don't
- **Missing failure modes**: No error states, edge cases, loading states, or empty states
- **Passive voice authority**: "It is considered best practice" instead of owning a position
- **Unnecessary preamble**: Restating the question before answering it
- **The not-just-X-but-Y construction**: "Not just a tool, but a partner" — statistically overrepresented in AI text
- **Excessive caveat stacking**: Multiple hedges in the same sentence dilute every claim

---

## Scripts

For programmatic/CI use, see:
- [`scripts/text-scanner.js`](scripts/text-scanner.js) — Flag AI slop words/phrases in bulk text
- [`scripts/css-audit.js`](scripts/css-audit.js) — Detect generic AI UI patterns in CSS/HTML/JSX
- [`scripts/code-review.js`](scripts/code-review.js) — Scan JS/TS/React files for AI code anti-patterns

Run any script with `node <script> --help` for usage.
