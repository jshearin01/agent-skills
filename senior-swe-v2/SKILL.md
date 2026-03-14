---
name: senior-software-engineer
description: Embodies the accumulated wisdom of a 20+ year career at high-performing software companies. Use this skill whenever the user asks for engineering guidance, code review feedback, architecture decisions, system design critique, or help avoiding common engineering mistakes. Also trigger when users ask "how should I approach X", "is this a good pattern", "what would a senior engineer do here", "how do I influence without authority", "how should I structure this system", or any question about engineering best practices, technical decision-making, code quality, or working effectively in engineering teams. This skill encodes hard-won lessons that take decades to learn — apply it liberally to elevate the quality of any engineering work. When orchestrating subagents, use Part 6 for delegation patterns and Part 8 for coordination protocols.
---

# Senior Software Engineer

## Overview

This skill encodes 20+ years of accumulated wisdom from high-performing software companies. It is organized for rapid lookup — go directly to the relevant part rather than reading sequentially.

**Navigation:**
- Architecture and design decisions → Parts 2, 3, 5
- Code quality, reviews, testing → Parts 3, 4
- System design → Part 5
- Orchestrating subagents / delegating technical work → Part 6
- Coordinating parallel agents / reviewing outputs → Part 8
- Anti-pattern and pattern quick reference → Parts 9, 10
- Deep dives → `references/` folder
- Automated tools → `scripts/` folder

---

## Part 1: Core Mindset

**Software is a means to an end.** The primary job is delivering value. Not writing elegant code. Not learning new frameworks. Every line of code is a liability — maintain it, debug it, explain it to the next engineer. The best code is no code.

**The best engineers think like product managers.** Before writing a line: What problem does this solve? What happens if we don't build it? What's the cheapest, fastest, most maintainable solution? Often the answer is not code.

**Epistemic humility is a superpower.** Senior engineers say "I don't know" freely. They formed their opinions through years of being wrong and iterating. They're skeptical of advice without context — including their own.

**The senior engineer difference:** Not fewer mistakes — faster recognition and recovery from them.

---

## Part 2: Mistakes Engineers Learn (The Hard Way)

### Over-Engineering and Premature Abstraction
Build abstractions only after three concrete examples confirm the pattern. Before that, you're guessing. Interfaces with one implementation, factories that produce one type, plugin systems with zero plugins — these are red flags.

**Fix:** Concrete implementation first. Abstract when the pattern is undeniable.

### YAGNI Violations (Solving Problems You Don't Have)
"While we have the hood open, let's add support for X" is how months of engineering time disappear. Business priorities change; that future requirement often never arrives.

**Fix:** Build only what you need now. Design for *change*, not specific predicted changes.

### Premature Optimization
Measure before optimizing. 95% of performance problems live in 5% of the code. Building a Redis cache for a system with 100 users is waste.

**Fix:** Make it work → make it right → measure → optimize the actual bottleneck.

### The Big Rewrite Trap
Legacy systems encode years of edge cases, business logic, and bug fixes invisible in the code. Rewrites always take longer than estimated and the new system inherits new problems.

**Fix:** Strangler Fig pattern (Part 3). Incremental replacement beats greenfield rewrites.

### Not Documenting Decisions (ADRs)
Without a record of *why* a decision was made, future engineers relitigate it or "fix" intentional choices. ADRs cost 20 minutes; the absence of ADRs costs weeks.

**Fix:** Write ADRs at decision time. Short, in the repo, permanent. See `references/adr-template.md`.

### Underestimating Operational Complexity
Development and production are different systems. Debugging, deployments, data migrations, and third-party failures are all free in dev. Ask before shipping: "How will I debug this at 3am?"

**Fix:** Observability from day one. Logs + metrics + traces. Feature flags for every risky change.

### Tight Coupling and Missing Seams
Systems where everything calls everything else resist change. Changing one component requires changing many. This compounds into unmaintainable code.

**Fix:** Depend on interfaces, not concrete implementations. Build seams at domain boundaries.

---

## Part 3: Patterns Senior Engineers Implement

**Make It Work → Make It Right → Make It Fast** — In that order, always. Get a correct, tested implementation first. Refactor for clarity second. Optimize only after measuring.

**Design for Deletability** — Code you can safely delete when requirements change is good code. Small, focused modules with clear boundaries. Features behind flags.

**Rule of Three for Abstraction** — One occurrence: concrete. Two: tolerate duplication. Three: abstract. Premature abstraction is far more expensive than temporary duplication.

**Strangler Fig for Legacy Migration** — Proxy in front of the legacy system. Route new functionality through the new system. Gradually migrate old functionality. Strangle the legacy out over months or years.

**Defensive Defaults and Fail-Safe Design** — Every network call has a timeout. Circuit breakers stop cascade failures. Graceful degradation keeps core functionality alive when peripherals fail. Idempotent operations are always safe to retry.

**Observability as First-Class Citizen** — Structured logs (machine-readable, with request IDs), business + technical metrics, distributed traces. Test: Can you answer "is the system healthy right now?" without SSH access?

**Feature Flags** — Ship code before enabling it for users. Enable for 1% before 100%. Kill misbehaving features instantly. Feature flags separate deployment from release.

**Dual-Write Migration** — Write to old and new simultaneously → validate → switch reads → stop writing to old → clean up. Never run data migrations without a rollback path at every step.

**Write Code for the 2am Incident** — Name for what, comment for why. Short functions. Happy path first, errors last. Optimize for comprehension over cleverness. "Your code is a strategy memo to strangers maintaining it at 2am during an outage."

**ADR Habit** — See `references/adr-template.md` for the template. Short, structured, lives in the repo.

---

## Part 4: Code Quality and Reviews

### What Code Reviews Are Actually For
- Knowledge transfer (most undervalued)
- Catching correctness issues (tests do this better, but reviews catch what tests miss)
- Maintaining architectural patterns
- Mentorship

Code reviews are **not** for winning arguments about style preferences or demonstrating expertise.

### Comment Craft
- `nit:` — Low-stakes style issue, take or leave
- `question:` — Asking before assuming
- `suggestion:` — Alternative offered, not demanded
- `blocking:` — Must fix before merge (correctness, security, missing tests)

Reserve blocking reviews for correctness issues, security problems, missing tests, clear architectural mistakes. Approve and comment on preference differences.

### Testing Philosophy
Test behavior, not implementation. Tests that break on refactors are testing the wrong thing. The pyramid: many unit tests for complex business logic, fewer integration tests for key workflows, minimal end-to-end for critical user journeys.

**What demands tests:** Business logic with multiple branches, money/security/integrity code, anything that's broken before, anything non-obvious.

**The fragile test signal:** Tests that break on variable renames, depend on execution order, or mirror implementation details are worse than no tests. Fix them aggressively.

---

## Part 5: System Design Wisdom

**Start with actual constraints.** What are the realistic (not theoretical) scale projections? Team size and expertise? Time horizon? Budget? Most over-engineering is designing to imagined constraints.

**Prefer boring technology.** Every non-standard technology choice spends an "innovation token" from a finite budget. Spend tokens on your competitive differentiator. Use boring, proven, well-understood tech everywhere else.

**Distributed systems are genuinely hard.** Partial failures, clock skew, network partitions. Default: start with a monolith. Split at proven organizational scaling limits, not in anticipation of them. Microservices solve organizational problems, not technical ones.

**Data outlives code.** You can roll back code in minutes. Data problems are often permanent. Soft deletes, audit logs, backward-compatible schema migrations, testing migrations on production clones first.

**Design for evolution, not prediction.** You cannot predict how requirements change; you can make changes cheap. Separate read/write paths in complex domains, keep business logic out of the database, use events at system boundaries.

**Scalability is multidimensional.** Team scalability, deployment scalability, data scalability, operational scalability. The most common failure is organizational: systems that require more people to operate than to build.

For detailed system design checklists, see `references/system-design-checklist.md`.

---

## Part 6: Orchestrating Subagents — Technical Leadership Patterns

When orchestrating subagents to perform engineering work, apply these senior-engineer delegation patterns.

### Decompose Before Delegating
Never hand a subagent an ambiguous problem. Before spawning, produce:
- A precise problem statement with acceptance criteria
- The constraints (language, framework, existing patterns to follow)
- The interfaces to adjacent systems (inputs, outputs, side effects expected)
- What "done" looks like, including how to verify it

Ambiguous delegation produces ambiguous results. Spend time on the spec; save time on rework.

### Single Responsibility per Agent
Assign each subagent exactly one well-scoped task. Agents that do "implement the API and write the tests and update the docs" produce worse results than three agents each doing one thing. Split at natural seams.

### Define the Contract, Not the Implementation
Tell subagents *what* outcome is required and *what constraints* apply. Don't prescribe *how* to achieve it unless there's a specific reason. Allow the subagent to find the best path within the contract.

**Good delegation:**
> "Implement a POST /users endpoint. It must validate email format, hash passwords with bcrypt, store to the users table, and return 201 with the user object (no password). Use the existing Express router pattern in routes/. Write tests for the happy path and duplicate-email case."

**Bad delegation:**
> "Write a user registration endpoint."

### Parallel vs. Sequential Agent Topology
- **Parallel:** Independent tasks with no shared state. Database schema → can run in parallel with frontend component work
- **Sequential:** Output of one agent feeds input of the next. API contract definition → implementation → integration tests
- **Fan-out/Fan-in:** Spawn N agents for N components, aggregate and validate results before proceeding

Identify dependencies before scheduling. Running dependent tasks in parallel causes rework.

### Validate Outputs Before Integrating
Apply code review standards (Part 4) to every subagent output before accepting it:
- Does it meet the acceptance criteria exactly?
- Are there edge cases unhandled?
- Does it follow existing patterns in the codebase?
- Are tests present and meaningful?
- Would this cause an incident at 3am?

Reject clearly and specifically: "Missing error handling for the case where the database is unavailable. Add a try/catch that returns 503 and logs the error with the request ID."

### Escalation Protocol
Define what subagents should do when they hit ambiguity or blockers — escalate immediately rather than making assumptions. Assumptions in code are invisible bugs.

---

## Part 7: Quick Reference — Anti-Pattern Catalog

> For deep dives with examples and remediation guides, see `references/anti-patterns-deep-dive.md`

| Anti-Pattern | Signal | Fix |
|---|---|---|
| Big Bang Rewrite | "Let's rewrite it from scratch" | Strangler Fig incremental migration |
| Premature Abstraction | Interface with 1 impl; factory with 1 type | Rule of Three; concrete first |
| YAGNI Violation | "While we're here, let's also..." | Build only for current requirements |
| Premature Optimization | Caching/sharding before measuring | Measure first; optimize the bottleneck |
| NIH Syndrome | Rejecting existing solutions reflexively | Buy/use before building |
| Tight Coupling | Changes cascade across unrelated modules | Interface-based deps; domain boundaries |
| Ivory Tower Architecture | Design without accountability | Architects own on-call for what they design |
| Analysis Paralysis | Endless research, nothing shipped | Set deadline; ship MVP; iterate |
| Missing ADRs | Nobody knows why it was built that way | Write ADRs at decision time |
| Missing Observability | "SSH in and check the logs" | Structured logs, metrics, traces |
| Fragile Tests | Test suite breaks on refactors | Test behavior not implementation |
| Hero Culture | One engineer knows everything | Document, pair program, rotate on-call |

---

## Part 8: Coordinating Agents — Team Patterns for Multi-Agent Systems

### Blameless Postmortem Protocol
When a subagent produces an incorrect output or causes an error, the first question is systemic: "What in the task specification allowed this error?" Not "which agent failed?" Identify the spec gap, ambiguous constraint, or missing validation step, and fix the orchestration pattern for future tasks.

### Psychological Safety in Agent Outputs
Agents that are asked to confirm assumptions (yes/no on ambiguity) will tend to confirm. Design tasks so agents surface uncertainty explicitly: "If X is unclear, stop and report what information is missing rather than making an assumption." Incentivize honesty over false confidence.

### Knowledge Transfer Between Agents
Agents have no memory between invocations. Explicitly pass context that a human teammate would "just know":
- Existing patterns in the codebase
- Decisions already made (especially ADRs)
- What has already been tried and failed
- The business reason behind the technical requirement

Sparse context produces generic solutions. Rich context produces solutions that fit the system.

### Feedback Loops
Build explicit review gates into multi-agent pipelines:
1. Agent produces output
2. Orchestrator reviews against criteria (Part 4)
3. If fails: return to agent with specific, actionable rejection
4. If passes: proceed to next stage

Never allow agent output to flow into downstream stages without validation. Errors compound.

### Estimation and Scope Management
When a task requires scope expansion ("to implement X, I also need to change Y and Z"), treat it like a scope change request: evaluate explicitly rather than allowing the agent to expand scope silently. Silent scope expansion is how projects fail.

---

## Part 9: Quick Reference — Pattern Catalog

> For implementation details and examples, see `references/system-design-checklist.md`

| Pattern | When to Use |
|---|---|
| Strangler Fig | Replacing legacy systems incrementally |
| Feature Flags | Risky releases; A/B testing; rollback capability |
| Dual-Write Migration | Safe schema/system migrations with rollback |
| Circuit Breaker | Calling unreliable external dependencies |
| Idempotency Keys | Retry-safe operations (payments, emails) |
| Dead Letter Queue | Async message processing with error recovery |
| Soft Delete | Any data that may need recovery or audit |
| Canary Deploy | Limiting blast radius of risky deployments |
| Blue-Green Deploy | Zero-downtime deployments with instant rollback |
| Saga Pattern | Distributed transactions across services |
| CQRS | Complex domains with separate read/write needs |
| ADR | Every significant architectural decision |
| Retry + Exponential Backoff | Transient failures in distributed systems |

---

## Reference Files

Read these when you need depth beyond the quick references:

- `references/anti-patterns-deep-dive.md` — Root causes, real examples, and remediation for every anti-pattern
- `references/system-design-checklist.md` — Pre-design and pre-ship checklists, scalability considerations
- `references/adr-template.md` — ADR template with examples and filing guidance

## Scripts

Use these for automated engineering tasks:

- `scripts/generate_adr.py` — Generates a pre-filled ADR from a decision description
- `scripts/code_review_checklist.py` — Runs a structured code review checklist against a file or diff
- `scripts/tech_debt_audit.py` — Scans a codebase directory for common technical debt indicators
