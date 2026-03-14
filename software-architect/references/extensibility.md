# Extensibility & Framework Design Reference

## Table of Contents
1. Extensibility Principles
2. Extension Point Patterns
3. Plugin Architecture
4. API Versioning Strategy
5. Configuration-Driven Behavior
6. Composability Patterns
7. Migration & Backward Compatibility

---

## 1. Extensibility Principles

### The Open/Closed Principle in Architecture
Software entities should be open for extension but closed for modification. At the architecture level, this means: new features should be addable without modifying core system code. The system provides well-defined extension points where new behavior plugs in.

### Predict Variation, Don't Predict Features
You can't predict which features will be needed. But you CAN predict which dimensions of the system will vary:
- **Business rules** vary by customer, region, or plan → Make rules configurable or pluggable
- **Data sources** change over time → Abstract behind repository interfaces
- **External integrations** get added and swapped → Use adapter pattern
- **UI components** get added frequently → Use component registry
- **Workflows** differ by context → Use pipeline/middleware pattern

Design extension points along these variation axes, not around speculative features.

### The Rule of Three
Don't create an abstraction until you have three concrete examples. One example is too few to understand the pattern. Two might be coincidence. Three reveals the actual axis of variation. Until you have three examples, use concrete implementations. When the third case arrives, refactor to extract the abstraction.

---

## 2. Extension Point Patterns

### Strategy Pattern (Swappable Behavior)
Define an interface for a family of algorithms. Let implementations be swapped at runtime.

```
Interface: PaymentProcessor
  method: processPayment(amount, currency) → Result

Implementations:
  StripeProcessor implements PaymentProcessor
  PayPalProcessor implements PaymentProcessor
  BraintreeProcessor implements PaymentProcessor

Usage:
  processor = resolve(PaymentProcessor)  // determined by config
  result = processor.processPayment(100, "USD")
```

**When to Use**: When you have a well-defined operation that can be performed by different implementations. Payment processing, notification delivery, storage backends, authentication providers.

### Middleware / Pipeline Pattern (Composable Processing)
Chain handlers that each process a request and pass it to the next handler. Each middleware can modify the request, modify the response, short-circuit the pipeline, or perform side effects.

```
Request → [Logging] → [Auth] → [RateLimit] → [Validation] → [Handler] → Response
```

**When to Use**: HTTP request processing, data transformation pipelines, event processing. When you need cross-cutting concerns that apply to many operations.

**Implementation Tips**:
- Middleware order matters — put auth before business logic, logging before everything
- Allow middleware to be registered globally or per-route/per-operation
- Make middleware composable — each middleware should work independently

### Observer / Event Hook Pattern (Reactive Extensions)
The system emits events at key lifecycle points. Extensions subscribe to events and react.

```
System Events:
  - user.created
  - order.placed
  - payment.completed
  - subscription.cancelled

Extension registration:
  on("user.created", sendWelcomeEmail)
  on("user.created", createDefaultPreferences)
  on("user.created", notifyAnalytics)
  on("order.placed", reserveInventory)
  on("order.placed", sendConfirmationEmail)
```

**When to Use**: When the core system shouldn't know about all the things that happen in response to its actions. When you want loose coupling between the core and extensions.

**Implementation Tips**:
- Events should be descriptive facts ("UserCreated"), not commands ("SendEmail")
- Include all relevant data in the event payload (avoid forcing subscribers to call back)
- Handle subscriber failures gracefully (one failed subscriber shouldn't block others)
- Document all available events as your extension API

### Decorator Pattern (Enhanced Behavior)
Wrap an existing component to add behavior without modifying it.

```
Base: UserRepository.findById(id) → User

Decorated:
  CachingUserRepository(inner: UserRepository)
    findById(id):
      cached = cache.get(id)
      if cached: return cached
      user = inner.findById(id)
      cache.set(id, user)
      return user

  AuditingUserRepository(inner: UserRepository)
    findById(id):
      log("User lookup", id)
      return inner.findById(id)

Composed:
  repo = AuditingUserRepository(CachingUserRepository(DatabaseUserRepository()))
```

**When to Use**: When you need to add cross-cutting behavior (caching, logging, retry, metrics) to existing components without modifying them.

---

## 3. Plugin Architecture

### Core System + Plugins
The core system provides base functionality and extension points. Plugins are self-contained modules that add capabilities by hooking into these extension points.

```
Core System:
  ├── Extension Registry (discovers and manages plugins)
  ├── Extension Points (well-defined interfaces)
  │   ├── DataSourceProvider
  │   ├── AuthenticationMethod  
  │   ├── NotificationChannel
  │   ├── ReportGenerator
  │   └── WebhookHandler
  └── Core Services (base functionality)

Plugins:
  ├── plugin-slack-notifications (implements NotificationChannel)
  ├── plugin-salesforce-sync (implements DataSourceProvider)
  ├── plugin-sso-okta (implements AuthenticationMethod)
  └── plugin-pdf-reports (implements ReportGenerator)
```

### Plugin Design Rules

1. **Plugins depend on core interfaces, never on other plugins.** If two plugins need to interact, they communicate through the core system's event bus.

2. **Core never depends on plugins.** The system must function without any plugins loaded.

3. **Plugins are isolated.** A failing plugin must not crash the core system. Wrap plugin execution in try/catch with graceful degradation.

4. **Plugins are self-describing.** Each plugin declares its name, version, required extension points, and configuration schema.

5. **Plugin lifecycle is managed by the core.** The core controls when plugins are loaded, initialized, and destroyed.

### Plugin Discovery Patterns

**Registry-based**: Plugins register themselves with a central registry at startup.
```json
{
  "name": "slack-notifications",
  "version": "1.2.0",
  "implements": ["NotificationChannel"],
  "config_schema": {
    "webhook_url": { "type": "string", "required": true },
    "channel": { "type": "string", "default": "#general" }
  }
}
```

**Convention-based**: Plugins are discovered by scanning a directory or package path.
```
plugins/
  ├── slack-notifications/
  │   ├── manifest.json
  │   └── index.ts
  ├── pdf-reports/
  │   ├── manifest.json
  │   └── index.ts
```

**Configuration-based**: Enabled plugins are listed in system configuration.
```yaml
plugins:
  - name: slack-notifications
    enabled: true
    config:
      webhook_url: ${SLACK_WEBHOOK_URL}
```

---

## 4. API Versioning Strategy

### Rule: APIs Are Contracts
Once published, an API version is a promise. Clients depend on it. Breaking changes break trust and break clients.

### Versioning Approaches

**URL Path Versioning** (Recommended for external APIs):
```
/api/v1/users
/api/v2/users
```
- Most explicit and discoverable
- Easy to route to different service versions
- Slight URL pollution

**Header Versioning**:
```
Accept: application/vnd.myapp.v2+json
```
- Cleaner URLs
- Less discoverable
- Harder to test in a browser

### Evolution Rules

**Safe (non-breaking) changes** — do these freely:
- Adding new endpoints
- Adding optional fields to request/response
- Adding new enum values (if clients handle unknown values)
- Relaxing validation (accepting wider input range)
- Adding new HTTP methods to existing endpoints

**Unsafe (breaking) changes** — require a new version:
- Removing or renaming fields
- Changing field types
- Removing endpoints
- Changing authentication mechanisms
- Tightening validation (rejecting previously valid input)
- Changing response structure

### Deprecation Process
1. Announce deprecation (documentation, API response headers, email)
2. Add `Sunset` header with date: `Sunset: Sat, 01 Mar 2026 00:00:00 GMT`
3. Monitor usage of deprecated version
4. Provide migration guide
5. Give minimum 6 months notice for external APIs
6. Remove only after confirmed zero traffic (or after the sunset date)

---

## 5. Configuration-Driven Behavior

### When to Use Configuration vs Code
| Scenario | Approach |
|---|---|
| Behavior varies by environment (dev/staging/prod) | Environment config |
| Behavior varies by customer/tenant | Tenant configuration |
| Behavior is A/B tested | Feature flags |
| Behavior changes frequently without deploys | Runtime configuration |
| Behavior is complex logic with many branches | Code (don't put business logic in config) |

### Feature Flags
Feature flags allow enabling/disabling features without deployment. They're essential for progressive rollout, A/B testing, and instant rollback.

**Implementation Tiers**:
- **Simple**: Boolean flags in config file (good for Stage 0–1)
- **Intermediate**: Database-backed flags with admin UI (good for Stage 1–2)
- **Advanced**: Third-party service (LaunchDarkly, Unleash, Flagsmith) with targeting rules, analytics, and gradual rollout (Stage 2+)

**Lifecycle Management**:
- Every feature flag has an owner and an expiration date
- Temporary flags (for rollout) should be removed within 30 days of full rollout
- Permanent flags (for configuration) should be documented
- Review stale flags quarterly — dead flags are technical debt

---

## 6. Composability Patterns

### Design for Composition
Modern systems succeed by composing well-defined building blocks, not by building monolithic features.

**Composability without extensibility** creates rigid assemblies — you can rearrange pieces but can't modify their behavior.
**Extensibility without composability** creates monolithic systems — you can add features but can't isolate or replace them.

Design for both: compose your architecture from discrete services/modules, then make each one extensible through defined interfaces.

### Interface Segregation
Don't force consumers to depend on interfaces they don't use. Split large interfaces into focused ones.

```
Bad:  UserService { create, read, update, delete, search, export, import, sendNotification }

Good: UserRepository { create, read, update, delete }
      UserSearch { search, filter }
      UserExport { exportCSV, exportPDF }
      UserNotification { sendNotification }
```

### Dependency Injection
Provide dependencies to components rather than having components create their own dependencies. This makes components testable, composable, and swappable.

```
Bad:  class OrderService { constructor() { this.db = new PostgresDB() } }

Good: class OrderService { constructor(db: Database) { this.db = db } }
      // In production: new OrderService(new PostgresDB())
      // In tests: new OrderService(new InMemoryDB())
```

---

## 7. Migration & Backward Compatibility

### Database Migration Strategy

**Additive-Only Migrations** (safe, no downtime):
- Add new columns (with defaults)
- Add new tables
- Add new indexes (use `CREATE INDEX CONCURRENTLY` in PostgreSQL)

**Destructive Migrations** (require careful planning):
- Removing columns → First stop writing to the column, deploy, then remove in a later migration
- Renaming columns → Add new column, dual-write, migrate data, switch reads, drop old column
- Changing types → Similar multi-step process

### The Expand-Contract Pattern
For any breaking schema change:
1. **Expand**: Add the new structure alongside the old one
2. **Migrate**: Copy/transform data from old to new
3. **Switch**: Update application to use new structure
4. **Contract**: Remove old structure after confirming zero usage

This pattern applies to databases, APIs, configuration formats, and message schemas.

### Schema Evolution for Events/Messages
Use a schema registry (Confluent Schema Registry, AWS Glue Schema Registry) to manage event schema versions. Rules:
- Always add fields, never remove or rename
- New fields must have defaults (so old consumers can ignore them)
- Use schema compatibility checks in CI (backward, forward, or full compatibility)
- Version schemas independently from service versions
