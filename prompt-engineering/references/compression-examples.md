# Prompt Compression Examples

Side-by-side before/after examples showing token reduction without quality loss.

---

## Example 1: Customer Support System Prompt

**Before (~160 tokens):**
```
You are a helpful customer support assistant for TechCorp. Your job is to help customers with any questions or issues they might have with our products and services. Please always be polite, empathetic, and professional in your responses. Try to resolve customer issues as efficiently as possible. If you're unable to resolve an issue, please let the customer know that you will escalate it to a human agent. Always make sure to ask if there's anything else you can help with at the end of each conversation. Do not share any internal company information that is not meant for customers. If a customer is upset, remain calm and empathetic.
```

**After (~60 tokens):**
```
You are TechCorp customer support. Help customers resolve product/service issues efficiently. Be empathetic and professional. If you can't resolve an issue, say you'll escalate to a human. Don't share internal company information. End responses by asking if there's anything else needed.
```

**Savings: ~62% | Quality: Same**

---

## Example 2: Data Extraction Prompt

**Before (~95 tokens):**
```
I would like you to carefully read the following text and extract specific pieces of information from it. Please look for the person's name, their email address, and their phone number if present. Format the information you find in a JSON format with the keys "name", "email", and "phone". If any information is not found in the text, please use null as the value for that field.
```

**After (~40 tokens):**
```
Extract from the text below. Return JSON only.

Fields: name, email, phone (use null if not found)

Text: {{text}}
```

**Savings: ~58%**

---

## Example 3: Code Review Prompt

**Before (~110 tokens):**
```
Please review the following code and provide feedback on it. I'd like you to look at things like code quality, potential bugs, security issues, performance problems, and whether the code follows best practices. Please be thorough and specific in your feedback, pointing out both what's good about the code and what could be improved. If there are any critical issues, please highlight those first.
```

**After (~45 tokens):**
```
Review this code. Flag: bugs, security issues, performance problems, best practice violations. Lead with critical issues. Note positives too.
```

**Savings: ~59%**

---

## Example 4: Classification with Few-Shot

Sometimes adding tokens (examples) is the right tradeoff for reliability.

**Before (vague, ~50 tokens):**
```
Read the customer review and determine if the sentiment is positive, negative, or neutral.

Review: {{review}}
```

**After (few-shot, ~90 tokens — more tokens, better results):**
```
Classify sentiment: Positive, Neutral, or Negative. Return the label only.

Examples:
"Absolutely love it!" → Positive
"It's okay, nothing special." → Neutral
"Broke after a week." → Negative

Review: {{review}}
Output:
```

---

## Example 5: Agent System Prompt

**Before (~200 tokens):**
```
You are an AI assistant that has been given access to various tools and capabilities. Your goal is to help users accomplish tasks by using these tools effectively. When you receive a task, you should carefully think about which tools you need to use and in what order. Always make sure to check your work and verify that you've accomplished what the user asked for. If you encounter any errors, try to handle them gracefully and inform the user. Don't do anything that the user hasn't asked for. Make sure to be efficient and don't take unnecessary steps. Always confirm with the user if you're unsure about what they want.
```

**After (~65 tokens):**
```
You are a task-execution agent with access to tools.

Rules:
- Plan before acting; use only necessary steps
- Verify output matches the request
- Handle errors gracefully and report them
- Ask for clarification when requests are ambiguous
- Never take actions beyond what's requested
```

**Savings: ~67%**

---

## When NOT to Compress

Some things look compressible but should be kept:
- **Few-shot examples** — earn their cost in accuracy
- **Edge case rules** — removing them breaks edge cases
- **Negative constraints** — "Do NOT include markdown" prevents formatting errors
- **JSON schemas** — take tokens but prevent parse failures
- **Safety/policy rules** — never compress these

## Decision Rule

For each phrase ask: "If I remove this, does model output change?"
- No change → remove
- Changes for worse → keep
- Changes for better → it was causing confusion; remove
