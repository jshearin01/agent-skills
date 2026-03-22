# Tool / Function Calling Design

Reference file for `llm-agent-architect` skill. Read this when designing tool schemas, execution loops, structured outputs, and the interface between LLMs and external systems.

---

## Core Concepts

Tools transform an LLM from a passive text generator into an active participant capable of completing real-world tasks. Every tool call is an I/O operation with real-world side effects — design accordingly.

**The tool use loop:**
```
LLM receives task + tools list
    │
    ▼
LLM decides: call tool? which tool? with what args?
    │
    ▼
Tool executes (external API, DB, code, etc.)
    │
    ▼
Result returned to LLM context
    │
    ▼
LLM evaluates result, continues or calls another tool
    │
    ▼
LLM determines task is complete → final output
```

---

## Tool Schema Design

The quality of your tool schemas directly determines tool selection accuracy. Ambiguous or overly broad schemas lead to wrong tool calls.

**Schema requirements:**
```json
{
  "name": "search_documents",
  "description": "Search the internal knowledge base for documents relevant to a query. Use this when you need to find specific information, policies, or procedures. Do NOT use for real-time data or external web content.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query. Be specific. Use keywords from the domain."
      },
      "filter_by_date": {
        "type": "string",
        "description": "Optional ISO date string. Only return documents created after this date.",
        "format": "date"
      },
      "max_results": {
        "type": "integer",
        "description": "Number of results to return. Default 5. Max 20.",
        "default": 5,
        "maximum": 20
      }
    },
    "required": ["query"]
  }
}
```

**Schema design rules:**
1. **Name tools by action, not object:** `search_documents` not `documents`
2. **Include explicit scope:** What should this tool NOT be used for?
3. **Describe parameters precisely:** Vague descriptions cause wrong argument values
4. **Set sensible defaults:** Reduce required decision-making from the LLM
5. **Fail the schema, not the tool:** Validate args before execution; return clear error messages
6. **Limit tool sets per agent:** 10–15 tools is practical maximum before selection accuracy degrades

---

## Tool Categories

**Read tools (safe, idempotent):**
- Search/retrieve: `search_documents`, `get_user_profile`, `list_items`
- Compute: `calculate`, `parse_date`, `format_output`
- Status checks: `check_order_status`, `get_weather`

**Write tools (side-effectful — require extra care):**
- Create: `create_task`, `send_email`, `insert_record`
- Update: `update_record`, `modify_setting`
- Delete: `delete_record`, `cancel_order`

**Design principle:** Separate read and write tools. Never bundle reading and writing into one tool call. For write tools:
- Log all executions before and after
- Implement idempotency keys where possible
- Require human-in-the-loop approval for high-stakes writes
- Return confirmation of what was changed

---

## Structured Output Design

LLMs should return structured outputs when the next step needs to parse or route the result programmatically.

**Use structured outputs when:**
- Results feed into another system, agent, or code
- You need to extract specific fields reliably
- You're routing based on the LLM's response

**Implementation pattern:**
```python
# Force structured output via response_format or tool schema
response = llm.call(
    messages=messages,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "task_result",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["success", "failure", "needs_clarification"]},
                    "result": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "next_action": {"type": "string", "enum": ["complete", "retry", "escalate"]}
                },
                "required": ["status", "result", "next_action"]
            }
        }
    }
)

# Always validate; never trust raw output
parsed = validate_and_parse(response.content)
```

**Validation-repair loop:**
```python
MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    raw = llm.call(messages)
    try:
        result = schema.validate(raw)
        break
    except ValidationError as e:
        if attempt == MAX_RETRIES - 1:
            raise  # Escalate after exhausting retries
        messages.append({
            "role": "user",
            "content": f"Your response was invalid: {e}. Please fix and try again."
        })
```

---

## Tool Execution Best Practices

**Timeout every external call:**
```python
async def execute_tool(tool_name, args, timeout_seconds=30):
    try:
        result = await asyncio.wait_for(
            tool_registry[tool_name](**args),
            timeout=timeout_seconds
        )
        return {"status": "success", "result": result}
    except asyncio.TimeoutError:
        return {"status": "error", "error": f"Tool {tool_name} timed out after {timeout_seconds}s"}
    except Exception as e:
        return {"status": "error", "error": str(e), "tool": tool_name}
```

**Retry with exponential backoff:**
```python
@retry(
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(TransientError)
)
async def call_tool_with_retry(tool_name, args):
    return await execute_tool(tool_name, args)
```

**Return meaningful errors to the LLM:**
```json
// Bad: {"error": true}
// Good:
{
  "status": "error",
  "error_type": "not_found",
  "message": "Document with ID 'abc123' does not exist. Use search_documents to find the correct ID.",
  "suggested_action": "retry_with_search"
}
```

Give the LLM enough context to self-correct. Terse error messages cause retry loops that waste tokens.

---

## Agentic Loop Design

**ReAct pattern (Reason + Act):**
```
Thought: [LLM reasons about what to do next]
Action: [tool_name with args]
Observation: [tool result]
Thought: [LLM evaluates result]
... repeat until ...
Final Answer: [task complete]
```

**Loop termination conditions (always define these):**
- Task completed successfully
- Max iterations reached (prevent infinite loops — default: 10–20)
- Tool returned terminal error
- LLM signals completion with structured output
- Human-in-the-loop intervention triggered

**Loop iteration budget:**
```python
MAX_ITERATIONS = 15  # Hard ceiling
WARN_AT = 10         # Log warning for long-running agents

for step in range(MAX_ITERATIONS):
    if step >= WARN_AT:
        logger.warning(f"Agent at step {step}/{MAX_ITERATIONS}")
    
    response = agent.step(context)
    
    if response.is_terminal:
        break
    
    context = update_context(context, response)
else:
    # Max iterations reached
    return escalate_to_human(context)
```

---

## Tool Access Control

Agents should only have access to the tools they need for their role. Unrestricted tool access:
- Degrades tool selection accuracy
- Creates security surface area
- Makes agents harder to test and evaluate

**Role-based tool assignment:**
```python
AGENT_TOOLS = {
    "researcher": ["search_web", "search_documents", "get_url_content"],
    "writer": ["search_documents", "format_text", "check_grammar"],
    "executor": ["create_task", "send_email", "update_record"],
    "orchestrator": ["spawn_agent", "read_agent_output", "write_result"]
}

def build_agent(role: str, **kwargs):
    return Agent(
        role=role,
        tools=[tool_registry[t] for t in AGENT_TOOLS[role]],
        **kwargs
    )
```

---

## MCP (Model Context Protocol) Integration

MCP standardizes how applications provide context and tools to LLMs. Use it when:
- Multiple agents need to share the same tool/resource servers
- You need standardized discovery of available tools
- You're building integrations with external data sources

**Architecture pattern:**
```
Agent A ──┐
Agent B ──┼──→ MCP Client ──→ MCP Server (tools + resources) ──→ External APIs
Agent C ──┘
```

**Best practice:** Deploy MCP servers separately from agents (e.g., on a serverless platform). Agents connect as clients. This allows tool servers to scale independently and be reused across agent types.

---

## Common Tool Calling Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| No timeouts on tool execution | Agents hang indefinitely | Always set timeout + error handling |
| Tool returns raw exception | LLM can't self-correct | Return structured error with context |
| Too many tools per agent | Selection accuracy degrades | Max 10–15 per agent; use specialization |
| No idempotency on writes | Duplicate side effects on retry | Add idempotency keys |
| Mixing read and write in one tool | Hard to reason about side effects | Separate read/write tools |
| Trusting raw LLM output for tool args | Type errors, injection risks | Validate args before execution |
| No max iteration limit | Infinite loops, runaway cost | Always define a hard ceiling |
