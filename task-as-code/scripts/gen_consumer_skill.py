#!/usr/bin/env python3
"""
Generate a consumer SKILL.md from a Task as Code (TaC) SDK folder.

Introspects the SDK's Python modules to extract:
  - Public function names, signatures, and docstrings
  - Prompt constant names (from llm.py)
  - Result type names (dataclasses in llm.py)
  - Module organization

Then generates a consumer SKILL.md that can teach any control-plane LLM to
orchestrate the SDK effectively.

Usage:
    python gen_consumer_skill.py <path-to-sdk>
    python gen_consumer_skill.py design-system-sdk/
    python gen_consumer_skill.py ./my-sdks/web-research-sdk/ --output custom-skill.md

The generated SKILL.md is written to <sdk-path>/SKILL.md by default.
Review and edit the output — especially the description frontmatter and examples.
"""

from __future__ import annotations

import ast
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Data Types
# ---------------------------------------------------------------------------

@dataclass
class FunctionInfo:
    name: str
    lineno: int
    args: list[str]
    return_type: str
    docstring: str
    first_line: str  # First line of docstring only


@dataclass
class ModuleInfo:
    name: str
    functions: list[FunctionInfo]
    prompt_constants: list[str]
    result_types: list[str]


# ---------------------------------------------------------------------------
# AST Introspection
# ---------------------------------------------------------------------------

def _get_annotation_str(node: ast.expr | None) -> str:
    """Convert an AST annotation node to a string representation."""
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Constant):
        return repr(node.value)
    if isinstance(node, ast.Attribute):
        return f"{_get_annotation_str(node.value)}.{node.attr}"
    if isinstance(node, ast.Subscript):
        return f"{_get_annotation_str(node.value)}[{_get_annotation_str(node.slice)}]"
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return f"{_get_annotation_str(node.left)} | {_get_annotation_str(node.right)}"
    if isinstance(node, ast.Tuple):
        return ", ".join(_get_annotation_str(e) for e in node.elts)
    if isinstance(node, ast.List):
        inner = ", ".join(_get_annotation_str(e) for e in node.elts)
        return f"[{inner}]"
    # Fallback: unparse if available (Python 3.9+)
    try:
        return ast.unparse(node)
    except AttributeError:
        return "..."


def _get_docstring(node: ast.FunctionDef) -> str:
    """Extract docstring from a function node."""
    if (
        node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        return node.body[0].value.value.strip()
    return ""


def _first_line(docstring: str) -> str:
    """Return the first non-empty line of a docstring."""
    for line in docstring.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def extract_module_info(path: Path, module_name: str) -> ModuleInfo:
    """Extract public functions, prompt constants, and result types from a module."""
    if not path.exists():
        return ModuleInfo(name=module_name, functions=[], prompt_constants=[], result_types=[])

    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ModuleInfo(name=module_name, functions=[], prompt_constants=[], result_types=[])

    functions: list[FunctionInfo] = []
    prompt_constants: list[str] = []
    result_types: list[str] = []

    for node in ast.walk(tree):
        # Collect _PROMPT_* constants
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("_PROMPT_"):
                    prompt_constants.append(target.id)

        # Collect dataclass names (result types)
        if isinstance(node, ast.ClassDef):
            is_dataclass = any(
                (isinstance(d, ast.Name) and d.id == "dataclass") or
                (isinstance(d, ast.Attribute) and d.attr == "dataclass")
                for d in node.decorator_list
            )
            if is_dataclass:
                result_types.append(node.name)

    # Collect top-level public functions only
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name.startswith("_"):
            continue

        all_args = node.args.args + node.args.kwonlyargs
        arg_strs = []
        for arg in all_args:
            if arg.arg in ("self", "cls"):
                continue
            ann = _get_annotation_str(arg.annotation) if arg.annotation else ""
            arg_strs.append(f"{arg.arg}: {ann}" if ann else arg.arg)

        return_type = _get_annotation_str(node.returns)
        docstring = _get_docstring(node)

        functions.append(FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            args=arg_strs,
            return_type=return_type,
            docstring=docstring,
            first_line=_first_line(docstring),
        ))

    return ModuleInfo(
        name=module_name,
        functions=functions,
        prompt_constants=prompt_constants,
        result_types=result_types,
    )


# ---------------------------------------------------------------------------
# SKILL.md Generator
# ---------------------------------------------------------------------------

def generate_skill_md(sdk_path: Path) -> str:
    """Generate a consumer SKILL.md by introspecting the SDK modules."""
    sdk_name = sdk_path.name.replace("-sdk", "")
    title = sdk_name.replace("-", " ").title()

    modules = {
        mod: extract_module_info(sdk_path / "sdk" / f"{mod}.py", mod)
        for mod in ["core", "llm", "orchestrate", "utils"]
    }

    # Build function tables
    core_table = _build_function_table(modules["core"])
    llm_table = _build_function_table(modules["llm"])
    orch_table = _build_function_table(modules["orchestrate"])
    utils_table = _build_function_table(modules["utils"])

    # Collect result type names for examples
    result_types = modules["llm"].result_types

    skill_md = f"""\
---
name: {sdk_name}-sdk
description: >
  Use the {sdk_name} SDK to programmatically execute {sdk_name.replace("-", " ")} tasks.
  Trigger when the user wants to orchestrate {sdk_name.replace("-", " ")} operations at
  scale, generate code using sdk.core.* or sdk.llm.* primitives, or needs a multi-turn
  agentic loop for complex {sdk_name.replace("-", " ")} workflows.
  Also trigger for: "automate {sdk_name.replace("-", " ")}", "build a {sdk_name} pipeline",
  "process multiple {sdk_name.replace("-", " ")} items", or when the task requires
  parallelism, batching, or state management across turns.
---

# {title} SDK

SDK for {sdk_name.replace("-", " ")} tasks. Generate Python code that imports and
orchestrates the SDK's primitives; your code runs in the same Python environment where
the SDK is installed.

## Patterns

### Pattern 1: Single-Turn with Batching
```python
from sdk import core, llm, utils

# Fetch, deduplicate, then batch-process with LLM
items = core.fetch_items(source="your_source", limit=20)
items = core.dedupe_by(items, key="id")

# Batch LLM classification (parallel, preserves order)
results = llm.classify_many(
    [item["content"] for item in items],
    categories=["category_a", "category_b"],
    concurrency=8,
)

for item, result in zip(items, results):
    if result and result.confidence > 0.7:
        print(f"{{item['id']}}: {{result.category}}")
```

### Pattern 2: Fan-Out then Aggregate
```python
from sdk import core, llm, utils

# Fan out over multiple sources, then aggregate
all_items = []
for source in ["source_a", "source_b", "source_c"]:
    batch = core.fetch_items(source=source, limit=10)
    all_items.extend(batch)

all_items = core.dedupe_by(all_items, key="id")

# LLM extraction in batches of 10
extracted = []
for chunk in utils.batch(all_items, size=10):
    batch_results = llm.classify_many(
        [i["content"] for i in chunk],
        categories=["a", "b", "c"],
    )
    extracted.extend(batch_results)

summary = llm.summarize_items(
    [{{**i, "result": r.__dict__ if r else None}} for i, r in zip(all_items, extracted)]
)
print(summary)
```

### Pattern 3: Multi-Turn Agentic Workflow
```python
from sdk import core, llm, orchestrate

def executor(state: orchestrate.TaskState) -> orchestrate.TaskState:
    # Fetch items, skip already-visited, process, accumulate
    new_items = core.fetch_items(source="...", limit=10)
    new_items = [i for i in new_items if i["id"] not in state.visited]

    state.visited.extend(i["id"] for i in new_items)

    classified = llm.classify_many(
        [i["content"] for i in new_items],
        categories=["category_a", "category_b"],
    )
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
print(f"Done: {{len(final.results)}} results in {{final.turn}} turns")
# Resume if interrupted: orchestrate.resume_task_loop(final.task_id, executor, lambda s: ...)
```

## Available Primitives

### `sdk.core` — Deterministic Operations
{core_table}

### `sdk.llm` — LLM-Powered Operations
{llm_table}

### `sdk.orchestrate` — Multi-Turn State
{orch_table}

### `sdk.utils` — Shared Helpers
{utils_table}

## State Management

State is persisted to `.tac_state/<task_id>/` after every turn.

```python
state.results    # list[dict] — accumulated output; extend freely each turn
state.visited    # list[str] — processed IDs; append to avoid reprocessing
state.metadata   # dict — arbitrary extras; all values must be JSON-serializable
state.turn       # int — current turn number (0-indexed)
state.task_id    # str — use to resume: resume_task_loop(state.task_id, ...)
state.status     # str — "running" | "completed" | "incomplete" | "failed"
```

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=<key>   # or OPENAI_API_KEY=<key>
python examples/simple_usage.py  # verify installation
```
"""
    return skill_md


def _build_function_table(module: ModuleInfo) -> str:
    """Build a markdown table of functions for a module."""
    if not module.functions:
        return "_No public functions found — implement this module._"

    rows = []
    for fn in module.functions:
        # Truncate args for display
        args_str = ", ".join(fn.args[:3])
        if len(fn.args) > 3:
            args_str += ", ..."

        # Truncate description
        desc = fn.first_line[:60] + ("..." if len(fn.first_line) > 60 else "")

        rows.append(f"| `{fn.name}({args_str})` | `{fn.return_type}` | {desc} |")

    header = "| Function | Returns | Description |"
    separator = "|---------|---------|-------------|"
    return "\n".join([header, separator] + rows)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    sdk_path = Path(sys.argv[1])

    # Parse --output flag
    output_path = None
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_path = Path(sys.argv[i + 1])

    if not sdk_path.exists():
        print(f"Error: {sdk_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    print(f"Introspecting SDK at: {sdk_path}")

    skill_md = generate_skill_md(sdk_path)

    out = output_path or (sdk_path / "SKILL.md")
    out.write_text(skill_md, encoding="utf-8")

    print(f"✓ Generated consumer SKILL.md: {out}")
    print()
    print("Important: Review the generated file and:")
    print("  1. Update the 'description' frontmatter with domain-specific vocabulary")
    print("  2. Replace Pattern 1-3 examples with real domain orchestration code")
    print("  3. Verify all functions appear in the tables (check for missing ones)")
    print("  4. Ensure examples reference actual function names from your implementation")
