# PRD Anti-Patterns for LLM Coding Agents

Common mistakes that lead to poor AI implementation outcomes and how to avoid them.

## 1. Vague Requirements

### The Problem

Vague requirements force the agent to make assumptions, leading to rework and iteration.

**❌ Bad Examples:**
```markdown
- "Make it better"
- "Improve the performance"
- "Fix the bugs"
- "Add error handling"
- "Make it secure"
- "Optimize the code"
- "Add tests"
```

These provide zero actionable guidance. The agent doesn't know:
- Better in what way?
- Which performance aspect?
- Which bugs?
- What error scenarios?
- Secure against what threats?
- Optimize for what metric?
- Test what functionality?

### The Solution

Be specific about what, where, how, and why:

**✅ Good Examples:**
```markdown
- "Refactor the getUserById function in @backend/services/user.ts to follow the Single Responsibility Principle by extracting database query logic into a separate repository layer"

- "Optimize the /api/products endpoint to respond in <200ms by implementing database query result caching with Redis (5-minute TTL) and adding an index on the products.category column"

- "Fix the race condition in payment processing where concurrent requests can create duplicate charges. Implement optimistic locking using the version column in the transactions table"

- "Add error handling to the file upload endpoint: validate file size (<5MB), check MIME type (images only), handle S3 upload failures with retry logic (max 3 attempts with exponential backoff)"

- "Implement rate limiting middleware using Redis to prevent brute force attacks: max 5 login attempts per IP per 15 minutes, return 429 status with Retry-After header"

- "Add unit tests for the calculateDiscount function covering: 0% discount, 10% member discount, 25% promotional discount, and invalid coupon code (should throw ValidationError)"
```

## 2. Assumed Context

### The Problem

Assuming the agent knows your project conventions, patterns, or implicit knowledge.

**❌ Bad Examples:**
```markdown
- "Follow our usual patterns"
- "Use the standard error handling"
- "Implement like we did before"
- "Add it to the right place"
- "Follow best practices"
```

The agent doesn't have access to:
- Your team's conventions
- Previous implementations (unless explicitly referenced)
- Unwritten rules
- Tribal knowledge

### The Solution

Make all context explicit or provide references:

**✅ Good Examples:**
```markdown
- "Follow the error handling pattern in @backend/api/users.ts where all errors use the AppError class:
  ```typescript
  throw new AppError('message', 'ERROR_CODE', statusCode);
  ```"

- "Implement authentication middleware following the same structure as @backend/middleware/rateLimit.ts:
  1. Extract required data from request
  2. Perform validation
  3. Either call next() or throw appropriate error
  4. No direct res.status().json() calls"

- "Add the new endpoint to @backend/api/routes/index.ts following the existing routing pattern (group by resource, use route.use() for middleware)"

- "Follow the coding standards documented in @.ai/standards/coding-standards.md:
  - TypeScript strict mode
  - JSDoc for all public functions
  - ESLint with zero warnings
  - Conventional commits"
```

## 3. Scope Creep Enablers

### The Problem

Open-ended requirements that allow unbounded feature expansion.

**❌ Bad Examples:**
```markdown
- "Add user management and any related features"
- "Implement authentication and whatever else is needed"
- "Create a dashboard with relevant widgets"
- "Build a notification system with appropriate delivery methods"
- "Add security features"
- "Include helpful utilities"
```

These invite the agent to:
- Add features you didn't ask for
- Implement authentication + authorization + password reset + 2FA + OAuth
- Exceed the 150-200 instruction limit
- Create maintenance burden

### The Solution

Explicit scope boundaries with "WILL" and "WILL NOT" lists:

**✅ Good Examples:**
```markdown
## Phase 1: Basic User Management

### Scope (WILL implement):
- User registration with email/password
- User login returning JWT token
- User profile viewing (GET /api/users/me)
- Password hashing with bcrypt

### Explicit Exclusions (WILL NOT implement):
- ❌ Password reset (Phase 2)
- ❌ Email verification (Phase 2)
- ❌ OAuth/SSO (Future consideration)
- ❌ 2FA (Future consideration)
- ❌ User roles/permissions (Phase 3)
- ❌ Profile editing (Phase 2)
- ❌ Account deletion (Phase 4)

If you think something outside this scope is necessary for basic functionality,
STOP and ask before implementing.
```

## 4. Context Bloat

### The Problem

Including excessive, irrelevant, or duplicate information that wastes the limited context window.

**❌ Bad Examples:**
```markdown
# Bad PRD with context bloat

## Background
Our company was founded in 2010 with a mission to revolutionize...
[5 paragraphs of company history]

## Previous Attempts
In 2015, we tried to build this feature but failed because...
[Long story about past failures]

## Technology Research
We evaluated 15 different frameworks. Here's our analysis:
[Pages of framework comparisons]

## Team Discussion
In our meeting on Jan 5, Bob suggested we should...
[Transcript of team debate]

## Requirements
[Finally gets to actual requirements, but agent's context is full]
```

This wastes valuable tokens on:
- Historical context agents don't need
- Decision-making process (just give the decision)
- Options not chosen (just document what to build)
- Meeting notes and discussions

### The Solution

Keep PRDs focused on actionable information only:

**✅ Good Examples:**
```markdown
# Focused PRD

## Overview
Build JWT-based authentication for the API.

## Technical Decisions
- Framework: Express.js 4.x (already in stack)
- Auth library: jsonwebtoken v9.0
- Password hashing: bcrypt (12 rounds)
- Token expiration: 24 hours

## Requirements
[Detailed, actionable requirements]

## Reference Documentation
- Architecture decision: @docs/adr/001-jwt-authentication.md
- Security standards: @.ai/standards/security.md
```

Move background to separate docs that can be loaded if needed:
```markdown
For project background and historical context, see @docs/background.md
(Don't load unless specifically relevant to implementation decisions)
```

## 5. Missing Constraints

### The Problem

Omitting performance, security, scalability, or quality requirements.

**❌ Bad Examples:**
```markdown
## Requirements
- Create endpoint to upload files
- Store files in database
- Return file URL

[No mention of:]
- File size limits?
- Allowed file types?
- Virus scanning?
- Access control?
- Performance expectations?
- Error handling?
```

Result: Agent might create an endpoint that:
- Accepts any file size (DoS vulnerability)
- Stores binaries in database (performance issue)
- Has no validation (security risk)
- Has poor error messages
- Doesn't handle edge cases

### The Solution

Always include non-functional requirements:

**✅ Good Examples:**
```markdown
## Functional Requirements
- Create endpoint to upload user profile images

## Constraints and Non-Functional Requirements

### Security
- Validate file type: Only JPEG, PNG (check magic bytes, not just extension)
- Maximum file size: 5MB (reject with clear error message)
- Scan for malware using ClamAV before accepting
- Generate unique filename (UUID) to prevent path traversal
- Validate image dimensions: min 100x100, max 4000x4000

### Performance
- Upload should complete in <10 seconds for 5MB file
- Use streaming upload, not buffer entire file in memory
- Resize images asynchronously (don't block request)
- Generate thumbnails in background job

### Storage
- Store files in S3, not database
- Use signed URLs with 1-hour expiration
- Configure S3 bucket: private, encryption enabled, versioning on

### Access Control
- Users can only upload to their own profile
- Validate JWT token before accepting upload
- Rate limit: max 10 uploads per hour per user

### Error Handling
- File too large: 413 with {"error": "File exceeds 5MB limit"}
- Invalid type: 400 with {"error": "Only JPEG and PNG allowed"}
- Upload failed: 500 with {"error": "Upload failed, try again"}
- Malware detected: 400 with {"error": "File rejected by security scan"}

### Observability
- Log all upload attempts with user ID, file size, type
- Emit metrics: upload_count, upload_duration, upload_size
- Alert on: >10% upload failures, malware detections
```

## 6. Implicit Dependencies

### The Problem

Not documenting required dependencies, environment setup, or prerequisites.

**❌ Bad Examples:**
```markdown
## Requirements
- Implement Redis caching
- Add Stripe payment processing
- Use PostgreSQL full-text search

[No mention of:]
- Redis version?
- Stripe API version?
- PostgreSQL extensions needed?
- Environment variables?
- Migration scripts?
```

Result: Agent doesn't know:
- What versions are compatible
- What needs to be installed
- What configuration is required
- What order to do things in

### The Solution

Document all dependencies and prerequisites explicitly:

**✅ Good Examples:**
```markdown
## Prerequisites

Must be completed before starting:
- [ ] PostgreSQL 15+ installed with pg_trgm extension enabled
- [ ] Redis 7.0+ running and accessible
- [ ] Stripe account created with test API keys
- [ ] Environment variables configured (see below)

## Dependencies

Add to package.json:
```json
{
  "dependencies": {
    "ioredis": "^5.3.0",
    "stripe": "^14.0.0",
    "pg": "^8.11.0"
  }
}
```

## Environment Variables

Required in .env file:
```bash
# Redis
REDIS_URL=redis://localhost:6379
REDIS_KEY_PREFIX=myapp:

# Stripe
STRIPE_API_KEY=sk_test_...    # Test key for development
STRIPE_WEBHOOK_SECRET=whsec_...

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/myapp
```

## Database Setup

Run migrations in order:
```bash
npm run migrate:001-add-trgm-extension
npm run migrate:002-create-search-index
```

## Implementation Order

Must be done in this sequence:
1. Install dependencies: `npm install`
2. Run database migrations
3. Start Redis server
4. Configure environment variables
5. Then implement features
```

## 7. Ambiguous Success Criteria

### The Problem

Unclear or subjective criteria that can't be verified.

**❌ Bad Examples:**
```markdown
- "Should be fast enough"
- "Must be user-friendly"
- "Should handle errors gracefully"
- "Needs good test coverage"
- "Should be maintainable"
```

These are:
- Unmeasurable
- Subjective
- Can't be tested automatically
- Lead to different interpretations

### The Solution

Make every criterion measurable and verifiable:

**✅ Good Examples:**
```markdown
## Success Criteria

### Performance (Measured)
- ✓ API response time: <200ms for 95th percentile
- ✓ Database query time: <50ms average
- ✓ Load test passes: 100 concurrent users, <1% error rate

Verification:
```bash
npm run benchmark  # Must show <200ms p95
npm run loadtest   # Must show <1% errors
```

### Usability (Measured)
- ✓ Error messages include specific action to fix
- ✓ All form validation shows inline errors
- ✓ Loading states show within 100ms

Verification: Manual testing checklist in @tests/usability.md

### Error Handling (Measured)
- ✓ All async functions have try-catch
- ✓ All errors use AppError class
- ✓ No unhandled promise rejections
- ✓ All error responses include error code and message

Verification:
```bash
npm run lint:error-handling  # Custom ESLint rule
npm test -- --testNamePattern="error handling"
```

### Test Coverage (Measured)
- ✓ Overall coverage ≥85%
- ✓ Critical paths coverage: 100%
- ✓ All public APIs have tests
- ✓ All error paths have tests

Verification:
```bash
npm run coverage  # Must show ≥85%
```

### Maintainability (Measured)
- ✓ Cyclomatic complexity <10 per function
- ✓ No functions >50 lines
- ✓ All public functions have JSDoc
- ✓ No code duplication >10 lines

Verification:
```bash
npm run complexity  # SonarQube or similar
npm run docs:coverage  # Check JSDoc coverage
```
```

## 8. Missing Test Strategy

### The Problem

Not specifying what to test or how to verify correctness.

**❌ Bad Examples:**
```markdown
- "Add tests"
- "Should be tested"
- "Include test coverage"
```

Doesn't specify:
- What scenarios to test?
- What test types (unit/integration/e2e)?
- What coverage is required?
- How to run tests?

### The Solution

Detailed test requirements with examples:

**✅ Good Examples:**
```markdown
## Testing Requirements

### Unit Tests (tests/unit/auth.test.ts)

Test the validatePassword function:
```typescript
describe('validatePassword', () => {
  it('returns true for correct password', async () => {
    const hash = await hashPassword('password123');
    expect(await validatePassword('password123', hash)).toBe(true);
  });

  it('returns false for incorrect password', async () => {
    const hash = await hashPassword('password123');
    expect(await validatePassword('wrongpass', hash)).toBe(false);
  });

  it('throws error for empty password', async () => {
    await expect(validatePassword('', 'hash')).rejects.toThrow(ValidationError);
  });
});
```

### Integration Tests (tests/integration/auth-api.test.ts)

Test the POST /api/auth/login endpoint:
```typescript
describe('POST /api/auth/login', () => {
  it('returns token for valid credentials', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({ email: 'test@example.com', password: 'password123' });
    
    expect(response.status).toBe(200);
    expect(response.body.data.token).toMatch(/^eyJ/); // JWT format
  });

  it('returns 401 for invalid credentials', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({ email: 'test@example.com', password: 'wrong' });
    
    expect(response.status).toBe(401);
    expect(response.body.error.code).toBe('INVALID_CREDENTIALS');
  });
});
```

### E2E Tests (tests/e2e/login-flow.test.ts)

Test complete login flow:
```typescript
describe('Login Flow', () => {
  it('completes full authentication flow', async () => {
    // Navigate to login
    await page.goto('/login');
    
    // Fill form
    await page.fill('[name=email]', 'test@example.com');
    await page.fill('[name=password]', 'password123');
    await page.click('button[type=submit]');
    
    // Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    
    // Verify user info displayed
    await expect(page.locator('[data-testid=user-email]')).toHaveText('test@example.com');
  });
});
```

### Coverage Requirements
- Overall: ≥85%
- auth.ts module: 100% (critical path)
- Error handlers: 100%
- Happy paths: 100%

Run tests:
```bash
npm test                    # All tests
npm run test:unit          # Unit tests only
npm run test:integration   # Integration tests only
npm run test:e2e           # E2E tests only
npm run coverage           # Coverage report
```
```

## 9. Lack of Error Scenarios

### The Problem

Only specifying happy path, ignoring error cases.

**❌ Bad Examples:**
```markdown
## Requirements
- User can create an account
- User receives confirmation email

[No mention of:]
- What if email already exists?
- What if email is invalid?
- What if email service is down?
- What if password is too weak?
```

### The Solution

Document all error scenarios explicitly:

**✅ Good Examples:**
```markdown
## User Registration Endpoint

### Success Case
POST /api/auth/register
Request: { email: "user@example.com", password: "SecurePass123!" }
Response: 201 Created
```json
{
  "success": true,
  "data": {
    "id": "usr_123",
    "email": "user@example.com"
  }
}
```

### Error Cases

**Email Already Exists (409 Conflict)**
Request: { email: "existing@example.com", password: "pass123" }
Response:
```json
{
  "success": false,
  "error": {
    "code": "EMAIL_EXISTS",
    "message": "An account with this email already exists"
  }
}
```

**Invalid Email Format (400 Bad Request)**
Request: { email: "notanemail", password: "pass123" }
Response:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_EMAIL",
    "message": "Please provide a valid email address",
    "details": { "field": "email" }
  }
}
```

**Weak Password (400 Bad Request)**
Request: { email: "user@example.com", password: "123" }
Response:
```json
{
  "success": false,
  "error": {
    "code": "WEAK_PASSWORD",
    "message": "Password must be at least 8 characters with uppercase, lowercase, and numbers",
    "details": { "field": "password" }
  }
}
```

**Email Service Failure (503 Service Unavailable)**
When email sending fails:
- Still create the account
- Log the email failure
- Return success to user
- Retry email send in background job

**Database Failure (500 Internal Server Error)**
When database is unavailable:
Response:
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Service temporarily unavailable, please try again"
  }
}
```
- Don't expose internal error details to user
- Log full error with stack trace
- Alert on-call engineer
```

## 10. Monolithic Specifications

### The Problem

Creating one massive PRD instead of phased approach.

**❌ Bad Example:**
```markdown
# PRD: Complete E-Commerce Platform

## Requirements
1. User authentication (20 requirements)
2. Product catalog (30 requirements)
3. Shopping cart (15 requirements)
4. Payment processing (25 requirements)
5. Order management (20 requirements)
6. Inventory tracking (15 requirements)
7. Admin dashboard (20 requirements)
8. Email notifications (10 requirements)
9. Analytics (15 requirements)

Total: 170 requirements [Exceeds 150-200 limit!]
```

This leads to:
- Context window overload
- Implementation confusion
- Increased error rate
- Maintenance difficulty

### The Solution

Break into phases of 30-50 requirements each:

**✅ Good Example:**
```markdown
# PRD: E-Commerce Platform

## Phase 1: User Management (Week 1) - 35 requirements
- User registration
- Login/logout
- Profile management
- Password reset

## Phase 2: Product Catalog (Week 2) - 40 requirements
- Product CRUD
- Categories
- Search
- Filters

## Phase 3: Shopping Experience (Week 3) - 45 requirements
- Shopping cart
- Wishlist
- Product reviews
- Recommendations

## Phase 4: Checkout & Payment (Week 4) - 30 requirements
- Checkout flow
- Stripe integration
- Order confirmation
- Email receipts

[Each phase gets its own detailed specification file]
```

## Summary: PRD Health Checklist

Before finalizing a PRD, verify:

- [ ] ✅ All requirements are specific and actionable
- [ ] ✅ All necessary context is explicit (no assumptions)
- [ ] ✅ Scope boundaries are clearly defined (WILL/WILL NOT lists)
- [ ] ✅ Context is lean (no historical fluff, reference external docs)
- [ ] ✅ All constraints documented (performance, security, scalability)
- [ ] ✅ All dependencies and prerequisites listed with versions
- [ ] ✅ All success criteria are measurable and verifiable
- [ ] ✅ Test strategy is detailed with examples
- [ ] ✅ All error scenarios documented
- [ ] ✅ Requirements divided into phases of 30-50 items each

If any item is unchecked, revise the PRD before sending to the agent.
