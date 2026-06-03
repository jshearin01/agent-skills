---
name: task-as-code
description: >
  Generate a reusable, platform-agnostic Python SDK for any task domain using the Task as
  Code (TaC) pattern — the generalized form of Perplexity's Search as Code architecture.
  Use this skill whenever someone wants to make a complex multi-step task reusable and
  programmable: building an SDK for a domain (design systems, data analysis, document
  processing, code review, market research, competitive intelligence), creating a workflow
  that benefits from parallelism and composable primitives, or packaging agentic task logic
  so any LLM can orchestrate it via generated code. Trigger on: build me an SDK for X,
  make X programmatic, create a reusable workflow for X, turn X into code, generate a
  design system SDK, I want to automate X with an LLM, package this as a reusable skill,
  or any request to structure a complex domain task as composable Python building blocks.
---

# Task as Code (TaC)

A meta-skill for creating domain-specific, reusable Python SDKs that expose task
primitives for LLM orchestration — the platform-agnostic generalization of Perplexity's
Search as Code (SaC) architecture.

## What is Task as Code?

Traditional LLM usage treats a task as a single prompt: hand the model a goal and expect
everything in one context window. TaC inverts this: instead of a monolithic prompt, you
expose the task's *building blocks* as a Python SDK. A control-plane LLM then generates
Python code that composes those building blocks into a bespoke pipeline for each specific
request.

**The three layers of every TaC SDK:**

1. **Control Plane** — An LLM generates Python orchestration code tailored to each request
2. **SDK Layer** — Composable Python primitives (atomic ops + LLM sub-calls with embedded prompts)
3. **State Layer** — Filesystem-based persistence for multi-turn agentic workflows

This gives you composability, efficiency (parallelism, batching), reusability across
projects, and adaptability — the control-plane LLM designs a new pipeline per request,
not a fixed one.

**Read `references/pattern-theory.md` for the full TaC architecture deep dive before starting.**

---

## When to Create a TaC SDK

TaC is the right pattern when:
- The task has 5+ repeatable atomic operations (fetch, filter, transform, score, etc.)
- Workflows vary enough per request that a single prompt is inefficient or fragile
- The task benefits from parallelism or multi-turn state (many sub-calls per task)
- You want the task reusable across projects as an installable packaged skill

It's overkill when the task is a single LLM call with minor variation. Use a prompt
template in that case.

---

## Step 1: Analyze the Task Domain

Before writing any code, reason carefully about the domain. Ask:

1. **What is the goal?** (e.g., "generate a design system", "analyze a codebase")
2. **What are the atomic operations?** List every distinct sub-operation the task requires
3. **Which operations are deterministic vs. intelligence-requiring?**
   - Deterministic: fetch, filter, sort, deduplicate, transform → `core.py`
   - Intelligence-required: extract, classify, generate, summarize, validate → `llm.py`
4. **What data flows between operations?** Define input/output types per primitive
5. **What state must persist across turns?** (partial results, visited items, counters)

Document this analysis as inline comments — it seeds the auto-generated SKILL.md.

**Read `references/sdk-design.md` before Step 3 (implementation).**

---

## Step 2: Design the Primitive Hierarchy

Organize primitives into two tiers:

**Tier 1 — Atomic Primitives** (lowest level, single-purpose):
- One thing, pure Python, no LLM calls
- Named with verbs: `fetch_`, `filter_`, `dedupe_`, `score_`, `transform_`, `batch_`
- Typed parameters and return types throughout

**Tier 2 — Composite Operations** (higher level, common patterns):
- Combine 2–4 atomics into common workflows
- May include one LLM sub-call
- Named for the compound action: `fetch_and_rank_`, `search_and_extract_`

**Domain type → primitive pattern mapping:**

| Domain Type | Example | Core Primitives | LLM Primitives |
|------------|---------|----------------|----------------|
| Retrieval | Web research | `fetch_`, `filter_`, `dedupe_`, `rank_` | `extract_`, `verify_` |
| Generation | Design systems | `parse_spec_`, `validate_`, `assemble_` | `plan_`, `generate_`, `refine_` |
| Analysis | Code review | `load_`, `profile_`, `segment_`, `score_` | `classify_`, `summarize_` |
| Transformation | ETL / format conversion | `read_`, `map_`, `normalize_`, `write_` | `enrich_`, `infer_` |

---

## Step 3: Scaffold the SDK Structure

Run the scaffold script to create the folder structure:

```bash
python scripts/scaffold_sdk.py <task-name>
```

This creates:

```
<task-name>-sdk/
├── SKILL.md              ← Consumer skill (generate last, in Step 6)
├── sdk/
│   ├── __init__.py       ← Public API exports
│   ├── core.py           ← Tier 1 atomic primitives (deterministic)
│   ├── llm.py            ← Tier 2 LLM-powered operations + embedded prompts
│   ├── orchestrate.py    ← Agentic loop + TaskState + filesystem persistence
│   └── utils.py          ← Shared helpers (call_llm, parse_json, retry, batch)
├── examples/
│   ├── simple_usage.py   ← Stateless single-turn example
│   └── agentic_usage.py  ← Multi-turn agentic example with state save/load
├── prompts/
│   └── system.md         ← System prompt for the control-plane LLM
└── requirements.txt
```

---

## Step 4: Implement the SDK Modules

### `sdk/core.py` — Atomic Primitives

Write pure Python functions. Rules:
- Every function has type hints + complete docstring (Args/Returns/Example)
- No global state; all dependencies are explicit parameters
- Functions are idempotent where possible
- Raise descriptive exceptions, never silently fail

```python
# Pattern for core.py
def fetch_items(
    source: str,
    limit: int = 10,
    filters: dict[str, str] | None = None,
) -> list[dict]:
    """Fetch items from source with optional filtering.

    Args:
        source: URL or identifier for the data source.
        limit: Maximum number of items to return.
        filters: Optional key-value filters to apply.

    Returns:
        List of item dicts with at minimum {"id", "content"} keys.

    Example:
        items = fetch_items("https://api.example.com/data", limit=20)
    """
    ...
```

### `sdk/llm.py` — LLM-Powered Operations

Embed prompts as module-level constants. The most important rule: each function owns
exactly ONE `_PROMPT_*` constant, never assembled inline.

```python
# Pattern for llm.py
_PROMPT_CLASSIFY = """\
Classify the item into one of: {categories}.
Return JSON: {{"category": "<choice>", "confidence": <0-1>, "reason": "<sentence>"}}
Item: {item}"""

@dataclass
class ClassifyResult:
    category: str
    confidence: float
    reason: str

def classify_item(item: str, categories: list[str], client=None) -> ClassifyResult | None:
    """Classify an item into one of the provided categories. ..."""
    prompt = _PROMPT_CLASSIFY.format(categories=", ".join(categories), item=item)
    raw = call_llm(prompt, client=client)
    return parse_json_robust(raw, ClassifyResult)

def classify_many(items, categories, concurrency=8, client=None) -> list[ClassifyResult | None]:
    """Batch-classify items using thread-pool concurrency. ..."""
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        return [f.result() for f in [pool.submit(classify_item, i, categories, client) for i in items]]
```

**Provide both `_single` and `_many` variants for every LLM operation.** Batch functions
are the primary path for production use.

### `sdk/orchestrate.py` — Agentic Loop + State

See `references/sdk-design.md` §State Management for the full `TaskState` schema and
turn-loop pattern. At minimum implement:
- `TaskState` — serializable dataclass with `task_id`, `goal`, `turn`, `results`, `visited`, `metadata`
- `save_state(state, state_dir)` — atomic write (write-temp-then-rename)
- `load_state(state_dir, task_id)` — returns `TaskState | None`
- `run_task_loop(goal, executor_fn, goal_met_fn, max_turns)` — the main loop
- `resume_task_loop(task_id, executor_fn, goal_met_fn)` — resume interrupted runs

### `sdk/utils.py` — Shared Helpers

Include: `call_llm`, `parse_json_robust`, `retry`, `batch`, `dedupe_by`, `flatten`.

`call_llm` must be provider-agnostic: auto-detect `ANTHROPIC_API_KEY` → use `anthropic`
SDK; else `OPENAI_API_KEY` → use `openai` SDK; else raise `LLMConfigError`.

See `references/sdk-design.md` for complete implementation patterns.

---

## Step 5: Write Examples and System Prompt

**`examples/simple_usage.py`** — 3–5 core SDK functions, stateless, runnable with
`python examples/simple_usage.py` (with env vars set).

**`examples/agentic_usage.py`** — demonstrates `run_task_loop`, state save/load,
and `resume_task_loop` for interrupted recovery.

**`prompts/system.md`** — the system prompt the control-plane LLM reads when using
the SDK. Must stay under 2,000 tokens. Structure:
1. Purpose statement (1 paragraph)
2. Available modules with function table
3. 2–3 complete few-shot orchestration examples
4. State management cheatsheet

---

## Step 6: Generate the Consumer SKILL.md

Run the generator after implementing all modules:

```bash
python scripts/gen_consumer_skill.py <task-name>-sdk/
```

Or generate manually following `references/skill-output-template.md`.

The consumer SKILL.md ships with the SDK and teaches other LLMs to use it. It must:
- Have YAML frontmatter with a triggering `description`
- Stay under 2,000 tokens / 500 lines
- Lead with 2–3 complete code examples before any explanation
- List ALL public functions in a table grouped by module
- Show the state management pattern explicitly

---

## Output Checklist

Before considering the SDK complete:

- [ ] `sdk/__init__.py` exports all public functions from all modules
- [ ] Every `core.py` / `llm.py` function has type hints + docstring + example
- [ ] Every `llm.py` function has a module-level `_PROMPT_*` constant
- [ ] `orchestrate.py` implements `TaskState`, `save_state`, `load_state`, `run_task_loop`, `resume_task_loop`
- [ ] `utils.py` implements `call_llm` (provider-agnostic), `parse_json_robust`, `retry`, `batch`, `dedupe_by`, `flatten`
- [ ] `examples/simple_usage.py` runs without modification (with env vars set)
- [ ] `examples/agentic_usage.py` demonstrates state save/load and produces `.tac_state/`
- [ ] `prompts/system.md` < 2,000 tokens, includes function table + 2 code examples
- [ ] `SKILL.md` < 500 lines, has frontmatter, lists all public functions
- [ ] `requirements.txt` pins all direct dependencies

---

## Reference Files

| File | When to Read |
|------|-------------|
| `references/pattern-theory.md` | **Before starting** — TaC pattern theory, domain taxonomy, failure modes |
| `references/sdk-design.md` | **Before implementing** — naming, prompts, state management, testing |
| `references/skill-output-template.md` | **Before Step 6** — template + rules for the consumer SKILL.md |

## Scripts

| Script | Usage |
|--------|-------|
| `scripts/scaffold_sdk.py <name>` | Scaffold the full SDK folder with placeholder files |
| `scripts/validate_sdk.py <path>` | Validate SDK completeness and quality |
| `scripts/gen_consumer_skill.py <path>` | Introspect SDK and generate the consumer SKILL.md |
