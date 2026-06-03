# Consumer SKILL.md Output Template

This is the template for the `SKILL.md` that ships with every generated TaC SDK.
It teaches control-plane LLMs to use the SDK via few-shot examples and concise reference.

---

## Design Rules for the Consumer SKILL.md

1. **Stay under 2,000 tokens (~500 lines)** — model context is precious
2. **Lead with examples, not explanation** — show 2–3 complete runnable code patterns first
3. **Group by workflow, not by module** — organize examples by goal, not by file
4. **Explicit state management** — always show `save_state`/`load_state` usage, even if brief
5. **Complete function tables** — list ALL public functions; partial tables mislead
6. **Triggering description** — the `description` frontmatter is how the skill auto-triggers;
   make it specific to the domain vocabulary (use domain nouns, domain verbs)

---

## Template

Copy this template, replace all `<...>` placeholders with domain content, and delete
any placeholder lines that aren't relevant.

```markdown
---
name: <task-name>-sdk
description: Use the <task-name> SDK to programmatically <task goal in plain language>.
Trigger when the user wants to <use case 1>, <use case 2>, or <use case 3>.
Also trigger when orchestrating sdk.<module>.*() calls for <domain noun> tasks,
or when building code pipelines that involve <domain-specific verb phrases>.
---

# <Task Name> SDK

SDK for <concise description of what the SDK enables>. Generate Python code that
imports and orchestrates the SDK's primitives; your code runs in the same Python
environment where the SDK is installed.

## Patterns

### Pattern 1: <Most Common Single-Turn Use Case>
```python
from sdk import core, llm

# <What this pattern achieves in one line>
items = core.fetch_<x>(source="...", limit=20)
items = core.dedupe_by(items, key="id")
results = llm.extract_<y>_many(
    [i["content"] for i in items],
    concurrency=8,
)
# Process results...
for item, result in zip(items, results):
    if result:
        print(f"{item['id']}: {result.<field>}")
```

### Pattern 2: <Second Common Use Case with LLM Classification>
```python
from sdk import core, llm, utils

# <What this pattern achieves>
batches = list(utils.batch(items, size=10))
all_classified = []
for batch in batches:
    classified = llm.classify_<x>_many(
        batch,
        categories=["<category_a>", "<category_b>"],
    )
    all_classified.extend(classified)

# Aggregate
by_category = {}
for item, result in zip(items, all_classified):
    if result and result.confidence > 0.7:
        by_category.setdefault(result.category, []).append(item)
```

### Pattern 3: Multi-Turn Agentic Workflow
```python
from sdk import core, llm, orchestrate

def executor(state: orchestrate.TaskState) -> orchestrate.TaskState:
    # <What happens each turn>
    new_items = core.fetch_<x>("...", limit=10)
    # Skip already-visited items
    new_items = [i for i in new_items if i["id"] not in state.visited]
    state.visited.extend(i["id"] for i in new_items)
    # Process and accumulate
    processed = llm.extract_<y>_many([i["content"] for i in new_items])
    state.results.extend([
        {**item, "extracted": r.__dict__ if r else None}
        for item, r in zip(new_items, processed)
    ])
    return state

final = orchestrate.run_task_loop(
    goal="<describe the goal>",
    executor_fn=executor,
    goal_met_fn=lambda s: len(s.results) >= 50,
    max_turns=5,
)
print(f"Done: {len(final.results)} results in {final.turn} turns")
# Resume if interrupted: orchestrate.resume_task_loop(final.task_id, executor, goal_met_fn)
```

## Available Primitives

### `sdk.core` — Deterministic Operations
| Function | Args | Returns | What it does |
|----------|------|---------|-------------|
| `fetch_<x>(source, limit, filters)` | `str, int, dict` | `list[dict]` | <description> |
| `filter_<x>(items, criteria)` | `list, dict` | `list[dict]` | <description> |
| `dedupe_by(items, key)` | `list, str` | `list[dict]` | Remove duplicates by field |
| `score_<x>(item, reference)` | `dict, str` | `float` | <description> |
| `segment_<x>(content, max_size)` | `str, int` | `list[str]` | <description> |

### `sdk.llm` — LLM-Powered Operations
| Function | Args | Returns | What it does |
|----------|------|---------|-------------|
| `extract_<x>(text)` | `str` | `ExtractResult \| None` | <description> |
| `classify_<x>(item, categories)` | `str, list[str]` | `ClassifyResult \| None` | <description> |
| `generate_<x>(spec)` | `str` | `GenerateResult \| None` | <description> |
| `summarize_<x>(items)` | `list[dict]` | `str \| None` | <description> |
| `*_many(items, concurrency=8)` | `list, int` | `list[Result \| None]` | Batch variant of any llm function |

### `sdk.orchestrate` — Multi-Turn State
| Function | Args | Returns | What it does |
|----------|------|---------|-------------|
| `run_task_loop(goal, executor_fn, goal_met_fn, max_turns)` | `str, Callable, Callable, int` | `TaskState` | Run agentic loop until done |
| `save_state(state, state_dir)` | `TaskState, Path` | `Path` | Persist state to disk |
| `load_state(state_dir, task_id)` | `Path, str` | `TaskState \| None` | Load saved state |
| `resume_task_loop(task_id, executor_fn, goal_met_fn)` | `str, Callable, Callable` | `TaskState` | Resume interrupted run |

### `sdk.utils` — Shared Helpers
| Function | What it does |
|----------|-------------|
| `call_llm(prompt, model, client, max_tokens)` | Provider-agnostic LLM call |
| `parse_json_robust(text)` | Parse JSON from LLM output (handles markdown fences) |
| `retry(fn, attempts, base_delay)` | Retry with exponential backoff |
| `batch(items, size)` | Yield batches of `size` from a list |
| `dedupe_by(items, key)` | Remove duplicates (also available in `core`) |
| `flatten(list_of_lists)` | Flatten one level of nesting |

## State Management

State is persisted to `.tac_state/<task_id>/state.json` after every turn.

```python
state.results    # list[dict] — accumulated output; extend freely
state.visited    # list[str] — IDs already processed; append to avoid reprocessing
state.metadata   # dict — arbitrary domain-specific data; add keys freely
state.turn       # int — current turn number (0-indexed)
state.status     # str — "running" | "completed" | "incomplete" | "failed"
```

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<key>   # or OPENAI_API_KEY=<key>
python examples/simple_usage.py  # verify installation
```
```

---

## Checklist: Before Shipping the Consumer SKILL.md

- [ ] `name` frontmatter matches the SDK folder name
- [ ] `description` uses domain-specific vocabulary that triggers correctly
- [ ] All three pattern examples are runnable (not pseudocode)
- [ ] Pattern 3 shows `resume_task_loop` usage
- [ ] All public functions appear in the tables (no omissions)
- [ ] All `<...>` placeholders have been replaced
- [ ] File is under 2,000 tokens (estimate: ~15 tokens/line → 130 lines max for inline code)
- [ ] The setup section has the correct `requirements.txt` install command
