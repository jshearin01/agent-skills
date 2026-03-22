---
name: llm-agent-architect
description: "Expert LLM workflow and agent platform architect skill for designing scalable, production-grade agentic AI systems using API-based LLMs. Use this skill whenever you are designing, building, or reviewing any LLM agent system, workflow platform, or multi-agent architecture. Trigger on requests involving agent system design, multi-agent coordination, orchestrator/worker patterns, RAG pipeline architecture, tool/function calling design, agent memory and state management, LLM observability and evaluation pipelines, context window management, agentic workflow decomposition, or any system where LLMs call other LLMs. Also trigger when asked to build a copilot, assistant, agent, pipeline, or workflow of any kind. This skill encodes 2025-era best practices distilled from Anthropic, OpenAI, Microsoft, AWS, and Google engineering teams."
---

# LLM Agent Platform Architect

A comprehensive skill for designing scalable, production-grade LLM agent systems and workflow platforms. Covers the five pillars of modern agentic AI: multi-agent coordination, RAG pipelines, tool/function calling, memory & state, and observability & evals.

## Reference Files

Load these when working on the corresponding pillar. Each is self-contained.

| File | When to Read |
|------|-------------|
| `references/multi-agent-patterns.md` | Designing orchestration topology, routing, agent roles |
| `references/rag-pipeline.md` | Building retrieval-augmented generation systems |
| `references/tool-calling.md` | Designing tool contracts, schemas, and execution loops |
| `references/memory-state.md` | Managing context windows, short/long-term memory |
| `references/observability-evals.md` | Tracing, metrics, evals, LLM-as-judge |

---

## Core Principles (Always Apply)

Before reading any reference file, internalize these platform-wide invariants:

### 1. API-First Reality
All LLMs are accessed via API. Every design decision carries a **token cost** and **latency cost**. Design with the assumption that LLM calls are expensive I/O operations, not cheap function calls.

- Treat each LLM call like a database query: minimize round-trips, batch where possible, cache aggressively.
- Token budget is the primary constraint. Design prompts, context windows, and memory schemas to fit within it efficiently.
- Default to smaller/cheaper models for sub-agents; reserve large models for orchestration and complex reasoning.

### 2. Stateless LLMs, Stateful Systems
LLMs have no memory between calls. All state must be explicitly managed externally and injected into context.

- Every agent run is a fresh LLM call. State lives in databases, queues, and external stores — not in the model.
- Context window = working memory. Everything not in the context window does not exist to the model.
- Design state handoffs as versioned, schema-validated contracts (not free-text).

### 3. Modularity Over Monoliths
Never build a single mega-agent that does everything. Decompose by responsibility.

- Each agent should have a single, well-defined role with constrained tool access.
- Smaller, specialized agents are cheaper, faster, easier to debug, and easier to eval individually.
- Use composition (agents calling agents via tools or handoffs) to handle complexity.

### 4. Fail Safely, Recover Gracefully
LLM outputs are non-deterministic. Every output is potentially wrong or malformed.

- Validate all structured outputs at the boundary (use JSON Schema, Pydantic, or equivalent).
- Implement retry logic with exponential backoff + jitter for transient failures.
- Design fallback paths for every critical step. Never assume the LLM will produce valid output.
- Log everything. You will need traces to debug production failures.

### 5. Evaluate Continuously
You cannot know if your agent is working correctly without systematic evaluation.

- Ship observability (traces, metrics) before shipping features.
- Build eval datasets from production traces early.
- Use LLM-as-judge for quality metrics that can't be checked with code.

---

## Architecture Decision Flow

Use this to determine which reference files to load and what patterns to apply:

```
START: What are you building?
│
├── Need multiple LLMs working together?
│   └── → Read: references/multi-agent-patterns.md
│       Patterns: orchestrator-worker, hierarchical, swarm, handoff/routing
│
├── Need to ground responses in external documents or data?
│   └── → Read: references/rag-pipeline.md
│       Patterns: ingestion, chunking, embedding, retrieval, reranking
│
├── Need the LLM to call APIs, run code, or use external services?
│   └── → Read: references/tool-calling.md
│       Patterns: tool schemas, execution loops, structured outputs, error handling
│
├── Need the agent to remember across sessions or long tasks?
│   └── → Read: references/memory-state.md
│       Patterns: working memory, episodic/semantic/procedural memory, STM/LTM flow
│
└── Need to monitor, debug, or improve the system in production?
    └── → Read: references/observability-evals.md
        Patterns: OTel tracing, metrics, eval datasets, LLM-as-judge
```

Most real systems need multiple pillars. Load all relevant reference files.

---

## Platform Layers (Always Design These)

Every LLM platform, regardless of complexity, needs these layers:

```
┌─────────────────────────────────────────────────────┐
│                    API Gateway Layer                 │  ← Rate limiting, auth, routing
├─────────────────────────────────────────────────────┤
│              Orchestration / Workflow Layer          │  ← Agent coordination, task decomp
├─────────────────────────────────────────────────────┤
│                  Agent Execution Layer               │  ← Individual agent logic + tools
├─────────────────────────────────────────────────────┤
│               Memory & Context Layer                 │  ← State, history, retrieval
├─────────────────────────────────────────────────────┤
│            Model API Layer (External LLMs)           │  ← Anthropic, OpenAI, Google APIs
├─────────────────────────────────────────────────────┤
│              Observability & Eval Layer              │  ← Tracing, metrics, evals
└─────────────────────────────────────────────────────┘
```

Design each layer independently. Avoid coupling them directly — use well-defined interfaces between layers.

---

## Complexity vs. Capability Trade-offs

Use the simplest architecture that solves the problem:

| Complexity | Pattern | Use When |
|-----------|---------|----------|
| Low | Single agent + tools | One well-defined task, deterministic workflow |
| Medium | Linear chain of agents | Sequential steps with clear dependencies |
| Medium-High | Orchestrator + parallel workers | Independent subtasks that can run concurrently |
| High | Hierarchical multi-agent | Multi-domain tasks requiring specialist coordination |
| Very High | Dynamic agent network | Emergent, open-ended tasks with unknown structure |

**Anti-pattern**: Don't add orchestration complexity you don't need. Every layer of indirection adds latency, cost, and debugging surface area.

---

## Quick Reference: Critical Limits & Numbers

Keep these numbers in mind across all design decisions:

| Constraint | Typical Value | Design Implication |
|-----------|--------------|-------------------|
| LLM context window | 128K–200K tokens | Must manage what goes in; don't assume you can fit everything |
| Context cliff | ~2,500 tokens (response quality drops) | Keep individual retrieved chunks small |
| Optimal chunk size (RAG) | 400–512 tokens w/ 10-20% overlap | Start here, tune from metrics |
| Reranking latency cost | 50–100ms | Worth it for precision; skip for latency-critical paths |
| Max tools per agent | ~15–20 (practical) | More than this degrades tool selection accuracy |
| Handoff payload | As small as possible | Only pass what the next agent strictly needs |
| Parallel sub-agents | 3–10 (typical) | Beyond ~10, coordination overhead dominates |

---

## Output Checklist

When designing or reviewing an LLM agent system, verify:

- [ ] Each agent has a single, well-defined role with constrained tool access
- [ ] All agent-to-agent handoffs use validated, versioned schemas
- [ ] Retry and fallback logic exists at every LLM call boundary
- [ ] Context window budget is explicitly managed (not assumed to fit)
- [ ] State is stored externally; no reliance on in-context persistence
- [ ] Tracing/observability is instrumented at the workflow level
- [ ] At least one eval dimension is defined per agent (correctness, groundedness, latency, cost)
- [ ] Human-in-the-loop escalation paths exist for high-stakes decisions
- [ ] Parallel vs. sequential execution decisions are explicit and justified
- [ ] RAG retrieval is validated (not assumed correct) before generation
