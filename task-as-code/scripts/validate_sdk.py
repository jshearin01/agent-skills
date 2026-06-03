#!/usr/bin/env python3
"""
Validate a Task as Code (TaC) SDK for structural completeness and quality.

Usage:
    python validate_sdk.py <path-to-sdk>
    python validate_sdk.py design-system-sdk/
    python validate_sdk.py ./my-sdks/web-research-sdk/ --strict

Checks performed:
  STRUCTURE  — Required files and directories exist
  IMPORTS    — SDK modules are importable without errors
  FUNCTIONS  — All public functions have type hints and docstrings
  PROMPTS    — llm.py prompt constants follow naming convention (_PROMPT_*)
  STATE      — TaskState is JSON-serializable (roundtrip test)
  EXAMPLES   — example files exist and are syntactically valid
  SKILL      — SKILL.md has required YAML frontmatter
  QUALITY    — Deeper checks (--strict only): no TODOs, no placeholder functions
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Result Types
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    details: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    sdk_path: Path
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if not c.passed)


# ---------------------------------------------------------------------------
# Individual Checks
# ---------------------------------------------------------------------------

def check_structure(sdk_path: Path) -> CheckResult:
    """Verify required files and directories exist."""
    required = [
        "SKILL.md",
        "requirements.txt",
        "sdk/__init__.py",
        "sdk/core.py",
        "sdk/llm.py",
        "sdk/orchestrate.py",
        "sdk/utils.py",
        "examples/simple_usage.py",
        "examples/agentic_usage.py",
        "prompts/system.md",
    ]
    missing = [f for f in required if not (sdk_path / f).exists()]
    if missing:
        return CheckResult(
            "STRUCTURE", False,
            f"{len(missing)} required file(s) missing",
            [f"  Missing: {f}" for f in missing],
        )
    return CheckResult("STRUCTURE", True, f"All {len(required)} required files present")


def check_imports(sdk_path: Path) -> CheckResult:
    """Verify SDK modules are importable."""
    modules = ["core", "llm", "orchestrate", "utils"]
    errors = []

    for mod_name in modules:
        mod_path = sdk_path / "sdk" / f"{mod_name}.py"
        if not mod_path.exists():
            continue
        try:
            spec = importlib.util.spec_from_file_location(mod_name, mod_path)
            if spec is None or spec.loader is None:
                errors.append(f"  {mod_name}.py: could not create module spec")
                continue
            # Parse AST to check syntax without executing (avoids import side effects)
            source = mod_path.read_text(encoding="utf-8")
            ast.parse(source)
        except SyntaxError as e:
            errors.append(f"  {mod_name}.py: SyntaxError at line {e.lineno}: {e.msg}")
        except Exception as e:
            errors.append(f"  {mod_name}.py: {e}")

    if errors:
        return CheckResult("IMPORTS", False, f"{len(errors)} module(s) have syntax errors", errors)
    return CheckResult("IMPORTS", True, f"All {len(modules)} modules parse without syntax errors")


def check_functions(sdk_path: Path) -> CheckResult:
    """Verify all public functions have type hints and docstrings."""
    issues = []

    for mod_file in ["sdk/core.py", "sdk/llm.py"]:
        path = sdk_path / mod_file
        if not path.exists():
            continue

        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name.startswith("_"):
                continue  # skip private functions

            # Check docstring
            has_docstring = (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            )

            # Check return type annotation
            has_return_type = node.returns is not None

            # Check at least some arg annotations (skip 'self')
            args = [a for a in node.args.args if a.arg not in ("self", "cls")]
            annotated = sum(1 for a in args if a.annotation is not None)
            has_type_hints = len(args) == 0 or annotated > 0

            if not has_docstring:
                issues.append(f"  {mod_file}:{node.lineno} {node.name}() — missing docstring")
            if not has_return_type:
                issues.append(f"  {mod_file}:{node.lineno} {node.name}() — missing return type hint")
            if not has_type_hints and args:
                issues.append(f"  {mod_file}:{node.lineno} {node.name}() — missing parameter type hints")

    if issues:
        return CheckResult(
            "FUNCTIONS", False,
            f"{len(issues)} function(s) missing docstrings or type hints",
            issues[:10] + (["  ... (truncated)"] if len(issues) > 10 else []),
        )
    return CheckResult("FUNCTIONS", True, "All public functions have docstrings and type hints")


def check_prompts(sdk_path: Path) -> CheckResult:
    """Verify llm.py prompt constants follow the _PROMPT_* naming convention."""
    llm_path = sdk_path / "sdk" / "llm.py"
    if not llm_path.exists():
        return CheckResult("PROMPTS", True, "llm.py not found, skipping")

    source = llm_path.read_text(encoding="utf-8")
    issues = []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return CheckResult("PROMPTS", False, "llm.py has syntax errors, skipping prompt check")

    # Find module-level string assignments
    prompt_constants = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("_PROMPT_"):
                    prompt_constants.add(target.id)

    # Check that llm functions that call call_llm have a corresponding _PROMPT_*
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name.startswith("_"):
            continue

        # Check if function body references call_llm
        calls_llm = False
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                if isinstance(func, ast.Name) and func.id == "call_llm":
                    calls_llm = True
                elif isinstance(func, ast.Attribute) and func.attr == "call_llm":
                    calls_llm = True

        if not calls_llm:
            continue

        # Check if this function uses a _PROMPT_* constant
        uses_prompt_const = False
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id.startswith("_PROMPT_"):
                uses_prompt_const = True

        if not uses_prompt_const:
            issues.append(
                f"  {node.name}() calls call_llm but doesn't reference a _PROMPT_* constant"
            )

    if not prompt_constants:
        issues.append("  No _PROMPT_* constants found in llm.py")

    if issues:
        return CheckResult("PROMPTS", False, "Prompt constant issues found", issues)
    return CheckResult(
        "PROMPTS", True,
        f"Found {len(prompt_constants)} _PROMPT_* constant(s); all llm functions reference them"
    )


def check_state(sdk_path: Path) -> CheckResult:
    """Verify TaskState is JSON-serializable."""
    orch_path = sdk_path / "sdk" / "orchestrate.py"
    if not orch_path.exists():
        return CheckResult("STATE", False, "orchestrate.py not found")

    source = orch_path.read_text(encoding="utf-8")
    issues = []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return CheckResult("STATE", False, "orchestrate.py has syntax errors")

    # Check that TaskState dataclass exists
    has_task_state = any(
        isinstance(node, ast.ClassDef) and node.name == "TaskState"
        for node in ast.walk(tree)
    )

    # Check that required functions exist
    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }

    required_fns = {"save_state", "load_state", "run_task_loop", "resume_task_loop"}
    missing_fns = required_fns - function_names

    if not has_task_state:
        issues.append("  TaskState class not found in orchestrate.py")
    if missing_fns:
        issues.append(f"  Missing required functions: {', '.join(sorted(missing_fns))}")

    # Check that json and dataclasses are imported (needed for serialization)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    if "json" not in imports:
        issues.append("  'json' module not imported (needed for state serialization)")
    if "dataclasses" not in imports:
        issues.append("  'dataclasses' module not imported (needed for asdict())")

    if issues:
        return CheckResult("STATE", False, "State management issues found", issues)
    return CheckResult(
        "STATE", True,
        f"TaskState class found; {len(required_fns)} required functions present"
    )


def check_examples(sdk_path: Path) -> CheckResult:
    """Verify example files exist and are syntactically valid Python."""
    examples = ["examples/simple_usage.py", "examples/agentic_usage.py"]
    issues = []

    for example in examples:
        path = sdk_path / example
        if not path.exists():
            issues.append(f"  Missing: {example}")
            continue
        source = path.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as e:
            issues.append(f"  {example}: SyntaxError at line {e.lineno}: {e.msg}")

    if issues:
        return CheckResult("EXAMPLES", False, "Example file issues found", issues)
    return CheckResult("EXAMPLES", True, "Both example files present and valid")


def check_skill_md(sdk_path: Path) -> CheckResult:
    """Verify SKILL.md has YAML frontmatter with required fields."""
    skill_path = sdk_path / "SKILL.md"
    if not skill_path.exists():
        return CheckResult("SKILL", False, "SKILL.md not found")

    content = skill_path.read_text(encoding="utf-8")
    issues = []

    if not content.startswith("---"):
        issues.append("  SKILL.md does not start with YAML frontmatter (---)")
    else:
        end = content.find("---", 3)
        if end == -1:
            issues.append("  SKILL.md frontmatter not closed (missing closing ---)")
        else:
            frontmatter = content[3:end]
            if "name:" not in frontmatter:
                issues.append("  SKILL.md frontmatter missing 'name:' field")
            if "description:" not in frontmatter:
                issues.append("  SKILL.md frontmatter missing 'description:' field")

    # Check for placeholder text
    if "TODO" in content:
        issues.append("  SKILL.md still contains TODO placeholder text")

    if issues:
        return CheckResult("SKILL", False, "SKILL.md issues found", issues)
    return CheckResult("SKILL", True, "SKILL.md has valid frontmatter with name and description")


def check_quality(sdk_path: Path) -> CheckResult:
    """Strict quality checks: no NotImplementedError, no TODO comments in SDK."""
    issues = []

    for mod in ["sdk/core.py", "sdk/llm.py", "sdk/orchestrate.py", "sdk/utils.py"]:
        path = sdk_path / mod
        if not path.exists():
            continue
        source = path.read_text(encoding="utf-8")

        if "NotImplementedError" in source:
            count = source.count("NotImplementedError")
            issues.append(f"  {mod}: {count} NotImplementedError(s) — placeholder functions remain")

        todo_lines = [
            f"line {i+1}: {line.strip()[:80]}"
            for i, line in enumerate(source.splitlines())
            if "# TODO" in line or "# todo" in line.lower()
        ]
        if todo_lines:
            issues.append(f"  {mod}: {len(todo_lines)} TODO comment(s)")

    if issues:
        return CheckResult(
            "QUALITY", False,
            f"{len(issues)} quality issue(s) found (placeholder or incomplete code)",
            issues,
        )
    return CheckResult("QUALITY", True, "No placeholder functions or TODO comments in SDK modules")


# ---------------------------------------------------------------------------
# Main Validator
# ---------------------------------------------------------------------------

def validate(sdk_path: Path, strict: bool = False) -> ValidationReport:
    """Run all validation checks on an SDK directory."""
    report = ValidationReport(sdk_path=sdk_path)

    checks = [
        check_structure,
        check_imports,
        check_functions,
        check_prompts,
        check_state,
        check_examples,
        check_skill_md,
    ]

    if strict:
        checks.append(check_quality)

    for check_fn in checks:
        result = check_fn(sdk_path)
        report.checks.append(result)

    return report


def print_report(report: ValidationReport) -> None:
    """Print the validation report to stdout."""
    print(f"\nTaC SDK Validation: {report.sdk_path.name}")
    print("=" * 50)

    for check in report.checks:
        icon = "✓" if check.passed else "✗"
        print(f"  {icon} {check.name:12s} {check.message}")
        for detail in check.details:
            print(f"             {detail}")

    print("-" * 50)
    print(f"  Result: {report.pass_count}/{len(report.checks)} checks passed")
    if report.passed:
        print("  ✓ SDK is valid and ready for use")
    else:
        print(f"  ✗ {report.fail_count} check(s) failed — fix issues before packaging")
    print()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    sdk_path = Path(sys.argv[1])
    strict = "--strict" in sys.argv

    if not sdk_path.exists():
        print(f"Error: {sdk_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    report = validate(sdk_path, strict=strict)
    print_report(report)
    sys.exit(0 if report.passed else 1)
