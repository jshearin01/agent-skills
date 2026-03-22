# Memory & State Management

Reference file for `llm-agent-architect` skill. Read this when designing how agents remember information across steps, sessions, or agent boundaries.

---

## The Core Challenge

LLMs are stateless. Every API call starts from zero. The context window is the agent's only native "memory" — everything outside it doesn't exist to the model. All persistence must be implemented by the system, not by the LLM.

```
What the LLM sees:           What actually needs to persist:
┌────────────────────┐       ┌─────────────────────────────────┐
│ System prompt      │       │ User preferences (cross-session) │
│ Injected memories  │       │ Task state & progress            │
│ Current messages   │  ←──  │ Long conversation history        │
│ Retrieved context  │       │ Learned patterns & skills        │
│ Tool outputs       │       │ Agent-to-agent handoff state     │
└────────────────────┘       └─────────────────────────────────┘
   Context Window                   External Storage
```

---

## Memory Taxonomy

### Short-Term Memory (STM) / Working Memory
- **What:** The active context window during a single agent run
- **Where:** The LLM's input prompt itself
- **Lifetime:** Single conversation or task session
- **Size limit:** Context window size (~128K–200K tokens)
- **Management:** Summarization, filtering, selective retention

### Long-Term Memory (LTM)
Three biologically-inspired types:

| Type | What It Stores | Example | Storage |
|------|---------------|---------|---------|
| **Episodic** | Specific past interactions and events | "Last time user X asked about Y, we resolved it by Z" | Vector DB (conversation summaries) |
| **Semantic** | General facts, world knowledge, domain info | User preferences, organizational policies, domain ontologies | Vector DB + structured DB |
| **Procedural** | How to do things, skills, SOPs | Agent instructions, validated workflows, successful patterns | System prompts, tool schemas, retrieval |

---

## Memory Architecture for Production Systems

```
                        ┌─────────────────┐
                        │  Context Window  │  ← Working Memory (active)
                        │  (STM)          │
                        └────────┬────────┘
                                 │ inject/retrieve
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
    │  Recall Store│   │ Archival     │   │  Procedural      │
    │  (Episodic)  │   │ Store        │   │  Memory          │
    │  Recent      │   │ (Semantic)   │   │  (System prompts │
    │  conversations│   │ Long-term    │   │  + tool schemas) │
    │  + summaries │   │ knowledge    │   └──────────────────┘
    └──────────────┘   └──────────────┘
    Key-value or        Vector DB           Versioned files
    structured DB       with metadata       or prompt registry
```

---

## Memory Operations (The Core Cycle)

Every memory system needs these five operations:

### 1. Encode (Store)
Decide what's worth remembering and how to represent it.
```python
# After conversation, extract memorable facts
memories = llm.extract_memories(
    conversation=recent_messages,
    instructions="Extract key facts, decisions, user preferences, and unresolved questions."
)
memory_store.insert(memories, user_id=user_id)
```

### 2. Retrieve
Surface relevant memories at query time.
```python
# Retrieval combines: semantic similarity + recency + importance
relevant = memory_store.query(
    query=current_message,
    user_id=user_id,
    top_k=5,
    recency_weight=0.3,
    importance_weight=0.3,
    similarity_weight=0.4
)
```

### 3. Update / Consolidate
Merge new experiences with existing knowledge. Prevent contradiction accumulation.
```python
manager = MemoryManager(
    instructions="Extract new facts. Update existing memories if contradicted. Merge similar memories."
)
updated = manager.process(new_conversation, existing_memories)
```

### 4. Compress (Summarize)
When context grows too long, compress older content while preserving essential information.
```python
if token_count(context) > COMPRESSION_THRESHOLD:
    summary = llm.summarize(
        content=context[:-RECENT_N_MESSAGES],
        instructions="Preserve all decisions, open questions, and key facts. Compress background context."
    )
    context = [summary_message(summary)] + context[-RECENT_N_MESSAGES:]
```

### 5. Forget (Prune)
Active forgetting prevents catastrophic interference from stale or incorrect memories.
```python
def prune_memories(memories, max_age_days=90, relevance_threshold=0.3):
    """Remove old, low-relevance, or contradicted memories."""
    return [m for m in memories 
            if m.age_days < max_age_days 
            and m.relevance_score > relevance_threshold
            and not m.is_contradicted]
```

---

## STM Management Strategies

### Strategy A: Full History (Simple, Expensive)
Pass the complete conversation history to the LLM every time.
- **Use when:** Conversations are short (<50 turns), context window is large, simplicity matters
- **Problem:** Context grows linearly; cost and latency grow with it

### Strategy B: Sliding Window
Keep only the last N messages.
- **Use when:** Older context is truly irrelevant
- **Problem:** Loses important early-conversation information

### Strategy C: Summarization Compression (Recommended)
Periodically compress older messages into a running summary; keep recent messages verbatim.
```
[Full summary of turns 1–40] + [Verbatim turns 41–50]
```
- **Use when:** Long conversations where both early context and recent context matter
- **Trigger compression at:** ~70–80% of context budget (before overflow)

### Strategy D: Selective Retention
The agent explicitly decides what to keep in context (via tool calls like `remember_this`).
- **Use when:** The agent is capable of judging relevance; high-stakes or long-horizon tasks
- **Challenge:** Requires the agent to be reliable at self-assessment

---

## LTM: Hot Path vs. Background Memory Formation

**Hot path (explicit/synchronous):** Agent writes to memory during the task via tool calls.
- Lower latency for the current task (no batch lag)
- More selective — agent decides what matters
- Risk: Adds tool call overhead to active tasks; agent may misjudge importance

**Background (implicit/asynchronous):** A background process analyzes conversations after they end and extracts memories.
- Higher recall — systematic, not dependent on agent judgment
- No overhead during active tasks
- Lag before memories are available

**Recommended:** Use background memory formation for most cases. Reserve hot-path writes for time-critical, high-importance information (e.g., user explicitly says "remember this for next time").

---

## Episodic → Semantic Consolidation

The hallmark of learning systems: convert specific experiences (episodic) into general principles (semantic).

```
Episodic: "On Task #1234, approach X worked for user type A"
Episodic: "On Task #5678, approach X worked for user type A"
Episodic: "On Task #9012, approach X worked for user type A"
         ↓ Background consolidation process
Semantic: "For user type A tasks, approach X is the reliable strategy"
```

This is how SOPs, best-practice libraries, and reusable agent skills should be built — not manually, but by having the system extract patterns from its own operational history.

---

## Multi-Agent Shared Memory

When multiple agents need to share state:

**Pattern 1: Shared External Store**
All agents read/write to the same external store (vector DB + structured DB). Works well but requires conflict resolution for concurrent writes.

**Pattern 2: Hierarchical Memory**
Orchestrator maintains strategic memory (goals, plan state). Workers maintain task-specific memory. Orchestrator aggregates worker summaries.

**Pattern 3: Memory Broadcasting**
When one agent learns something important, a publish-subscribe system notifies other agents who might benefit.

**Required for all shared memory systems:**
- Namespacing by agent role and task ID to prevent cross-contamination
- Access control: agents only see memory relevant to their role
- Write conflict resolution (last-write-wins for non-critical; human review for critical)

---

## State Management for Long-Running Tasks

Tasks that span multiple agent sessions need explicit state checkpointing.

**State object pattern:**
```python
@dataclass
class TaskState:
    task_id: str
    schema_version: str = "1.0.0"
    status: str  # pending, in_progress, blocked, complete, failed
    
    # Progress tracking
    completed_steps: List[str]
    current_step: str
    remaining_steps: List[str]
    
    # Results accumulation
    artifacts: Dict[str, str]  # key → storage reference (not content)
    
    # Context for resumption
    last_checkpoint_summary: str  # compressed context for resuming
    
    # Metadata
    created_at: datetime
    last_updated: datetime
    error_log: List[str]
```

**Checkpointing rules:**
- Checkpoint after every significant step (not every tool call)
- Store artifacts by reference (URL or ID), not by value
- Include a compressed "resumption summary" — the essential context needed to continue
- Checkpoint before any human-in-the-loop gate (state survives if human takes days to respond)

---

## Context Window Budget Planning

Explicitly allocate your context window before writing any agent:

```
Example 128K token budget allocation:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
System prompt:              3,000 tokens  (2.3%)
Current task description:   1,000 tokens  (0.8%)
Injected memories (LTM):    5,000 tokens  (3.9%)
RAG context (retrieved):    8,000 tokens  (6.3%)
Conversation history (STM): 10,000 tokens (7.8%)
Tool call history:          5,000 tokens  (3.9%)
Output buffer:              2,000 tokens  (1.6%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total used:                 34,000 tokens (26.6%)
Remaining headroom:         94,000 tokens (safety buffer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Note: Design to stay under 30% for most tasks;
use more only when the task truly requires it.
```

---

## Common Memory Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Naive "add-all" memory | Grows unbounded, contradictions accumulate, performance degrades | Implement pruning + consolidation |
| Stuffing everything into context | Context bloat, "lost in the middle" degradation | Selective retrieval; inject only relevant memories |
| No LTM for long-horizon tasks | Agent starts from scratch each session | Implement episodic + semantic stores |
| Storing content, not references | Context explodes with artifact content | Store artifacts externally; pass references |
| No compression trigger | Agents hit context limits mid-task | Set compression threshold at 70–80% of budget |
| Single shared memory for all agents | Role contamination, security issues | Namespace memory by agent role and task |
