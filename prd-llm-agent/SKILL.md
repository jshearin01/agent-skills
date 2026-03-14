---
name: prd-llm-agent
description: Create Product Requirements Documents (PRDs) optimized for implementation by LLM Coding Agents like Claude Code, Cursor, Devin, and Aider. Use when building PRDs that will be consumed by autonomous AI coding agents, when converting existing PRDs for AI implementation, when creating technical specifications for AI-driven development, or when the user mentions creating specs for "AI agents," "LLM coding tools," "Claude Code," "Cursor," "autonomous coding," or similar AI-powered development workflows.
---

# PRD for LLM Coding Agents

Create Product Requirements Documents that function as executable specifications for autonomous AI coding agents while maintaining flexibility for optimal solution exploration.

## Core Principles

### 1. Specifications as Programming Interfaces
PRDs for LLM Coding Agents differ fundamentally from traditional human-oriented PRDs:

**Traditional PRDs:**
- Optimize for human comprehension and stakeholder alignment
- Present features holistically
- Implied scope through omission
- Focus on "what" and "why," leaving "how" flexible

**AI-Optimized PRDs:**
- Function as programming interfaces for autonomous execution
- Dependency-ordered, testable phases
- Explicit scope boundaries (AI cannot infer from omission)
- Precise enough to execute, structured enough to sequence
- Constrained to prevent scope drift, flexible for AI exploration

### 2. The 150-200 Instruction Limit
Research shows frontier LLMs can follow approximately 150-200 instructions with reasonable consistency before performance degrades.

**Solution: Phased Approaches**
- Structure work as 5-6 phases with 30-50 requirements each
- Each phase is a complete, testable unit
- Rather than one massive 300-requirement specification

### 3. Explicit Boundaries Are Mandatory
Every boundary must be stated positively:
- ❌ Implied: Don't mention authentication (assuming agent won't add it)
- ✅ Explicit: "Do NOT implement user authentication in this phase. Authentication will be handled in Phase 3."

## PRD Structure

### Executive Summary
Brief summary for those who won't read the entire document:

```markdown
## Executive Summary

**Project:** [Name]
**Purpose:** [1-2 sentence description]
**Success Criteria:** [Key measurable outcomes]
**Timeline:** [Target launch]
**Strategic Alignment:** [How this fits company strategy]
```

### Strategic Context
Why build this feature/product:

```markdown
## Strategic Context

**Business Value:** [Why this matters to the business]
**Market Opportunity:** [Size, growth, timing]
**Competitive Advantage:** [What makes this unique]
**User Pain Point:** [Problem being solved]
```

### Phased Implementation Plan
Break work into manageable phases:

```markdown
# Phase 1: [Name] (Estimated: X hours)

## Scope
What WILL be implemented:
- Feature A with specific behavior
- Feature B following pattern in @existing-file.ts
- Feature C using library X v2.x

## Explicit Exclusions
What will NOT be implemented:
- ❌ Authentication (Phase 3)
- ❌ Rate limiting (Phase 4)
- ❌ Real-time updates (Future consideration)

## Prerequisites
Must be complete before starting:
- [ ] Database migration 001 applied
- [ ] API v2 endpoints deployed
- [ ] Test environment configured

## Dependencies
External requirements:
- Stripe API v2023-10-16
- Redis ≥7.0
- Node.js ≥20.x

## Success Criteria
Measurable outcomes:
- [ ] All CRUD endpoints functional
- [ ] Unit tests pass (≥85% coverage)
- [ ] API response time <200ms (95th percentile)
- [ ] API documentation generated
- [ ] Zero linting errors

## Testing Requirements
- Unit tests for all business logic
- Integration tests for API endpoints
- E2E test for primary user flow
- Performance benchmark: `npm run benchmark`

## Verification Steps
After implementation:
1. Run all tests: `npm test`
2. Check coverage: `npm run coverage`
3. Verify linting: `npm run lint`
4. Compare against requirements above and list any not addressed
```

### Functional Requirements
Use precise, testable format:

```markdown
## Feature: User Authentication

### Requirements

**[REQ-001] JWT Token Generation** (MUST)
The system MUST generate JWT tokens upon successful login.

Acceptance Criteria:
- [ ] Token includes user ID, email, and role claims
- [ ] Token expires after 24 hours
- [ ] Token is signed with HS256 algorithm
- [ ] Invalid credentials return 401 status

Test: `npm test -- auth/jwt.test.js`
Success Metric: 100% test pass rate

**[REQ-002] Token Validation Middleware** (MUST)
The system MUST validate JWT tokens on protected endpoints.

Acceptance Criteria:
- [ ] Middleware checks Authorization header
- [ ] Expired tokens return 401
- [ ] Invalid tokens return 401
- [ ] Valid tokens populate req.user
- [ ] Missing tokens return 401

Implementation Pattern: Follow @backend/middleware/auth.ts
Test: `npm test -- middleware/auth.test.js`
```

### Technical Specifications

```markdown
## Technical Architecture

### Technology Stack
- Backend: Node.js 20.x with Express 4.x
- Database: PostgreSQL 15
- Caching: Redis 7.0
- Testing: Jest 29.x
- Documentation: OpenAPI 3.0

### File Structure
Follow existing pattern:
```
backend/
  api/
    routes/        # Route definitions
    controllers/   # Request handlers
    services/      # Business logic
    models/        # Data models
  middleware/      # Express middleware
  utils/          # Helper functions
  tests/          # Test files
```

### Code Standards
See @.ai/standards/coding-standards.md for detailed guidelines.

Key requirements:
- Use TypeScript strict mode
- All functions must have JSDoc comments
- All public APIs must have OpenAPI documentation
- Error handling: ALWAYS use AppError class
- Never use console.log in production code
- Prefer async/await over callbacks

### Database Schema
See @database/schema.sql for complete schema.

For this phase, tables needed:
- users (id, email, password_hash, created_at)
- sessions (id, user_id, token, expires_at)

### API Design
Follow REST conventions in @.ai/standards/api-design.md

Endpoints for this phase:
```
POST   /api/auth/login      # User login
POST   /api/auth/logout     # User logout
POST   /api/auth/refresh    # Token refresh
GET    /api/auth/me         # Get current user
```

Response format:
```json
{
  "success": true,
  "data": { /* response data */ },
  "error": null
}
```

Error format:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly message",
    "details": { /* additional context */ }
  }
}
```
```

### Non-Functional Requirements

```markdown
## Non-Functional Requirements

### Performance
- API response time: <200ms (95th percentile)
- Database query time: <50ms (95th percentile)
- Maximum concurrent users: 1,000
- Cache hit rate: >80%

### Security
- Passwords MUST be hashed with bcrypt (12 rounds)
- Tokens MUST use secure random generation
- All inputs MUST be validated and sanitized
- SQL injection prevention: Use parameterized queries only
- XSS prevention: Sanitize all user inputs
- CSRF protection: Required for all state-changing operations

### Reliability
- Uptime target: 99.9%
- Error rate: <0.1%
- Failed request retry: Exponential backoff (max 3 attempts)
- Database connection pooling: Min 5, Max 20

### Scalability
- Horizontal scaling: Stateless application design
- Database: Read replicas for scaling reads
- Caching: Redis for session storage
- Rate limiting: 100 requests/minute per user

### Maintainability
- Code coverage: ≥85%
- Documentation coverage: 100% of public APIs
- Linting: Zero errors, zero warnings
- Type safety: TypeScript strict mode
```

### Error Handling Standards

```markdown
## Error Handling

### Error Class Usage
ALWAYS use the AppError class:

```typescript
// Correct
throw new AppError(
  'User not found',
  'USER_NOT_FOUND',
  404
);

// Incorrect - NEVER do this
throw new Error('User not found');
console.error('User not found');
```

### Error Categories
Follow patterns in @backend/utils/errors.ts:

- ValidationError: Invalid input (400)
- AuthenticationError: Auth failure (401)
- AuthorizationError: Permission denied (403)
- NotFoundError: Resource not found (404)
- ConflictError: Resource conflict (409)
- InternalError: System error (500)

### Error Logging
```typescript
// Include context in error logs
logger.error('Failed to create user', {
  error: error.message,
  email: sanitizedEmail,
  timestamp: Date.now()
});
```
```

### Documentation Requirements

```markdown
## Documentation

### Code Comments
- Every function: JSDoc with description, parameters, returns, examples
- Complex logic: Inline comments explaining "why," not "what"
- Public APIs: OpenAPI/Swagger documentation

Example:
```typescript
/**
 * Validates and creates a new user account
 * 
 * @param {Object} userData - User registration data
 * @param {string} userData.email - User email address
 * @param {string} userData.password - Plain text password (will be hashed)
 * @returns {Promise<User>} Created user object (without password)
 * @throws {ValidationError} If email/password invalid
 * @throws {ConflictError} If email already exists
 * 
 * @example
 * const user = await createUser({
 *   email: 'user@example.com',
 *   password: 'SecurePass123!'
 * });
 */
async function createUser(userData) {
  // Implementation
}
```

### API Documentation
Generate OpenAPI spec from code comments.
Serve at `/api/docs` using Swagger UI.
Include authentication examples.

### README Updates
Update project README.md with:
- New features added
- Environment variables required
- Migration instructions
- Breaking changes (if any)
```

### Testing Strategy

```markdown
## Testing

### Test Coverage Requirements
- Overall coverage: ≥85%
- Critical paths: 100%
- Edge cases: All identified scenarios

### Unit Tests
Test individual functions in isolation:
```typescript
// tests/services/auth.test.ts
describe('AuthService', () => {
  describe('validatePassword', () => {
    it('should return true for valid password', async () => {
      const isValid = await validatePassword(
        'password123',
        hashedPassword
      );
      expect(isValid).toBe(true);
    });

    it('should return false for invalid password', async () => {
      const isValid = await validatePassword(
        'wrongpassword',
        hashedPassword
      );
      expect(isValid).toBe(false);
    });
  });
});
```

### Integration Tests
Test API endpoints with database:
```typescript
// tests/integration/auth.test.ts
describe('POST /api/auth/login', () => {
  it('should return token for valid credentials', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({
        email: 'test@example.com',
        password: 'password123'
      });

    expect(response.status).toBe(200);
    expect(response.body.data.token).toBeDefined();
  });
});
```

### E2E Tests
Test complete user flows:
```typescript
// tests/e2e/user-registration-flow.test.ts
describe('User Registration Flow', () => {
  it('should complete full registration and login', async () => {
    // Register
    const registerResponse = await register(userData);
    expect(registerResponse.status).toBe(201);

    // Login
    const loginResponse = await login(credentials);
    expect(loginResponse.status).toBe(200);

    // Access protected resource
    const token = loginResponse.body.data.token;
    const profileResponse = await getProfile(token);
    expect(profileResponse.status).toBe(200);
  });
});
```

### Performance Tests
Benchmark critical operations:
```typescript
// tests/performance/auth.benchmark.js
describe('Authentication Performance', () => {
  it('should handle 100 concurrent logins', async () => {
    const startTime = Date.now();
    const promises = Array(100).fill().map(() => login());
    await Promise.all(promises);
    const duration = Date.now() - startTime;
    
    expect(duration).toBeLessThan(5000); // 5 seconds
  });
});
```
```

### Success Metrics

```markdown
## Success Metrics

### Technical Metrics
- ✅ Test coverage ≥85%
- ✅ Build time <5 minutes
- ✅ API response time <200ms (95th percentile)
- ✅ Error rate <0.1%
- ✅ Zero linting errors
- ✅ Zero TypeScript errors
- ✅ All security scans pass

### Business Metrics (if applicable)
- User adoption rate
- Feature usage metrics
- Performance improvements
- Error reduction
- Time saved

### AI-Specific Metrics (for AI features)
- Model accuracy ≥90%
- Hallucination rate <2%
- Response latency <1s
- User satisfaction ≥4.0/5.0
```

## Implementation Workflow

### 1. Pre-Implementation Planning
Before writing code, agent should:

```markdown
Provide implementation plan:
1. List all files to be created/modified
2. Outline step-by-step implementation sequence
3. Identify potential breaking changes
4. Describe rollback strategy
5. List all dependencies to install
```

### 2. Iterative Development
Agent should work in this loop:

```markdown
For each requirement:
1. Implement the feature
2. Write/update tests
3. Run tests: `npm test`
4. Fix any failures
5. Verify against acceptance criteria
6. Move to next requirement
```

### 3. Quality Verification
After implementation:

```markdown
Quality checklist:
- [ ] All tests pass: `npm test`
- [ ] Coverage meets threshold: `npm run coverage`
- [ ] No linting errors: `npm run lint`
- [ ] No type errors: `npm run typecheck`
- [ ] Build succeeds: `npm run build`
- [ ] Documentation generated: `npm run docs`
- [ ] Security scan passes: `npm audit`
```

### 4. Git Integration
Commit with standards:

```markdown
Commit message format (Conventional Commits):
feat(auth): add JWT authentication middleware

- Implement token generation and validation
- Add authentication middleware for protected routes
- Include comprehensive test suite (95% coverage)
- Update API documentation

Closes #123
```

## Reference Files

This skill includes detailed reference documentation:

### references/best-practices.md
Deep dive into PRD best practices:
- Specificity requirements
- Example-driven documentation
- Self-verification patterns
- LLM-as-a-Judge evaluation
- Context engineering techniques

Read when creating complex PRDs or facing common pitfalls.

### references/anti-patterns.md
Common mistakes to avoid:
- Vague requirements
- Assumed context
- Scope creep enablers
- Context bloat
- Missing constraints

Consult when reviewing PRDs or troubleshooting agent issues.

### references/agents-context.md
Understanding LLM Coding Agents:
- Agent autonomy levels
- Claude Code, Cursor, Devin, Aider capabilities
- Context file systems (AGENTS.md, CLAUDE.md, .cursorrules)
- Context window management
- Tool integration (MCP)

Read when optimizing for specific agents or understanding agent behavior.

## Examples

### Example 1: Simple Feature Addition
**User Request:** "Create a PRD for adding email verification to our user registration"

**Response:**
```markdown
# PRD: Email Verification Feature

## Executive Summary
Add email verification to user registration to reduce spam accounts and ensure valid contact information.

## Phase 1: Email Verification (Estimated: 4-5 hours)

### Scope
- Email verification token generation
- Verification email sending
- Email verification endpoint
- Update user model with verified status

### Explicit Exclusions
- ❌ Password reset (separate feature)
- ❌ Email change verification (future enhancement)
- ❌ SMS verification (future consideration)

### Requirements

[REQ-001] Generate Verification Token (MUST)
Generate secure random token when user registers.

Acceptance Criteria:
- [ ] Token is cryptographically secure (32 bytes)
- [ ] Token expires after 24 hours
- [ ] Token is unique per user
- [ ] Token is stored hashed in database

Implementation: Use crypto.randomBytes(32).toString('hex')
Test: `npm test -- tests/auth/verification-token.test.js`
...
```

### Example 2: Complex Multi-Phase Project
**User Request:** "Create a PRD for building a real-time collaborative document editor"

**Response:**
```markdown
# PRD: Real-Time Collaborative Document Editor

## Executive Summary
Build Google Docs-style collaborative document editing with real-time synchronization, conflict resolution, and presence indicators.

## Phased Implementation

### Phase 1: Basic Document Management (Week 1)
Scope: CRUD operations for documents, no real-time features yet
Exclusions: Real-time sync, collaboration, presence
Requirements: 15 specific requirements with test criteria
...

### Phase 2: WebSocket Infrastructure (Week 2)
Scope: Real-time communication foundation
Prerequisites: Phase 1 complete, Redis installed
Requirements: 12 specific requirements
...

### Phase 3: Operational Transformation (Week 3)
Scope: Conflict resolution for concurrent edits
Prerequisites: Phase 2 complete
Requirements: 18 specific requirements with algorithm specs
...

[Each phase includes full specification as shown in templates above]
```

## Templates

### assets/prd-template.md
Complete PRD template ready to customize.
Copy and fill in for new projects.

### assets/phase-template.md
Template for individual phase specifications.
Use when adding phases to existing PRDs.

### assets/requirements-template.md
Template for writing individual requirements.
Ensures consistency in requirement documentation.
