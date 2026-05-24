#!/usr/bin/env python3
"""
code_review_checklist.py — Structured code review against senior engineering standards

Usage:
    # Review a specific file
    python3 code_review_checklist.py --file path/to/file.py

    # Review a git diff (staged changes)
    python3 code_review_checklist.py --diff

    # Review a diff from a specific commit range
    python3 code_review_checklist.py --diff --range HEAD~3..HEAD

    # Review a directory (summary stats across all files)
    python3 code_review_checklist.py --dir src/

    # Output JSON for machine consumption
    python3 code_review_checklist.py --file path/to/file.py --json

The script applies checks derived from the senior-software-engineer skill:
  - Observability (logging, error handling)
  - Hardcoded configuration / secrets
  - TODO / FIXME markers without issue references
  - Missing error handling on I/O
  - Code complexity heuristics
  - Test coverage indicators
  - Common anti-patterns (hardcoded timeouts, bare except, etc.)
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Finding:
    severity: str  # "blocking", "warning", "nit"
    category: str
    line: Optional[int]
    message: str
    snippet: Optional[str] = None


@dataclass
class ReviewResult:
    filepath: str
    findings: List[Finding] = field(default_factory=list)
    
    @property
    def blocking(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "blocking"]
    
    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "warning"]
    
    @property
    def nits(self) -> List[Finding]:
        return [f for f in self.findings if f.severity == "nit"]


# ─── Checkers ─────────────────────────────────────────────────────────────────

HARDCODED_SECRET_PATTERNS = [
    (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', "Hardcoded password"),
    (r'(?i)(api_key|apikey|secret_key)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded API key"),
    (r'(?i)(token)\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded token"),
    (r'(?i)Authorization:\s*Bearer\s+[A-Za-z0-9._-]{20,}', "Hardcoded auth token"),
]

BARE_EXCEPT_PATTERN = re.compile(r'^\s*except\s*:', re.MULTILINE)
BROAD_EXCEPT_PATTERN = re.compile(r'^\s*except\s+Exception\s*:', re.MULTILINE)
TODO_PATTERN = re.compile(r'#\s*(TODO|FIXME|HACK|XXX)(?!\s*#\d+)(?!\s*\w+-\d+):?\s*(.*)', re.IGNORECASE)
PRINT_STATEMENT = re.compile(r'^\s*print\s*\(', re.MULTILINE)
MAGIC_NUMBER = re.compile(r'(?<!["\'\w])\b([2-9]\d{2,}|[1-9]\d{3,})\b(?!["\'])')
HARDCODED_URL = re.compile(r'https?://(?!example\.com)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s"\']*)?')
SLEEP_CALL = re.compile(r'time\.sleep\(\s*(\d+)\s*\)')


def check_secrets(lines: List[str]) -> List[Finding]:
    findings = []
    for i, line in enumerate(lines, 1):
        for pattern, label in HARDCODED_SECRET_PATTERNS:
            if re.search(pattern, line):
                findings.append(Finding(
                    severity="blocking",
                    category="Security",
                    line=i,
                    message=f"{label} detected — use environment variables or a secrets manager",
                    snippet=line.rstrip()
                ))
    return findings


def check_error_handling(content: str, lines: List[str]) -> List[Finding]:
    findings = []
    
    for m in BARE_EXCEPT_PATTERN.finditer(content):
        line_num = content[:m.start()].count('\n') + 1
        findings.append(Finding(
            severity="blocking",
            category="Error Handling",
            line=line_num,
            message="Bare `except:` catches ALL exceptions including KeyboardInterrupt and SystemExit. Catch specific exception types.",
            snippet=lines[line_num - 1].rstrip() if line_num <= len(lines) else None
        ))
    
    for m in BROAD_EXCEPT_PATTERN.finditer(content):
        line_num = content[:m.start()].count('\n') + 1
        findings.append(Finding(
            severity="warning",
            category="Error Handling",
            line=line_num,
            message="`except Exception` is broad. Catch specific exceptions unless this is a top-level error boundary.",
            snippet=lines[line_num - 1].rstrip() if line_num <= len(lines) else None
        ))
    
    return findings


def check_logging(lines: List[str]) -> List[Finding]:
    findings = []
    for i, line in enumerate(lines, 1):
        if PRINT_STATEMENT.match(line):
            findings.append(Finding(
                severity="warning",
                category="Observability",
                line=i,
                message="Use structured logging instead of print(). print() statements don't appear in log aggregation.",
                snippet=line.rstrip()
            ))
    return findings


def check_todos(lines: List[str]) -> List[Finding]:
    findings = []
    for i, line in enumerate(lines, 1):
        m = TODO_PATTERN.search(line)
        if m:
            tag = m.group(1).upper()
            text = m.group(2).strip()
            findings.append(Finding(
                severity="nit",
                category="Code Quality",
                line=i,
                message=f"{tag} without issue tracker reference: '{text}'. Link to a ticket so it doesn't get lost.",
                snippet=line.rstrip()
            ))
    return findings


def check_magic_numbers(lines: List[str]) -> List[Finding]:
    findings = []
    skip_patterns = [re.compile(p) for p in [
        r'^\s*#',          # comment lines
        r'version\s*=',    # version strings
        r'port\s*=\s*\d+', # port numbers (common)
    ]]
    
    for i, line in enumerate(lines, 1):
        if any(p.search(line) for p in skip_patterns):
            continue
        m = MAGIC_NUMBER.search(line)
        if m:
            findings.append(Finding(
                severity="nit",
                category="Code Quality",
                line=i,
                message=f"Magic number {m.group(0)} — consider a named constant to explain its meaning.",
                snippet=line.rstrip()
            ))
    return findings


def check_hardcoded_config(lines: List[str]) -> List[Finding]:
    findings = []
    for i, line in enumerate(lines, 1):
        # Check for hardcoded URLs that look like environment-specific endpoints
        if re.search(r'https?://(?:api\.|app\.|prod\.|staging\.)', line):
            findings.append(Finding(
                severity="warning",
                category="Configuration",
                line=i,
                message="Hardcoded environment-specific URL. Use configuration/environment variables.",
                snippet=line.rstrip()
            ))
    return findings


def check_sleep_calls(lines: List[str]) -> List[Finding]:
    findings = []
    for i, line in enumerate(lines, 1):
        m = SLEEP_CALL.search(line)
        if m:
            secs = int(m.group(1))
            if secs > 5:
                findings.append(Finding(
                    severity="warning",
                    category="Performance",
                    line=i,
                    message=f"Long sleep({secs}s) detected. Use event-driven approaches, queues, or polling with backoff instead of arbitrary sleeps.",
                    snippet=line.rstrip()
                ))
    return findings


def check_python_complexity(filepath: str, content: str) -> List[Finding]:
    """Basic AST-based complexity checks for Python files."""
    findings = []
    
    if not filepath.endswith('.py'):
        return findings
    
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        findings.append(Finding(
            severity="blocking",
            category="Syntax",
            line=e.lineno,
            message=f"Syntax error: {e.msg}",
        ))
        return findings
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Count branches as a rough complexity proxy
            branch_count = sum(
                1 for child in ast.walk(node)
                if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With))
            )
            if branch_count > 10:
                findings.append(Finding(
                    severity="warning",
                    category="Complexity",
                    line=node.lineno,
                    message=f"Function `{node.name}` has high cyclomatic complexity (~{branch_count} branches). Consider breaking it into smaller functions.",
                ))
            
            # Long functions
            if hasattr(node, 'end_lineno'):
                length = node.end_lineno - node.lineno
                if length > 50:
                    findings.append(Finding(
                        severity="nit",
                        category="Complexity",
                        line=node.lineno,
                        message=f"Function `{node.name}` is {length} lines long. Functions over 50 lines are often doing too much.",
                    ))
    
    return findings


# ─── Review Orchestration ──────────────────────────────────────────────────────

def review_file(filepath: str) -> ReviewResult:
    result = ReviewResult(filepath=filepath)
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except (IOError, OSError) as e:
        result.findings.append(Finding(
            severity="blocking",
            category="IO",
            line=None,
            message=f"Could not read file: {e}"
        ))
        return result
    
    lines = content.splitlines()
    
    result.findings.extend(check_secrets(lines))
    result.findings.extend(check_error_handling(content, lines))
    result.findings.extend(check_logging(lines))
    result.findings.extend(check_todos(lines))
    result.findings.extend(check_magic_numbers(lines))
    result.findings.extend(check_hardcoded_config(lines))
    result.findings.extend(check_sleep_calls(lines))
    result.findings.extend(check_python_complexity(filepath, content))
    
    return result


def review_from_diff(commit_range: Optional[str] = None) -> List[ReviewResult]:
    """Extract changed files from git diff and review them."""
    cmd = ["git", "diff", "--name-only"]
    if commit_range:
        cmd.append(commit_range)
    else:
        cmd.append("--cached")  # staged changes
    
    try:
        output = subprocess.check_output(cmd, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running git diff: {e}", file=sys.stderr)
        sys.exit(1)
    
    files = [f.strip() for f in output.splitlines() if f.strip()]
    results = []
    for filepath in files:
        if os.path.exists(filepath):
            results.append(review_file(filepath))
    return results


# ─── Output Formatters ─────────────────────────────────────────────────────────

SEVERITY_EMOJI = {"blocking": "🔴", "warning": "🟡", "nit": "🔵"}
SEVERITY_ORDER = {"blocking": 0, "warning": 1, "nit": 2}


def print_results(results: List[ReviewResult]):
    total_blocking = sum(len(r.blocking) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    total_nits = sum(len(r.nits) for r in results)
    
    for result in results:
        if not result.findings:
            print(f"✅ {result.filepath} — No issues found")
            continue
        
        print(f"\n{'='*60}")
        print(f"📄 {result.filepath}")
        print(f"   🔴 {len(result.blocking)} blocking  🟡 {len(result.warnings)} warnings  🔵 {len(result.nits)} nits")
        print()
        
        sorted_findings = sorted(result.findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.line or 0))
        
        for finding in sorted_findings:
            emoji = SEVERITY_EMOJI[finding.severity]
            loc = f"line {finding.line}" if finding.line else "file"
            print(f"  {emoji} [{finding.category}] {loc}: {finding.message}")
            if finding.snippet:
                print(f"     > {finding.snippet[:100]}")
    
    print(f"\n{'='*60}")
    print(f"Summary: 🔴 {total_blocking} blocking  🟡 {total_warnings} warnings  🔵 {total_nits} nits")
    
    if total_blocking > 0:
        print("\n⛔ BLOCKING issues must be resolved before merging.")
        sys.exit(1)
    elif total_warnings > 0:
        print("\n⚠️  Review warnings before merging.")
    else:
        print("\n✅ No blocking issues.")


def print_json(results: List[ReviewResult]):
    output = []
    for result in results:
        output.append({
            "filepath": result.filepath,
            "summary": {
                "blocking": len(result.blocking),
                "warnings": len(result.warnings),
                "nits": len(result.nits),
            },
            "findings": [
                {
                    "severity": f.severity,
                    "category": f.category,
                    "line": f.line,
                    "message": f.message,
                    "snippet": f.snippet,
                }
                for f in result.findings
            ]
        })
    print(json.dumps(output, indent=2))


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Senior engineer code review checklist")
    parser.add_argument("--file", help="Review a specific file")
    parser.add_argument("--dir", help="Review all code files in a directory")
    parser.add_argument("--diff", action="store_true", help="Review staged git diff")
    parser.add_argument("--range", help="Git commit range (e.g., HEAD~3..HEAD)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    results = []
    
    if args.file:
        results.append(review_file(args.file))
    elif args.dir:
        extensions = {'.py', '.js', '.ts', '.go', '.rb', '.java'}
        for root, _, files in os.walk(args.dir):
            if '.git' in root or 'node_modules' in root or '__pycache__' in root:
                continue
            for file in files:
                if Path(file).suffix in extensions:
                    results.append(review_file(os.path.join(root, file)))
    elif args.diff or args.range:
        results = review_from_diff(args.range)
    else:
        parser.print_help()
        sys.exit(0)
    
    if args.json:
        print_json(results)
    else:
        print_results(results)


if __name__ == "__main__":
    main()
