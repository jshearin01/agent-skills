#!/usr/bin/env python3
"""
Scaffold a Task as Code (TaC) SDK folder structure.

Usage:
    python scaffold_sdk.py <task-name> [output-dir]

Examples:
    python scaffold_sdk.py design-system
    python scaffold_sdk.py web-research ./my-sdks/
    python scaffold_sdk.py code-review /tmp/

Creates:
    <task-name>-sdk/
    ├── SKILL.md              (placeholder — generate with gen_consumer_skill.py after implementation)
    ├── sdk/
    │   ├── __init__.py
    │   ├── core.py           (atomic deterministic primitives — implement these)
    │   ├── llm.py            (LLM-powered operations with embedded prompts — implement these)
    │   ├── orchestrate.py    (TaskState + agentic loop — pre-implemented, domain-agnostic)
    │   └── utils.py          (call_llm, parse_json_robust, retry, batch — pre-implemented)
    ├── examples/
    │   ├── simple_usage.py
    │   └── agentic_usage.py
    ├── prompts/
    │   └── system.md
    └── requirements.txt
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def scaffold(task_name: str, output_dir: Path | None = None) -> Path:
    """Create the SDK folder structure for a given task name.

    Args:
        task_name: Kebab-case task name (e.g., "design-system").
        output_dir: Parent directory for the SDK folder (default: cwd).

    Returns:
        Path to the created SDK directory.
    """
    if output_dir is None:
        output_dir = Path.cwd()

    sdk_dir = output_dir / f"{task_name}-sdk"
    if sdk_dir.exists():
        print(f"Error: {sdk_dir} already exists.", file=sys.stderr)
        sys.exit(1)

    sdk_dir.mkdir(parents=True)
    (sdk_dir / "sdk").mkdir()
    (sdk_dir / "examples").mkdir()
    (sdk_dir / "prompts").mkdir()

    files = {
        sdk_dir / "SKILL.md": _skill_md_placeholder(task_name),
        sdk_dir / "requirements.txt": _requirements(),
        sdk_dir / "sdk" / "__init__.py": _init_py(task_name),
        sdk_dir / "sdk" / "core.py": _core_py(task_name),
        sdk_dir / "sdk" / "llm.py": _llm_py(task_name),
        sdk_dir / "sdk" / "orchestrate.py": _orchestrate_py(task_name),
        sdk_dir / "sdk" / "utils.py": _utils_py(),
        sdk_dir / "examples" / "simple_usage.py": _simple_usage(task_name),
        sdk_dir / "examples" / "agentic_usage.py": _agentic_usage(task_name),
        sdk_dir / "prompts" / "system.md": _system_md(task_name),
    }

    for path, content in files.items():
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")

    return sdk_dir


# ---------------------------------------------------------------------------
# File content generators
# ---------------------------------------------------------------------------

def _skill_md_placeholder(name: str) -> str:
    return f"""\
        ---
        name: {name}-sdk
        description: TODO — Replace with a description of what this SDK does and when to use it.
        ---

        # {_title(name)} SDK

        > **TODO:** Generate this file after implementing the SDK modules:
        > `python scripts/gen_consumer_skill.py {name}-sdk/`
        """


def _requirements() -> str:
    return """\
        anthropic>=0.40.0
        # openai>=1.0.0  # Uncomment if using OpenAI instead of Anthropic
        # Add domain-specific dependencies below:
        # requests>=2.31.0
        # beautifulsoup4>=4.12.0
        """


def _init_py(name: str) -> str:
    return f'''\
        """
        {_title(name)} SDK — Task as Code (TaC) package.

        Usage:
            from sdk import core, llm, orchestrate, utils

        See SKILL.md for orchestration patterns and examples.
        """

        from . import core, llm, orchestrate, utils

        __all__ = ["core", "llm", "orchestrate", "utils"]
        __version__ = "0.1.0"
        '''


def _core_py(name: str) -> str:
    return f'''\
        """
        {_title(name)} SDK — Atomic deterministic primitives.

        Rules:
          - No LLM calls in this module
          - Every function: typed, docstring'd with Args/Returns/Example
          - Functions are idempotent where possible
          - Raise descriptive exceptions, never silently fail

        TODO: Replace the placeholder functions below with domain-specific
        primitives following the naming convention: verb_noun(params) -> typed_result
        """

        from __future__ import annotations

        from typing import Any


        def fetch_items(
            source: str,
            limit: int = 10,
            filters: dict[str, str] | None = None,
        ) -> list[dict[str, Any]]:
            """Fetch items from source with optional filtering.

            Args:
                source: URL or identifier for the data source.
                limit: Maximum number of items to return.
                filters: Optional key-value filters to apply.

            Returns:
                List of item dicts with at minimum {{"id", "content"}} keys.

            Example:
                items = fetch_items("https://api.example.com/data", limit=20)
            """
            raise NotImplementedError("Implement domain-specific fetch logic here")


        def filter_items(
            items: list[dict[str, Any]],
            criteria: dict[str, Any],
        ) -> list[dict[str, Any]]:
            """Filter items by exact field match criteria.

            Args:
                items: List of item dicts to filter.
                criteria: Dict of field: value pairs; items must match all criteria.

            Returns:
                Filtered list of items.

            Example:
                active = filter_items(items, {{"status": "active"}})
            """
            return [
                item for item in items
                if all(item.get(k) == v for k, v in criteria.items())
            ]


        def dedupe_by(items: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
            """Remove duplicate items by a field key (first occurrence kept).

            Args:
                items: List of item dicts.
                key: Field name to use as deduplication key.

            Returns:
                List with duplicates removed.

            Example:
                unique = dedupe_by(items, "url")
            """
            seen: set = set()
            result = []
            for item in items:
                val = item.get(key)
                if val not in seen:
                    seen.add(val)
                    result.append(item)
            return result


        def score_items(
            items: list[dict[str, Any]],
            score_field: str = "score",
            reverse: bool = True,
        ) -> list[dict[str, Any]]:
            """Sort items by a numeric score field.

            Args:
                items: List of item dicts with a numeric score field.
                score_field: Name of the field containing the score.
                reverse: If True, highest scores first (default True).

            Returns:
                Items sorted by score.

            Example:
                ranked = score_items(items, score_field="relevance_score")
            """
            return sorted(items, key=lambda x: x.get(score_field, 0), reverse=reverse)
        '''


def _llm_py(name: str) -> str:
    return f'''\
        """
        {_title(name)} SDK — LLM-powered operations.

        Rules:
          - Each function has ONE _PROMPT_* constant at module level
          - Prompts are templates with {{variable}} placeholders, never f-strings in bodies
          - Returns typed dataclass results, never raw strings
          - Every operation has a _many() batch variant

        TODO: Replace placeholder functions with domain-specific LLM operations.
        """

        from __future__ import annotations

        from concurrent.futures import ThreadPoolExecutor
        from dataclasses import dataclass
        from typing import Any

        from .utils import call_llm, parse_json_robust


        # ---------------------------------------------------------------------------
        # Prompts — ONE constant per function, at module level
        # ---------------------------------------------------------------------------

        _PROMPT_CLASSIFY = """\
        Classify the item into exactly one of these categories: {{categories}}.
        Return JSON only (no markdown): {{"category": "<choice>", "confidence": <0.0-1.0>, "reason": "<one sentence>"}}
        Return {{"category": "unknown", "confidence": 0.0, "reason": "cannot classify"}} if unsure.
        Item: {{item}}"""


        _PROMPT_SUMMARIZE = """\
        Summarize the following items into a single concise paragraph (2-4 sentences).
        Focus on patterns, key findings, and actionable insights.
        Items (JSON): {{items_json}}"""


        # ---------------------------------------------------------------------------
        # Result Types
        # ---------------------------------------------------------------------------

        @dataclass
        class ClassifyResult:
            category: str
            confidence: float
            reason: str


        # ---------------------------------------------------------------------------
        # Functions
        # ---------------------------------------------------------------------------

        def classify_item(
            item: str,
            categories: list[str],
            client: Any = None,
        ) -> ClassifyResult | None:
            """Classify an item into one of the provided categories.

            Args:
                item: Text content to classify.
                categories: List of valid category labels.
                client: Optional LLM client (uses default env-var client if None).

            Returns:
                ClassifyResult with category, confidence, reason. None on failure.

            Example:
                result = classify_item("Revenue grew 20%", ["positive", "negative", "neutral"])
                # ClassifyResult(category="positive", confidence=0.95, reason="...")
            """
            prompt = _PROMPT_CLASSIFY.format(
                categories=", ".join(categories),
                item=item,
            )
            raw = call_llm(prompt, client=client)
            if raw is None:
                return None
            data = parse_json_robust(raw)
            if not data or not isinstance(data, dict):
                return None
            try:
                return ClassifyResult(
                    category=data["category"],
                    confidence=float(data["confidence"]),
                    reason=data["reason"],
                )
            except (KeyError, ValueError):
                return None


        def classify_many(
            items: list[str],
            categories: list[str],
            concurrency: int = 8,
            client: Any = None,
        ) -> list[ClassifyResult | None]:
            """Batch-classify items using thread-pool concurrency.

            Args:
                items: List of texts to classify.
                categories: List of valid category labels.
                concurrency: Number of parallel LLM calls.
                client: Optional LLM client (uses default if None).

            Returns:
                List of ClassifyResult (or None for failures), same order as input.

            Example:
                results = classify_many(texts, ["positive", "negative"])
                # list[ClassifyResult | None], same length as texts
            """
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                futures = [
                    pool.submit(classify_item, item, categories, client)
                    for item in items
                ]
                return [f.result() for f in futures]


        def summarize_items(
            items: list[dict[str, Any]],
            client: Any = None,
        ) -> str | None:
            """Summarize a list of items into a concise paragraph.

            Args:
                items: List of item dicts to summarize.
                client: Optional LLM client (uses default if None).

            Returns:
                Summary string, or None on failure.

            Example:
                summary = summarize_items(results[:20])
            """
            import json as _json
            prompt = _PROMPT_SUMMARIZE.format(
                items_json=_json.dumps(items[:50], ensure_ascii=False),
            )
            return call_llm(prompt, client=client)
        '''


def _orchestrate_py(name: str) -> str:
    return f'''\
        """
        {_title(name)} SDK — Agentic orchestration layer.

        Provides TaskState, filesystem-based state persistence, and run_task_loop
        for multi-turn agentic workflows with recovery support.

        This module is domain-agnostic — use as-is or extend TaskState.metadata
        for domain-specific extra fields.
        """

        from __future__ import annotations

        import dataclasses
        import json
        import uuid
        from dataclasses import dataclass, field
        from datetime import datetime, timezone
        from pathlib import Path
        from typing import Callable


        DOMAIN_NAME = "{name}"


        def _utcnow() -> str:
            return datetime.now(timezone.utc).isoformat()


        @dataclass
        class TaskState:
            """Serializable state for a multi-turn TaC task.

            Fields:
                task_id: UUID4 identifier for this task run.
                goal: Natural language description of the task goal.
                domain: SDK domain name (auto-set to DOMAIN_NAME).
                turn: Current turn number (0-indexed, incremented after each executor call).
                status: "running" | "completed" | "incomplete" | "failed"
                results: Accumulated output; extend with dicts each turn.
                visited: Processed identifiers; append to avoid reprocessing.
                metadata: Arbitrary domain-specific extras; all values must be JSON-serializable.
                created_at: ISO 8601 UTC timestamp of task creation.
                updated_at: ISO 8601 UTC timestamp of last state save.
            """
            task_id: str
            goal: str
            domain: str = DOMAIN_NAME
            turn: int = 0
            status: str = "running"
            results: list[dict] = field(default_factory=list)
            visited: list[str] = field(default_factory=list)
            metadata: dict = field(default_factory=dict)
            created_at: str = field(default_factory=_utcnow)
            updated_at: str = field(default_factory=_utcnow)


        def save_state(state: TaskState, state_dir: Path) -> Path:
            """Persist TaskState to filesystem atomically.

            Uses write-to-temp-then-rename for atomic writes on POSIX systems.

            Args:
                state: TaskState to persist.
                state_dir: Root directory for state storage.

            Returns:
                Path to the saved state.json file.
            """
            task_dir = state_dir / state.task_id
            task_dir.mkdir(parents=True, exist_ok=True)

            state_file = task_dir / "state.json"
            tmp_file = task_dir / "state.json.tmp"
            tmp_file.write_text(
                json.dumps(dataclasses.asdict(state), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp_file.rename(state_file)
            return state_file


        def load_state(state_dir: Path, task_id: str) -> TaskState | None:
            """Load TaskState from filesystem.

            Args:
                state_dir: Root directory for state storage.
                task_id: ID of the task to load.

            Returns:
                TaskState if found and valid, None otherwise.
            """
            state_file = state_dir / task_id / "state.json"
            if not state_file.exists():
                return None
            try:
                data = json.loads(state_file.read_text(encoding="utf-8"))
                return TaskState(**data)
            except Exception as e:
                print(f"[load_state] Failed to load {{state_file}}: {{e}}")
                return None


        def _log_turn(state: TaskState, state_dir: Path) -> None:
            """Append a structured turn entry to the task log."""
            log_file = state_dir / state.task_id / "turns.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps({{
                    "turn": state.turn,
                    "status": state.status,
                    "result_count": len(state.results),
                    "visited_count": len(state.visited),
                    "timestamp": state.updated_at,
                }}) + "\\n")


        def run_task_loop(
            goal: str,
            executor_fn: Callable[[TaskState], TaskState],
            goal_met_fn: Callable[[TaskState], bool],
            max_turns: int = 10,
            state_dir: Path = Path(".tac_state"),
        ) -> TaskState:
            """Run an agentic task loop until the goal is met or max_turns is reached.

            Creates a new TaskState and persists it after every turn.

            Args:
                goal: Natural language description of what to achieve.
                executor_fn: Callable(TaskState) -> TaskState. Called each turn.
                             Should update state.results and state.visited.
                goal_met_fn: Callable(TaskState) -> bool. Returns True when done.
                max_turns: Maximum number of turns before stopping with "incomplete".
                state_dir: Root directory for persisting task state.

            Returns:
                Final TaskState with status "completed" or "incomplete".

            Example:
                def executor(state):
                    items = core.fetch_items("source", limit=5)
                    state.results.extend(items)
                    return state

                final = run_task_loop(
                    goal="collect 20 items",
                    executor_fn=executor,
                    goal_met_fn=lambda s: len(s.results) >= 20,
                )
                print(f"Done: {{len(final.results)}} in {{final.turn}} turns")
            """
            state = TaskState(task_id=str(uuid.uuid4()), goal=goal)

            while state.turn < max_turns and not goal_met_fn(state):
                state = executor_fn(state)
                state.turn += 1
                state.updated_at = _utcnow()
                save_state(state, state_dir)
                _log_turn(state, state_dir)

            state.status = "completed" if goal_met_fn(state) else "incomplete"
            state.updated_at = _utcnow()
            save_state(state, state_dir)
            return state


        def resume_task_loop(
            task_id: str,
            executor_fn: Callable[[TaskState], TaskState],
            goal_met_fn: Callable[[TaskState], bool],
            max_additional_turns: int = 5,
            state_dir: Path = Path(".tac_state"),
        ) -> TaskState:
            """Resume an interrupted task loop from saved state.

            Args:
                task_id: ID of the task to resume (from a previous run's state.task_id).
                executor_fn: Same executor function used in the original run.
                goal_met_fn: Same goal predicate used in the original run.
                max_additional_turns: Number of additional turns to allow.
                state_dir: Directory containing saved state.

            Returns:
                Updated TaskState after resuming.

            Raises:
                ValueError: If task_id is not found in state_dir.

            Example:
                final = resume_task_loop(
                    task_id="abc-123-...",
                    executor_fn=executor,
                    goal_met_fn=lambda s: len(s.results) >= 50,
                )
            """
            state = load_state(state_dir, task_id)
            if state is None:
                raise ValueError(
                    f"No saved state found for task_id={{task_id!r}} in {{state_dir}}"
                )

            state.status = "running"
            max_turn = state.turn + max_additional_turns

            while state.turn < max_turn and not goal_met_fn(state):
                state = executor_fn(state)
                state.turn += 1
                state.updated_at = _utcnow()
                save_state(state, state_dir)
                _log_turn(state, state_dir)

            state.status = "completed" if goal_met_fn(state) else "incomplete"
            state.updated_at = _utcnow()
            save_state(state, state_dir)
            return state
        '''


def _utils_py() -> str:
    return '''\
        """
        Task as Code (TaC) — Shared utilities.

        Provider-agnostic LLM caller, robust JSON parsing, retry, and collection helpers.
        All utilities are standalone (no dependencies on other SDK modules).
        """

        from __future__ import annotations

        import json
        import os
        import random
        import sys
        import time
        from typing import Any, Iterator, TypeVar

        T = TypeVar("T")


        # ---------------------------------------------------------------------------
        # LLM Configuration
        # ---------------------------------------------------------------------------

        DEFAULT_MODEL_ANTHROPIC = "claude-sonnet-4-20250514"
        DEFAULT_MODEL_OPENAI = "gpt-4o"


        class LLMConfigError(RuntimeError):
            """Raised when no LLM API key is configured or client type is unsupported."""


        def call_llm(
            prompt: str,
            model: str | None = None,
            client: Any = None,
            max_tokens: int = 1024,
            temperature: float = 0.0,
            system: str | None = None,
        ) -> str | None:
            """Call an LLM with a prompt, auto-detecting provider from environment variables.

            Provider detection order:
              1. Use `client` if provided
              2. ANTHROPIC_API_KEY → anthropic.Anthropic()
              3. OPENAI_API_KEY → openai.OpenAI()

            Args:
                prompt: User message content.
                model: Model identifier. Defaults to provider-appropriate default.
                client: Pre-initialized LLM client (overrides env detection).
                max_tokens: Maximum tokens in the response.
                temperature: Sampling temperature (0.0 = deterministic).
                system: Optional system prompt.

            Returns:
                Response text string, or None on any failure.

            Raises:
                LLMConfigError: If no API key is found and no client is provided.
            """
            if client is None:
                client = _get_default_client()

            try:
                module = type(client).__module__.split(".")[0]

                if module == "anthropic":
                    kwargs: dict[str, Any] = {
                        "model": model or DEFAULT_MODEL_ANTHROPIC,
                        "max_tokens": max_tokens,
                        "messages": [{"role": "user", "content": prompt}],
                    }
                    if system:
                        kwargs["system"] = system
                    resp = client.messages.create(**kwargs)
                    return resp.content[0].text

                elif module == "openai":
                    messages: list[dict] = []
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
                    raise LLMConfigError(f"Unsupported client type: {type(client).__name__}")

            except LLMConfigError:
                raise
            except Exception as e:
                print(f"[call_llm] Error: {e}", file=sys.stderr)
                return None


        def _get_default_client() -> Any:
            """Auto-detect and return an LLM client from environment variables."""
            if os.environ.get("ANTHROPIC_API_KEY"):
                try:
                    import anthropic
                    return anthropic.Anthropic()
                except ImportError:
                    raise LLMConfigError(
                        "ANTHROPIC_API_KEY is set but 'anthropic' is not installed. "
                        "Run: pip install anthropic"
                    )

            if os.environ.get("OPENAI_API_KEY"):
                try:
                    import openai
                    return openai.OpenAI()
                except ImportError:
                    raise LLMConfigError(
                        "OPENAI_API_KEY is set but 'openai' is not installed. "
                        "Run: pip install openai"
                    )

            raise LLMConfigError(
                "No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variables."
            )


        # ---------------------------------------------------------------------------
        # JSON Parsing
        # ---------------------------------------------------------------------------

        def parse_json_robust(text: str | None) -> dict | list | None:
            """Parse JSON from LLM output robustly — handles markdown fences and stray text.

            Attempts in order:
              1. Direct json.loads()
              2. Strip ``` or ```json fences
              3. Find first JSON object {} or array [] in text

            Args:
                text: Raw LLM output string.

            Returns:
                Parsed Python dict or list, or None if all attempts fail.

            Example:
                data = parse_json_robust(\'\'\'```json\\n{"key": "value"}\\n```\'\'\')
                # {"key": "value"}
            """
            if not text:
                return None

            # Attempt 1: direct parse
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

            # Attempt 2: strip markdown fences
            stripped = text.strip()
            for fence in ("```json", "```"):
                if stripped.startswith(fence):
                    inner = stripped[len(fence):]
                    if inner.endswith("```"):
                        inner = inner[:-3]
                    try:
                        return json.loads(inner.strip())
                    except json.JSONDecodeError:
                        pass

            # Attempt 3: find JSON object or array in text
            for start_ch, end_ch in (("{", "}"), ("[", "]")):
                s = text.find(start_ch)
                e = text.rfind(end_ch)
                if s != -1 and e > s:
                    try:
                        return json.loads(text[s:e + 1])
                    except json.JSONDecodeError:
                        pass

            return None


        # ---------------------------------------------------------------------------
        # Retry
        # ---------------------------------------------------------------------------

        def retry(fn: Any, attempts: int = 3, base_delay: float = 1.0) -> Any:
            """Retry a zero-argument callable with exponential backoff and jitter.

            Args:
                fn: Zero-argument callable to retry.
                attempts: Maximum number of attempts (including the first).
                base_delay: Base delay in seconds; doubles each attempt with jitter.

            Returns:
                Return value of fn() on success.

            Raises:
                Last raised exception if all attempts fail.

            Example:
                result = retry(lambda: fetch_items("url"), attempts=3, base_delay=0.5)
            """
            last_exc: Exception | None = None
            for attempt in range(attempts):
                try:
                    return fn()
                except Exception as exc:
                    last_exc = exc
                    if attempt < attempts - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
                        time.sleep(delay)
            raise last_exc  # type: ignore[misc]


        # ---------------------------------------------------------------------------
        # Collection Utilities
        # ---------------------------------------------------------------------------

        def batch(items: list[T], size: int) -> Iterator[list[T]]:
            """Yield successive non-overlapping batches of `size` from items.

            Args:
                items: List to partition into batches.
                size: Maximum items per batch.

            Yields:
                Lists of at most `size` items.

            Example:
                for chunk in batch(list(range(25)), 10):
                    print(len(chunk))  # 10, 10, 5
            """
            for i in range(0, len(items), size):
                yield items[i:i + size]


        def dedupe_by(items: list[dict], key: str) -> list[dict]:
            """Deduplicate a list of dicts by a field key, keeping first occurrence.

            Args:
                items: List of dicts to deduplicate.
                key: Field to use as the deduplication key.

            Returns:
                List with duplicate-key items removed.

            Example:
                unique = dedupe_by(results, "url")
            """
            seen: set = set()
            result = []
            for item in items:
                val = item.get(key)
                if val not in seen:
                    seen.add(val)
                    result.append(item)
            return result


        def flatten(list_of_lists: list[list[T]]) -> list[T]:
            """Flatten exactly one level of list nesting.

            Args:
                list_of_lists: A list whose elements are lists.

            Returns:
                Single flat list combining all inner items.

            Example:
                flatten([[1, 2], [3, 4], [5]]) → [1, 2, 3, 4, 5]
            """
            return [item for sublist in list_of_lists for item in sublist]
        '''


def _simple_usage(name: str) -> str:
    title = _title(name)
    return f'''\
        """
        {title} SDK — Simple stateless usage example.

        Demonstrates single-turn use of core and llm primitives.
        Run: ANTHROPIC_API_KEY=<key> python examples/simple_usage.py
        """

        from __future__ import annotations
        import sys
        from pathlib import Path

        # Add parent dir to path for direct script execution
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from sdk import core, llm


        def main() -> None:
            print(f"=== {title} SDK — Simple Usage ===\\n")

            # TODO: Replace with real domain logic.
            # This example shows the pattern; adapt to your domain.

            # Step 1: Fetch raw items
            print("Step 1: Fetching items (replace with real source)...")
            # items = core.fetch_items("your-source-url", limit=20)
            # Placeholder for demonstration:
            items = [
                {{"id": "1", "content": "This quarter revenue increased significantly"}},
                {{"id": "2", "content": "Product launch was delayed due to supply chain"}},
                {{"id": "3", "content": "Customer satisfaction scores hit record high"}},
            ]
            print(f"  Fetched {{len(items)}} items")

            # Step 2: Deduplicate
            items = core.dedupe_by(items, key="id")
            print(f"  {{len(items)}} items after deduplication")

            # Step 3: LLM-powered classification
            print("\\nStep 2: Classifying items with LLM...")
            results = llm.classify_many(
                [item["content"] for item in items],
                categories=["positive", "negative", "neutral"],
                concurrency=4,
            )

            # Step 4: Display results
            print("\\nResults:")
            for item, result in zip(items, results):
                if result:
                    print(f"  [{{result.category:8s}}] {{result.confidence:.2f}} — {{item['content'][:50]}}")
                else:
                    print(f"  [FAILED  ]       — {{item['id']}}")

            print("\\n✓ Simple usage complete")


        if __name__ == "__main__":
            main()
        '''


def _agentic_usage(name: str) -> str:
    title = _title(name)
    return f'''\
        """
        {title} SDK — Multi-turn agentic usage example.

        Demonstrates multi-turn orchestration with state persistence and resume capability.
        Run: ANTHROPIC_API_KEY=<key> python examples/agentic_usage.py
        """

        from __future__ import annotations
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent))

        from sdk import core, orchestrate


        GOAL = "Collect 5 example items across multiple turns"


        def executor(state: orchestrate.TaskState) -> orchestrate.TaskState:
            """Execute one turn of the agentic loop.

            Replace with real domain logic:
            - Fetch new items (using state.visited for dedup)
            - Process with llm functions
            - Append results to state.results
            - Append processed IDs to state.visited
            """
            print(f"  Turn {{state.turn}}: collecting items...")

            # Placeholder: simulate collecting 2 items per turn
            # In production: fetch real items and skip state.visited
            batch_size = 2
            start = state.turn * batch_size
            new_items = [
                {{"id": str(start + i), "content": f"Item {{start + i}}", "turn": state.turn}}
                for i in range(batch_size)
                if str(start + i) not in state.visited
            ]

            state.visited.extend(item["id"] for item in new_items)
            state.results.extend(new_items)

            print(f"    Added {{len(new_items)}} items (total: {{len(state.results)}})")
            return state


        def goal_met(state: orchestrate.TaskState) -> bool:
            """Return True when we have enough results."""
            return len(state.results) >= 5


        def main() -> None:
            print(f"=== {title} SDK — Agentic Usage ===\\n")

            print(f"Goal: {{GOAL}}")
            print("Starting task loop...\\n")

            final = orchestrate.run_task_loop(
                goal=GOAL,
                executor_fn=executor,
                goal_met_fn=goal_met,
                max_turns=5,
            )

            print(f"\\n✓ Task {{final.status}} in {{final.turn}} turn(s)")
            print(f"  Results: {{len(final.results)}} items")
            print(f"  Task ID: {{final.task_id}}")
            print(f"  State saved to: .tac_state/{{final.task_id}}/")

            # Demonstrate resume capability
            print(f"\\nTo resume this task if interrupted, call:")
            print(f"  orchestrate.resume_task_loop(")
            print(f"      task_id={{final.task_id!r}},")
            print(f"      executor_fn=executor,")
            print(f"      goal_met_fn=goal_met,")
            print(f"  )")


        if __name__ == "__main__":
            main()
        '''


def _system_md(name: str) -> str:
    title = _title(name)
    return f"""\
        # {title} SDK — Control-Plane System Prompt

        You are an AI agent with access to the {name} SDK, a Python library providing
        composable primitives for {name.replace('-', ' ')} tasks.

        ## How to Use This SDK

        Generate Python code that imports and calls SDK functions. The code executes in
        an environment where the SDK is installed. Use `print()` to emit intermediate
        results you want to inspect. Write any additional logic you need directly in Python.

        ## Available Modules

        - `sdk.core` — Deterministic atomic operations (fetch, filter, dedupe, score, segment)
        - `sdk.llm` — LLM-powered operations with embedded prompts (classify, extract, generate, summarize)
        - `sdk.orchestrate` — Multi-turn state management (TaskState, run_task_loop, save/load)
        - `sdk.utils` — Shared helpers (call_llm, parse_json_robust, retry, batch, flatten)

        ## Available Functions

        ### sdk.core
        <!-- TODO: List domain-specific functions here after implementing core.py -->
        - `fetch_items(source, limit, filters)` → list[dict]
        - `filter_items(items, criteria)` → list[dict]
        - `dedupe_by(items, key)` → list[dict]
        - `score_items(items, score_field, reverse)` → list[dict]

        ### sdk.llm
        <!-- TODO: List domain-specific functions here after implementing llm.py -->
        - `classify_item(item, categories, client)` → ClassifyResult | None
        - `classify_many(items, categories, concurrency, client)` → list[ClassifyResult | None]
        - `summarize_items(items, client)` → str | None

        ### sdk.orchestrate
        - `run_task_loop(goal, executor_fn, goal_met_fn, max_turns, state_dir)` → TaskState
        - `save_state(state, state_dir)` → Path
        - `load_state(state_dir, task_id)` → TaskState | None
        - `resume_task_loop(task_id, executor_fn, goal_met_fn, max_additional_turns)` → TaskState

        ### sdk.utils
        - `call_llm(prompt, model, client, max_tokens, temperature, system)` → str | None
        - `parse_json_robust(text)` → dict | list | None
        - `retry(fn, attempts, base_delay)` → Any
        - `batch(items, size)` → Iterator[list]
        - `dedupe_by(items, key)` → list[dict]
        - `flatten(list_of_lists)` → list

        ## Pattern: Single-Turn
        ```python
        from sdk import core, llm, utils

        items = core.fetch_items(source="...", limit=20)
        items = core.dedupe_by(items, key="id")

        results = llm.classify_many(
            [i["content"] for i in items],
            categories=["category_a", "category_b"],
            concurrency=8,
        )

        for item, result in zip(items, results):
            if result and result.confidence > 0.7:
                print(f"{{item['id']}}: {{result.category}}")
        ```

        ## Pattern: Multi-Turn Agentic
        ```python
        from sdk import core, llm, orchestrate

        def executor(state):
            new_items = core.fetch_items("...", limit=10)
            new_items = [i for i in new_items if i["id"] not in state.visited]
            state.visited.extend(i["id"] for i in new_items)
            classified = llm.classify_many([i["content"] for i in new_items], ["a", "b"])
            state.results.extend([
                {{**item, "category": r.category if r else None}}
                for item, r in zip(new_items, classified)
            ])
            return state

        final = orchestrate.run_task_loop(
            goal="collect and classify 50 items",
            executor_fn=executor,
            goal_met_fn=lambda s: len(s.results) >= 50,
            max_turns=10,
        )
        ```

        ## State Management Cheatsheet
        ```python
        state.results    # list[dict] — accumulate output here
        state.visited    # list[str] — track processed IDs for dedup
        state.metadata   # dict — domain-specific data (all JSON-serializable)
        state.turn       # int — current turn (0-indexed)
        state.task_id    # str — use to resume: resume_task_loop(state.task_id, ...)
        ```

        ## Gap Filling
        Write any Python you need alongside SDK calls. Import standard library
        modules, write helper functions inline, use list comprehensions. The SDK
        provides domain primitives; your orchestration code fills the gaps.
        """


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _title(name: str) -> str:
    return name.replace("-", " ").title()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    task_name = sys.argv[1].lower().replace("_", "-")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    sdk_path = scaffold(task_name, output_dir)

    print(f"✓ Scaffolded SDK at: {sdk_path}")
    print(f"\nNext steps:")
    print(f"  1. Implement sdk/core.py  — domain-specific atomic primitives")
    print(f"  2. Implement sdk/llm.py   — domain-specific LLM operations + _PROMPT_* constants")
    print(f"  3. Update examples/       — replace placeholder logic with real domain examples")
    print(f"  4. Update prompts/system.md — replace TODO sections with real function list")
    print(f"  5. python scripts/validate_sdk.py {sdk_path}")
    print(f"  6. python scripts/gen_consumer_skill.py {sdk_path}")
