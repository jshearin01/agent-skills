# The 20 Most Expensive Architectural Mistakes

These anti-patterns come from real-world failures observed over 20 years of building systems. Each one has cost teams months of work, millions in revenue, or both. Learn from others' pain.

---

## 1. Premature Microservices
**The Mistake**: Splitting into microservices before you have product-market fit, operational maturity, or enough team members to justify it.
**Why It Happens**: Conference talks and blog posts from Netflix and Amazon make microservices sound inevitable. They are — at Netflix-scale. At your scale, they're premature.
**The Cost**: 3–6x development time, distributed debugging nightmares, deployment complexity that consumes engineering time.
**The Fix**: Start with a modular monolith. Extract services only when concrete scaling, deployment, or team-boundary needs arise (see Service Extraction Criteria in patterns.md).

## 2. Shared Database Between Services
**The Mistake**: Multiple services reading from and writing to the same database tables.
**Why It Happens**: It's the path of least resistance when extracting services from a monolith.
**The Cost**: Coupling that defeats the purpose of services. Schema changes require coordinating across all services. Performance issues in one service affect all.
**The Fix**: Each service owns its data. If Service B needs data from Service A, it calls Service A's API or subscribes to its events. Migration: use the Strangler Fig pattern to gradually redirect data access.

## 3. Ignoring the Database Until It's on Fire
**The Mistake**: Treating the database as "someone else's problem" until queries start timing out.
**Why It Happens**: Application developers focus on application code. Database performance is invisible until it's critical.
**The Cost**: Emergency scaling under pressure. Expensive rewrites. Outages during growth moments.
**The Fix**: From day one: monitor slow queries, review ORM-generated SQL, set up query logging. Before Stage 1: add indexes, connection pooling, and read replicas. See the Database Scaling Ladder in scaling.md.

## 4. N+1 Query Problem
**The Mistake**: Fetching a list of items, then issuing a separate query for each item's relationships.
**Why It Happens**: ORMs make it easy to lazy-load relationships, which generates N+1 queries invisibly.
**The Cost**: 100 items × 1 relationship = 101 database queries instead of 2. This scales linearly with data volume and destroys performance.
**The Fix**: Use eager loading (JOIN or batch queries). Log all database queries in development and flag any request that generates more than 10 queries.

## 5. Storing Secrets in Code or Config Files
**The Mistake**: API keys, database passwords, or encryption keys committed to version control.
**Why It Happens**: It's the fastest way to get something working locally.
**The Cost**: One leaked secret can compromise the entire system. Secrets in git history persist even after deletion.
**The Fix**: Environment variables for local dev. Secrets manager (Vault, AWS Secrets Manager) for production. Scan repos for secrets in CI (tools: gitleaks, trufflehog). See security.md § Secrets Management.

## 6. Big Bang Rewrites
**The Mistake**: Deciding to rewrite the entire system from scratch instead of incrementally improving it.
**Why It Happens**: The existing system is painful. A clean start sounds appealing. "This time we'll do it right."
**The Cost**: 12–24 months of development with zero new features. The new system ships with its own bugs. Institutional knowledge is lost. Often fails entirely — the old system evolves during the rewrite, and the new system never catches up.
**The Fix**: Strangler Fig pattern — incrementally replace parts of the old system with new implementations. New features go in the new system. Old features migrate gradually. Both systems run in parallel during transition.

## 7. Insufficient Logging and Observability
**The Mistake**: Deploying to production without structured logging, metrics, or tracing.
**Why It Happens**: Observability feels like overhead when building features.
**The Cost**: When something breaks in production (and it will), you can't diagnose it. Mean time to recovery (MTTR) goes from minutes to hours or days. You're debugging in the dark.
**The Fix**: Structured logging, health checks, and basic metrics from day one. Add distributed tracing when you have multiple services. The investment pays for itself on the first production incident.

## 8. Synchronous Call Chains
**The Mistake**: Service A calls Service B, which calls Service C, which calls Service D — all synchronously.
**Why It Happens**: It's the simplest way to compose service calls.
**The Cost**: Latency adds up (A's response time = A + B + C + D). Reliability multiplies down (if each service is 99.9% available, the chain is 99.6% available). One slow or failing service blocks the entire chain.
**The Fix**: Async communication for non-critical paths. Caching to reduce downstream calls. Circuit breakers to prevent cascading failures. Parallel calls where possible. Design for graceful degradation — if the recommendation service is slow, show defaults.

## 9. No API Versioning
**The Mistake**: Publishing an API without a versioning strategy. Making breaking changes to existing endpoints.
**Why It Happens**: "We only have one client right now." "We can coordinate the change."
**The Cost**: Broken clients. Forced simultaneous deployment of client and server. Loss of trust from API consumers.
**The Fix**: Version from day one (/api/v1/...). Follow evolution rules (additive changes only within a version). See extensibility.md § API Versioning Strategy.

## 10. Over-Abstracting Too Early
**The Mistake**: Creating generic frameworks, abstract base classes, and "flexible" architectures before you understand the actual requirements.
**Why It Happens**: Engineers love elegant abstractions. It feels productive to build a generic solution.
**The Cost**: The wrong abstraction is worse than no abstraction. It fights you when real requirements arrive that don't fit the assumed pattern. Removing a bad abstraction is harder than adding a good one.
**The Fix**: Follow the Rule of Three — don't abstract until you have three concrete examples. Write concrete code first. Refactor to abstraction when the pattern is clear.

## 11. Ignoring Backpressure
**The Mistake**: Assuming upstream services will always produce at a rate downstream can handle. Using unbounded queues.
**Why It Happens**: During testing, everything works because volumes are low.
**The Cost**: Memory exhaustion, cascading failures, data loss when buffers overflow without control.
**The Fix**: Bounded queues everywhere. Rate limiting at ingestion points. Load shedding for overload. Back-pressure signals (429, 503 with Retry-After). See scaling.md § Mass Scale Patterns.

## 12. Monolithic Database for All Workloads
**The Mistake**: Using a single PostgreSQL/MySQL instance for OLTP transactions, full-text search, analytics, time-series data, and caching.
**Why It Happens**: PostgreSQL is amazingly versatile, and "one database is simpler."
**The Cost**: Different workloads compete for resources. Analytics queries slow down user-facing queries. The database becomes the bottleneck for everything simultaneously.
**The Fix**: Start with one database (it's fine early on). As workloads diversify, use the right tool: Redis for caching, Elasticsearch for search, time-series DB for metrics, data warehouse for analytics. This is polyglot persistence — it's earned complexity.

## 13. Distributed Transactions
**The Mistake**: Trying to achieve ACID transactions across multiple services or databases.
**Why It Happens**: "We need consistency!" (Without analyzing whether eventual consistency is actually fine.)
**The Cost**: Two-phase commit is slow, fragile, and doesn't work across heterogeneous systems. Distributed locks cause contention and deadlocks.
**The Fix**: Design for eventual consistency where possible (it's fine for 95% of use cases). Use sagas with compensating actions for distributed workflows. Reserve strong consistency for the rare operations that truly need it (usually financial transactions within a single service).

## 14. No Load Testing
**The Mistake**: Never testing the system under realistic load before it experiences real load.
**Why It Happens**: "We'll scale when we need to." Load testing takes effort to set up.
**The Cost**: Performance problems discovered by users during peak traffic. Emergency scaling under pressure. Revenue loss.
**The Fix**: Load test before launch. Load test before every major release. Simulate realistic traffic patterns (not just uniform load). Test at 2x expected peak to find headroom.

## 15. Configuration Drift
**The Mistake**: Making manual infrastructure changes (SSH into servers, click around in the console) without recording them.
**Why It Happens**: "It's just a quick fix." "I'll document it later."
**The Cost**: Environments diverge. "It works in staging but not in production" becomes routine. Disaster recovery is impossible because nobody knows the actual configuration.
**The Fix**: Infrastructure as Code (Terraform, Pulumi, CloudFormation). All infrastructure changes go through code review and CI/CD. No manual changes in production — ever.

## 16. Ignoring Data Growth
**The Mistake**: Designing schemas and queries as if the data volume will stay the same forever.
**Why It Happens**: Current data volumes are small. Queries are fast enough today.
**The Cost**: Table scans that take seconds with 1M rows take minutes with 100M rows. Storage costs explode. Backups take longer than the backup window.
**The Fix**: Design indexes for expected query patterns at 10–100x current volume. Implement data retention policies (archive or delete old data). Plan for data tiering (hot/warm/cold storage). Monitor table sizes and query performance trends.

## 17. Security as an Afterthought
**The Mistake**: Planning to "add security later" after the features are built.
**Why It Happens**: Security doesn't generate revenue. Features do.
**The Cost**: Retrofitting security is 10–100x more expensive than building it in. A security breach can destroy a company. See: Equifax, Target, SolarWinds.
**The Fix**: Security is architecture, not a feature. Follow the Security Checklist by Stage in security.md. Do lightweight threat modeling for every new feature.

## 18. Not Designing for Failure
**The Mistake**: Assuming dependencies (databases, APIs, network) will always be available.
**Why It Happens**: In development and testing, everything is up. Failures are rare.
**The Cost**: One failed dependency cascades to system-wide outage. No graceful degradation. Users see error pages.
**The Fix**: Assume everything will fail. Circuit breakers, retries with backoff, timeouts, fallback responses, bulkheads. Test failure scenarios (chaos engineering at scale, manual failure injection at any scale).

## 19. Tight Coupling to Third-Party Services
**The Mistake**: Calling third-party APIs directly from business logic throughout the codebase.
**Why It Happens**: The API client is easy to import. "We're committed to this vendor."
**The Cost**: When you need to switch vendors (and you will), you're rewriting code across the entire codebase. Outages in the third-party service cascade into your system without any control.
**The Fix**: Adapter pattern. Wrap every third-party integration behind an interface you define. Your business logic calls your interface. The adapter translates to the specific vendor's API. Switching vendors means writing a new adapter, not rewriting business logic.

## 20. No Architecture Decision Records
**The Mistake**: Making significant architecture decisions without documenting the context, alternatives considered, and rationale.
**Why It Happens**: "Everyone knows why we chose X." "Documentation is overhead."
**The Cost**: 6 months later, nobody remembers why. New team members question every decision. Decisions get relitigated repeatedly. The same mistakes are repeated because lessons aren't captured.
**The Fix**: Write an ADR for every significant architecture decision. Takes 15–30 minutes. Saves hours of future discussion. See templates/adr-template.md.

---

## Summary: Red Flags in Code Reviews

When reviewing code or architecture, these patterns should trigger immediate concern:

| Red Flag | Likely Problem |
|---|---|
| Direct database queries across module boundaries | Tight coupling, shared database anti-pattern |
| Secrets in source code or config files | Security vulnerability |
| No error handling on external calls | No failure design |
| Synchronous chain of 3+ service calls | Latency and reliability cascade |
| No index on a column used in WHERE/JOIN | Performance time bomb |
| ORM lazy loading in a loop | N+1 query problem |
| No structured logging in a service | Observability gap |
| No health check endpoint | Unmonitorable service |
| Unbounded list/query with no pagination | Memory bomb waiting to happen |
| Hardcoded URLs/connection strings | Configuration drift |
| No input validation on user-facing endpoints | Security vulnerability |
| No timeout on HTTP/DB client calls | Resource leak waiting to happen |
