# Task as Code (TaC) — Pattern Theory

## Table of Contents
1. Origin: Search as Code
2. The Generalization
3. Three Architectural Layers
4. Task Domain Taxonomy
5. The Control-Plane LLM's Role
6. Failure Modes to Avoid

---

## 1. Origin: Search as Code

Perplexity's Search as Code (SaC, 2026) introduced a new architecture for agentic search.
Instead of calling a search API as a monolithic black box, they rearchitected their search
stack into composable Python SDK primitives. A control-plane LLM generates Python code
that orchestrates these primitives — running in a secure sandbox — to build bespoke
retrieval pipelines tailored to each specific request.

The results were dramatic: SaC achieved 2.5× higher performance than non-SaC systems on
the WANDR complex research benchmark, while reducing token usage by up to 85% on specific
tasks. The key mechanism: instead of forcing models into repeated serial function calls
(where each call brings ALL results into model context), models write code that runs
hundreds of retrieval operations deterministically, then surface only the most relevant
information as model context.

The architectural insight SaC demonstrated:
> "Every part of this architecture is necessary to unlock these capabilities. Without
> intelligent models, the system cannot reason over search strategy. Without sandboxes,
> models are forced into serial I/O and inefficient token-space processing. And without
> an atomized search stack, the model has nothing to orchestrate."

---

## 2. The Generalization

SaC's power comes not from search-specific properties but from a general architectural
principle: **expose domain operations as composable SDK primitives, then let a
control-plane LLM generate orchestration code.**

This principle applies to any task domain with sufficient complexity:

| Domain | Traditional Approach | TaC Approach |
|--------|---------------------|--------------|
| Web Research | Call search API → hand full results to model | `sdk.search.web_many()`, `sdk.llm.extract_fields()`, `sdk.core.dedupe_by()` |
| Design System Generation | Giant "generate a design system" prompt | `generate_color_tokens()`, `create_component()`, `validate_contrast()`, `assemble_theme()` |
| Data Analysis | Paste CSV, ask for insights | `load_dataset()`, `profile_column()`, `detect_anomalies()`, `score_correlation()`, `summarize_trends()` |
| Code Review | Paste code, ask for feedback | `parse_ast()`, `detect_patterns()`, `score_complexity()`, `classify_smell()`, `suggest_refactor()` |
| Document Processing | "Summarize this document" | `chunk_document()`, `extract_entities()`, `classify_section()`, `score_relevance()`, `synthesize_summary()` |
| Competitive Intelligence | "Research competitor X" | `fetch_company_data()`, `extract_product_features()`, `score_threat()`, `compare_positioning()` |

The pattern is always: **atomic primitives + embedded LLM sub-calls + orchestrating code.**

---

## 3. Three Architectural Layers

### Layer 1: Control Plane (the orchestrating LLM)

The control-plane LLM:
- Reads the task goal and the SDK's `SKILL.md`
- Generates Python code that orchestrates SDK calls into a task-specific pipeline
- Adapts the pipeline to the specific request — NOT a fixed pipeline
- Handles control flow: conditionals, loops, fan-outs, retries, early exits

**Key insight:** The LLM should not be writing business logic inline. It should be
*assembling pre-built, domain-specific primitives* into a pipeline. Think of the LLM
as a senior engineer who knows the SDK well enough to write orchestration code, but
delegates the actual domain operations to the SDK's battle-tested functions.

**Gap filling:** When the SDK doesn't cover something, the model writes plain Python
code alongside SDK calls. The SDK provides core domain primitives; Python fills gaps.
A complex regex, a custom aggregation, a domain-specific heuristic — these belong in
the generated orchestration code, not in the SDK itself.

### Layer 2: SDK Layer (domain primitives)

The SDK provides:

- **Atomic primitives (`core.py`)** — single-purpose, deterministic, typed Python functions
- **LLM-powered operations (`llm.py`)** — functions encapsulating exactly one LLM sub-call,
  with the prompt stored as a module-level constant
- **Composite helpers** — optional shortcuts combining 2–4 primitives for common patterns;
  these are conveniences, never the only path

The SDK is designed for the control-plane LLM, not for human developers. Its design goals:
- **Discoverable** — function names predict behavior; no surprises
- **Composable** — outputs of one function are valid inputs of another
- **Batch-capable** — every operation has a `*_many` variant for high-volume use
- **Transparent** — all prompts visible at module level, not buried in logic

### Layer 3: State Layer (filesystem persistence)

Multi-turn agentic workflows need to persist intermediate state across turns. TaC uses
filesystem-based serialization (JSON files) rather than in-memory state (REPL variables).

**Why filesystem over REPL?**

Perplexity tested both approaches and found: filesystem-based serialization provides
better reliability on long trajectories. The hypothesis is that requiring models to
*declare* what state matters — by writing serialization code — helps them manage
state more deliberately. Implicit REPL state accumulates without accounting, leading
to "cluttered namespace" problems on long runs (like a 100-cell Jupyter notebook).

**State layout:**
```
.tac_state/
└── <task_id>/
    ├── state.json       ← Current TaskState (atomically overwritten each turn)
    ├── turns.jsonl      ← Append-only turn log (one entry per turn)
    └── artifacts/       ← Large intermediate files
        ├── turn_0/
        └── turn_1/
```

---

## 4. Task Domain Taxonomy

Different domains require different SDK shapes. The four main domain types:

### Type 1: Retrieval Domains
**Goal:** Find and collect relevant information from external sources.

**Examples:** Web research, knowledge base search, patent discovery, news monitoring

**Primitive pattern:**
- `fetch_*` — acquire data (HTTP, API, filesystem)
- `filter_*` — narrow by criteria  
- `rank_*` / `score_*` — relevance scoring
- `dedupe_*` — remove duplicates by key
- `extract_*` *(LLM)* — pull structured fields from unstructured text
- `verify_*` *(LLM)* — confirm facts, validate extraction quality

**Orchestration shape:** fan-out over query variants → filter → rank → extract → verify → dedupe

**Key challenge:** Token pollution. Monolithic search brings ALL results into context; TaC
primitives let the model filter/extract before surfacing anything to the main context.

### Type 2: Generation Domains
**Goal:** Produce structured artifacts from specifications.

**Examples:** Design systems, code generation, report writing, API design, test suite creation

**Primitive pattern:**
- `parse_spec_*` *(LLM)* — understand and normalize the input specification
- `plan_*` *(LLM)* — decompose spec into ordered sub-tasks
- `generate_*` *(LLM)* — produce atomic artifact components
- `validate_*` — check generated artifacts against rules (deterministic + LLM)
- `assemble_*` — combine components into the final artifact
- `refine_*` *(LLM)* — improve artifact based on validation feedback

**Orchestration shape:** parse → plan → parallel generate → validate → assemble → refine loop

**Key challenge:** Coherence across components. The `assemble_*` and `validate_*` functions
must enforce cross-component consistency (e.g., design tokens used consistently across
all components).

### Type 3: Analysis Domains
**Goal:** Produce insights, scores, or structured summaries from input data.

**Examples:** Code review, data analysis, security audit, UX review, financial analysis

**Primitive pattern:**
- `load_*` — read input data in various formats
- `profile_*` — compute statistical or structural properties
- `segment_*` / `chunk_*` — divide input into analysis units
- `classify_*` *(LLM)* — assign categories to segments
- `score_*` — compute quality/relevance/risk scores
- `summarize_*` *(LLM)* — produce natural language synthesis

**Orchestration shape:** load → profile → segment → parallel classify/score → aggregate → summarize

**Key challenge:** Analysis unit sizing. Segments must be large enough to be meaningful but
small enough for LLM calls to be accurate. Profile the input first to set segment sizes.

### Type 4: Transformation Domains
**Goal:** Convert input data into a different structure, format, or schema.

**Examples:** ETL pipelines, format conversion, data normalization, schema migration

**Primitive pattern:**
- `read_*` — parse source format
- `validate_schema_*` — verify input structure
- `map_*` — transform fields according to mapping rules
- `normalize_*` — standardize values (dates, currencies, units)
- `enrich_*` *(LLM)* — add inferred fields from existing data
- `write_*` — serialize to target format

**Orchestration shape:** read → validate → map → normalize → enrich → write

**Key challenge:** Data fidelity. Every transformation must be auditable. Build a
`transform_record(record, context)` function that returns `{"input": record, "output": transformed, "changes": [...]}`
for full traceability.

---

## 5. The Control-Plane LLM's Role

The control-plane LLM reads the SDK's `SKILL.md` and `prompts/system.md` before
generating orchestration code. Its cognitive model of the SDK must include:

1. **What primitives exist** — the function inventory (from the SKILL.md table)
2. **When to use each** — the usage guidance in SKILL.md
3. **How to compose them** — the few-shot examples in SKILL.md
4. **How to manage state** — the state management section in SKILL.md

The control-plane LLM brings domain-agnostic orchestration skills (loops, parallelism,
error handling, data transformation) and applies them to the SDK's domain-specific
primitives. The SDK teaches the domain; the model brings the orchestration.

**Implication for SDK design:** Every function in the SDK must be self-describing.
The LLM cannot run the code to experiment. It must infer correct usage from the function
name, docstring, and type hints alone. This is why naming and docstrings are not optional.

---

## 6. Failure Modes to Avoid

### Failure 1: Coarse SDK (Insufficiently Atomic)
The SDK exposes only end-to-end operations like `do_the_whole_task()`. The
control-plane LLM can't adapt the pipeline — there's nothing to compose.

**Fix:** Expose primitives at the lowest useful level of abstraction. High-level helpers
are aliases for common combinations, not the only options.

### Failure 2: Prompt Pollution (Prompts Mixed into Logic)
LLM prompts are buried inside functions or dynamically assembled from string fragments
in the function body. This makes them invisible to users of the SDK and impossible
to tune without reading implementation code.

**Fix:** Every LLM sub-call function owns exactly ONE `_PROMPT_*` constant at module
level. Prompts are templates with explicit `{variable}` placeholders, never f-strings
constructed dynamically inside function bodies.

### Failure 3: Implicit State (REPL-style Accumulation)
State grows implicitly as variables accumulate across turns. Long trajectories become
unpredictable as the namespace gets cluttered with partially-processed data.

**Fix:** Use explicit `TaskState` dataclasses with typed fields. Persist via
`save_state`. State transitions must be declared and logged, not implied.

### Failure 4: Monolithic `llm.py` (One Giant Prompt)
The SDK has one `llm.do_everything(task_description)` function that hands the whole
task to a model in a single prompt. This defeats the purpose of TaC.

**Fix:** Each LLM function does ONE thing. "Extract entities", "Classify sentiment",
"Generate a color token" are each separate functions with separate focused prompts.

### Failure 5: Missing Batch Variants
The SDK has `classify_item()` but not `classify_many()`. Processing 100 items requires
100 serial LLM calls instead of 100 parallel calls.

**Fix:** Every LLM operation must have a `*_many` batch variant using
`ThreadPoolExecutor` for immediate parallelism.

### Failure 6: Opaque Consumer SKILL.md
The consumer `SKILL.md` is just a function reference (docstrings pasted in). There are
no examples, no orchestration patterns, no guidance on when to use what.

**Fix:** The SKILL.md leads with 2–3 complete runnable code examples. Function tables
come after. The model learns by seeing patterns before studying a reference.
