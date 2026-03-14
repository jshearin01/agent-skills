# Scaling & Performance Reference

## Table of Contents
1. The Database Scaling Ladder
2. Caching Strategy Guide
3. Performance Budgets & Monitoring
4. Async Processing Patterns
5. Sharding Strategies
6. Mass Scale Patterns
7. Cost Optimization

---

## 1. The Database Scaling Ladder

Database scaling is almost always the first bottleneck. Attack these steps in order — each gives you 2–10x headroom before needing the next step.

### Step 1: Query Optimization (10–100x improvement possible)
This is the highest-ROI scaling activity at any stage. Do this BEFORE adding infrastructure.

- **Index review**: Every WHERE clause, JOIN condition, and ORDER BY should have a supporting index. Use `EXPLAIN ANALYZE` to verify.
- **Eliminate N+1 queries**: The #1 ORM performance killer. If you fetch a list of items and then query for each item's relationships individually, you have an N+1. Use eager loading / joins.
- **Avoid unnecessary JOINs**: OpenAI found that a single 12-table join was responsible for multiple high-severity outages. Break complex joins into application-level composition.
- **Review ORM-generated SQL**: ORMs generate SQL you didn't write. Review it. Log slow queries and fix them.
- **Set statement timeouts**: Prevent runaway queries from consuming all database resources. PostgreSQL: `statement_timeout`. MySQL: `max_execution_time`.
- **Configure idle connection timeouts**: Long-running idle transactions block autovacuum and cause bloat. Set `idle_in_transaction_session_timeout` in PostgreSQL.

### Step 2: Connection Pooling (2–5x improvement)
Creating a new database connection for every request is expensive (TCP handshake, TLS negotiation, authentication). Connection pooling maintains a pool of reusable connections.

- **PostgreSQL**: Use PgBouncer in transaction mode for maximum efficiency
- **MySQL**: Use ProxySQL or built-in connection pooling
- **Application-level**: Most ORMs and database drivers support connection pooling. Configure min/max pool size based on load testing.

**Rule of thumb**: Pool size = (2 × CPU cores) + number of disks. Going higher usually hurts performance due to contention.

### Step 3: Read Replicas (2–10x read capacity)
Most applications are read-heavy (10:1 or higher read-to-write ratio). Offload reads to replicas.

- Route write queries to the primary, read queries to replicas
- Accept replication lag (typically milliseconds to seconds)
- Implement read-after-write consistency where needed: after a user writes, route THEIR reads to primary briefly
- Start with 1–2 replicas, add more as needed
- Monitor replication lag — if it grows, investigate replica capacity or network issues

### Step 4: Caching (10–100x read throughput)
See § Caching Strategy Guide below for detailed patterns.

### Step 5: Functional Partitioning
Split different workloads into different databases. The users database doesn't need to be on the same instance as the analytics database.

- Align partitioning with service/module boundaries
- Each database can be scaled independently
- Eliminates contention between different workload types

### Step 6: Sharding (near-unlimited horizontal scale)
Split a single logical database across multiple physical databases based on a shard key. See § Sharding Strategies below.

---

## 2. Caching Strategy Guide

### When to Cache
- Data that is read frequently but changes infrequently
- Expensive computations that produce the same result for the same input
- External API responses that are unlikely to change within a window
- Session data and user preferences

### When NOT to Cache
- Data that must be strongly consistent (financial transactions, inventory counts)
- Data that changes with every request
- Large data that would exceed cache memory without proportional benefit

### Caching Patterns

**Cache-Aside (Lazy Loading)**
```
1. Application checks cache
2. If cache hit → return cached data
3. If cache miss → query database → store result in cache → return data
```
- Most common pattern. Simple to implement.
- Risk: cache miss storms after cache flush or cold start
- Mitigation: staggered TTLs, cache warming on deploy

**Write-Through**
```
1. Application writes to cache AND database simultaneously
2. Reads always come from cache
```
- Ensures cache is always consistent with database
- Higher write latency (writing to two places)
- Good for data that is written and then immediately read

**Write-Behind (Write-Back)**
```
1. Application writes to cache
2. Cache asynchronously writes to database
```
- Lowest write latency
- Risk of data loss if cache fails before database write
- Good for high-write workloads where some data loss is tolerable (analytics, counters)

### Cache Hierarchy
```
L1: In-Process Cache (fastest, smallest, per-instance)
    → Application memory. ~microsecond latency. 
    → Use for: config, feature flags, very hot data
    → Risk: inconsistency across instances. Use short TTL or pub/sub invalidation.

L2: Distributed Cache (fast, larger, shared across instances)
    → Redis or Memcached. ~millisecond latency.
    → Use for: session data, computed results, API responses
    → This is your primary caching layer for most applications.

L3: CDN Cache (edge, largest, geographically distributed)
    → CloudFront, Cloudflare, Fastly. ~10ms latency from edge.
    → Use for: static assets, public API responses, pre-rendered pages
```

### Cache Invalidation
"There are only two hard things in computer science: cache invalidation and naming things." — Phil Karlton

- **TTL-based**: Set an expiration time. Simplest approach. Accept stale data within the TTL window.
- **Event-based**: Invalidate cache when the underlying data changes. More complex but more accurate.
- **Version-based**: Include a version number in cache keys. Increment version on data change.

**Recommendation**: Start with TTL-based (it covers 90% of cases). Add event-based invalidation only for data where staleness is unacceptable.

### Redis Best Practices
- Set maxmemory and eviction policy (`allkeys-lru` for caches, `noeviction` for queues)
- Use Redis Cluster for horizontal scaling beyond single-node capacity
- Monitor memory usage, hit rate, and connection count
- Don't use Redis as a primary database — it's a cache and a data structure store
- Set TTL on ALL cache keys (avoid unbounded cache growth)
- Use consistent hashing for client-side sharding
- Target 95%+ cache hit ratio; investigate if below 90%

---

## 3. Performance Budgets & Monitoring

### Define Budgets Upfront
Every system should have explicit performance budgets:

| Metric | Acceptable | Warning | Critical |
|---|---|---|---|
| API Response p50 | < 100ms | < 250ms | > 500ms |
| API Response p95 | < 250ms | < 500ms | > 1s |
| API Response p99 | < 500ms | < 1s | > 2s |
| Error Rate | < 0.1% | < 1% | > 5% |
| Database Query | < 50ms | < 200ms | > 1s |
| Page Load (TTI) | < 2s | < 4s | > 6s |

These are starting points — adjust for your specific use case. Real-time trading has different requirements than a content management system.

### The Four Golden Signals (Google SRE)
Monitor these for every service:

1. **Latency**: How long requests take. Track p50, p95, p99. Distinguish between successful and failed requests.
2. **Traffic**: How much demand is on your system. Requests per second, concurrent users.
3. **Errors**: Rate of failed requests. Include both explicit errors (500s) and implicit errors (wrong results, timeouts).
4. **Saturation**: How "full" your system is. CPU, memory, disk, connection pool utilization. Alert before you hit 100%.

### USE Method (for infrastructure)
For every resource (CPU, memory, disk, network):
- **U**tilization: % of resource in use
- **S**aturation: Work queued because the resource is busy
- **E**rrors: Error events on the resource

### Observability Stack Recommendation
```
Metrics:    Prometheus + Grafana (or cloud-native: CloudWatch, Stackdriver)
Logging:    Structured JSON logs → Loki or ELK (Elasticsearch + Logstash + Kibana)
Tracing:    OpenTelemetry → Jaeger or Tempo
Alerting:   PagerDuty or Opsgenie, triggered by Prometheus/Grafana alerts
Profiling:  Continuous profiling (Pyroscope, Parca) for production performance analysis
```

### Alerting Philosophy
- Alert on SLO violations, not on individual metric thresholds
- Use multiple severity levels (page for critical, ticket for warning)
- Every alert should be actionable — if there's nothing to do, it's not an alert, it's noise
- Review and prune alerts quarterly — alert fatigue is deadly

---

## 4. Async Processing Patterns

### When to Go Async
Move work off the critical path when:
- The user doesn't need the result immediately (email sending, report generation)
- The work is computationally expensive (image processing, data aggregation)
- The work involves unreliable external services (third-party APIs)
- The work can be retried if it fails (payment processing, webhook delivery)

### Pattern: Task Queue
```
[Web Server] → enqueue job → [Queue (Redis/SQS/RabbitMQ)] → [Worker] → process
                                                                ↓
                                                     [Dead Letter Queue] (for failed jobs)
```

**Best Practices**:
- Make workers idempotent (processing the same job twice produces the same result)
- Set reasonable timeouts (don't let workers hang forever)
- Implement exponential backoff for retries (1s, 2s, 4s, 8s...)
- Use a dead letter queue for jobs that fail repeatedly
- Monitor queue depth — growing queues mean workers can't keep up
- Include job metadata (created_at, attempt_count, correlation_id)

### Pattern: Event-Driven Processing
```
[Service A] → publish event → [Event Bus (Kafka/SNS)] → [Service B]
                                                       → [Service C]
                                                       → [Service D]
```

Fan-out: one event triggers multiple consumers. Each consumer processes at its own pace.

### Pattern: Saga (Distributed Transaction)
When an operation spans multiple services and you need all-or-nothing semantics:

**Choreography** (event-based):
```
OrderService: create order → emit OrderCreated
PaymentService: hear OrderCreated → charge card → emit PaymentCompleted
InventoryService: hear PaymentCompleted → reserve stock → emit StockReserved
OrderService: hear StockReserved → confirm order
```
Each service listens for events and acts. Compensation events handle failures (PaymentFailed → cancel order).

**Orchestration** (coordinator-based):
```
SagaOrchestrator:
  1. Tell OrderService: create order
  2. Tell PaymentService: charge card
  3. Tell InventoryService: reserve stock
  4. If any step fails: call compensating actions in reverse order
```
A central orchestrator directs the workflow. Easier to understand and debug, but the orchestrator is a single point of control.

---

## 5. Sharding Strategies

### When to Shard
Only when you've exhausted steps 1–5 of the database scaling ladder. Sharding introduces significant complexity — it's the last resort for relational databases.

### Shard Key Selection
The shard key determines how data is distributed. This is a **Type 1 decision** — very hard to change later.

**Good shard keys**:
- Have high cardinality (many unique values)
- Distribute data evenly across shards
- Align with your most common query patterns (most queries should hit a single shard)
- Example: `tenant_id` for multi-tenant apps, `user_id` for user-centric apps

**Bad shard keys**:
- Low cardinality (status, category) — creates hotspots
- Monotonically increasing (auto-increment ID with range sharding) — all new data goes to one shard
- Unrelated to query patterns — forces cross-shard queries

### Sharding Approaches

**Hash Sharding**: `shard = hash(key) % num_shards`
- (+) Even distribution
- (-) Range queries span all shards
- (-) Adding shards requires redistribution (use consistent hashing to mitigate)

**Range Sharding**: `shard = lookup(key_range)`
- (+) Range queries are efficient (within a range)
- (-) Uneven distribution if data isn't uniform
- (-) Hotspots on the shard receiving new data

**Directory/Lookup Sharding**: Central lookup table maps keys to shards
- (+) Maximum flexibility in data placement
- (-) Lookup table is a single point of failure and potential bottleneck

**Geographic Sharding**: Data sharded by geographic region
- (+) Data locality for users (low latency)
- (+) Regulatory compliance (data residency)
- (-) Cross-region queries are expensive

### Modern Alternatives to Manual Sharding
Before implementing manual sharding, consider:
- **Vitess**: MySQL-compatible sharding middleware (used by YouTube, Slack)
- **Citus**: PostgreSQL extension for distributed tables
- **CockroachDB**: Distributed SQL with automatic sharding
- **PlanetScale**: Managed Vitess-based MySQL
- **Aurora/Spanner**: Cloud-native distributed databases

These handle shard management, rebalancing, and cross-shard queries — complexity you'd otherwise build yourself.

---

## 6. Mass Scale Patterns

### Load Shedding
When the system is overloaded, deliberately drop low-priority requests to protect high-priority ones.
```
if system_load > 90%:
    if request.priority == "low":
        return 503 Service Unavailable (Retry-After: 30)
    if request.priority == "medium" and system_load > 95%:
        return 503
    # High priority requests always proceed
```

### Back-Pressure
When a downstream service can't keep up, signal the upstream to slow down rather than buffering indefinitely (which leads to memory exhaustion and cascading failure).
- Use bounded queues (reject new items when full)
- Implement flow control in streaming protocols
- Return 429 or 503 with Retry-After headers

### Circuit Breaker
Prevent cascading failures by stopping calls to a failing service.
```
States: CLOSED (normal) → OPEN (failing, reject calls) → HALF-OPEN (test recovery)

CLOSED: Calls pass through. Track failure rate.
        If failure rate > threshold (e.g., 50% in last 10 calls) → OPEN

OPEN:   All calls immediately return fallback/error. No actual calls made.
        After timeout (e.g., 30s) → HALF-OPEN

HALF-OPEN: Allow a small number of test calls through.
           If they succeed → CLOSED
           If they fail → OPEN
```

### Bulkhead Pattern
Isolate failures by limiting the resources available to each component.
- Separate thread pools / connection pools per downstream dependency
- If the recommendation service connection pool is exhausted, it doesn't affect the checkout service's connections
- Container resource limits (CPU/memory) as infrastructure-level bulkheads

### Progressive Rollout
Never deploy to 100% of users at once at scale.
```
1. Deploy to canary (1% of traffic)
2. Monitor error rate, latency, business metrics for 15 minutes
3. Expand to 10%, monitor for 30 minutes
4. Expand to 50%, monitor for 1 hour
5. Full rollout
Automated rollback if error rate exceeds threshold at any step.
```

---

## 7. Cost Optimization

Architecture decisions at scale are directly visible in the infrastructure bill. Design for cost efficiency from the start.

### Principles
- **Right-size resources**: Don't provision for peak when you can auto-scale. Reserved instances for baseline, spot/preemptible for burst.
- **Hot/warm/cold data tiering**: Recent data in fast storage (SSD), historical data in cheap storage (S3, Glacier). This is the pattern OpenAI's ChatGPT team and many others use — hot data in PostgreSQL, cold data in S3 as Parquet files.
- **Avoid egress costs**: Data transfer between regions and out of cloud is expensive. Co-locate services that communicate frequently.
- **Cache aggressively**: A Redis cache hit costs ~1000x less than a database query at scale.
- **Use serverless for bursty workloads**: Lambda/Cloud Functions for infrequent, variable-load tasks. Don't use serverless for steady-state high-throughput (it becomes more expensive).
- **Monitor and alert on spend**: Set billing alerts at 50%, 80%, and 100% of budget. Review the bill monthly.
