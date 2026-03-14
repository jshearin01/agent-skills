# Prompt Engineering Techniques — Deep Reference

## 1. Clarity & Specificity

The single highest-ROI technique. Modern LLMs are highly literal — they do what you say, not what you mean.

**Principle**: Include task, scope, format, tone, length, and audience in one clear instruction.

**Before:**
```
Explain climate change.
```

**After:**
```
Write a 3-paragraph explanation of climate change for high school students. Use plain language. Cover: what it is, why it's happening, and one practical action readers can take.
```

**Checklist for clarity:**
- [ ] Task verb is explicit (summarize, extract, classify, generate, compare)
- [ ] Scope is bounded (word count, topic limit, time frame)
- [ ] Audience is specified if relevant
- [ ] Tone/style is defined if it matters
- [ ] Output format is stated

---

## 2. XML Tags for Structure

Especially effective for Claude. Use XML tags to separate prompt sections so the model parses them unambiguously.

**Standard tags:**
```xml
<instructions>...</instructions>
<context>...</context>
<examples>...</examples>
<output_format>...</output_format>
<input>{{user_input}}</input>
```

**When to use:**
- Prompt has 3+ distinct sections
- You mix instructions, examples, and variable input
- You want the model to clearly distinguish "rules" from "data"

**Example:**
```xml
<instructions>
Classify the customer review below as Positive, Neutral, or Negative.
Return only the label — no explanation.
</instructions>

<examples>
<example>
Review: "Works great, fast shipping!"
Label: Positive
</example>
<example>
Review: "Arrived broken, very disappointed."
Label: Negative
</example>
</examples>

<input>{{review_text}}</input>
```

---

## 3. Few-Shot / Multishot Examples

Show the model what you want instead of only telling it. Examples are the most reliable way to lock in format, tone, and edge-case handling.

**Rules for good examples:**
- 3–5 examples for complex tasks; 1–2 for simple format enforcement
- Examples should be **diverse** (cover different cases, not the same case repeated)
- Examples should be **realistic** (mirror your actual data)
- Wrap in `<example>` tags (Claude), or use `Input:` / `Output:` prefixes

**Before (no examples):**
```
Extract the action item and owner from meeting notes.
```

**After (with examples):**
```
Extract the action item and owner from meeting notes. Return JSON.

<examples>
<example>
Notes: "John will send the report by Friday."
Output: {"action": "Send report", "owner": "John", "due": "Friday"}
</example>
<example>
Notes: "We need someone to book the venue — Sarah volunteered."
Output: {"action": "Book venue", "owner": "Sarah", "due": null}
</example>
</examples>

Notes: {{notes}}
Output:
```

---

## 4. Chain-of-Thought (CoT)

Improves accuracy on reasoning, math, logic, and multi-step tasks by making the model think before answering.

**Simple CoT:**
```
Think step by step, then give your final answer.
```

**Structured CoT (Claude):**
```
Reason through the problem in <thinking> tags. Then put only your final answer in <answer> tags.
```

**When to use CoT:**
- Math or logic problems
- Classification with nuanced edge cases
- Multi-criteria evaluation
- Any task where accuracy > speed

**When NOT to use:**
- Simple fact lookup (wastes tokens)
- Tasks needing extremely short output
- Real-time applications where latency matters

**Token cost note:** CoT increases output tokens significantly. For cost-sensitive applications, use only when accuracy truly requires it.

---

## 5. Role Prompting (System Prompts)

Giving the model a persona or expertise context improves tone, depth, and domain accuracy.

**Template:**
```
You are a [ROLE] with [EXPERIENCE/EXPERTISE]. You [BEHAVIORAL TRAIT].
```

**Example:**
```
You are a senior software engineer specializing in Python and system design. You write code that is production-ready, well-commented, and follows PEP 8.
```

**Tips:**
- Make the role specific to the task (not just "helpful assistant")
- Add behavioral constraints in the role definition
- Don't over-describe — 1–3 sentences is usually enough

---

## 6. Output Format Control

Explicitly specify the output structure. Never assume the model will format correctly without instruction.

**Techniques:**

**a) Direct specification:**
```
Return a JSON object with these fields: name (string), score (0-10), reason (string, max 20 words).
```

**b) Schema example:**
```
Return JSON matching this schema:
{
  "summary": "string",
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0-1.0
}
```

**c) Prefilling (Claude API only):**
Set the start of the assistant's message to force format:
```json
{
  "messages": [
    {"role": "user", "content": "Analyze this text: ..."},
    {"role": "assistant", "content": "{"}  // prefill forces JSON response
  ]
}
```

**d) Negative constraints:**
```
Do not include any explanation or preamble. Return only the requested data.
```

---

## 7. Prompt Chaining

Break complex tasks into sequential prompts. Each prompt does one thing well.

**Pattern:**
```
Prompt 1: Extract raw data → output JSON
Prompt 2: Validate/transform data → output clean JSON  
Prompt 3: Generate final report from clean data → output Markdown
```

**When to chain:**
- Task has distinct stages that benefit from intermediate validation
- Single prompt is unreliable due to complexity
- You need to branch based on intermediate output

**Token consideration:** Chaining uses more total tokens but produces more reliable output. Worth it for high-stakes tasks.

---

## 8. Uncertainty Permission

Dramatically reduces hallucination. Give the model explicit permission to say it doesn't know.

**Add to any factual prompt:**
```
If you don't have enough information to answer confidently, say "I'm not certain" rather than guessing.
```

**For analysis:**
```
If the data is insufficient to draw a conclusion, say so explicitly instead of speculating.
```

---

## 9. Constraint-Based Prompting

Add specific constraints to bound the output.

**Length constraints:**
- "In exactly 2 sentences"
- "Under 100 words"
- "In 3 bullet points"

**Scope constraints:**
- "Focus only on financial implications, not technical ones"
- "Cover only events from 2020–2024"

**Format constraints:**
- "Use plain text only, no markdown"
- "Use headers for each section"
- "Start each bullet with a verb"

---

## 10. Negative Prompting

Explicitly state what NOT to do. More reliable than hoping the model infers it.

```
Do NOT:
- Include disclaimers or caveats
- Repeat the question in your answer
- Use bullet points (use prose only)
- Speculate beyond the provided data
```

---

## Token Optimization Techniques

### Compression Checklist

Run every prompt through this before finalizing:

1. **Remove filler openers**: Delete "I want you to...", "Please...", "Could you..."
2. **Use imperatives**: "Summarize" not "Please provide a summary of"
3. **Cut meta-commentary**: Delete "As an AI, I will..." type language from system prompts
4. **Collapse redundant rules**: If two rules say the same thing, keep one
5. **Replace prose with lists**: Multi-part instructions as bullets use fewer tokens
6. **Set output length**: Saves output tokens (more expensive than input on most APIs)
7. **Use short variable names**: `{{text}}` not `{{the_user_input_text_to_process}}`
8. **Trim examples**: Use the minimum number that gets the point across

### Before/After: System Prompt Compression

**Before (127 tokens):**
```
You are a helpful AI assistant. Your role is to assist users with questions about our product. Please be polite, professional, and friendly in all your responses. Make sure to always answer questions thoroughly and comprehensively. If you don't know something, please let the user know. Do not make up information. Always be honest.
```

**After (47 tokens):**
```
You are a product support assistant. Answer user questions about our product accurately and professionally. If you don't know something, say so — never fabricate information.
```

**Savings: 63% reduction. Zero quality loss.**

---

## Prompting Anti-Patterns to Avoid

### Over-Engineering
More complex ≠ better. Add complexity only when simpler prompts fail.

### Contradictory Instructions
"Be comprehensive but brief" forces the model to guess. Define both: "Cover these 3 points in under 100 words total."

### Buried Critical Instructions
The model pays more attention to the beginning and end of prompts. Critical rules belong at the top.

### Unparseable Instructions
Long paragraphs of mixed instructions are hard for models to follow. Use structured lists.

### Missing Variable Markers
Always mark dynamic inputs: `{{user_message}}`, `{{document}}`, `{{date}}`
