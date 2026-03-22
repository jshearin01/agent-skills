# Multi-Agent Coordination Patterns

Reference file for `llm-agent-architect` skill. Read this when designing orchestration topology, agent roles, routing logic, and inter-agent communication.

---

## Pattern Overview

| Pattern | Control | Best For | Token Cost |
|---------|---------|----------|-----------|
| Orchestrator-Worker | Centralized | Complex multi-domain tasks with oversight | Medium |
| Hierarchical | Multi-level | Enterprise workflows, nested delegation | Medium-High |
| Sequential Chain | Linear | Pipeline tasks with clear step ordering | Low |
| Parallel Fan-Out | Distributed | Independent subtasks needing speed | Medium |
| Swarm (Decentralized) | Emergent | Open-ended research, creative tasks | High |
| Handoff / Routing | Dynamic | Domain routing, triage, specialization | Low-Medium |

---

## Pattern 1: Orchestrator-Worker (Recommended Default)

The orchestrator receives the top-level task, decomposes it, delegates to specialized workers, and synthesizes results.

**Structure:**
```
User Request
    │
    ▼
Orchestrator Agent
├── Decomposes task into subtasks
├── Delegates to Worker A (parallel) ──→ Result A
├── Delegates to Worker B (parallel) ──→ Result B
├── Delegates to Worker C (sequential after A) ──→ Result C
└── Synthesizes final output
```

**Design Rules:**
- The orchestrator should NOT execute tasks itself — only plan and synthesize.
- Workers should be given explicit scope: objective, output format, tool access, and boundaries.
- Scale effort to task complexity: embed scaling rules in the orchestrator's system prompt.
- Teach the orchestrator to detect task overlap and prevent duplicate work across workers.

**When workers should write to shared storage instead of returning to orchestrator:**
- Large outputs (>2K tokens) — bypass orchestrator to avoid context bloat
- File artifacts (reports, code) — write directly to a shared filesystem or store
- The orchestrator reads the reference, not the full content

**System prompt template for orchestrator:**
```
You are the orchestrating agent for [DOMAIN]. Your job is to:
1. Analyze the user's request and decompose it into discrete subtasks
2. Assign each subtask to the appropriate specialist agent
3. For independent subtasks, dispatch workers in parallel
4. For dependent subtasks, enforce sequential ordering
5. Validate worker outputs meet quality criteria before synthesis
6. Synthesize a final, coherent response

Worker agents available: [LIST WITH CAPABILITIES]
Output format for worker invocation: [SCHEMA]
```

---

## Pattern 2: Hierarchical Multi-Level

Extends orchestrator-worker with multiple delegation levels. A root orchestrator delegates to sub-orchestrators, who further delegate to leaf workers.

**Use when:**
- Tasks span multiple distinct domains, each complex enough to need sub-orchestration
- You need clear audit trails across organizational boundaries
- Tasks have both strategic planning and tactical execution phases

**Pitfall:** Deep hierarchies amplify latency and cost exponentially. Limit to 2–3 levels maximum. Prefer flat orchestrator-worker over deep hierarchies unless complexity demands it.

---

## Pattern 3: Sequential Chain (Pipeline)

Each agent's output becomes the next agent's input. No parallel execution.

```
Input → Agent A → Agent B → Agent C → Output
```

**Use when:** Steps have strict data dependencies and ordering is deterministic.

**Implementation:**
```python
# Pseudo-code for sequential chain
context = {"task": user_input}
for agent in [research_agent, outline_agent, writer_agent, critic_agent]:
    result = agent.run(context)
    context = merge(context, result)  # Accumulate state
final_output = context["final_draft"]
```

**Key concern:** Context accumulates. After step 3–4, you may hit context limits. Use summarization or selective context passing between steps.

---

## Pattern 4: Parallel Fan-Out + Merge

Dispatch multiple workers simultaneously for independent subtasks, then merge results.

```
                    ┌→ Worker A (domain 1) ─┐
Orchestrator ──── ──├→ Worker B (domain 2) ─┼──→ Merge Agent → Output
                    └→ Worker C (domain 3) ─┘
```

**When to parallelize:** Tasks span independent domains with no data dependency between them.

**When NOT to parallelize:** Tasks where Worker B needs Worker A's output first; tasks so small that coordination overhead dominates.

**Routing rules (embed in orchestrator's CLAUDE.md or system prompt):**
```
## Parallel Dispatch Rules
- Dispatch parallel agents when subtasks are domain-independent
- Domains: [frontend, backend, database] → always parallel
- Sequential when: Output of step N is input to step N+1
- Group micro-tasks: Don't spawn 10 agents for 10 small tasks; group by domain
```

---

## Pattern 5: Swarm (Decentralized)

No central controller. Agents communicate via shared memory/message space. Intelligence emerges from collective interaction.

**Use when:** Open-ended research, creative tasks, adversarial debate, diverse perspectives needed.

**Caution:** Hard to debug, high token cost, unpredictable depth. Use timeout controls. Only consider when centralized orchestration demonstrably fails.

**Implementation checklist:**
- [ ] Shared memory store (vector DB or key-value) accessible to all agents
- [ ] Convergence criteria defined (when does the swarm stop?)
- [ ] Timeout controls to prevent infinite loops
- [ ] Output aggregation strategy (voting, merge, summarization)

---

## Pattern 6: Handoff / Routing

A triage agent (or the orchestrator) routes tasks to the most appropriate specialist based on content analysis. Only one agent at a time owns the task.

**Use when:**
- The right agent depends on the content of the request (not known upfront)
- Tasks require domain specialization that emerges mid-workflow
- You want to prevent infinite handoff loops (enforce max handoff depth)

**Routing strategies:**
```
Strategy A: LLM-based routing (flexible, slower)
  → Triage agent reads request, decides which specialist owns it
  → Best when routing logic is complex/ambiguous

Strategy B: Classifier-based routing (fast, cheaper)
  → Small classifier model or embedding similarity decides routing
  → Best for high-volume, well-defined routing decisions

Strategy C: Rule-based routing (deterministic, cheapest)
  → If request contains [keywords/patterns] → route to [agent]
  → Best for known, stable task types
```

**Combining patterns:** A triage agent can hand off to a specialist, and that specialist can use sub-agents as tools for narrow subtasks. This is the recommended pattern for customer-facing agent systems.

---

## Inter-Agent Communication: Schema Standards

Free-text handoffs are the #1 source of context loss and bugs. Treat agent-to-agent communication like a versioned API.

**Handoff payload schema (required fields):**
```json
{
  "schemaVersion": "1.0.0",
  "traceId": "uuid-here",
  "taskId": "task-identifier",
  "role": "AgentName",
  "objective": "Clear statement of what this agent should accomplish",
  "outputFormat": "Description or JSON schema of expected output",
  "context": {
    "relevant_prior_work": "Summary only, not full history",
    "tool_state": {},
    "constraints": []
  },
  "outputContract": {
    "requiredFields": ["field1", "field2"],
    "qualityThreshold": {}
  }
}
```

**Validation rules:**
1. Validate incoming payload schema before processing (fail fast)
2. On validation failure: retry with repair prompt OR escalate to human review
3. Log both invalid payloads and validator errors for forensic analysis
4. Use Pydantic or JSON Schema for runtime validation

---

## Context Window Management in Multi-Agent Systems

The context window is the agent's entire reality. Manage it deliberately.

**The "game of telephone" problem:** Each handoff risks compressing, losing, or distorting information. Mitigate by:
- Having sub-agents write large outputs directly to external storage; pass a reference, not the content
- Summarizing completed phases before spawning new agents
- Maintaining a structured "research plan" or "task state" document that any agent can retrieve

**Context budget allocation:**
```
System prompt:          ~1,000–3,000 tokens (fixed)
Task description:       ~500–1,000 tokens
Relevant memory/RAG:    ~2,000–5,000 tokens
Tool outputs:           ~1,000–3,000 tokens
Conversation history:   ~1,000–2,000 tokens (summarize aggressively)
Output buffer:          ~1,000–2,000 tokens
─────────────────────────────────────────
Total budget:           ~128K tokens (manage to ~20K for safety)
```

**Context overflow strategy:**
- Spawn fresh sub-agents with clean context windows for new phases
- Pass only the essential "handoff" document to the new agent
- Store full history in external memory; retrieve selectively

---

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Mega-agent with 30+ tools | Poor tool selection, high token cost | Split into specialized agents |
| Free-text handoffs | Context loss, parsing errors | Use validated JSON schemas |
| Unlimited handoff depth | Infinite loops, runaway cost | Enforce max_depth and timeout |
| All-sequential pipelines | Slow, doesn't use parallelism | Identify and parallelize independent tasks |
| Orchestrator executing tasks | Context bloat, unclear responsibility | Orchestrator plans only; workers execute |
| Vague worker invocations | Duplicate work, missed coverage | Include scope, format, tool access, and boundaries |
| Over-parallelizing | Coordination overhead dominates | Group micro-tasks; 3–7 workers is typical |
