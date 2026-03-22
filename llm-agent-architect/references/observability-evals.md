# Observability & Evaluation

Reference file for `llm-agent-architect` skill. Read this when instrumenting LLM systems for production monitoring, building eval pipelines, or debugging agent failures.

---

## Why LLM Observability Is Different

Traditional software observability (CPU, memory, error rates) is necessary but insufficient for LLM systems. LLMs fail silently: technically successful API calls that return plausible-sounding but wrong, hallucinated, or low-quality outputs. Standard metrics won't catch this.

You need three layers of observability:
1. **Operational:** Latency, cost, error rates, token usage (traditional ops)
2. **Behavioral:** What the agent actually did (traces of every step)
3. **Quality:** Was the output correct, grounded, and safe? (evals)

---

## The Tracing Foundation

Traces are the primary artifact for understanding LLM system behavior. Every request should produce a complete end-to-end trace showing every LLM call, tool call, retrieval, and agent step.

**Use OpenTelemetry (OTel) as the standard.** The OTel GenAI Semantic Conventions (v1.37+) provide a standardized schema for LLM telemetry that all major observability platforms (Datadog, Honeycomb, Grafana) can ingest.

**What to trace per LLM span:**
```python
span.set_attribute("gen_ai.operation.name", "chat")           # "chat", "tool_call", "agent_run"
span.set_attribute("gen_ai.system", "anthropic")              # LLM provider
span.set_attribute("gen_ai.request.model", "claude-sonnet-4") # Model used
span.set_attribute("gen_ai.request.max_tokens", 1000)
span.set_attribute("gen_ai.response.finish_reason", "end_turn")
span.set_attribute("gen_ai.usage.input_tokens", 1234)
span.set_attribute("gen_ai.usage.output_tokens", 567)
span.set_attribute("gen_ai.usage.cost_usd", 0.00234)          # Compute from token pricing
span.set_attribute("gen_ai.request.latency_ms", 1830)
span.set_attribute("trace_id", parent_trace_id)               # Link to parent workflow
```

**What to trace per agent/workflow span:**
- Agent name and role
- Input task / user message
- Output result
- Tools called (list)
- Sub-agents spawned
- Memory retrieved (IDs, not content)
- Handoff state (where it came from, where it went)
- Final status: success / failure / escalated

---

## Metrics to Track (Minimum Viable Set)

### Operational Metrics
| Metric | Why It Matters |
|--------|---------------|
| Request latency (p50/p99/p999) | User experience and SLA compliance |
| Token usage (input/output) by agent | Cost attribution and optimization |
| Cost per request / per workflow | Budget management |
| Error rate by agent and tool | Reliability monitoring |
| Tool call success rate | Detect flaky tools |
| Retry rate | Indicates prompt or tool instability |

### Quality Metrics (via evals)
| Metric | Why It Matters |
|--------|---------------|
| Task completion rate | Is the agent actually finishing tasks? |
| Groundedness | Is the output supported by context? |
| Hallucination rate | Is the agent making things up? |
| Tool selection accuracy | Is the agent using the right tools? |
| Output format compliance | Are structured outputs valid? |
| User satisfaction (if applicable) | Ground truth from humans |

---

## Eval Pipeline Design

Evals are automated quality checks that run continuously against your LLM system. Build them early — don't wait until you have quality problems.

**Three categories of evals:**

### Category 1: Deterministic / Code-Based Evals
For outputs where correctness is objective.
```python
def eval_structured_output_valid(response: str) -> EvalResult:
    """Check that response is valid JSON matching our schema."""
    try:
        parsed = json.loads(response)
        schema.validate(parsed)
        return EvalResult(passed=True, score=1.0)
    except (json.JSONDecodeError, ValidationError) as e:
        return EvalResult(passed=False, score=0.0, reason=str(e))

def eval_tool_call_accuracy(expected_tool: str, actual_tool: str) -> EvalResult:
    return EvalResult(passed=(expected_tool == actual_tool), score=float(expected_tool == actual_tool))
```

### Category 2: Reference-Based Evals
Compare output against a known-good reference answer.
```python
def eval_answer_similarity(predicted: str, reference: str) -> EvalResult:
    # Use embedding cosine similarity or exact match
    score = cosine_similarity(embed(predicted), embed(reference))
    return EvalResult(passed=(score > 0.85), score=score)
```

### Category 3: LLM-as-Judge Evals
For subjective quality dimensions that can't be checked with code. An LLM evaluates another LLM's output.

**Groundedness eval:**
```python
GROUNDEDNESS_PROMPT = """
You are evaluating whether an AI assistant's response is grounded in the provided context.

CONTEXT:
{context}

RESPONSE TO EVALUATE:
{response}

Score the response on a scale of 0-1:
- 1.0: Every claim in the response is directly supported by the context
- 0.5: Most claims are supported, but some extrapolation occurs
- 0.0: The response makes claims not supported by or contradicted by the context

Respond with JSON: {"score": 0.0-1.0, "reasoning": "brief explanation"}
"""

def eval_groundedness(context: str, response: str) -> EvalResult:
    raw = judge_llm.call(GROUNDEDNESS_PROMPT.format(context=context, response=response))
    result = json.loads(raw)
    return EvalResult(score=result["score"], reasoning=result["reasoning"])
```

**LLM-as-judge guidelines:**
- Use a strong model as judge (ideally different from the model being evaluated)
- Provide explicit rubrics with score anchors — never ask for subjective "good/bad"
- Run each eval 3x and average to reduce variance
- Calibrate judge against human annotations before trusting scores
- Common dimensions: groundedness, relevance, coherence, completeness, safety

---

## Eval Dataset Management

Eval datasets are your system's test suite. Treat them like production code.

**Building your first eval dataset:**
1. Start with 20–50 manually curated examples covering the main use cases
2. Promote interesting production traces into the dataset (1-click in most platforms)
3. Include edge cases: ambiguous queries, adversarial inputs, failure modes
4. Version your datasets — track changes over time
5. Split: 80% for ongoing regression testing, 20% held-out for final validation

**Eval dataset schema:**
```json
{
  "id": "eval-001",
  "input": {
    "user_message": "What is our refund policy?",
    "context": ["Document 1 text...", "Document 2 text..."]
  },
  "expected_output": {
    "contains": ["30 days", "receipt required"],
    "format": "structured",
    "groundedness": "high"
  },
  "tags": ["rag", "policy", "customer-service"],
  "created_from": "production_trace_id_abc123"
}
```

**Run evals at three frequencies:**
- **Per-commit:** Fast deterministic evals only (<2 min). Gate deployment.
- **Per-day:** Full suite including LLM-as-judge. Alert on regressions.
- **Per-week:** Human annotation sample. Ground truth calibration.

---

## Production Monitoring

### Alert On
| Alert | Threshold | Action |
|-------|-----------|--------|
| Error rate spike | >5% in 5 min | Page on-call, route to fallback |
| Latency p99 > SLA | >10s (typical) | Scale or notify |
| Cost per request increase | >50% week-over-week | Audit token usage by agent |
| Groundedness score drop | >10% from baseline | Review recent prompt changes |
| Tool failure rate spike | >10% | Check tool health |
| Max iteration breaches | >1% of runs | Review agent loop logic |

### Dashboard Essentials
Every LLM platform needs these views:

1. **Workflow trace view:** End-to-end trace of a single request (all steps, all agents, all tools)
2. **Quality trends:** Groundedness, task completion, eval scores over time
3. **Cost breakdown:** By agent, by model, by user, by feature
4. **Error analysis:** Error types, frequency, which agents/tools are failing
5. **Token usage heatmap:** Where tokens are being spent; identify optimization targets

---

## Observability Tool Selection

**Framework-agnostic (recommended for new systems):**
- **Langfuse** (open-source, self-hostable, OTel compatible) — strong for teams wanting full ownership
- **Braintrust** (SaaS, CI/CD integration) — best UX for PM+engineer collaboration; used by Stripe, Notion
- **Arize/Phoenix** (open-source) — strong ML monitoring + LLM

**If using LangChain/LangGraph:**
- LangSmith (native integration, one env var setup)

**Enterprise / existing infra:**
- Datadog (native OTel GenAI SemConv support)
- Use OpenTelemetry Collector to route to existing backends

**Key capabilities to require:**
- [ ] End-to-end trace spanning all agents and tools
- [ ] Input/output capture per LLM call (with PII redaction controls)
- [ ] LLM-as-judge eval support
- [ ] Dataset management (promote traces → eval cases)
- [ ] Cost tracking per model/provider
- [ ] OTel export (avoid vendor lock-in)
- [ ] Self-hostable option (for data residency requirements)

---

## The Feedback Loop: Traces → Evals → Improvements

The most powerful pattern in LLM operations:

```
Production traffic
        │
        ▼
Traces captured in observability platform
        │
        ▼ (human or automated review)
Interesting/failing traces promoted to eval dataset
        │
        ▼
Eval runs identify pattern of failures
        │
        ▼
Prompt changes / agent logic changes deployed
        │
        ▼
Eval suite validates improvement before deployment
        │
        ▼ (cycle continues)
Production traffic monitored for regression
```

**Implementation:**
1. Enable 100% trace capture in observability platform
2. Set up automated eval runners (daily)
3. Create a "review queue" for low-scoring traces
4. When a pattern is identified, add 5+ examples to the eval dataset
5. Fix the prompt/logic issue
6. Validate fix improves eval scores
7. Deploy with eval gate in CI/CD

---

## Human-in-the-Loop (HITL) Integration

Some decisions should require human approval before the agent proceeds.

**When to require HITL:**
- High-stakes actions (send external email, modify production data, make payment)
- Agent expresses low confidence (below threshold)
- Anomalous inputs (adversarial, out-of-distribution)
- Regulatory / compliance checkpoints
- After N failed attempts at a task

**HITL design patterns:**
```python
def requires_human_approval(action: Action, context: Context) -> bool:
    return (
        action.is_irreversible and action.estimated_impact > IMPACT_THRESHOLD
        or context.confidence_score < CONFIDENCE_THRESHOLD
        or action.type in ALWAYS_REQUIRE_APPROVAL_TYPES
    )

# Checkpoint state BEFORE waiting for human input
# Human may take hours/days to respond
if requires_human_approval(action, context):
    task_state.checkpoint()  # Save everything
    send_approval_request(action, context, task_id)
    return  # Agent suspends until approval received
```

**Mandatory:** Always persist state at HITL gates. Agents must be resumable without re-executing prior steps.
