# PRD: [Project Name]

## Executive Summary

**Project:** [Project Name]  
**Purpose:** [1-2 sentence description of what this project does and why it matters]  
**Success Criteria:** [Key measurable outcomes]  
**Timeline:** [Target launch date or timeline]  
**Strategic Alignment:** [How this fits company/product strategy]

## Strategic Context

**Business Value:** [Why this matters to the business - revenue, cost savings, competitive advantage]

**Market Opportunity:** [Market size, growth rate, timing considerations]

**Competitive Advantage:** [What makes this unique or better than alternatives]

**User Pain Point:** [Specific problem being solved for users]

## Phased Implementation Plan

### Phase 1: [Phase Name] (Estimated: X hours/days)

#### Scope
What WILL be implemented in this phase:
- [ ] Feature A with specific behavior
- [ ] Feature B following pattern in @existing-file.ts
- [ ] Feature C using library X v2.x
- [ ] Feature D with XYZ characteristics

#### Explicit Exclusions
What will NOT be implemented in this phase:
- ❌ [Feature/capability] (Phase [N])
- ❌ [Feature/capability] (Future consideration)
- ❌ [Feature/capability] (Not planned)

#### Prerequisites
Must be complete before starting this phase:
- [ ] Prerequisite 1
- [ ] Prerequisite 2
- [ ] Prerequisite 3

#### Dependencies
External requirements:
- Service/API: [Name] v[version]
- Library: [Name] ≥[version]
- Infrastructure: [Requirement]

#### Success Criteria
Measurable outcomes for this phase:
- [ ] All functional requirements met
- [ ] Unit test coverage ≥85%
- [ ] Performance: [specific metric]
- [ ] Documentation: [specific requirement]
- [ ] Zero [severity] errors/warnings

---

## Functional Requirements

### Feature: [Feature Name]

#### [REQ-001] [Requirement Title] (MUST/SHOULD/MAY)
[Detailed description of the requirement]

**Acceptance Criteria:**
- [ ] Specific testable condition 1
- [ ] Specific testable condition 2
- [ ] Specific testable condition 3

**Implementation Pattern:** [Reference to example or pattern to follow]  
**Test Command:** `[command to run tests]`  
**Success Metric:** [How to measure success]

#### [REQ-002] [Requirement Title] (MUST/SHOULD/MAY)
[Detailed description]

**Acceptance Criteria:**
- [ ] Condition 1
- [ ] Condition 2

**Implementation Pattern:** Follow @path/to/reference-file.ts  
**Test Command:** `npm test -- specific.test.js`  
**Success Metric:** [Specific metric]

---

## Technical Specifications

### Technology Stack
- Backend: [Technology] v[version]
- Frontend: [Technology] v[version]
- Database: [Technology] v[version]
- Caching: [Technology] v[version]
- Testing: [Technology] v[version]

### File Structure
Follow existing pattern:
```
[project-root]/
  [directory]/
    [subdirectory]/  # Purpose
    [subdirectory]/  # Purpose
  [directory]/        # Purpose
```

### Code Standards
See @.ai/standards/coding-standards.md for detailed guidelines.

Key requirements:
- [Standard 1]
- [Standard 2]
- [Standard 3]
- Error handling: ALWAYS use [ErrorClass]
- Logging: [Specific requirement]

### Database Schema
See @database/schema.sql for complete schema.

Tables needed for this phase:
- [table_name] ([columns])
- [table_name] ([columns])

### API Design
Follow REST conventions in @.ai/standards/api-design.md

Endpoints for this phase:
```
[METHOD]   [/api/path]      # Description
[METHOD]   [/api/path]      # Description
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

---

## Non-Functional Requirements

### Performance
- API response time: <[X]ms ([percentile])
- Database query time: <[X]ms ([percentile])
- Maximum concurrent users: [number]
- Cache hit rate: >[X]%

### Security
- [Specific security requirement]
- [Specific security requirement]
- [Specific security requirement]
- Input validation: [Specific requirement]
- Authentication: [Specific requirement]

### Reliability
- Uptime target: [X]%
- Error rate: <[X]%
- Retry strategy: [Specific approach]
- Database: [Specific requirement]

### Scalability
- Horizontal scaling: [Approach]
- Database: [Scaling strategy]
- Caching: [Approach]
- Rate limiting: [Specific limits]

### Maintainability
- Code coverage: ≥[X]%
- Documentation coverage: [X]% of public APIs
- Linting: Zero errors, zero warnings
- Type safety: [Requirement]

---

## Error Handling Standards

### Error Class Usage
ALWAYS use the [ErrorClass]:

```[language]
// Correct
[example of correct error handling]

// Incorrect - NEVER do this
[example of incorrect error handling]
```

### Error Categories
Follow patterns in @path/to/errors.ts:

- [ErrorType]: [Description] ([HTTP Status])
- [ErrorType]: [Description] ([HTTP Status])
- [ErrorType]: [Description] ([HTTP Status])

### Error Logging
```[language]
// Include context in error logs
[example of proper error logging]
```

---

## Documentation Requirements

### Code Comments
- Every function: [Documentation standard] with description, parameters, returns, examples
- Complex logic: Inline comments explaining "why," not "what"
- Public APIs: [Documentation format]

Example:
```[language]
/**
 * [Description]
 * 
 * @param {[Type]} [name] - [description]
 * @returns {[Type]} [description]
 * @throws {[ErrorType]} [condition]
 * 
 * @example
 * [example usage]
 */
```

### API Documentation
- Generate [format] from code comments
- Serve at [path]
- Include authentication examples

### README Updates
Update project README.md with:
- New features added
- Environment variables required
- Migration instructions
- Breaking changes (if any)

---

## Testing Strategy

### Test Coverage Requirements
- Overall coverage: ≥[X]%
- Critical paths: [X]%
- Edge cases: All identified scenarios

### Unit Tests
Test individual functions in isolation:
```[language]
// [path to test file]
describe('[Component]', () => {
  describe('[method]', () => {
    it('should [expected behavior]', async () => {
      // Arrange
      [setup code]
      
      // Act
      [action code]
      
      // Assert
      [assertion code]
    });
  });
});
```

### Integration Tests
Test component interactions:
```[language]
// [path to integration test]
describe('[Feature]', () => {
  it('should [complete workflow]', async () => {
    // Test implementation
  });
});
```

### E2E Tests
Test complete user flows:
```[language]
// [path to e2e test]
describe('[User Flow]', () => {
  it('should [complete scenario]', async () => {
    // Test implementation
  });
});
```

### Performance Tests
Benchmark critical operations:
```[language]
// [path to performance test]
describe('[Performance]', () => {
  it('should [meet benchmark]', async () => {
    // Benchmark implementation
  });
});
```

---

## Success Metrics

### Technical Metrics
- ✅ Test coverage ≥[X]%
- ✅ Build time <[X] minutes
- ✅ API response time <[X]ms ([percentile])
- ✅ Error rate <[X]%
- ✅ Zero [severity] errors/warnings
- ✅ All security scans pass

### Business Metrics (if applicable)
- [Metric]: [Target]
- [Metric]: [Target]
- [Metric]: [Target]

### AI-Specific Metrics (for AI features)
- Model accuracy ≥[X]%
- Hallucination rate <[X]%
- Response latency <[X]s
- User satisfaction ≥[X]/5.0

---

## Implementation Workflow

### 1. Pre-Implementation Planning
Before writing code, provide:

1. **File Plan:**
   - List all files to be created
   - List all files to be modified
   - Explain purpose of each file

2. **Implementation Steps:**
   - Step-by-step sequence
   - Dependencies between steps
   - Verification points

3. **Breaking Changes:**
   - List backwards-incompatible changes
   - Migration path
   - Version compatibility

4. **Rollback Strategy:**
   - How to revert if needed
   - Data rollback procedures
   - Feature flag configuration

### 2. Iterative Development
For each requirement:
1. Implement the feature
2. Write/update tests
3. Run tests: `[test command]`
4. Fix any failures
5. Verify against acceptance criteria
6. Move to next requirement

### 3. Quality Verification
After implementation:

Quality checklist:
- [ ] All tests pass: `[test command]`
- [ ] Coverage meets threshold: `[coverage command]`
- [ ] No linting errors: `[lint command]`
- [ ] No type errors: `[typecheck command]`
- [ ] Build succeeds: `[build command]`
- [ ] Documentation generated: `[docs command]`
- [ ] Security scan passes: `[security command]`

### 4. Git Integration
Commit with standards:

```
[type]([scope]): [subject]

[body]

[footer]
```

Example:
```
feat(auth): add JWT authentication middleware

- Implement token generation and validation
- Add authentication middleware for protected routes
- Include comprehensive test suite (95% coverage)
- Update API documentation

Closes #[issue-number]
```

---

## Context Files Reference

### Required Reading
- `@.ai/standards/coding-standards.md` - Always follow
- `@.ai/standards/error-handling.md` - For error patterns
- `@database/schema.sql` - For database structure

### Optional Reading (Load as Needed)
- `@.ai/patterns/authentication.md` - When implementing auth
- `@.ai/patterns/caching.md` - When implementing caching
- `@docs/adr/` - For architecture decisions

---

## Verification Checklist

Before considering implementation complete:

- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Coverage meets threshold
- [ ] No linting errors
- [ ] No type errors
- [ ] Documentation updated
- [ ] Examples provided
- [ ] Edge cases handled
- [ ] Error messages user-friendly
- [ ] Security vulnerabilities addressed
- [ ] Performance benchmarks met

For any item not checked, explain the blocker.

---

## Notes and Considerations

[Add any additional notes, considerations, or context specific to this project]
