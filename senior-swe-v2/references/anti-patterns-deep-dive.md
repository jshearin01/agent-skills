# Anti-Patterns Deep Dive

> Read this file when you need root causes, war stories, and detailed remediation guidance beyond the quick-reference table in SKILL.md Part 7.

## Table of Contents

1. [The Big Bang Rewrite](#1-the-big-bang-rewrite)
2. [Premature Abstraction](#2-premature-abstraction)
3. [YAGNI Violations](#3-yagni-violations)
4. [Premature Optimization](#4-premature-optimization)
5. [Not-Invented-Here (NIH) Syndrome](#5-not-invented-here-nih-syndrome)
6. [Tight Coupling](#6-tight-coupling)
7. [Ivory Tower Architecture](#7-ivory-tower-architecture)
8. [Analysis Paralysis](#8-analysis-paralysis)
9. [Missing ADRs](#9-missing-adrs)
10. [Missing Observability](#10-missing-observability)
11. [Fragile Tests](#11-fragile-tests)
12. [Hero Culture](#12-hero-culture)

---

## 1. The Big Bang Rewrite

**Root cause:** Accumulated frustration with a codebase leads to the conclusion that the only path forward is to throw it away and start over. Engineers underestimate how much implicit knowledge lives in the existing system.

**Why it almost always fails:**
- The existing system encodes years of edge case handling, regulatory requirements, and compensating behaviors for broken upstream APIs — none of which appear in any requirements document
- The business doesn't pause during the rewrite; new requirements accumulate
- "This time we'll do it right" reasoning ignores that the team will make new, different mistakes
- The two systems must eventually be reconciled — that cutover is often as complex as the rewrite itself
- Engineer motivation collapses when a rewrite runs 2x-4x over estimate (it always does)

**Famous failures:**
- Netscape's Mozilla rewrite gave IE 3 years of uncontested market dominance
- HealthCare.gov's initial failure stemmed partly from over-engineered greenfield architecture rather than incremental improvement

**Remediation:**
1. **Identify the actual pain.** Is it performance? Maintainability? Deployment speed? Solve the specific problem.
2. **Strangler Fig pattern.** Put a routing layer in front. Route new features to new code. Migrate old features one at a time. The old system is never "replaced" all at once — it's gradually strangled.
3. **Modular decomposition.** Extract the most painful module first, get it right in isolation, replace the old version. Repeat.
4. **Measure before proposing a rewrite.** "The codebase is a mess" is not a metric. "Median time to implement a feature is 6 weeks and regression rate is 40%" is.

---

## 2. Premature Abstraction

**Root cause:** Abstractions that were created before the actual shape of the problem was understood. Often driven by "I might need this later" thinking or a desire to demonstrate design sophistication.

**How to identify it:**
- Interfaces with exactly one implementation
- Abstract base classes with one concrete child
- "Strategy" patterns where the strategy never changes at runtime
- Plugin systems with zero plugins
- Elaborate factory hierarchies for objects that come in one flavor
- Understanding the system requires knowing multiple design patterns simultaneously
- New developers can't figure out where the actual logic is

**The cost:**
- Every layer of unnecessary abstraction is cognitive load on every future engineer
- "Flexible" architectures become rigid when changes must accommodate every theoretical use case
- Wrong abstractions are harder to remove than duplicated concrete code

**The Rule of Three:**
1. First occurrence: Concrete implementation. Don't abstract.
2. Second occurrence: Tolerate the duplication. Resist.
3. Third occurrence: You now understand the pattern. Abstract correctly.

**Remediation:**
- Don't refactor to abstract; refactor to understand, then abstract
- If an abstraction has been in place for months with one implementation, delete the abstraction
- Work from concrete → abstract, never the reverse

---

## 3. YAGNI Violations

**Root cause:** Engineers are optimizers by nature. They see a future requirement and want to prepare for it. This feels responsible; it is usually waste.

**Classic manifestations:**
- `"While we have the hood open, let's add that field we'll need later"` — the requirement changes, the work is done twice
- Multi-database abstraction layers for systems with one database
- Elaborate plugin architectures for applications with no extension use case
- Scalability infrastructure designed for 1,000x current load, at 1/100th current scale
- Generic "framework" code for a problem that has one specific instance

**The math:**
- The future requirement arrives 30% of the time
- When it does arrive, it's different from what you anticipated 70% of the time
- You pay the maintenance and complexity cost of the speculative code 100% of the time
- Expected value of YAGNI violations is almost always negative

**The legitimate exception:**
Design for *change* without pre-building *specific* changes. "Make the database layer replaceable" is different from "build support for MySQL, Postgres, and MongoDB right now." Good architecture makes future changes cheap; YAGNI violations pre-build them.

**Remediation:**
- When someone says "we might need...", ask: "Is this in any current requirement?"
- When someone says "while we're here...", stop and evaluate the scope change explicitly
- Defer implementation until the requirement is real and understood

---

## 4. Premature Optimization

**Root cause:** Engineers optimize code because it's interesting and satisfying, not because there's a demonstrated problem.

**What premature optimization produces:**
- Complex code that's harder to understand and maintain
- Optimizations in the wrong place (the actual bottleneck is elsewhere)
- Architectural decisions locked in before load characteristics are understood
- Weeks spent achieving millisecond improvements in code paths called 10 times per day

**The correct sequence:**
1. Make it work (with tests proving correctness)
2. Make it right (clean, clear, maintainable)
3. Measure in production-like conditions
4. Optimize the **specific measured bottleneck**
5. Measure again to confirm improvement

**Profiling beats intuition every time.** Engineers consistently identify the wrong bottleneck without profiling data. The 5% of code that actually matters is almost never the obvious candidate.

**Legitimate early optimization:**
Some architectural decisions have high switching costs (database choice, API shape, message queue topology). Think carefully about these. But low-level implementation optimization — caching, algorithmic complexity, connection pooling — should wait for measured need.

---

## 5. Not-Invented-Here (NIH) Syndrome

**Root cause:** Engineers want control, familiarity, and the satisfaction of building. Using external solutions feels like admitting defeat or introducing risk. Sometimes justified; often not.

**Signs of NIH syndrome:**
- "We can build a better X than what's available" without evidence
- Rejecting a library because "we don't know what's in it"
- Building custom auth, custom queues, custom ORMs when battle-tested alternatives exist
- Preference for homegrown solutions that have the same bugs as existing solutions, just newer

**The true cost of building what already exists:**
- Implementation time (months)
- Testing and hardening (months more)
- Ongoing maintenance and security patches (forever)
- New bugs in the places the existing solution already fixed
- Opportunity cost of the problems you didn't solve instead

**When to build instead of buy:**
- The capability is genuinely core to your competitive differentiation
- No existing solution fits your requirements and customization would cost more than building
- You need full control (security, compliance, specific performance characteristics)
- Long-term maintenance cost of buying genuinely exceeds building (rare)

**The test:** Would a competitor having this capability be a meaningful advantage? If not, it's not a differentiator — use what exists.

---

## 6. Tight Coupling

**Root cause:** Organic growth without explicit attention to seams. Direct calls between components feel natural and fast; the cost accumulates invisibly.

**Tight coupling manifests as:**
- Direct instantiation (`new ConcreteService()`) instead of injection
- Shared mutable state between components
- Business logic that depends on specific database schemas
- Service A knowing the internal structure of Service B's data
- Changes in one module requiring changes in 5 unrelated modules
- "God objects" that know too much about too much

**The cascading change smell:** If adding a field to a database table requires changes in 8 files across 4 modules, you have a coupling problem.

**How to create seams deliberately:**
- Depend on interfaces/protocols, not concrete implementations
- Pass dependencies in; don't reach for them
- Define explicit module contracts (published interfaces, event schemas)
- Keep I/O at the edges; keep business logic in the middle
- Treat your own internal APIs as if they were external — design them with the same care

**The seam test:** If you wanted to replace this component with a different implementation, how many places in the code would you need to change? Ideally: one.

---

## 7. Ivory Tower Architecture

**Root cause:** Architects or senior engineers who define architecture without operational accountability. Design disconnected from implementation reality.

**How it develops:**
- Engineers promoted to "architect" role and removed from day-to-day implementation
- Technical decisions made without input from engineers who will implement them
- No mechanism for architects to receive feedback from production operations
- "Design docs" that exist but are never reconciled with what was actually built

**The accountability test:**
The person who designed a system should be on the on-call rotation for it. This alone eliminates most ivory tower architecture. Architects who carry a pager design very differently than those who don't.

**Remediation:**
- Require architects to own at least one implementation milestone per quarter
- Route incident retrospectives to the people who made the design decisions
- Design docs should have a named owner who receives feedback when the system fails
- "You designed it, you operate it" culture

---

## 8. Analysis Paralysis

**Root cause:** The desire to find the optimal solution before committing. Reasonable up to a point; pathological when it prevents shipping.

**Signs:**
- Research phase running longer than the estimated implementation
- "We need to evaluate one more option before deciding"
- Design documents that grow but never reach conclusion
- Team alignment cited as the blocker (when in fact no decision has been proposed)

**The research vs. commit failure mode:**
Research informs decisions; it doesn't make them. At some point, someone has to say "based on what we know, we're choosing X." That requires accepting some irreducible uncertainty.

**The reversal test:** For most technical decisions, ask "is this reversible?" If yes, make the call quickly. Save deliberation for genuinely irreversible architectural decisions (database choice, API contracts, data models that will be hard to migrate).

**The time-box technique:**
Set an explicit deadline for the decision phase. "We will decide by Thursday, based on whatever we've learned by then." Ship a decision. Measure. Revise if needed.

---

## 9. Missing ADRs

**Root cause:** Decisions feel obvious in the moment; the context is only missing later. "Everyone knows why we did this" is true until the people who knew leave.

**The compounding problem:**
- Engineers "fix" things that were intentionally built that way for important reasons
- Teams relitigate decisions made years ago, redoing the same analysis and reaching the same conclusion
- Onboarding takes months longer because context is oral, not written
- Post-mortems can't identify whether a failure was caused by a deviation from intended architecture or by the intended architecture itself

**What an ADR must contain:**
1. **Context** — What problem were we solving? What constraints existed?
2. **Decision** — What did we choose?
3. **Alternatives considered** — What did we reject, and why?
4. **Consequences** — What are the trade-offs? What becomes harder?
5. **Status** — Accepted / Superseded by ADR-XXX / Deprecated
6. **Date and decision-makers**

**What an ADR must not contain:**
- Extensive implementation detail (that belongs in code comments and docs)
- Revisable opinions (the decision, once made, is recorded as made; update with a new ADR if superseded)

**Filing pattern:** `docs/adr/ADR-001-postgres-as-primary-datastore.md`. Numbered, slug-named, in the repo.

See `references/adr-template.md` for a ready-to-use template.

---

## 10. Missing Observability

**Root cause:** Observability is treated as infrastructure, not as a feature. "We'll add monitoring later" — but later never comes until there's a production incident.

**The three pillars and why each matters:**
- **Logs:** What happened? Structured logs with consistent fields (request ID, user ID, timestamp, outcome, duration) are the foundation of incident debugging
- **Metrics:** Is the system healthy? Business metrics (orders/minute, email deliveries/hour) and technical metrics (error rate, latency P50/P99, queue depth)
- **Traces:** Why is this slow? Distributed tracing connects a single request across multiple services

**The operational test:** Without SSHing into any machine, can you answer:
- Is the system healthy right now?
- What was the error rate 6 hours ago?
- Which requests are slowest?
- What happened to request ID abc-123?

If the answer to any of these is "no," observability is incomplete.

**The alerting trap:** Alert on symptoms (user-visible impact), not causes (infrastructure metrics). "Error rate > 1% for 5 minutes" is a good alert. "CPU > 80%" is usually noise.

---

## 11. Fragile Tests

**Root cause:** Tests that test implementation rather than behavior. They provide false security and create real drag.

**Signs of fragile tests:**
- A refactor that doesn't change behavior breaks 30 tests
- Tests import and call private methods
- Tests depend on execution order (state leaks between tests)
- Tests use fixed timestamps (`2024-01-01`) instead of relative time
- Mocks are so elaborate they mirror the implementation being tested
- Every test in a class breaks when you rename a private field

**The cost:**
- Developers learn to work around the test suite rather than with it
- PRs include "fix tests that broke for unrelated reasons" commits
- Coverage metrics are high; confidence is low

**What tests should do:**
- Verify the public contract of a component — inputs, outputs, side effects
- Survive internal refactors
- Run fast enough to run in a pre-commit hook

**Remediation:**
- Test public interfaces, not private implementations
- Use time injection (pass a clock object) rather than fixed dates
- Test state, not interactions (verify outcomes, not that mock.method was called N times)
- Delete tests that break on refactors and rewrite them to test behavior

---

## 12. Hero Culture

**Root cause:** Organizations reward individual heroics (staying up all night to fix a crisis) more than system improvements that prevent crises. Over time this selects for heroes and against sustainable systems.

**How it manifests:**
- One engineer who is the only one who understands system X
- On-call rotation that unofficially routes everything to the expert
- Knowledge concentrated in people, not documentation
- Incidents resolved by the hero, not by runbooks
- New hires dependent on the hero for months

**The single-point-of-failure risk:**
When the hero leaves (and they will), the knowledge leaves with them. This is a business risk, not just a team inconvenience.

**Systemic fixes:**
- Require runbooks for every on-call category — the answer must be in the runbook, not in the hero's head
- Pair programming and code review as knowledge transfer, not just quality gates
- Rotate on-call so everyone has exposure to production
- Document as you go; never let "ask Jane" be an acceptable answer to a process question
- Celebrate the engineer who made an incident not happen (through system improvement) as much as the one who fixed it after it did
