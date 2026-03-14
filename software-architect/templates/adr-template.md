# ADR Template

Use this template for every significant architecture decision. A significant decision is one that:
- Affects the structure or behavior of the system at a high level
- Is hard to reverse (Type 1 decision)
- Involves trade-offs that should be documented for future reference
- Will be questioned by future team members who weren't present for the discussion

## Template

```markdown
# ADR-[NUMBER]: [TITLE]

**Status**: [Proposed | Accepted | Deprecated | Superseded by ADR-XXX]
**Date**: [YYYY-MM-DD]
**Author**: [Name]
**Review Date**: [Date to revisit this decision, typically 3-6 months out]

## Context

What is the issue or situation that motivates this decision?
What are the constraints (technical, organizational, regulatory)?
What is the current state of the system relevant to this decision?

## Decision Drivers

- [Driver 1: e.g., "Need to handle 10x current write throughput within 6 months"]
- [Driver 2: e.g., "Team has deep PostgreSQL expertise but no MongoDB experience"]
- [Driver 3: e.g., "Must comply with GDPR data residency requirements"]

## Options Considered

### Option A: [Name]
Description of the option.

**Pros**:
- [Pro 1]
- [Pro 2]

**Cons**:
- [Con 1]
- [Con 2]

**Estimated effort**: [T-shirt size: S/M/L/XL]

### Option B: [Name]
Description of the option.

**Pros**:
- [Pro 1]
- [Pro 2]

**Cons**:
- [Con 1]
- [Con 2]

**Estimated effort**: [T-shirt size: S/M/L/XL]

### Option C: [Name]
(Include at least 2 options. 3 is ideal.)

## Decision

We chose **[Option X]** because [concise rationale linking back to decision drivers].

## Consequences

### Positive
- [What becomes easier or better]

### Negative
- [What becomes harder or worse — be honest]

### Risks
- [Risks we're accepting and how we'll mitigate them]

## Related Decisions
- [ADR-XXX: Related decision]
- [Link to relevant design doc]
```

## Example ADR

```markdown
# ADR-003: Use PostgreSQL as Primary Database

**Status**: Accepted
**Date**: 2025-01-15
**Author**: Architecture Team
**Review Date**: 2025-07-15

## Context

We are building a new SaaS platform for project management. The application has a
relational data model (users, projects, tasks, comments) with complex querying needs
(filtering, sorting, full-text search across tasks and comments). Expected scale is
10,000 users in year 1, with a target of 500,000 users by year 3.

## Decision Drivers

- Need ACID transactions for financial operations (subscriptions, billing)
- Complex querying across related entities (tasks ↔ projects ↔ users)
- Full-text search on task descriptions and comments
- Team has 3 engineers with strong PostgreSQL experience, 0 with MongoDB
- Budget constraints favor managed open-source over proprietary databases

## Options Considered

### Option A: PostgreSQL
Mature relational database with strong JSON support and full-text search.

**Pros**:
- ACID transactions, robust relational model
- Built-in full-text search (sufficient for our scale)
- JSONB for semi-structured data (flexibility where needed)
- Team expertise is strongest here
- Excellent managed options (RDS, Cloud SQL, Supabase)

**Cons**:
- Horizontal write scaling requires sharding (complex)
- Vertical scaling has limits (but sufficient for our 3-year target)

**Estimated effort**: S (team already knows it)

### Option B: MongoDB
Document database with flexible schema.

**Pros**:
- Flexible schema for evolving data model
- Built-in sharding for horizontal scaling
- Good for read-heavy workloads with denormalized data

**Cons**:
- No ACID transactions across collections (added in 4.0 but with caveats)
- Denormalization means data duplication and consistency challenges
- Zero team experience — learning curve would slow initial development
- Would need separate solution for full-text search at scale

**Estimated effort**: L (team learning curve)

### Option C: MySQL
Widely-used relational database.

**Pros**:
- Mature, well-understood
- Good managed options (RDS, PlanetScale)

**Cons**:
- Weaker JSON support than PostgreSQL
- No built-in full-text search as capable as PostgreSQL's
- Less team experience than PostgreSQL

**Estimated effort**: M

## Decision

We chose **PostgreSQL** because it aligns with our relational data model, provides
ACID transactions for billing operations, includes sufficient full-text search for
our scale, and leverages existing team expertise. The vertical scaling path
(read replicas + connection pooling + query optimization) provides sufficient
headroom for our 3-year growth target before sharding would be needed.

## Consequences

### Positive
- Fast development start (team expertise)
- Single database handles relational queries AND full-text search
- Strong ecosystem of tools and extensions

### Negative
- If we exceed write scaling limits (unlikely within 3 years), sharding
  PostgreSQL is complex. Would evaluate Citus or Vitess at that point.

### Risks
- Risk: Full-text search performance at 500K users with large text corpus
- Mitigation: Benchmark at 10x expected volume. If insufficient, migrate
  search to Elasticsearch (additive change, not a rewrite).

## Related Decisions
- ADR-001: Modular monolith architecture
- ADR-002: Managed cloud infrastructure (AWS)
```
