# Architecture Patterns Reference

## Table of Contents
1. Modular Monolith
2. Service-Oriented Architecture (SOA)
3. Microservices
4. Event-Driven Architecture
5. CQRS + Event Sourcing
6. Cell-Based Architecture
7. Hexagonal / Clean Architecture
8. Service Extraction Criteria

---

## 1. Modular Monolith

**What**: A single deployable unit with strict internal module boundaries. Modules communicate through defined interfaces, not direct database access.

**When to Use**: Stages 0–1. Teams under 20 developers. When you need fast iteration and simple deployment. This is the **default starting architecture** for nearly all new projects.

**Structure**:
```
monolith/
├── modules/
│   ├── users/        # Owns: users, profiles, sessions tables
│   ├── billing/      # Owns: invoices, payments, subscriptions tables
│   ├── content/      # Owns: posts, comments, media tables
│   └── notifications/ # Owns: notification_preferences, delivery_log tables
├── shared/            # Auth, logging, config — used by all modules
└── main.py/ts/go      # Single entry point
```

**Rules**:
- Each module owns its database tables exclusively. No module queries another's tables.
- Modules expose interfaces (functions, classes, or internal APIs). Other modules call these interfaces.
- Modules can share a database instance but should use separate schemas or table prefixes as a convention.
- Circular dependencies between modules are forbidden. If A depends on B and B depends on A, extract the shared logic into a third module or rethink boundaries.

**Why It Works**: You get the organizational benefits of service boundaries without the operational complexity of distributed systems. When you eventually need to extract a service, the boundaries are already drawn — you're extracting a module with a defined interface, not untangling spaghetti.

**Tradeoffs**:
- (+) Simple deployment, simple debugging, simple transactions
- (+) Refactoring boundaries is cheap (just move code, no network calls)
- (-) Single scaling unit — you scale everything together
- (-) Shared process means one bad module can affect others (memory leaks, CPU hogs)
- (-) Deployment coupling — all modules deploy together

---

## 2. Service-Oriented Architecture (SOA)

**What**: Multiple services communicating over well-defined APIs, typically organized around business capabilities. Coarser-grained than microservices.

**When to Use**: Stage 1–2. When specific modules have genuinely different scaling, deployment, or technology needs. When team boundaries align with service boundaries.

**Key Principles**:
- Services are organized around business capabilities, not technical layers
- Each service owns its data store
- Services communicate through APIs (sync) or events (async)
- Services can be deployed independently

**Tradeoffs**:
- (+) Independent scaling per service
- (+) Independent deployment reduces blast radius
- (+) Teams can move independently
- (-) Network calls replace function calls (latency, failure modes)
- (-) Distributed transactions are hard — prefer eventual consistency or sagas
- (-) Operational complexity increases (more things to deploy, monitor, debug)

---

## 3. Microservices

**What**: Fine-grained services, each doing one thing well, independently deployable and scalable.

**When to Use**: Stage 2–3. Large organizations with multiple independent teams. When you have the operational maturity (CI/CD per service, distributed tracing, container orchestration, on-call rotation per service).

**Prerequisites** (you need ALL of these before adopting microservices):
1. CI/CD pipeline per service
2. Container orchestration (Kubernetes or equivalent)
3. Distributed tracing (OpenTelemetry, Jaeger, etc.)
4. Service mesh or API gateway for routing and security
5. Centralized logging and monitoring
6. Teams organized around services (not around tech layers)

**Common Failure Mode**: "Distributed Monolith" — microservices that must be deployed together, share a database, or have synchronous call chains. This gives you all the complexity of microservices with none of the benefits. If your services can't be deployed and scaled independently, they're not microservices.

**Tradeoffs**:
- (+) Maximum scaling flexibility
- (+) Technology diversity (right tool per service)
- (+) Independent team velocity
- (-) Highest operational complexity
- (-) Debugging distributed issues is genuinely hard
- (-) Data consistency across services requires sagas or event-driven patterns
- (-) Testing is more complex (contract testing becomes essential)

---

## 4. Event-Driven Architecture

**What**: Services communicate through events rather than direct API calls. An event represents something that happened ("OrderPlaced", "UserRegistered"). Other services react to events asynchronously.

**When to Use**: When you need decoupling between services. When operations don't need synchronous responses. When you have fan-out patterns (one event triggers multiple reactions). When you need audit trails (event log). Stage 1+ for specific subsystems, Stage 2+ as a primary pattern.

**Key Components**:
- **Event Producer**: Service that emits events when something happens
- **Event Bus/Broker**: Message infrastructure (Kafka, RabbitMQ, SQS, NATS)
- **Event Consumer**: Service that reacts to events
- **Event Store** (optional): Persistent log of all events for replay/audit

**Patterns**:
- **Event Notification**: Fire-and-forget. Producer emits event, doesn't care who listens.
- **Event-Carried State Transfer**: Event includes all relevant data so consumers don't need to call back.
- **Event Sourcing**: Store state as a sequence of events, not as current state. Powerful for audit trails and temporal queries.

**Critical Rules**:
- Events are immutable facts. Never modify published events.
- Design events as contracts. Use schema evolution (add fields, don't remove/rename).
- Handle duplicate events (make consumers idempotent).
- Handle out-of-order events (include timestamps, sequence numbers, or design for commutativity).

**Tradeoffs**:
- (+) Extreme decoupling — services don't need to know about each other
- (+) Natural scalability — consumers process at their own pace
- (+) Built-in audit trail (event log)
- (+) Resilience — if a consumer is down, events queue up and are processed later
- (-) Eventual consistency — data may not be immediately consistent across services
- (-) Debugging is harder — "why did this happen?" requires tracing through event chains
- (-) Error handling is more complex — what happens when a consumer fails?

---

## 5. CQRS + Event Sourcing

**What**: Command Query Responsibility Segregation separates the write model (commands) from the read model (queries). Often paired with Event Sourcing, where state is stored as a sequence of events.

**When to Use**: When read and write patterns differ dramatically (e.g., 100:1 read-to-write ratio). When you need different data representations for different consumers. When audit trails or temporal queries are required. Stage 2+ for specific subsystems.

**Architecture**:
```
[Client] --command--> [Write Model] --event--> [Event Store]
                                                     |
                                                     v
                                              [Projection/Materialized View]
                                                     |
                                                     v
[Client] --query--> [Read Model (denormalized, cached, optimized for reads)]
```

**When NOT to Use**: Simple CRUD applications. When eventual consistency between read and write models is unacceptable. When the added complexity doesn't justify the benefit.

**Tradeoffs**:
- (+) Read and write models scale independently
- (+) Read models can be optimized per use case (different projections for different consumers)
- (+) Full audit trail with event sourcing
- (+) Can replay events to rebuild read models or create new projections
- (-) Significant complexity increase
- (-) Eventual consistency between write and read models
- (-) Event schema evolution requires careful planning

---

## 6. Cell-Based Architecture

**What**: The system is divided into independent "cells," each containing a complete copy of the service stack serving a subset of users/tenants. A routing layer directs traffic to the appropriate cell.

**When to Use**: Stage 3. When blast-radius containment is critical (a failure in one cell doesn't affect others). When operating at massive global scale. When tenant isolation is a requirement.

**Architecture**:
```
[Global Router]
     |
     ├── [Cell A: US-East] -- Complete stack serving users 0-1M
     ├── [Cell B: US-West] -- Complete stack serving users 1M-2M
     ├── [Cell C: EU] -- Complete stack serving users 2M-3M
     └── [Cell D: Asia] -- Complete stack serving users 3M-4M
```

**Tradeoffs**:
- (+) Maximum blast-radius containment
- (+) Independent scaling per cell
- (+) Natural geographic distribution
- (-) Cross-cell queries are expensive
- (-) Data consistency across cells requires careful design
- (-) Higher infrastructure cost (duplicate stacks)

---

## 7. Hexagonal / Clean Architecture

**What**: An internal code organization pattern (not a deployment pattern) that separates business logic from external concerns (databases, APIs, frameworks). The core domain has no dependencies on infrastructure.

**Structure**:
```
┌─────────────────────────────────┐
│        External World           │
│  (HTTP, CLI, Events, Cron)      │
└────────────┬────────────────────┘
             │ Adapters (Controllers, Event Handlers)
             v
┌─────────────────────────────────┐
│          Ports (Interfaces)     │
│  (Service interfaces, Repo      │
│   interfaces, Event interfaces) │
└────────────┬────────────────────┘
             │
             v
┌─────────────────────────────────┐
│      Domain / Business Logic    │
│  (Entities, Value Objects,      │
│   Domain Services, Rules)       │
│  ** ZERO external dependencies  │
└────────────┬────────────────────┘
             │ Ports (Interfaces)
             v
┌─────────────────────────────────┐
│       Infrastructure Adapters   │
│  (Database repos, API clients,  │
│   Email services, File storage) │
└─────────────────────────────────┘
```

**When to Use**: Always, as an internal code organization pattern within any module or service. This is not a deployment architecture — it's how you structure code inside a deployable unit.

**Key Benefit**: Your business logic can be tested without a database, HTTP server, or any framework. This makes tests fast, reliable, and focused on behavior.

---

## 8. Service Extraction Criteria

Before extracting a module into a separate service, answer YES to at least 3 of these 5 questions:

1. **Different scaling needs?** Does this component need to scale independently (e.g., it handles 10x more traffic than the rest)?
2. **Different deployment cadence?** Does this component need to be deployed more or less frequently than the rest?
3. **Different technology requirements?** Does this component genuinely need a different language, runtime, or database?
4. **Different team ownership?** Is there a dedicated team that owns this component and wants to move independently?
5. **Failure isolation?** Would a failure in this component be acceptable to isolate from the rest of the system?

**If fewer than 3 are YES**: Keep it as a module in the monolith. The operational overhead of a separate service isn't justified.

**Extraction Process**:
1. Ensure the module has a clean interface (no direct DB access from other modules)
2. Create an API that mirrors the internal interface
3. Deploy the new service alongside the monolith
4. Route traffic to the new service gradually (feature flag or percentage-based)
5. Monitor for performance and correctness differences
6. Cut over fully once confident
7. Remove the module code from the monolith

Never do a "big bang" extraction. Always incremental.
