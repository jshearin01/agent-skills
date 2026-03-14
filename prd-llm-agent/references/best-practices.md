# PRD Best Practices for LLM Coding Agents

## Specificity Over Brevity

Every vague instruction costs iteration time. The difference between a working implementation and hours of revision is usually just missing details.

### Examples of Specificity

**❌ Vague:**
- "Fix the payment processing"
- "Make it better"
- "Improve performance"
- "Add error handling"

**✅ Specific:**
- "Add unit tests for the payment retry logic in processPayment(), especially the exponential backoff when Stripe returns a 429"
- "Refactor the authentication middleware to follow SOLID principles as documented in @.ai/standards/architecture.md"
- "Optimize the /api/users endpoint to return results in <200ms by implementing pagination (100 items per page) and adding database indexes on email and created_at columns"
- "Implement error handling using the AppError class from @backend/utils/errors.ts with specific error codes for validation (400), authentication (401), and not found (404) errors"

## Example-Driven Documentation

### Provide Code Examples

Always include concrete examples of expected patterns:

```markdown
### Authentication Middleware

Follow this pattern from @backend/middleware/auth.ts:

```typescript
export async function authMiddleware(req, res, next) {
  try {
    const token = extractToken(req.headers.authorization);
    const user = await verifyToken(token);
    req.user = user;
    next();
  } catch (error) {
    throw new AuthenticationError('Invalid token');
  }
}
```

New middleware should follow the same structure:
- Extract credentials from request
- Verify/validate credentials
- Attach result to req object
- Call next() or throw appropriate error
```

### Show Input/Output Examples

For APIs, always specify exact request/response formats:

```markdown
### POST /api/users

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "usr_1234567890",
    "email": "user@example.com",
    "name": "John Doe",
    "createdAt": "2026-01-15T10:30:00Z"
  },
  "error": null
}
```

**Error Response (400):**
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```
```

## Link to Source of Truth

### Reference Existing Patterns

Point to authoritative examples in the codebase:

```markdown
## Error Handling

Follow the error handling pattern in @backend/api/users.ts:

```typescript
// Correct pattern
try {
  const user = await createUser(userData);
  res.status(201).json({ success: true, data: user });
} catch (error) {
  if (error instanceof ValidationError) {
    res.status(400).json({
      success: false,
      error: { code: error.code, message: error.message }
    });
  }
  // ... handle other error types
}
```

Do NOT invent your own error handling patterns.
```

### Reference Documentation

Link to project standards:

```markdown
### Code Standards

Follow ALL standards in @.ai/standards/coding-standards.md:
- TypeScript strict mode
- JSDoc comments for all public functions
- ESLint configuration with zero warnings
- Prettier formatting
- Conventional Commits for git messages
```

## Demand Planning Before Execution

### Complex Tasks Require Planning First

For any task involving multiple files or complex logic, require the agent to plan first:

```markdown
## Implementation Requirements

Before implementing this feature, provide:

1. **File Plan:**
   - List all files to be created
   - List all files to be modified
   - Explain purpose of each file

2. **Implementation Steps:**
   - Step 1: Set up database schema
   - Step 2: Create data models
   - Step 3: Implement business logic
   - Step 4: Add API endpoints
   - Step 5: Write tests
   - Step 6: Add documentation

3. **Breaking Changes:**
   - List any backwards-incompatible changes
   - Describe migration path for existing data
   - Outline version compatibility

4. **Rollback Strategy:**
   - How to revert changes if issues arise
   - Database rollback procedures
   - Feature flag configuration

After plan approval, proceed with implementation.
```

### Use Planning Prompts

End complex requirements with explicit planning instructions:

```markdown
**Before coding:**
Think through the implementation approach:
- What design patterns apply?
- What edge cases exist?
- What could break existing functionality?
- What tests are needed?

Provide a brief plan, then implement.
```

## Self-Verification Patterns

### Build Verification Into Requirements

Make verification automatic:

```markdown
## Verification Steps

After implementation, the agent MUST:

1. **Run Tests:**
   ```bash
   npm test
   ```
   Expectation: All tests pass, coverage ≥85%

2. **Check Linting:**
   ```bash
   npm run lint
   ```
   Expectation: Zero errors, zero warnings

3. **Type Check:**
   ```bash
   npm run typecheck
   ```
   Expectation: Zero TypeScript errors

4. **Build:**
   ```bash
   npm run build
   ```
   Expectation: Build succeeds without errors

5. **Requirement Checklist:**
   Review each requirement and mark completion:
   - [ ] REQ-001: JWT token generation - COMPLETE
   - [ ] REQ-002: Token validation - COMPLETE
   - [ ] REQ-003: Error handling - COMPLETE
   
   List any incomplete requirements and explain why.
```

### Require Self-Review

Include self-review prompts:

```markdown
## Self-Review Checklist

Before considering implementation complete, verify:

- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] No linting errors
- [ ] No type errors
- [ ] Documentation updated
- [ ] Examples provided
- [ ] Edge cases handled
- [ ] Error messages user-friendly
- [ ] Security vulnerabilities checked
- [ ] Performance acceptable

For any item not checked, explain the blocker.
```

## LLM-as-a-Judge Evaluation

### Subjective Quality Checks

For criteria that are hard to test automatically (code style, readability, architectural patterns), use LLM-as-a-Judge:

```markdown
## Code Quality Review

After implementation, run this quality review:

**Review Prompt:**
"Review the implementation against @.ai/standards/code-quality.md
Flag any violations in these categories:

1. **Naming Conventions:**
   - Functions: camelCase, descriptive verbs
   - Classes: PascalCase, singular nouns
   - Constants: UPPER_SNAKE_CASE
   - Files: kebab-case

2. **Code Organization:**
   - Single Responsibility Principle
   - DRY (Don't Repeat Yourself)
   - Clear separation of concerns
   - Logical file structure

3. **Comment Quality:**
   - JSDoc for all public APIs
   - Inline comments for complex logic
   - No commented-out code
   - Comments explain 'why' not 'what'

4. **Error Handling:**
   - All errors caught and handled
   - Meaningful error messages
   - Proper error types used
   - No silent failures

5. **Test Coverage:**
   - All business logic tested
   - Edge cases covered
   - Error paths tested
   - Integration tests for APIs

Provide specific examples of violations with line numbers and suggested fixes."

Expected outcome: Zero violations or documented exceptions with justification.
```

### Architectural Review

For architectural decisions:

```markdown
## Architecture Review

Review the implementation's architectural choices:

**Review Prompt:**
"Analyze this implementation against our architectural principles in @.ai/standards/architecture.md:

1. **SOLID Principles:**
   - Single Responsibility: Each class/function does one thing
   - Open/Closed: Extensible without modification
   - Liskov Substitution: Subtypes are substitutable
   - Interface Segregation: No fat interfaces
   - Dependency Inversion: Depend on abstractions

2. **Design Patterns:**
   - Are appropriate patterns used?
   - Are patterns applied correctly?
   - Is any anti-pattern present?

3. **Scalability:**
   - Can this handle 10x current load?
   - Are there bottlenecks?
   - Is caching appropriate?

4. **Maintainability:**
   - Is code easy to understand?
   - Is it easy to modify?
   - Is it testable?

Provide recommendations for improvements."
```

## Conformance Testing

### Language-Independent Test Suites

Create test suites that verify behavior regardless of implementation:

```markdown
## Conformance Tests

The implementation MUST pass these conformance tests:

```yaml
# tests/conformance/auth-api.yaml
conformance_tests:
  - name: "Login with valid credentials"
    request:
      method: POST
      url: /api/auth/login
      body:
        email: "test@example.com"
        password: "ValidPass123!"
    expected:
      status: 200
      body_schema:
        type: object
        required: [success, data, error]
        properties:
          success: {type: boolean, const: true}
          data:
            type: object
            required: [token, user]
          error: {type: "null"}

  - name: "Login with invalid credentials"
    request:
      method: POST
      url: /api/auth/login
      body:
        email: "test@example.com"
        password: "WrongPassword"
    expected:
      status: 401
      body_schema:
        properties:
          success: {const: false}
          error:
            properties:
              code: {const: "INVALID_CREDENTIALS"}

  - name: "Login with missing fields"
    request:
      method: POST
      url: /api/auth/login
      body: {}
    expected:
      status: 400
      body_schema:
        properties:
          error:
            properties:
              code: {const: "VALIDATION_ERROR"}
```

Run conformance tests:
```bash
npm run conformance:auth
```

All tests MUST pass before considering feature complete.
```

## Context Engineering

### Manage Limited Attention Budget

LLMs have limited context windows and retrieval performance degrades with each token. Think of context as a limited "attention budget."

**Best Practices:**

1. **Clear Context Between Tasks:**
   ```markdown
   After completing each major feature or phase, start a new conversation
   or use the /clear command to reset context.
   
   This prevents context pollution from unrelated previous work.
   ```

2. **Progressive Disclosure:**
   ```markdown
   Don't load all documentation at once. Instead:
   
   "For database schema details, see @database/schema.sql"
   "For authentication implementation, read @.ai/guides/auth-implementation.md"
   "For API patterns, reference @backend/api/users.ts"
   
   The agent will load these only when needed.
   ```

3. **Modular Requirements:**
   ```markdown
   Break large features into small, focused requirements.
   Each requirement should be implementable in isolation with minimal context.
   ```

4. **Reference Don't Duplicate:**
   ```markdown
   ❌ Don't duplicate database schemas in PRD
   ✅ Reference: "Use schema from @database/schema.sql"
   
   ❌ Don't copy entire coding standards
   ✅ Reference: "Follow standards in @.ai/standards/coding-standards.md"
   ```

### Structured Context Loading

Guide the agent on when to load context:

```markdown
## Required Context

**Always Load:**
- @.ai/standards/coding-standards.md
- @backend/utils/errors.ts (error handling patterns)

**Load When Implementing Database Features:**
- @database/schema.sql
- @backend/models/README.md

**Load When Implementing APIs:**
- @backend/api/users.ts (reference implementation)
- @.ai/standards/api-design.md

**Load When Writing Tests:**
- @tests/helpers/setup.ts
- @.ai/standards/testing.md
```

## Quantifiable Success Metrics

### Make Every Metric Measurable

**❌ Vague:**
- "Good performance"
- "High quality code"
- "Secure implementation"

**✅ Measurable:**
- "API response time <200ms for 95th percentile"
- "Test coverage ≥85%, critical paths at 100%"
- "Zero HIGH or CRITICAL severity vulnerabilities in security scan"

### Technical Metrics Template

```markdown
## Success Metrics

### Performance
- API latency: <200ms (p95), <50ms (p50)
- Database query time: <50ms average
- Page load time: <2 seconds
- Time to interactive: <3 seconds
- Cache hit rate: >80%

### Quality
- Test coverage: ≥85% overall, 100% for critical paths
- Linting: Zero errors, zero warnings
- Type safety: Zero TypeScript errors
- Build time: <5 minutes
- Bundle size: <500KB gzipped

### Reliability
- Uptime: 99.9%
- Error rate: <0.1%
- Failed request retry success: >95%
- Data consistency: 100%

### Security
- Security scan: Zero HIGH/CRITICAL vulnerabilities
- Dependency audit: All vulnerabilities patched
- Authentication: 100% of protected endpoints secured
- Input validation: 100% of inputs validated

### Maintainability
- Cyclomatic complexity: <10 per function
- Documentation: 100% of public APIs documented
- Code duplication: <3%
- Technical debt ratio: <5%
```

### AI-Specific Metrics

For features that incorporate AI/LLM capabilities:

```markdown
## AI Feature Success Metrics

### Accuracy
- Prediction accuracy: ≥90%
- Precision: ≥85%
- Recall: ≥85%
- F1 score: ≥0.85

### Quality
- Hallucination rate: <2%
- Harmful output rate: <0.1%
- Response relevance: ≥90%
- User satisfaction: ≥4.0/5.0

### Performance
- Response latency: <1s (p95)
- Token efficiency: <1000 tokens per request average
- Cache hit rate: >70%
- Cost per request: <$0.01

### Monitoring
- Continuous evaluation on 1000 labeled queries
- Weekly model drift analysis
- Daily hallucination rate monitoring
- Real-time latency tracking
```

## Progressive Refinement

### Iterative Specification Development

PRDs evolve. Build in iteration:

```markdown
## Version History

### v1.0 - Initial Specification (2026-01-15)
- Basic CRUD operations
- JWT authentication
- PostgreSQL storage

### v1.1 - Refinements Based on Agent Feedback (2026-01-16)
- Added explicit error handling requirements
- Clarified database schema relationships
- Added performance benchmarks
- Included conformance test suite

### v1.2 - Post-Implementation Updates (2026-01-17)
- Documented actual implementation patterns
- Added lessons learned
- Updated success metrics based on results
- Added troubleshooting guide
```

### Feedback Loops

Build in feedback mechanisms:

```markdown
## Continuous Improvement

After each phase implementation:

1. **Agent Feedback:**
   - What requirements were unclear?
   - What additional context would have helped?
   - What assumptions were made?
   - What edge cases were discovered?

2. **PRD Updates:**
   - Clarify ambiguous requirements
   - Add discovered edge cases
   - Update patterns based on implementation
   - Document decisions made

3. **Pattern Library:**
   - Extract reusable patterns
   - Document in @.ai/patterns/
   - Reference in future PRDs
```

This creates a virtuous cycle of improvement where each implementation makes future PRDs better.
