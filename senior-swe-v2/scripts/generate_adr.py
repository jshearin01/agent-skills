#!/usr/bin/env python3
"""
generate_adr.py — Generate a pre-filled Architecture Decision Record (ADR)

Usage:
    python3 generate_adr.py --title "Use PostgreSQL as primary database" \
                             --context "We need a relational database for user data" \
                             --decision "Use PostgreSQL 15 on AWS RDS" \
                             --output docs/adr/

    python3 generate_adr.py --interactive

The script:
  1. Determines the next ADR number by scanning the output directory
  2. Scaffolds a complete ADR template pre-filled with provided values
  3. Writes it to the correct filename in the ADR directory
  4. Updates (or creates) the ADR index README.md
"""

import argparse
import os
import re
import sys
from datetime import date


def find_next_adr_number(adr_dir: str) -> int:
    """Scan directory for existing ADRs and return the next available number."""
    if not os.path.exists(adr_dir):
        return 1
    
    max_num = 0
    pattern = re.compile(r'^ADR-(\d+)-', re.IGNORECASE)
    
    for filename in os.listdir(adr_dir):
        match = pattern.match(filename)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)
    
    return max_num + 1


def slugify(title: str) -> str:
    """Convert a title to a filename-safe slug."""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = re.sub(r'-+', '-', slug)
    return slug


def generate_adr_content(
    number: int,
    title: str,
    context: str = "",
    decision: str = "",
    decision_makers: str = "Engineering team",
) -> str:
    """Generate the full ADR markdown content."""
    today = date.today().strftime("%Y-%m-%d")
    padded_num = str(number).zfill(3)
    
    return f"""# ADR-{padded_num}: {title}

## Status

Proposed

## Date

{today}

## Decision Makers

{decision_makers}

## Context

{context if context else "[Describe the problem, constraints, and forces at play. What would happen if no decision were made? Write this so someone not in any meetings can understand why this decision was needed.]"}

## Decision

{decision if decision else "[State the decision clearly and directly. Not 'we considered several options' — state the actual choice.]"}

## Alternatives Considered

### Option A: [Name]
**Description:** [What is this option?]
**Pros:** [Why might someone choose this?]
**Cons:** [Why was it rejected?]

### Option B: [Name]
**Description:** [What is this option?]
**Pros:** [Why might someone choose this?]
**Cons:** [Why was it rejected?]

### Option C (Chosen): [Name]
**Description:** [What is this option?]
**Pros:** [Why was this chosen?]
**Cons:** [What are the known downsides?]

## Consequences

### Positive
- [What becomes better, easier, or possible because of this decision?]

### Negative
- [What becomes harder or more constrained because of this decision?]

### Risks
- [What could go wrong? What assumptions could be violated?]

## Related ADRs

- [Link to related ADRs, if any]
"""


def update_index(adr_dir: str, number: int, title: str, status: str, today: str):
    """Create or update the ADR index README."""
    index_path = os.path.join(adr_dir, "README.md")
    padded_num = str(number).zfill(3)
    slug = slugify(title)
    filename = f"ADR-{padded_num}-{slug}.md"
    new_row = f"| [ADR-{padded_num}]({filename}) | {title} | {status} | {today} |"
    
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            content = f.read()
        # Append new row before end of file
        content = content.rstrip() + "\n" + new_row + "\n"
    else:
        content = f"""# Architecture Decision Records

| # | Title | Status | Date |
|---|---|---|---|
{new_row}
"""
    
    with open(index_path, 'w') as f:
        f.write(content)
    
    print(f"  Updated index: {index_path}")


def interactive_mode() -> dict:
    """Collect ADR details interactively from the user."""
    print("\n=== ADR Generator — Interactive Mode ===\n")
    
    title = input("Decision title (e.g., 'Use PostgreSQL as primary database'): ").strip()
    if not title:
        print("Error: title is required.")
        sys.exit(1)
    
    print("\nContext (what problem are you solving? press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    context = "\n".join(lines).strip()
    
    print("\nDecision (what did you choose? press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    decision = "\n".join(lines).strip()
    
    decision_makers = input("\nDecision makers (default: 'Engineering team'): ").strip()
    if not decision_makers:
        decision_makers = "Engineering team"
    
    output = input("\nOutput directory (default: 'docs/adr'): ").strip()
    if not output:
        output = "docs/adr"
    
    return {
        "title": title,
        "context": context,
        "decision": decision,
        "decision_makers": decision_makers,
        "output": output,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate a pre-filled Architecture Decision Record (ADR)"
    )
    parser.add_argument("--title", help="Decision title")
    parser.add_argument("--context", default="", help="Problem context")
    parser.add_argument("--decision", default="", help="The decision made")
    parser.add_argument("--decision-makers", default="Engineering team")
    parser.add_argument("--output", default="docs/adr", help="Output directory")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive or not args.title:
        params = interactive_mode()
    else:
        params = {
            "title": args.title,
            "context": args.context,
            "decision": args.decision,
            "decision_makers": args.decision_makers,
            "output": args.output,
        }
    
    adr_dir = params["output"]
    os.makedirs(adr_dir, exist_ok=True)
    
    number = find_next_adr_number(adr_dir)
    padded_num = str(number).zfill(3)
    slug = slugify(params["title"])
    filename = f"ADR-{padded_num}-{slug}.md"
    filepath = os.path.join(adr_dir, filename)
    
    content = generate_adr_content(
        number=number,
        title=params["title"],
        context=params["context"],
        decision=params["decision"],
        decision_makers=params["decision_makers"],
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    today = date.today().strftime("%Y-%m-%d")
    update_index(adr_dir, number, params["title"], "Proposed", today)
    
    print(f"\n✓ Created ADR: {filepath}")
    print(f"  Next step: Fill in the Alternatives Considered and Consequences sections.")
    print(f"  When finalized, change Status from 'Proposed' to 'Accepted'.")


if __name__ == "__main__":
    main()
