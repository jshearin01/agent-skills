# SDK Design Guide for Task as Code

## Table of Contents
1. Naming Conventions
2. Type Conventions
3. Prompt Engineering for SDK Functions
4. Module Implementation Details
5. State Management Patterns
6. Provider-Agnostic LLM Utility
7. Testing an SDK

---

## 1. Naming Conventions

### Module Names (fixed)
- `core.py` — deterministic atomic primitives only; no LLM calls
- `llm.py` — LLM-powered operations; each function owns one `_PROMPT_*` constant
- `orchestrate.py` — agentic loop, TaskState, filesystem persistence
- `utils.py` — shared infrastructure: `call_llm`, `parse_json_robust`, `retry`, `batch`

### Function Naming
All functions use `verb_noun` or `verb_noun_qualifier` patterns.

**Deterministic (`core.py`):**
```
fetch_<resource>(source, limit, ...)     → list[dict]
filter_<by_criteria>(items, criteria)    → list[dict]
dedupe_by(items, key)                    → list[dict]
score_<metric>(item, reference)          → float
transform_<how>(item, config)            → dict
segment_<how>(content, max_size)         → list[str]
rank_by(items, score_fn)                 → list[dict]
```

**LLM-powered (`llm.py`):**
```
extract_<what>(text, ...)               → ExtractResult | None
classify_<what>(item, categories, ...)  → ClassifyResult | None
generate_<what>(spec, ...)              → GenerateResult | None
summarize_<what>(items, ...)            → str | None
verify_<what>(claim, evidence, ...)     → VerifyResult | None
refine_<what>(draft, feedback, ...)     → str | None
```

**Batch variants (same module as single):**
```
extract_<what>_many(items, ...)         → list[ExtractResult | None]
classify_<what>_many(items, ...)        → list[ClassifyResult | None]
```

**Avoid:**
- Generic names: `process()`, `handle()`, `run()` — opaque to the control-plane LLM
- Noun-only names: `extractor()`, `classifier()` — use verbs
- Model-leaking names: `call_gpt4()`, `claude_classify()` — SDK must be model-agnostic
- Abbreviations: `ext_ent()` for `extract_entities()` — clarity over brevity

---

## 2. Type Conventions

Use simple, JSON-serializable types throughout:

```python
# Scalars
str, int, float, bool

# Collections
list[str], list[dict[str, Any]], list[T]

# Records (use typed dataclasses for structured results)
@dataclass
class ClassifyResult:
    category: str
    confidence: float
    reason: str

# Optionals (LLM calls can fail)
ClassifyResult | None        # single LLM call
list[ClassifyResult | None]  # batch; preserves alignment with input list

# Paths
Path                         # for filesystem operations

# LLM client injection
client: Any = None           # inject in tests; auto-detect in production
```

**Never use:**
- Pydantic models (adds heavy dependency; dataclasses are sufficient)
- `Union[X, Y]` syntax (use `X | Y` in Python 3.10+)
- Opaque `dict` returns without documenting expected keys in the docstring

---

## 3. Prompt Engineering for SDK Functions

### The Single-Prompt-Per-Function Rule

Each function in `llm.py` owns exactly **ONE prompt constant** at module level.
Never build prompts dynamically in function bodies.

```python
# ✅ CORRECT: One constant, used once
_PROMPT_EXTRACT_ENTITIES = """\
Extract all named entities from the text below.
Return a JSON array: [{{"entity": str, "type": "PERSON|ORG|LOCATION|DATE", "context": str}}]
If no entities found, return [].
Text: {text}"""

def extract_entities(text: str, client=None) -> list[EntityResult]:
    prompt = _PROMPT_EXTRACT_ENTITIES.format(text=text)
    ...

# ❌ WRONG: Prompt assembled in function body
def extract_entities(text: str, entity_types=None, client=None):
    types = entity_types or ["PERSON", "ORG"]
    prompt = f"Extract {', '.join(types)} from: {text}"  # Dynamic, invisible, hard to tune
    ...
```

### Prompt Quality Rules

1. **One instruction** — the prompt does exactly one thing
2. **Explicit output format** — always specify JSON schema when returning structured data
3. **Failure handling** — state what to return when the model can't answer
4. **Concrete example** — include one input/output pair in prompts > 5 lines
5. **Minimal context** — no preamble, no pleasantries, no "As an AI assistant..."
6. **Under 300 tokens** — focused prompts get more reliable results than verbose ones

```python
# ✅ Good prompt: specific, structured, handles failure
_PROMPT_SCORE_RELEVANCE = """\
Score the relevance of the item to the goal on a scale of 0.0 to 1.0.
Return JSON: {{"score": <float>, "reason": "<one sentence>"}}
Return {{"score": 0.0, "reason": "not relevant"}} if clearly unrelated.
Goal: {goal}
Item: {item}"""

# ❌ Bad prompt: vague, no format, no failure handling
_PROMPT_SCORE_RELEVANCE = "How relevant is this item to the goal? Goal: {goal} Item: {item}"
```

### Batch Prompts vs. Single Prompts

**Always** provide both `fn(item)` and `fn_many(items, concurrency)`:

```python
def classify_item(item: str, categories: list[str], client=None) -> ClassifyResult | None:
    """Single-item classification. Use classify_many() for batches > 1."""
    ...

def classify_many(
    items: list[str],
    categories: list[str],
    concurrency: int = 8,
    client=None,
) -> list[ClassifyResult | None]:
    """Batch classification with thread-pool parallelism.
    
    Returns results in the same order as input items.
    None values indicate individual call failures (others still complete).
    """
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [
            pool.submit(classify_item, item, categories, client)
            for item in items
        ]
        return [f.result() for f in futures]
```

---

## 4. Module Implementation Details

### `core.py` Rules
1. Pure Python + standard library only (no LLM calls, no third-party I/O)
2. Every function: typed, docstring'd with Args/Returns/Example, idempotent where possible
3. Collections always returned as `list`, never generators (materialized, inspectable)
4. I/O functions (HTTP, file) include `timeout` parameter, raise on failure
5. Sort order is always explicit: don't return "some order"

### `llm.py` Rules
1. All prompts as `_PROMPT_*` constants at module top
2. Injectable `client: Any = None` parameter (uses `utils.call_llm` default if None)
3. Returns typed dataclass or `None` — never raw strings from LLM calls
4. `*_many` variants use `ThreadPoolExecutor` for synchronous batching
5. Graceful degradation: individual item failures return `None`, don't raise

### `orchestrate.py` Rules
1. `TaskState` must round-trip through `json.dumps(dataclasses.asdict(state))` without error
2. `save_state` writes atomically: write `.tmp`, then `rename()` (POSIX atomic)
3. `run_task_loop` logs every turn to `<state_dir>/<task_id>/turns.jsonl` (append-only)
4. `resume_task_loop` validates task_id exists before proceeding
5. The `executor_fn` signature is always `(TaskState) -> TaskState`
6. The `goal_met_fn` signature is always `(TaskState) -> bool`

### `utils.py` Rules
1. `call_llm` is provider-agnostic: detects from environment (see §6)
2. `parse_json_robust` tries: direct parse → strip markdown fences → find JSON in text
3. `retry` uses exponential backoff with jitter: `base * 2^attempt + random(0, base)`
4. All utilities are importable standalone — no dependencies on other SDK modules
5. No module-level state; no singletons that break testing

---

## 5. State Management Patterns

### TaskState Design

```python
@dataclass
class TaskState:
    task_id: str            # UUID4, auto-generated
    goal: str               # Natural language task description
    domain: str             # SDK domain name (e.g., "design-system")
    turn: int = 0           # Current turn number (0-indexed)
    status: str = "running" # running | completed | incomplete | failed
    results: list[dict] = field(default_factory=list)  # Accumulated output
    visited: list[str] = field(default_factory=list)   # Processed IDs (dedup)
    metadata: dict = field(default_factory=dict)        # Domain-specific extras
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)
```

**Rules for extending TaskState:**
- Add domain-specific fields to `metadata`, don't subclass `TaskState`
- All values in `metadata` must be JSON-serializable
- `results` items must be dicts (JSON-serializable)
- `visited` is a dedup guard — append identifiers already processed

### Atomic State Writes

```python
def save_state(state: TaskState, state_dir: Path) -> Path:
    task_dir = state_dir / state.task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = task_dir / "state.json"
    tmp_file = task_dir / "state.json.tmp"
    
    # Write to temp then rename — atomic on POSIX, near-atomic on Windows
    tmp_file.write_text(
        json.dumps(dataclasses.asdict(state), indent=2),
        encoding="utf-8",
    )
    tmp_file.rename(state_file)
    return state_file
```

### Turn Loop Pattern

```python
def run_task_loop(
    goal: str,
    executor_fn: Callable[[TaskState], TaskState],
    goal_met_fn: Callable[[TaskState], bool],
    max_turns: int = 10,
    state_dir: Path = Path(".tac_state"),
) -> TaskState:
    state = TaskState(task_id=str(uuid.uuid4()), goal=goal, domain=DOMAIN_NAME)
    
    while state.turn < max_turns and not goal_met_fn(state):
        state = executor_fn(state)          # User-provided executor
        state.turn += 1
        state.updated_at = _utcnow()
        save_state(state, state_dir)        # Persist after EVERY turn
        _log_turn(state, state_dir)         # Append to turns.jsonl
    
    state.status = "completed" if goal_met_fn(state) else "incomplete"
    save_state(state, state_dir)            # Final status save
    return state


def _log_turn(state: TaskState, state_dir: Path) -> None:
    log_file = state_dir / state.task_id / "turns.jsonl"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "turn": state.turn,
            "status": state.status,
            "result_count": len(state.results),
            "visited_count": len(state.visited),
            "timestamp": state.updated_at,
        }) + "\n")
```

---

## 6. Provider-Agnostic LLM Utility

```python
DEFAULT_MODEL_ANTHROPIC = "claude-sonnet-4-20250514"
DEFAULT_MODEL_OPENAI = "gpt-4o"


class LLMConfigError(RuntimeError):
    """Raised when no LLM API key is configured."""


def call_llm(
    prompt: str,
    model: str | None = None,
    client: Any = None,
    max_tokens: int = 1024,
    temperature: float = 0.0,
    system: str | None = None,
) -> str | None:
    """Provider-agnostic LLM call. Returns response text or None on failure."""
    if client is None:
        client = _get_default_client()
    
    try:
        module = type(client).__module__.split(".")[0]
        
        if module == "anthropic":
            kwargs = {
                "model": model or DEFAULT_MODEL_ANTHROPIC,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            resp = client.messages.create(**kwargs)
            return resp.content[0].text
        
        elif module == "openai":
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = client.chat.completions.create(
                model=model or DEFAULT_MODEL_OPENAI,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return resp.choices[0].message.content
        
        else:
            raise LLMConfigError(f"Unsupported client type: {type(client)}")
    
    except Exception as e:
        print(f"[call_llm] Error: {e}", file=sys.stderr)
        return None


def _get_default_client() -> Any:
    """Auto-detect LLM client from environment variables."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
            return anthropic.Anthropic()
        except ImportError:
            raise LLMConfigError(
                "ANTHROPIC_API_KEY is set but 'anthropic' package not installed. "
                "Run: pip install anthropic"
            )
    
    if os.environ.get("OPENAI_API_KEY"):
        try:
            import openai
            return openai.OpenAI()
        except ImportError:
            raise LLMConfigError(
                "OPENAI_API_KEY is set but 'openai' package not installed. "
                "Run: pip install openai"
            )
    
    raise LLMConfigError(
        "No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."
    )
```

---

## 7. Testing an SDK

### Minimal Test Set

For each new SDK, write at minimum:

```
tests/
├── test_core.py         ← Unit tests for each core primitive (mock I/O)
├── test_llm.py          ← Unit tests for each llm function (mock call_llm)
├── test_orchestrate.py  ← State roundtrip, loop termination, resume
├── test_utils.py        ← parse_json_robust, retry, batch, dedupe_by
└── conftest.py          ← Shared fixtures (temp dirs, mock clients)
```

### Key Test Patterns

**Mocking the LLM in tests:**
```python
@pytest.fixture
def mock_client(mocker):
    """Mock LLM client that returns canned responses."""
    client = mocker.MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='{"category": "A", "confidence": 0.9, "reason": "test"}')]
    )
    type(client).__module__ = MagicMock(return_value="anthropic.Anthropic")
    return client
```

**State roundtrip test:**
```python
def test_state_roundtrip(tmp_path):
    state = TaskState(task_id="test-123", goal="test goal")
    state.results.append({"id": 1, "data": "value"})
    save_state(state, tmp_path)
    loaded = load_state(tmp_path, "test-123")
    assert loaded.task_id == state.task_id
    assert loaded.results == state.results
```

**Batch alignment test:**
```python
def test_classify_many_preserves_order(mock_client):
    items = ["item_a", "item_b", "item_c"]
    results = classify_many(items, ["X", "Y"], client=mock_client)
    assert len(results) == len(items)  # Always same length as input
```

### SDK Quality Checklist
- [ ] `python -c "from sdk import core, llm, orchestrate, utils"` runs without errors
- [ ] All functions exported from `__init__.py` are callable
- [ ] `simple_usage.py` runs end-to-end with API key set
- [ ] `agentic_usage.py` creates `.tac_state/` and writes `state.json`
- [ ] `validate_sdk.py <path>` reports no errors
- [ ] Every `_PROMPT_*` constant is used by exactly one function
- [ ] No hardcoded API keys anywhere in the SDK
