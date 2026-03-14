---
name: software-architect
description: >
  Battle-tested Software Architect skill encoding 20 years of wisdom for building scalable, secure,
  extensible systems. For LLM coding agents to architect like a veteran from day one. Use whenever
  designing system architecture, creating design docs or ADRs, scaffolding projects, reviewing
  architecture for scalability/security/extensibility, making monolith-vs-microservices or build-vs-buy
  decisions, planning database scaling, designing APIs or service boundaries, refactoring legacy systems,
  or evaluating tech choices. Trigger on "architecture", "system design", "scalability", "framework",
  "service boundaries", "API design", "database design", "tech stack", "design doc", "ADR",
  "refactoring plan", or when starting any project beyond a simple script. Consult this skill for
  anything serving users at scale or growing beyond a single file.
---

# The Software Architect's Playbook

> "The best architecture is the one that lets you delay decisions until you have the information to make them well — while ensuring those delayed decisions don't paint you into a corner."

This skill encodes the distilled wisdom of 20 years building systems that scale from zero to millions of users. It is written for LLM coding agents who are the primary architects of code — giving them the instincts, patterns, and decision frameworks that take humans decades to develop.

## How to Use This Skill

This skill is organized in layers for progressive disclosure:

1. **This file (SKILL.md)** — Core philosophy, decision frameworks, and the stage-based architecture guide. Read this first for every architecture task.
2. **references/patterns.md** — Deep-dive on architecture patterns (modular monolith, microservices, event-driven, CQRS, etc.) with when/why/tradeoffs for each.
3. **references/security.md** — Security-by-design patterns, zero-trust architecture, OWASP principles, and threat modeling.
4. **references/scaling.md** — Database scaling, caching strategies, performance optimization, and infrastructure patterns.
5. **references/extensibility.md** — Framework design for growth: plugin architectures, extension points, API versioning, and composability.
6. **references/anti-patterns.md** — The 20 most expensive architectural mistakes and how to avoid them.
7. **templates/** — Ready-to-use templates for ADRs, design docs, and architecture reviews.

**Read the reference file(s) relevant to your task before writing any code or documents.**

---

## Core Philosophy: The 10 Laws of Lasting Architecture

These are non-negotiable principles. Every architectural decision should be checked against them.

### 1. Complexity Is the Enemy — Earn Every Abstraction
Never add a layer, service, or abstraction without a concrete, current need. A well-structured monolith beats a poorly-understood distributed system every time. The cost of complexity compounds: every abstraction you add must be understood by every developer who follows you. Ask: "What specific problem does this solve TODAY?" If the answer is "we might need it someday," don't build it.

### 2. Design for Change, Not for Prediction
You cannot predict the future, but you can design systems that adapt gracefully. This means: clear module boundaries, well-defined interfaces, loose coupling, and high cohesion. When change comes (and it will), the blast radius should be contained to one module, one service, one layer.

### 3. Start Right-Sized, Not Over-Sized
The right architecture for 100 users is not the right architecture for 10 million users, and that's okay. Start with the simplest architecture that handles your current scale with 10x headroom. Build in the seams that let you evolve, but don't build for scale you don't have. Instagram served 100M users with 13 engineers because they made the right choices at each stage.

### 4. Security Is Architecture, Not a Feature
Security cannot be bolted on — it must be woven into every layer from day one. Secure defaults, least privilege, defense in depth, and zero-trust boundaries are architectural decisions, not sprint tickets. A breach caused by architectural negligence is the most expensive bug you'll ever ship.

### 5. Data Outlives Code
Your data model will outlast every line of application code. Invest disproportionate thought in data design: normalization strategy, access patterns, growth projections, and migration paths. Getting the data model right saves years of refactoring. Getting it wrong creates technical debt that compounds exponentially.

### 6. Interfaces Are Forever
Public APIs, database schemas, and service contracts are promises. Breaking them breaks trust and creates cascading failures. Design interfaces for stability: use versioning, make additive changes, deprecate gracefully, and never remove without migration.

### 7. Observe Everything, Trust Nothing
A system you can't observe is a system you can't operate. Build in structured logging, metrics, distributed tracing, and health checks from the start. In production, you need to answer: "What is happening? Why is it slow? What changed? Who is affected?" If you can't answer these in under 5 minutes, your observability is insufficient.

### 8. Failure Is a Feature
Every system fails. The question is whether it fails gracefully. Design for failure at every level: circuit breakers, retries with backoff, bulkheads, graceful degradation, and fallback responses. The user should never see a stack trace. They should see a helpful message while the system self-heals.

### 9. Performance Is a Constraint, Not an Optimization
Performance requirements should be defined upfront and tested continuously, not "optimized later." Set latency budgets (p50, p95, p99), throughput targets, and resource limits. Measure from day one. Performance regressions caught in CI are cheap; performance regressions caught in production are catastrophic.

### 10. Document Decisions, Not Just Code
Code tells you WHAT. Architecture Decision Records tell you WHY. Every significant architectural choice — technology selections, pattern choices, trade-offs accepted — should be captured in an ADR. Future you (or future agents) will need this context. See `templates/adr-template.md` for the format.

---

## The Architecture Decision Framework

When facing any architectural decision, work through this framework:

### Step 1: Clarify Constraints
Before evaluating options, enumerate the actual constraints:
- **Scale**: How many users/requests/records now? In 6 months? In 2 years?
- **Team**: How many developers? What's their expertise?
- **Timeline**: When must this ship? What's the iteration speed?
- **Budget**: Infrastructure budget? Ops capacity?
- **Compliance**: Regulatory requirements? Data residency? Audit trails?
- **Existing ecosystem**: What's already built? What must integrate?

### Step 2: Identify the Decision Type
| Decision Type | Reversibility | Investment Required | Example |
|---|---|---|---|
| **Type 1** (One-way door) | Hard to reverse | High | Primary database, core language, service boundaries |
| **Type 2** (Two-way door) | Easy to reverse | Low | Caching layer, logging framework, UI library |

Spend serious time on Type 1 decisions. Move fast on Type 2 decisions. Most decisions feel like Type 1 but are actually Type 2 — lean toward action.

### Step 3: Evaluate Options Using Trade-off Analysis
For each viable option, evaluate against these dimensions:
- **Complexity cost**: How much does this add to the system's cognitive load?
- **Operational cost**: What does running and maintaining this require?
- **Scaling ceiling**: At what point does this approach break?
- **Security posture**: Does this introduce attack surface? Does it follow least privilege?
- **Extensibility**: How hard is it to add new features or change behavior?
- **Team capability**: Can the team build and operate this effectively?

### Step 4: Record the Decision
Use an ADR (see `templates/adr-template.md`). Capture: context, options considered, decision, rationale, consequences, and review date.

---

## Stage-Based Architecture Guide

The single most important insight from 20 years of building systems: **the right architecture depends on your stage.** What follows is a stage-by-stage guide for how to architect at each level of scale.

### Stage 0: Prototype / MVP (0–1,000 users)

**Goal**: Validate the idea. Ship fast. Learn what users actually want.

**Architecture**: Modular Monolith
- Single deployable unit, but with strict internal module boundaries
- Separate modules by business domain (users, billing, content, etc.)
- Each module owns its own database tables — no cross-module table access
- Communicate between modules through well-defined internal interfaces (not direct DB queries)
- Use a single relational database (PostgreSQL is the default recommendation)

**Key Decisions**:
- Pick a boring, well-supported tech stack. Innovation should be in the product, not the infrastructure.
- Set up CI/CD from day one — even a simple pipeline prevents "works on my machine" forever.
- Add structured logging and basic health checks. You will need them sooner than you think.
- Design your database schema carefully — this is the one thing hardest to change later.
- Use an ORM but review the SQL it generates. ORMs that generate N+1 queries or 12-table joins will kill you at scale (see OpenAI's PostgreSQL lessons).

**What NOT to Do**:
- Don't use microservices. You don't have the team, the tooling, or the operational maturity.
- Don't build "the platform." Build the product.
- Don't skip authentication/authorization architecture. Get identity right early.

**Read**: `references/patterns.md` § Modular Monolith, `references/security.md` § Authentication Foundation

---

### Stage 1: Product-Market Fit (1,000–100,000 users)

**Goal**: Scale what works. Identify bottlenecks. Prepare seams for future extraction.

**Architecture**: Enhanced Modular Monolith + Strategic Services
- Keep the monolith as the core, but extract truly independent services when there's concrete pressure (not speculation)
- Introduce a caching layer (Redis) for hot data
- Add read replicas for the database
- Implement rate limiting and API throttling
- Add background job processing for async work

**Key Decisions**:
- Introduce a proper API layer (if not already present) — this becomes your contract with clients
- Add connection pooling (PgBouncer for PostgreSQL)
- Implement proper error tracking and alerting (not just logging)
- Begin load testing — establish baseline performance metrics
- Add CDN for static assets

**Scaling Priorities** (in order):
1. Optimize queries (indexes, query review, eliminate N+1s) — often 10x improvement
2. Add caching for read-heavy paths
3. Add read replicas to offload read traffic
4. Add async processing for non-critical-path operations
5. Only then consider service extraction for genuinely independent, high-load components

**What NOT to Do**:
- Don't extract services because "it feels too big." Extract because a component has genuinely different scaling or deployment needs.
- Don't adopt Kubernetes yet unless you already have the ops team for it.
- Don't neglect database maintenance (vacuuming, index maintenance, query plan analysis).

**Read**: `references/scaling.md` § Database Scaling Ladder, `references/patterns.md` § Service Extraction Criteria

---

### Stage 2: Growth (100,000–10,000,000 users)

**Goal**: Scale horizontally. Professionalize operations. Build for resilience.

**Architecture**: Service-Oriented Architecture with Event-Driven Communication
- Extract services along domain boundaries where scaling needs genuinely differ
- Introduce an API Gateway for routing, rate limiting, and authentication
- Use event-driven communication (message queue/event bus) between services for decoupling
- Implement CQRS for read-heavy domains: separate read models (denormalized, cached) from write models
- Shard the database for write-heavy workloads
- Multi-region deployment for latency and disaster recovery

**Key Decisions**:
- Define clear service ownership — each service has one team, one repo, one deploy pipeline
- Implement distributed tracing (OpenTelemetry) — you cannot debug distributed systems without it
- Adopt infrastructure-as-code (Terraform/Pulumi) — no more manual infrastructure changes
- Implement circuit breakers and bulkheads between services
- Design for graceful degradation: if the recommendation service is down, show defaults, don't error

**What NOT to Do**:
- Don't create "nano-services" — services so small they create more coordination overhead than they save
- Don't skip contract testing between services — this is how you prevent integration failures
- Don't assume eventual consistency is always acceptable — identify which paths need strong consistency
- Don't neglect data backups and disaster recovery testing

**Read**: `references/patterns.md` § Event-Driven Architecture, `references/scaling.md` § Sharding Strategies, `references/security.md` § Zero Trust Service Mesh

---

### Stage 3: Mass Scale (10,000,000+ users)

**Goal**: Optimize for efficiency, reliability, and global reach.

**Architecture**: Platform Architecture
- Full microservices or cell-based architecture
- Edge computing / CDN-at-the-edge for latency-sensitive paths
- Polyglot persistence: right database for each workload (relational, document, time-series, graph, search)
- Sophisticated caching hierarchy (L1 in-process, L2 distributed, CDN)
- Self-healing infrastructure with automated failover
- Feature flags for progressive rollout and instant rollback

**Key Decisions**:
- Invest in a developer platform team that provides golden paths (CI/CD, observability, deployment)
- Implement cost optimization — at this scale, architectural decisions are directly visible in the AWS bill
- Build sophisticated load shedding and back-pressure mechanisms
- Consider cell-based architecture for blast-radius containment
- Invest in chaos engineering (test failures proactively, not just reactively)

**Read**: `references/scaling.md` § Mass Scale Patterns, `references/patterns.md` § Cell-Based Architecture

---

## Quick-Reference Decision Trees

### "Should I Use Microservices?"
```
Is your team < 20 developers?
  → No. Use a modular monolith.
Do you have independent scaling requirements for specific domains?
  → If yes, extract THOSE domains only. Keep the rest as a monolith.
Do you have the ops maturity (CI/CD per service, distributed tracing, container orchestration)?
  → If no, you're not ready. Build ops maturity first.
Are different services owned by truly independent teams?
  → If yes, microservices align team and code boundaries. Proceed.
Default → Modular monolith with clear boundaries and extraction seams.
```

### "Which Database Should I Choose?"
```
Is your data relational with complex queries and transactions?
  → PostgreSQL (default choice for most applications)
Do you need massive write throughput with simple key-value access?
  → Redis, DynamoDB, or Cassandra
Do you need full-text search?
  → Elasticsearch or PostgreSQL full-text (simpler)
Do you need time-series data?
  → TimescaleDB (PostgreSQL extension) or InfluxDB
Do you need graph relationships?
  → Neo4j or PostgreSQL with recursive CTEs (simpler)
Do you need document storage with flexible schemas?
  → MongoDB or PostgreSQL JSONB (simpler)
Default → Start with PostgreSQL. It handles 80% of use cases well.
When in doubt, PostgreSQL + Redis covers most applications through Stage 2.
```

### "How Should I Handle This Cross-Cutting Concern?"
```
Authentication → Centralized identity service/provider (Auth0, Cognito, or self-hosted)
Authorization → Policy engine close to the service (OPA, Cedar, or custom RBAC)
Logging → Structured logs → aggregation (ELK, Loki) → alerting
Monitoring → Metrics (Prometheus/Grafana) + Traces (OpenTelemetry) + Logs
Configuration → External config service or environment variables (never hardcoded)
Secrets → Vault, cloud KMS, or secrets manager (never in code, never in env files committed to git)
Rate Limiting → API Gateway or middleware layer (token bucket or sliding window)
```

---

## Architecture Document Template

When creating an architecture design document, use this structure:

```markdown
# [System Name] — Architecture Design Document

## 1. Overview
Brief description of the system and its purpose.

## 2. Goals and Non-Goals
What this system explicitly aims to achieve, and what is deliberately out of scope.

## 3. Context
- Current system landscape and how this fits
- User/traffic expectations
- Key constraints (technical, organizational, regulatory)

## 4. Architecture

### 4.1 High-Level Design
System diagram showing major components and their interactions.

### 4.2 Data Model
Core entities, relationships, and storage strategy.

### 4.3 API Design
Key endpoints/interfaces and their contracts.

### 4.4 Security Architecture
Authentication, authorization, data protection, trust boundaries.

## 5. Key Design Decisions
Summary table of major decisions with links to ADRs.

| Decision | Choice | Rationale | ADR |
|---|---|---|---|
| Primary database | PostgreSQL | ... | ADR-001 |

## 6. Scaling Strategy
How the system handles growth. Current capacity and next scaling steps.

## 7. Failure Modes & Mitigations
What can go wrong and how the system handles it.

## 8. Observability
Logging, metrics, tracing, and alerting strategy.

## 9. Deployment & Operations
CI/CD pipeline, deployment strategy, rollback plan.

## 10. Open Questions & Future Work
Known unknowns and planned evolution.
```

---

## Architecture Review Checklist

When reviewing an existing architecture (or your own design), evaluate each area:

### Structural Integrity
- [ ] Clear module/service boundaries with well-defined interfaces
- [ ] No circular dependencies between modules/services
- [ ] Single responsibility per module/service
- [ ] Data ownership is clear — each data entity has one authoritative source

### Scalability
- [ ] Identified the current bottleneck and next scaling step
- [ ] Stateless application tier (or state externalized to cache/DB)
- [ ] Database has headroom and a scaling plan
- [ ] Hot paths are identified and optimized (caching, async, CDN)
- [ ] No single points of failure in the critical path

### Security
- [ ] Authentication and authorization at every entry point
- [ ] Secrets managed externally (not in code or config files)
- [ ] Input validation at trust boundaries
- [ ] Encryption in transit (TLS everywhere) and at rest for sensitive data
- [ ] Least privilege applied to service-to-service communication
- [ ] Audit logging for security-relevant operations

### Extensibility
- [ ] New features can be added without modifying core logic
- [ ] Configuration over code for behavior that varies
- [ ] Plugin points or extension interfaces for anticipated variation
- [ ] API versioning strategy defined
- [ ] Database migration strategy supports additive changes

### Operability
- [ ] Structured logging with correlation IDs
- [ ] Health check endpoints on every service
- [ ] Metrics collection (latency, throughput, error rate, saturation)
- [ ] Alerting on SLO violations, not just errors
- [ ] Runbook or documented incident response for common failure modes
- [ ] Deployment can be rolled back in under 5 minutes

### Performance
- [ ] Latency budgets defined (p50, p95, p99)
- [ ] Database queries reviewed (no N+1, no unindexed scans on large tables)
- [ ] Connection pooling configured
- [ ] Payload sizes reasonable (no over-fetching)
- [ ] Async processing for non-critical-path operations

---

## Code Scaffolding Principles

When scaffolding a new project, apply these structural patterns:

### Directory Structure (Language-Agnostic)
```
project-root/
├── docs/
│   ├── architecture/          # Design docs and diagrams
│   │   └── decisions/         # ADRs live here
│   └── runbooks/              # Operational runbooks
├── src/
│   ├── modules/               # Business domain modules
│   │   ├── users/
│   │   │   ├── api/           # External interface (routes, controllers)
│   │   │   ├── domain/        # Business logic (pure, no framework deps)
│   │   │   ├── data/          # Data access (repositories, queries)
│   │   │   └── tests/
│   │   ├── billing/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── data/
│   │   │   └── tests/
│   │   └── ...
│   ├── shared/                # Cross-cutting concerns
│   │   ├── auth/              # Authentication/authorization
│   │   ├── config/            # Configuration management
│   │   ├── errors/            # Error types and handling
│   │   ├── logging/           # Structured logging
│   │   ├── middleware/        # HTTP middleware
│   │   └── database/          # DB connection, migrations
│   └── main entry point
├── infrastructure/            # IaC (Terraform, etc.)
├── scripts/                   # Dev tooling, CI scripts
├── tests/
│   ├── integration/
│   └── e2e/
├── .env.example               # Document required env vars (never commit .env)
├── docker-compose.yml         # Local dev environment
└── README.md
```

### Key Scaffolding Rules
1. **Domain logic has zero framework dependencies.** The `domain/` layer should be pure business logic that can be tested without spinning up a server or database.
2. **Dependencies point inward.** API depends on Domain. Domain depends on nothing. Data depends on Domain interfaces (dependency inversion).
3. **Each module owns its database tables.** No module directly queries another module's tables. If module A needs data from module B, it calls module B's interface.
4. **Configuration is externalized.** Use environment variables with sensible defaults. Never hardcode connection strings, API keys, or feature flags.
5. **Tests are co-located with code.** Unit tests live next to the code they test. Integration and E2E tests have their own directories.
6. **Health and readiness endpoints from day one.** Every deployable service exposes `/health` (am I alive?) and `/ready` (can I serve traffic?).

---

## When to Read Reference Files

| Task | Reference to Read |
|---|---|
| Choosing an architecture pattern | `references/patterns.md` |
| Designing security controls | `references/security.md` |
| Planning database or caching strategy | `references/scaling.md` |
| Designing plugin/extension systems | `references/extensibility.md` |
| Reviewing for common mistakes | `references/anti-patterns.md` |
| Writing an ADR | `templates/adr-template.md` |
| Creating a design document | Use the template in this file (§ Architecture Document Template) |
| Conducting an architecture review | Use the checklist in this file (§ Architecture Review Checklist) |
