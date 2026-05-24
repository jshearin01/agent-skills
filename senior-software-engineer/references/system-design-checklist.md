# System Design Checklists

> Use these checklists before starting a design (pre-design) and before shipping (pre-ship). They encode the questions senior engineers have learned to ask after being surprised by their absence.

## Table of Contents

1. [Pre-Design Checklist](#1-pre-design-checklist)
2. [Pre-Ship Checklist](#2-pre-ship-checklist)
3. [Scalability Considerations](#3-scalability-considerations)
4. [Data Design Guidelines](#4-data-design-guidelines)
5. [API Design Standards](#5-api-design-standards)
6. [Pattern Reference with Implementation Notes](#6-pattern-reference-with-implementation-notes)

---

## 1. Pre-Design Checklist

Answer every question before drawing a single diagram or writing a line of code.

### Problem Clarity
- [ ] Can I state the user problem in one sentence?
- [ ] What happens if we don't build this? (Quantified if possible)
- [ ] Who are the actual users? Have I talked to any of them?
- [ ] What does success look like, and how will we measure it?
- [ ] Are there non-code solutions worth considering first?

### Constraints (Real, Not Imagined)
- [ ] Current traffic: requests/day, peak concurrent users?
- [ ] Projected traffic in 12 months (conservative estimate, not aspirational)?
- [ ] Team size that will build, own, and operate this?
- [ ] Time to first production deployment?
- [ ] Compliance or security requirements that constrain design?
- [ ] Budget for compute/storage at scale?
- [ ] SLA required (99%? 99.9%? 99.99%?) — these are radically different designs

### Technology Selection
- [ ] Have I exhausted managed services and existing libraries before proposing to build?
- [ ] Does the team have expertise in the proposed stack, or is this an innovation token spend?
- [ ] What are the known failure modes of the chosen technology?
- [ ] Who will be on-call for this system, and do they know this stack?
- [ ] Is the technology still actively maintained?

### Architecture
- [ ] Where are the domain boundaries? What belongs together, what belongs separate?
- [ ] What are the interfaces between components? Are they well-defined?
- [ ] What's the failure behavior if each dependency fails?
- [ ] Is there a data ownership model? Which system is the source of truth for each data type?
- [ ] Have I considered the eventual operational costs (not just build costs)?

### Documentation
- [ ] Is there an ADR for each significant decision? (See `references/adr-template.md`)
- [ ] Is there a design doc that captures context, alternatives, and trade-offs?

---

## 2. Pre-Ship Checklist

Before declaring a system production-ready.

### Correctness
- [ ] Unit tests cover all non-trivial business logic branches
- [ ] Integration tests cover the key workflows
- [ ] Edge cases documented and handled: empty inputs, maximum sizes, concurrent updates
- [ ] Error handling verified: what happens when dependencies fail?
- [ ] Data validation at every entry point (don't trust external inputs)

### Observability
- [ ] Structured logs with: request ID, user ID, operation, outcome, duration
- [ ] Health check endpoint returning meaningful status
- [ ] Key business metrics instrumented (what does "working" look like as a number?)
- [ ] Alerting configured on user-visible symptoms (not just CPU/memory)
- [ ] Runbook written: what does on-call do when the alert fires?

### Security
- [ ] Authentication required where needed; authorization verified (not just "logged in")
- [ ] All external inputs validated and sanitized
- [ ] Secrets in environment variables / secrets manager, not in code or config files
- [ ] SQL queries parameterized (never string-interpolated)
- [ ] Dependency vulnerabilities scanned
- [ ] Sensitive data not logged

### Operations
- [ ] Deployment process documented and tested
- [ ] Rollback procedure documented and tested
- [ ] Database migrations backward-compatible (tested on production-size data clone)
- [ ] Feature flagged if risky (can be disabled without deployment)
- [ ] Load tested at realistic peak (not just unit tested)
- [ ] Configuration externalized (no environment-specific values in code)

### Team Readiness
- [ ] At least 2 engineers understand the system (no single point of knowledge)
- [ ] On-call rotation updated to include this system
- [ ] Runbook reviewed by someone other than the author

---

## 3. Scalability Considerations

### Traffic Scaling
**Before scaling infrastructure, measure:**
- Current request volume and growth rate
- P50, P95, P99 latency (not just averages)
- Error rate breakdown by type
- Database query times and N+1 patterns

**Common scaling interventions (in order of increasing complexity):**
1. Index the queries that are slow (almost always the first win)
2. Cache read-heavy data at the application layer
3. Add read replicas for read-heavy workloads
4. Vertical scaling (bigger instances — often underrated)
5. Horizontal scaling with load balancing
6. Database sharding (only after the above exhausted; very high operational cost)

**Signs you don't need to scale yet:**
- Your infrastructure is at <40% utilization under peak load
- Latency is acceptable to users
- You're scaling speculatively for load that doesn't exist

### Team Scaling
Systems that scale to large teams have these properties:
- **Independent deployability:** Teams can deploy their services without coordinating with others
- **Clear ownership:** Each service/component has a single owning team
- **Stable interfaces:** APIs change through versioning, not breaking changes
- **Autonomous testing:** Teams can test their components without standing up the entire system

Microservices only deliver team scaling benefits when these properties are present. Without them, microservices add operational overhead with no benefit.

### Data Volume Scaling
- Partition large tables before they become unmanageable (not after)
- Separate OLTP (transactional) and OLAP (analytical) workloads early
- Archive old data rather than letting tables grow unbounded
- Index creation on large tables requires planning (may lock the table)

---

## 4. Data Design Guidelines

### The Golden Rules
1. **Data outlives code.** Schema decisions made today will constrain engineers for years. Take them seriously.
2. **Soft delete everything meaningful.** `deleted_at TIMESTAMP NULL` costs nothing; recovery from a hard delete costs everything.
3. **Audit log for state changes.** For any data that matters: who changed it, when, from what, to what.
4. **Don't trust your own database.** Validate in application code before inserting. Validate after reading. Databases accumulate garbage.

### Schema Migration Best Practices
| Change | Risk | Approach |
|---|---|---|
| Add nullable column | Low | Direct migration |
| Add non-null column without default | High | Add nullable → backfill → add constraint |
| Rename column | High | Add new column → dual-write → migrate reads → drop old |
| Remove column | Medium | Stop using it in code first → wait one deploy → then drop |
| Add index | Medium | Use `CREATE INDEX CONCURRENTLY` in Postgres; test timing on prod-size data |
| Change column type | Very High | New column → copy data → validate → swap |

**Never run untested migrations against production.** Always test against a clone of production data.

### Consistency Tradeoffs
- **Strong consistency:** Every read reflects the latest write. Requires coordination. Higher latency.
- **Eventual consistency:** Reads may be stale. Simpler to scale. Requires application-level handling of stale data.
- **Choose strong consistency as the default** for financial data, inventory, and anything where inconsistency has real consequences. Opt into eventual consistency explicitly, with eyes open.

---

## 5. API Design Standards

### REST Principles (Pragmatic)
- Resources are nouns (`/users`, `/orders/123`), not verbs (`/getUser`, `/createOrder`)
- Use HTTP methods semantically: GET (read), POST (create), PUT/PATCH (update), DELETE (delete)
- Return appropriate status codes: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable, 500 Server Error
- Errors return structured bodies: `{"error": "validation_failed", "message": "email is required", "field": "email"}`
- Paginate list endpoints: `{"data": [...], "cursor": "...", "has_more": true}`

### Versioning
- Version in the URL (`/v1/users`) or Accept header — pick one, be consistent
- Never make breaking changes to an existing version
- Support N-1 versions minimum; give consumers 3+ months notice before deprecation

### Breaking vs. Non-Breaking Changes
**Non-breaking (safe):** Adding new optional fields, adding new endpoints, adding new enum values (if consumers handle unknown values)

**Breaking (requires versioning):** Removing fields, renaming fields, changing field types, changing HTTP method or path, removing enum values

### Contract Testing
If you own an API consumed by others, contract tests (consumer-driven) are the best way to catch breaking changes before they reach production. Libraries: Pact (most languages), Dredd.

---

## 6. Pattern Reference with Implementation Notes

### Strangler Fig
**When:** Replacing a legacy system. Never use a big-bang approach.
**How:**
1. Create a routing proxy/facade in front of the legacy system
2. New features go to the new system
3. Migrate features one at a time, routing through the proxy
4. The legacy system is retired when all routes point to the new system

**Key discipline:** The proxy must remain thin. Business logic does not live in the proxy.

---

### Circuit Breaker
**When:** Calling any external dependency that can fail (databases, APIs, queues).
**States:** Closed (normal) → Open (dependency failing, fast-fail) → Half-Open (testing recovery)
**Thresholds:** Open after N failures in window; close after M successes in half-open

```python
# Conceptual example
if circuit_breaker.is_open("payment_service"):
    return CachedResponse or ServiceUnavailableError
result = call_payment_service()
circuit_breaker.record(result)
```

---

### Dual-Write Migration
**When:** Migrating data from one schema or system to another safely.
**Steps:**
1. Write to both old and new simultaneously (new writes go to both)
2. Read from old (old is source of truth)
3. Run backfill job to populate new with historical data
4. Compare old vs. new for consistency
5. Switch reads to new (old is still backup)
6. Remove writes to old
7. Remove old system

**Never skip steps.** Each step is a rollback point.

---

### Idempotency Keys
**When:** Any operation that must not be duplicated (payments, email sends, inventory changes).
**How:** Client generates a unique key per logical operation. Server stores key with outcome. On retry with same key, return stored outcome without re-executing.

```sql
CREATE TABLE idempotency_keys (
    key         VARCHAR(255) PRIMARY KEY,
    outcome     JSONB NOT NULL,
    created_at  TIMESTAMP NOT NULL,
    expires_at  TIMESTAMP NOT NULL
);
```

---

### Feature Flags
**When:** Every non-trivial production release.
**Minimum viable implementation:**

```python
def feature_enabled(feature_name: str, user_id: str = None) -> bool:
    config = get_feature_config(feature_name)
    if not config.enabled:
        return False
    if config.rollout_pct == 100:
        return True
    if user_id:
        # Consistent bucketing: same user always gets same result
        return (hash(f"{feature_name}:{user_id}") % 100) < config.rollout_pct
    return False
```

Flag state should be queryable without a deployment. Store flags in a database or a service like LaunchDarkly, not in code constants.
