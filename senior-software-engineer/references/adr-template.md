# Architecture Decision Record (ADR) Template and Guide

> Use this reference whenever you need to document an architectural decision. ADRs are permanent, short, and live in the codebase next to the code they describe.

## The Template

Copy this template into `docs/adr/ADR-NNN-short-description.md`:

```markdown
# ADR-NNN: [Short imperative title — what was decided]

## Status

[Accepted | Superseded by ADR-NNN | Deprecated | Proposed]

## Date

YYYY-MM-DD

## Decision Makers

[Names or teams who made this decision]

## Context

[1-3 paragraphs. What is the issue? What forces are at play? What constraints exist?
What would happen if no decision were made? Write this so that someone who was
not in any meetings can understand why this decision was needed.]

## Decision

[1-2 paragraphs. What was decided? State it clearly and directly.
Not "we considered several options" — state the actual choice.]

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
- [What becomes harder, more constrained, or impossible because of this decision?]

### Risks
- [What could go wrong? What assumptions could be violated?]

## Related ADRs

- ADR-NNN: [Title] — [How it relates]
```

---

## Worked Example: ADR-001

```markdown
# ADR-001: Use PostgreSQL as the Primary Relational Datastore

## Status

Accepted

## Date

2024-03-15

## Decision Makers

Engineering team (Alice, Bob, Carol), reviewed by CTO

## Context

We are building a new SaaS platform and need to choose a primary relational database.
The platform will handle user accounts, subscription billing, and user-generated content.
We need ACID transactions for billing operations, good JSON support for semi-structured
content metadata, and a hosting option compatible with our AWS infrastructure.

The team has 3 engineers with 5+ years of PostgreSQL experience and 1 with MySQL experience.
We are targeting launch in 4 months with a small team, so operational complexity is a key
constraint.

## Decision

We will use PostgreSQL 15 hosted on AWS RDS as the primary relational datastore for all
structured data. We will use the managed RDS service (not self-hosted) to minimize
operational burden.

## Alternatives Considered

### Option A: MySQL (AWS RDS)
**Description:** MySQL on managed RDS.
**Pros:** Widely supported, good managed options, team has some familiarity.
**Cons:** Inferior JSON support compared to PostgreSQL. JSON queries would require
application-level parsing. Less expressive query language for complex reports.

### Option B: Amazon Aurora PostgreSQL
**Description:** AWS's MySQL/PostgreSQL-compatible distributed database.
**Pros:** Better read scalability than RDS; automatic failover.
**Cons:** 3-5x cost of equivalent RDS instance. Our scale does not justify this cost.
Aurora migration is available as a future path when we need it.

### Option C (Chosen): PostgreSQL on AWS RDS
**Description:** Standard PostgreSQL 15 on managed AWS RDS.
**Pros:**
- Team expertise reduces ramp-up and incident risk
- JSONB support handles our semi-structured content needs without a separate store
- LISTEN/NOTIFY useful for real-time notification features
- Aurora migration path available when needed
- Lower cost than Aurora for our current scale
**Cons:**
- Limited to single-region writes (can use read replicas for reads)
- Scaling ceiling lower than Aurora (acceptable for current projections)

## Consequences

### Positive
- Fastest time to productive development given team expertise
- Reduces incident risk from team unfamiliarity
- JSONB support eliminates need for a separate document store for content metadata
- Managed RDS reduces operational overhead substantially

### Negative
- We are more constrained to AWS than with a database that has better multi-cloud support
- Not the best choice if we ever need multi-master writes across regions (unlikely in 2 years)

### Risks
- If growth significantly exceeds projections, we may need to migrate to Aurora sooner
  than planned. Mitigation: Aurora is a compatible upgrade path, not a rewrite.
- RDS pricing could increase. Mitigation: migration to Aurora or self-hosted is viable.

## Related ADRs

- ADR-004: Use Redis for Session Storage — offloads session data from PostgreSQL
- ADR-007: Event Sourcing for Billing Domain — uses PostgreSQL but with append-only pattern
```

---

## ADR Anti-Patterns to Avoid

### The Empty ADR
```markdown
# ADR-005: Use React

## Decision
We will use React for the frontend.
```
This records *what* but not *why*. Future engineers don't know if React was chosen because of team expertise, performance requirements, or an arbitrary coin flip. The *context* and *alternatives* are the valuable parts.

### The Revisable Opinion
An ADR is a permanent record of a decision made at a point in time. Don't go back and edit it when the decision turns out to be wrong. Instead, write a new ADR that supersedes the old one:

```markdown
## Status

Superseded by ADR-012 (switched to Vue due to team hiring constraints, 2025-01-20)
```

The old ADR remains. The history is preserved.

### The Implementation Manual
ADRs record decisions, not implementations. "Use PostgreSQL for the primary database" is an ADR. "How to set up a PostgreSQL connection pool in Python" is documentation.

### The Missing Negative Consequences
Every decision has tradeoffs. An ADR with only positive consequences in the "Consequences" section is not honest and is not useful. Future engineers need to know what you gave up to understand when the decision should be revisited.

---

## Filing and Organization

### Naming Convention
```
docs/adr/ADR-001-postgresql-primary-database.md
docs/adr/ADR-002-redis-session-storage.md
docs/adr/ADR-003-strangler-fig-for-legacy-api.md
```

- Prefix with `ADR-` and a zero-padded number
- Short, lowercase, hyphenated description of the decision
- Number sequentially; never reuse or reorder numbers

### Index File
Maintain `docs/adr/README.md` with a table of all ADRs:

```markdown
# Architecture Decision Records

| # | Title | Status | Date |
|---|---|---|---|
| [ADR-001](ADR-001-postgresql-primary-database.md) | PostgreSQL as Primary Database | Accepted | 2024-03-15 |
| [ADR-002](ADR-002-redis-session-storage.md) | Redis for Session Storage | Accepted | 2024-03-20 |
| [ADR-003](ADR-003-event-driven-notifications.md) | Event-Driven Notifications | Superseded by ADR-008 | 2024-04-01 |
```

### When to Write One
Write an ADR when:
- You're choosing between two or more meaningfully different technical approaches
- The decision will be hard to reverse later
- Future engineers are likely to question why it was done this way
- You're deviating from an established pattern or prior decision

Do **not** write an ADR for:
- Implementation details (variable naming, folder structure)
- Decisions that are trivially reversible
- Tactical choices within an already-decided architecture
