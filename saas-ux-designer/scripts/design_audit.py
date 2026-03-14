#!/usr/bin/env python3
"""
design_audit.py - SaaS UI/UX Design Auditor

Scans HTML/CSS/JSX/TSX/Svelte files for AI slop patterns and UX anti-patterns.
Produces a prioritized report of issues with suggested fixes.

Usage:
    python design_audit.py <path>           # audit single file
    python design_audit.py <directory>      # audit entire directory
    python design_audit.py <path> --json    # output JSON report
    python design_audit.py <path> --strict  # treat warnings as errors
"""

import re
import sys
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


# ─────────────────────────────────────────
# Issue definitions
# ─────────────────────────────────────────

@dataclass
class Issue:
    priority: str       # critical | high | medium | low
    category: str       # typography | color | layout | ux | accessibility | motion
    message: str
    fix: str
    line: Optional[int] = None
    evidence: Optional[str] = None


@dataclass
class AuditResult:
    filepath: str
    issues: List[Issue] = field(default_factory=list)

    @property
    def critical(self): return [i for i in self.issues if i.priority == "critical"]
    @property
    def high(self): return [i for i in self.issues if i.priority == "high"]
    @property
    def medium(self): return [i for i in self.issues if i.priority == "medium"]
    @property
    def low(self): return [i for i in self.issues if i.priority == "low"]
    @property
    def score(self):
        weights = {"critical": 10, "high": 4, "medium": 2, "low": 1}
        penalty = sum(weights[i.priority] for i in self.issues)
        return max(0, 100 - penalty)


# ─────────────────────────────────────────
# Audit rules
# ─────────────────────────────────────────

RULES = [

    # ── Accessibility (Critical) ──
    {
        "priority": "critical",
        "category": "accessibility",
        "pattern": r'placeholder(?:\s*=\s*)["\'](?!.*aria-label)[^"\']{3,}',
        "condition": lambda m, content: 'aria-label' not in content[max(0, content.rfind('<', 0, m.start())):m.end()+200],
        "message": "Input may be using placeholder as label",
        "fix": "Add a visible <label> element. Placeholder text disappears on focus and is not accessible.",
    },
    {
        "priority": "critical",
        "category": "accessibility",
        "pattern": r'outline\s*:\s*0|outline\s*:\s*none',
        "message": "Focus outline removed — keyboard users cannot navigate",
        "fix": "Never remove focus outlines. Replace with a custom outline: 'outline: 2px solid var(--color-border-focus); outline-offset: 2px' or use box-shadow instead.",
    },
    {
        "priority": "critical",
        "category": "accessibility",
        "pattern": r'<(img|svg)[^>]+>(?![^<]*alt)',
        "message": "Image or SVG may be missing alt attribute",
        "fix": "Add alt='descriptive text' or alt='' for decorative images. All SVGs used as content need aria-label.",
    },
    {
        "priority": "critical",
        "category": "accessibility",
        "pattern": r'on(?:click|keydown)=["\'][^"\']*["\'](?![^>]*role=)',
        "condition": lambda m, content: 'button' not in content[max(0, m.start()-10):m.start()].lower() and '<a ' not in content[max(0, m.start()-10):m.start()],
        "message": "Click handler on a non-interactive element (may be a div/span)",
        "fix": "Use <button> or <a> elements for interactive elements — not divs. Adds keyboard and screen reader support automatically.",
    },

    # ── AI Slop: Typography (High) ──
    {
        "priority": "high",
        "category": "typography",
        "pattern": r"""['"]Inter['"]|font-family:\s*['"]?Inter['"]?""",
        "message": "Inter font detected — generic AI slop indicator",
        "fix": "Choose a font with personality: DM Sans, Plus Jakarta Sans, Bricolage Grotesque, IBM Plex Sans, Sohne, or Geist. Read references/aesthetic-systems.md for font pairing guidance.",
    },
    {
        "priority": "medium",
        "category": "typography",
        "pattern": r"""['"](?:Roboto|Open Sans|Lato|Nunito)['"]""",
        "message": "Generic safe font detected — no visual personality",
        "fix": "Replace with a more distinctive choice. Even system-ui with good weights has more personality than generic web fonts.",
    },
    {
        "priority": "medium",
        "category": "typography",
        "pattern": r'font-weight\s*:\s*[45]00\b',
        "message": "Mid-range font weights dominating (400-500 only)",
        "fix": "Add contrast by using extreme weights (700-900 for headings, 200-300 for large display text). Flat weight range = flat visual hierarchy.",
    },
    {
        "priority": "low",
        "category": "typography",
        "pattern": r'text-transform\s*:\s*uppercase',
        "message": "All-caps text detected",
        "fix": "Use sparingly and only for labels/badges, never for body text or headings. All-caps reduces readability and can feel aggressive at scale.",
    },

    # ── AI Slop: Color (High) ──
    {
        "priority": "high",
        "category": "color",
        "pattern": r'(?:#7c3aed|#8b5cf6|#6d28d9|#4c1d95|rgb\(124,\s*58,\s*237\))',
        "message": "Purple accent detected — most common AI slop color",
        "fix": "Choose an accent color that reflects the product's personality. Terracotta, teal, amber, forest green, navy — anything more intentional than default purple.",
    },
    {
        "priority": "high",
        "category": "color",
        "pattern": r'background(?:-color)?\s*:\s*(?:#fff(?:fff)?|white)\b',
        "message": "Pure white (#ffffff) background — flat and harsh",
        "fix": "Use a slightly warm or cool off-white: #fafaf9, #f8f7f4, #f9fafb. Pure white has no depth and increases eye strain.",
    },
    {
        "priority": "medium",
        "category": "color",
        "pattern": r'(?:background|background-image)\s*:\s*linear-gradient\([^)]*(?:#[0-9a-f]{3,6}[^)]*){3,}',
        "message": "Complex gradient with many stops detected",
        "fix": "Limit gradients to 2-3 stops. Complex gradients often look muddy and unintentional. Read references/aesthetic-systems.md for gradient guidance.",
    },
    {
        "priority": "low",
        "category": "color",
        "pattern": r'color\s*:\s*(?:#fff(?:fff)?|white)\s*;[^}]*background[^:]*:\s*(?:#fff(?:fff)?|white)',
        "message": "White text on white background — possible contrast issue",
        "fix": "Verify contrast ratio is at least 4.5:1 for body text (WCAG AA).",
    },

    # ── AI Slop: Layout (Medium) ──
    {
        "priority": "medium",
        "category": "layout",
        "pattern": r'(?:class|className)=["\'][^"\']*(?:grid-cols-3|three.col)[^"\']*["\']',
        "message": "3-column grid detected — most common AI layout pattern",
        "fix": "3-col feature grids are extremely overused. Try 2-col with more depth, asymmetric layouts, or a list format with richer content per item.",
    },
    {
        "priority": "low",
        "category": "layout",
        "pattern": r'border-radius\s*:\s*(?:9999px|999px|50px)',
        "message": "Maximum border radius (pill/circle) used everywhere",
        "fix": "Reserve pill border-radius for badges and tags. Buttons and cards look more intentional with moderate radius (6-12px). Excessive rounding = AI slop aesthetic.",
    },
    {
        "priority": "medium",
        "category": "layout",
        "pattern": r'box-shadow\s*:\s*0\s+\d+px\s+\d+px\s+\d+px\s+rgba\(\s*0\s*,\s*0\s*,\s*0\s*,\s*0\.\d+\s*\)',
        "count_threshold": 5,
        "message": "Same shadow formula repeated many times",
        "fix": "Define shadow tokens in CSS variables (--shadow-sm, --shadow-md etc) and reference them. Read references/design-tokens.md for the shadow system.",
    },

    # ── UX Anti-patterns (High) ──
    {
        "priority": "high",
        "category": "ux",
        "pattern": r'<input[^>]+type=["\'](?:text|email|search|password)["\'][^>]*>(?!\s*<!--)',
        "condition": lambda m, content: '<label' not in content[max(0, m.start()-500):m.start()],
        "message": "Input without nearby label element",
        "fix": "Every input must have an associated <label>. Use placeholder only as supplemental hint, never as the label.",
    },
    {
        "priority": "high",
        "category": "ux",
        "pattern": r'<select[^>]*>',
        "condition": lambda m, content: 'searchable' not in content[m.start():m.start()+500].lower() and len(re.findall(r'<option', content[m.start():m.start()+1000])) > 8,
        "message": "Long select dropdown (8+ options) without search",
        "fix": "Selects with >8 options should be replaced with a searchable combobox/autocomplete. Long dropdowns are frustrating to scroll through.",
    },
    {
        "priority": "medium",
        "category": "ux",
        "pattern": r'(?:disabled|aria-disabled=["\']true["\'])[^>]*>',
        "condition": lambda m, content: 'title=' not in content[m.start():m.start()+200] and 'aria-describedby' not in content[m.start():m.start()+200],
        "message": "Disabled element may lack explanation",
        "fix": "Disabled buttons/inputs should have a tooltip or text explaining why and how to enable. Silent disabled states confuse users.",
    },
    {
        "priority": "medium",
        "category": "ux",
        "pattern": r'onmouseover|:hover[^{]*{[^}]*(?:dropdown|menu|submenu)',
        "message": "Hover-triggered dropdown/menu detected",
        "fix": "Hover menus break on keyboard navigation and touch devices. Use click-triggered popovers/menus instead.",
    },

    # ── Motion (Low-Medium) ──
    {
        "priority": "medium",
        "category": "motion",
        "pattern": r'animation[^;]+(?:bounce|shake|wobble|rubber|elastic)',
        "message": "Playful/bouncy animation in potential production UI",
        "fix": "Use spring animations (cubic-bezier(0.34, 1.56, 0.64, 1)) for subtle overshoot rather than cartoon-style bounce. Reserve for delight moments, not routine interactions.",
    },
    {
        "priority": "low",
        "category": "motion",
        "pattern": r'transition\s*:\s*all\b',
        "message": "'transition: all' is a performance antipattern",
        "fix": "Only transition specific properties: 'transition: background-color 150ms ease, box-shadow 150ms ease'. Animating 'all' triggers layout recalculation.",
    },
    {
        "priority": "medium",
        "category": "motion",
        "pattern": r'@keyframes|animation\s*:',
        "condition": lambda m, content: 'prefers-reduced-motion' not in content,
        "message": "Animations exist but no prefers-reduced-motion media query found",
        "fix": "Add @media (prefers-reduced-motion: reduce) to disable animations for users with motion sensitivity. Read references/design-tokens.md for the motion token approach.",
    },

    # ── Missing states (Medium) ──
    {
        "priority": "medium",
        "category": "ux",
        "pattern": r'<(form|button)[^>]*>',
        "condition": lambda m, content: ':loading' not in content and 'data-loading' not in content and 'isLoading' not in content and 'aria-busy' not in content,
        "message": "Form/button may be missing loading state",
        "fix": "Interactive buttons and forms must show a loading state when processing. Use aria-busy='true' + spinner inside the button.",
    },
]


# ─────────────────────────────────────────
# Audit engine
# ─────────────────────────────────────────

def audit_file(filepath: Path) -> AuditResult:
    result = AuditResult(filepath=str(filepath))

    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        result.issues.append(Issue(
            priority="critical",
            category="system",
            message=f"Could not read file: {e}",
            fix="Ensure the file is readable and UTF-8 encoded."
        ))
        return result

    lines = content.split('\n')

    for rule in RULES:
        pattern = rule["pattern"]
        try:
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
        except re.error:
            continue

        # Apply optional condition filter
        condition = rule.get("condition")
        if condition:
            matches = [m for m in matches if condition(m, content)]

        # Apply count threshold (only flag if pattern appears N+ times)
        threshold = rule.get("count_threshold", 1)
        if len(matches) < threshold:
            continue

        for match in matches[:3]:  # Cap at 3 instances per rule per file
            line_num = content[:match.start()].count('\n') + 1
            evidence = lines[line_num - 1].strip() if line_num <= len(lines) else None

            result.issues.append(Issue(
                priority=rule["priority"],
                category=rule["category"],
                message=rule["message"],
                fix=rule["fix"],
                line=line_num,
                evidence=evidence[:120] if evidence else None,
            ))
            break  # Only report first instance per rule per file (reduce noise)

    return result


def audit_path(path: Path) -> List[AuditResult]:
    EXTENSIONS = {'.html', '.css', '.jsx', '.tsx', '.ts', '.js', '.svelte', '.vue'}
    SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', '.next', '__pycache__', 'vendor'}

    results = []
    if path.is_file():
        if path.suffix in EXTENSIONS:
            results.append(audit_file(path))
    elif path.is_dir():
        for f in sorted(path.rglob('*')):
            if any(skip in f.parts for skip in SKIP_DIRS):
                continue
            if f.is_file() and f.suffix in EXTENSIONS:
                results.append(audit_file(f))
    return results


# ─────────────────────────────────────────
# Reporting
# ─────────────────────────────────────────

PRIORITY_COLORS = {
    "critical": "\033[91m",  # red
    "high":     "\033[93m",  # yellow
    "medium":   "\033[94m",  # blue
    "low":      "\033[90m",  # gray
}
RESET = "\033[0m"
BOLD = "\033[1m"


def print_report(results: List[AuditResult], strict: bool = False):
    total_issues = sum(len(r.issues) for r in results)
    total_critical = sum(len(r.critical) for r in results)
    total_high = sum(len(r.high) for r in results)

    print(f"\n{BOLD}{'━' * 60}{RESET}")
    print(f"{BOLD}  SaaS UI/UX Design Audit Report{RESET}")
    print(f"{'━' * 60}\n")

    for result in results:
        if not result.issues:
            print(f"  ✅ {result.filepath} — No issues found")
            continue

        print(f"\n{BOLD}📄 {result.filepath}{RESET} (score: {result.score}/100)")
        print(f"   {'─' * 50}")

        # Group by priority
        for priority in ["critical", "high", "medium", "low"]:
            issues = [i for i in result.issues if i.priority == priority]
            if not issues:
                continue
            color = PRIORITY_COLORS[priority]
            label = priority.upper().ljust(8)
            for issue in issues:
                print(f"\n   {color}{BOLD}[{label}]{RESET} {issue.category.upper()}")
                print(f"   {BOLD}Problem{RESET}: {issue.message}")
                if issue.line:
                    print(f"   {BOLD}Line{RESET}:    {issue.line}")
                if issue.evidence:
                    print(f"   {BOLD}Found{RESET}:   {issue.evidence}")
                print(f"   {BOLD}Fix{RESET}:     {issue.fix}")

    # Summary
    print(f"\n{'━' * 60}")
    print(f"{BOLD}  Summary{RESET}")
    print(f"{'━' * 60}")
    print(f"  Files audited: {len(results)}")
    print(f"  Total issues:  {total_issues}")
    print(f"  {PRIORITY_COLORS['critical']}Critical: {total_critical}{RESET}  "
          f"{PRIORITY_COLORS['high']}High: {total_high}{RESET}  "
          f"{PRIORITY_COLORS['medium']}Medium: {sum(len(r.medium) for r in results)}{RESET}  "
          f"{PRIORITY_COLORS['low']}Low: {sum(len(r.low) for r in results)}{RESET}")

    avg_score = sum(r.score for r in results) / len(results) if results else 100
    grade = "A" if avg_score >= 90 else "B" if avg_score >= 75 else "C" if avg_score >= 60 else "D"
    print(f"\n  {BOLD}Average Score: {avg_score:.0f}/100 ({grade}){RESET}")

    if total_critical > 0:
        print(f"\n  {PRIORITY_COLORS['critical']}{BOLD}⚠ {total_critical} CRITICAL issues must be fixed immediately{RESET}")

    print(f"{'━' * 60}\n")

    if strict and (total_critical > 0 or total_high > 0):
        sys.exit(1)


def json_report(results: List[AuditResult]) -> dict:
    return {
        "summary": {
            "files_audited": len(results),
            "total_issues": sum(len(r.issues) for r in results),
            "critical": sum(len(r.critical) for r in results),
            "high": sum(len(r.high) for r in results),
            "medium": sum(len(r.medium) for r in results),
            "low": sum(len(r.low) for r in results),
            "average_score": round(sum(r.score for r in results) / len(results), 1) if results else 100,
        },
        "files": [
            {
                "path": r.filepath,
                "score": r.score,
                "issues": [
                    {
                        "priority": i.priority,
                        "category": i.category,
                        "message": i.message,
                        "fix": i.fix,
                        "line": i.line,
                        "evidence": i.evidence,
                    }
                    for i in r.issues
                ]
            }
            for r in results
        ]
    }


# ─────────────────────────────────────────
# CLI Entry point
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Audit SaaS UI files for AI slop patterns and UX anti-patterns"
    )
    parser.add_argument("path", help="File or directory to audit")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--strict", action="store_true", help="Exit with code 1 if critical/high issues found")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(f"Error: Path '{path}' does not exist.")
        sys.exit(1)

    results = audit_path(path)
    if not results:
        print("No auditable files found (looking for .html, .css, .jsx, .tsx, .js, .svelte, .vue)")
        sys.exit(0)

    if args.json:
        print(json.dumps(json_report(results), indent=2))
    else:
        print_report(results, strict=args.strict)


if __name__ == "__main__":
    main()
