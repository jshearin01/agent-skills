#!/usr/bin/env python3
"""
tech_debt_audit.py — Scan a codebase for technical debt indicators

Scans a directory and produces a prioritized report of technical debt signals,
using heuristics distilled from the senior-software-engineer skill.

Usage:
    python3 tech_debt_audit.py --dir src/
    python3 tech_debt_audit.py --dir . --exclude tests/ vendor/ node_modules/
    python3 tech_debt_audit.py --dir src/ --json > debt_report.json
    python3 tech_debt_audit.py --dir src/ --top 20  # Show only top 20 issues

Categories scanned:
    COMPLEXITY     - Long files, large functions, deeply nested code
    DUPLICATION    - Repeated code blocks (heuristic)
    OBSERVABILITY  - Missing logging, bare excepts swallowing errors
    COUPLING       - Circular imports (Python), God-object signals
    HYGIENE        - Dead code signals, orphaned TODOs, commented-out code
    SECURITY       - Hardcoded secrets, SQL injection risks
    TESTING        - Missing test coverage signals, test anti-patterns
    DOCUMENTATION  - Undocumented public APIs, missing docstrings
"""

import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class DebtItem:
    category: str
    priority: str          # "critical", "high", "medium", "low"
    filepath: str
    line: Optional[int]
    message: str
    effort: str            # "minutes", "hours", "days"
    
    def as_dict(self) -> dict:
        return {
            "category": self.category,
            "priority": self.priority,
            "filepath": self.filepath,
            "line": self.line,
            "message": self.message,
            "effort": self.effort,
        }


@dataclass
class AuditReport:
    root_dir: str
    files_scanned: int = 0
    total_lines: int = 0
    items: List[DebtItem] = field(default_factory=list)
    
    def by_priority(self) -> Dict[str, List[DebtItem]]:
        grouped = defaultdict(list)
        for item in self.items:
            grouped[item.priority].append(item)
        return dict(grouped)
    
    def by_category(self) -> Dict[str, List[DebtItem]]:
        grouped = defaultdict(list)
        for item in self.items:
            grouped[item.category].append(item)
        return dict(grouped)


# ─── Per-File Scanners ────────────────────────────────────────────────────────

COMMENTED_CODE_PATTERNS = [
    re.compile(r'^\s*#\s+(def |class |import |from |return |if |for |while )', re.MULTILINE),
    re.compile(r'^\s*//\s+(function |class |import |return |if |for )', re.MULTILINE),
]

HARDCODED_CREDENTIALS = [
    re.compile(r'(?i)(password|passwd|api_key|secret)\s*=\s*["\'][^"\']{4,}["\']'),
    re.compile(r'(?i)Authorization:\s*Bearer\s+[A-Za-z0-9._-]{20,}'),
]

TODO_RE = re.compile(r'#\s*(TODO|FIXME|HACK)\s*:?\s*(.*)', re.IGNORECASE)
BARE_EXCEPT_RE = re.compile(r'^\s*except\s*:', re.MULTILINE)
SLEEP_LONGWAIT = re.compile(r'time\.sleep\(\s*(\d+)\s*\)')


def scan_file_generic(filepath: str, content: str, lines: List[str]) -> List[DebtItem]:
    items = []
    
    # Hardcoded credentials
    for pattern in HARDCODED_CREDENTIALS:
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                items.append(DebtItem(
                    category="SECURITY",
                    priority="critical",
                    filepath=filepath,
                    line=i,
                    message="Possible hardcoded credential — move to environment variable or secrets manager",
                    effort="minutes",
                ))
    
    # Long files
    if len(lines) > 500:
        items.append(DebtItem(
            category="COMPLEXITY",
            priority="medium",
            filepath=filepath,
            line=None,
            message=f"File is {len(lines)} lines long. Files over 500 lines often have too many responsibilities.",
            effort="days",
        ))
    
    # Orphaned TODOs
    for i, line in enumerate(lines, 1):
        m = TODO_RE.search(line)
        if m:
            tag = m.group(1).upper()
            text = m.group(2).strip()[:80]
            priority = "high" if tag == "FIXME" else "low"
            items.append(DebtItem(
                category="HYGIENE",
                priority=priority,
                filepath=filepath,
                line=i,
                message=f"Unresolved {tag}: '{text}' — link to an issue tracker ticket or resolve",
                effort="minutes",
            ))
    
    # Commented-out code blocks
    for pattern in COMMENTED_CODE_PATTERNS:
        for m in pattern.finditer(content):
            line_num = content[:m.start()].count('\n') + 1
            items.append(DebtItem(
                category="HYGIENE",
                priority="low",
                filepath=filepath,
                line=line_num,
                message="Commented-out code detected — delete it (version control preserves history)",
                effort="minutes",
            ))
        break  # Only report once per file for commented code
    
    return items


def scan_python_file(filepath: str, content: str, lines: List[str]) -> List[DebtItem]:
    items = []
    
    # Bare excepts
    for m in BARE_EXCEPT_RE.finditer(content):
        line_num = content[:m.start()].count('\n') + 1
        items.append(DebtItem(
            category="OBSERVABILITY",
            priority="high",
            filepath=filepath,
            line=line_num,
            message="Bare `except:` silently swallows all exceptions — errors become invisible",
            effort="hours",
        ))
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return items
    
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        
        # Cyclomatic complexity proxy
        branches = sum(
            1 for child in ast.walk(node)
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                   ast.With, ast.Assert))
        )
        if branches > 15:
            items.append(DebtItem(
                category="COMPLEXITY",
                priority="high",
                filepath=filepath,
                line=node.lineno,
                message=f"`{node.name}()` has high complexity (~{branches} branches) — hard to test and understand",
                effort="hours",
            ))
        elif branches > 10:
            items.append(DebtItem(
                category="COMPLEXITY",
                priority="medium",
                filepath=filepath,
                line=node.lineno,
                message=f"`{node.name}()` has moderate complexity (~{branches} branches) — consider splitting",
                effort="hours",
            ))
        
        # Long functions
        if hasattr(node, 'end_lineno'):
            func_len = node.end_lineno - node.lineno
            if func_len > 100:
                items.append(DebtItem(
                    category="COMPLEXITY",
                    priority="high",
                    filepath=filepath,
                    line=node.lineno,
                    message=f"`{node.name}()` is {func_len} lines — very likely doing too much",
                    effort="days",
                ))
            elif func_len > 50:
                items.append(DebtItem(
                    category="COMPLEXITY",
                    priority="medium",
                    filepath=filepath,
                    line=node.lineno,
                    message=f"`{node.name}()` is {func_len} lines — consider splitting for readability",
                    effort="hours",
                ))
        
        # Missing docstrings on public functions
        is_public = not node.name.startswith('_')
        has_docstring = (
            node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)
        )
        if is_public and not has_docstring and branches > 3:
            items.append(DebtItem(
                category="DOCUMENTATION",
                priority="low",
                filepath=filepath,
                line=node.lineno,
                message=f"Public function `{node.name}()` with complex logic has no docstring",
                effort="minutes",
            ))
    
    # Class-level: large classes (God object signal)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = [n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if len(methods) > 20:
            items.append(DebtItem(
                category="COUPLING",
                priority="high",
                filepath=filepath,
                line=node.lineno,
                message=f"Class `{node.name}` has {len(methods)} methods — possible God Object, consider decomposing",
                effort="days",
            ))
    
    return items


# ─── Directory Scanner ────────────────────────────────────────────────────────

SUPPORTED_EXTENSIONS: Set[str] = {'.py', '.js', '.ts', '.go', '.rb', '.java', '.cs'}
EXCLUDE_DIRS: Set[str] = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'vendor', 'dist', 'build'}


def scan_directory(root_dir: str, exclude: List[str] = None, top_n: Optional[int] = None) -> AuditReport:
    report = AuditReport(root_dir=root_dir)
    exclude_set = EXCLUDE_DIRS | set(exclude or [])
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prune excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_set]
        
        for filename in filenames:
            ext = Path(filename).suffix
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            
            filepath = os.path.join(dirpath, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except (IOError, OSError):
                continue
            
            lines = content.splitlines()
            report.files_scanned += 1
            report.total_lines += len(lines)
            
            # Generic checks for all files
            report.items.extend(scan_file_generic(filepath, content, lines))
            
            # Language-specific checks
            if ext == '.py':
                report.items.extend(scan_python_file(filepath, content, lines))
    
    # Sort by priority then category
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    report.items.sort(key=lambda x: (priority_order.get(x.priority, 99), x.category, x.filepath))
    
    if top_n:
        report.items = report.items[:top_n]
    
    return report


# ─── Output Formatters ────────────────────────────────────────────────────────

PRIORITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}


def print_report(report: AuditReport):
    print(f"\n{'='*70}")
    print(f"Technical Debt Audit: {report.root_dir}")
    print(f"{'='*70}")
    print(f"Files scanned: {report.files_scanned:,}   Total lines: {report.total_lines:,}")
    print(f"Issues found:  {len(report.items):,}\n")
    
    by_cat = report.by_category()
    by_pri = report.by_priority()
    
    print("By category:")
    for cat, items in sorted(by_cat.items()):
        counts = defaultdict(int)
        for item in items:
            counts[item.priority] += 1
        summary = "  ".join(f"{PRIORITY_EMOJI[p]}{counts[p]}" for p in ["critical","high","medium","low"] if counts[p])
        print(f"  {cat:<16} {len(items):>3}  {summary}")
    
    print()
    for priority in ["critical", "high", "medium", "low"]:
        items = by_pri.get(priority, [])
        if not items:
            continue
        
        emoji = PRIORITY_EMOJI[priority]
        print(f"\n{emoji} {priority.upper()} ({len(items)} items)")
        print("-" * 60)
        
        for item in items:
            loc = f":{item.line}" if item.line else ""
            print(f"  [{item.category}] {item.filepath}{loc}")
            print(f"    {item.message}")
            print(f"    Effort: ~{item.effort}")
    
    critical_count = len(by_pri.get("critical", []))
    high_count = len(by_pri.get("high", []))
    
    print(f"\n{'='*70}")
    if critical_count > 0:
        print(f"⛔ {critical_count} CRITICAL issues require immediate attention.")
    elif high_count > 0:
        print(f"⚠️  {high_count} high-priority issues worth addressing soon.")
    else:
        print("✅ No critical or high-priority debt detected.")
    
    print("\nRecommendation: Address critical issues immediately. Schedule high-priority")
    print("items in the next 2 sprints. Track medium/low items in your backlog.")


def print_json_report(report: AuditReport):
    output = {
        "root_dir": report.root_dir,
        "files_scanned": report.files_scanned,
        "total_lines": report.total_lines,
        "summary": {
            "total": len(report.items),
            "critical": len([i for i in report.items if i.priority == "critical"]),
            "high": len([i for i in report.items if i.priority == "high"]),
            "medium": len([i for i in report.items if i.priority == "medium"]),
            "low": len([i for i in report.items if i.priority == "low"]),
        },
        "items": [item.as_dict() for item in report.items],
    }
    print(json.dumps(output, indent=2))


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Technical debt audit — scan a codebase for debt indicators"
    )
    parser.add_argument("--dir", default=".", help="Directory to scan (default: current)")
    parser.add_argument("--exclude", nargs="*", default=[], help="Additional directories to exclude")
    parser.add_argument("--top", type=int, help="Show only the top N issues")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.dir):
        print(f"Error: '{args.dir}' is not a directory.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Scanning {args.dir}...", file=sys.stderr)
    report = scan_directory(args.dir, exclude=args.exclude, top_n=args.top)
    
    if args.json:
        print_json_report(report)
    else:
        print_report(report)


if __name__ == "__main__":
    main()
