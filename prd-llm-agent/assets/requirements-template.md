# Requirement Template

Use this template for documenting individual requirements to ensure consistency and completeness.

---

## [REQ-XXX] [Requirement Title]

**Priority:** MUST / SHOULD / MAY  
**Category:** [Functional / Non-Functional / Security / Performance]  
**Phase:** [Phase number/name]  
**Estimated Effort:** [X hours]  
**Assigned To:** [Agent/Team] (if applicable)

---

### Description

[Clear, detailed description of what needs to be implemented. Be specific about the behavior, inputs, outputs, and edge cases.]

**User Story (if applicable):**  
As a [role], I want to [action] so that [benefit].

---

### Acceptance Criteria

**Must Have:**
- [ ] [Specific, testable condition that must be met]
- [ ] [Specific, testable condition that must be met]
- [ ] [Specific, testable condition that must be met]

**Should Have:**
- [ ] [Desirable condition that should be met]
- [ ] [Desirable condition that should be met]

**Success Looks Like:**
[Describe the end state when this requirement is successfully implemented]

---

### Technical Specification

#### Implementation Approach

**Pattern to Follow:**  
Reference: `@[path/to/reference-file]`

**Code Structure:**
```[language]
// Expected structure or pseudocode
[example implementation pattern]
```

**Key Decisions:**
- [Technical decision and rationale]
- [Technical decision and rationale]

#### Files Affected

**Create:**
```
[path/to/new-file.ext]           # Purpose: [description]
[path/to/new-file.ext]           # Purpose: [description]
```

**Modify:**
```
[path/to/existing-file.ext]      # Changes: [description]
[path/to/existing-file.ext]      # Changes: [description]
```

**Reference:**
```
[path/to/reference-file.ext]     # Use as: [pattern/example]
```

---

### Input/Output Specification

#### Input

**Format:**
```[language or json]
{
  "field1": "type and constraints",
  "field2": "type and constraints"
}
```

**Validation Rules:**
- `field1`: [validation rules]
- `field2`: [validation rules]

**Example Valid Input:**
```[language or json]
{
  "field1": "example-value",
  "field2": "example-value"
}
```

**Example Invalid Input:**
```[language or json]
{
  "field1": "invalid-value"  // Reason why invalid
}
```

#### Output

**Success Response:**
```[language or json]
{
  "success": true,
  "data": {
    "field1": "value",
    "field2": "value"
  },
  "error": null
}
```

**Error Response:**
```[language or json]
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "User-friendly error message",
    "details": {
      "field": "problematic-field",
      "reason": "specific-reason"
    }
  }
}
```

---

### Error Handling

#### Error Scenarios

**Scenario 1: [Error Condition]**
- **Trigger:** [What causes this error]
- **Error Code:** `ERROR_CODE`
- **HTTP Status:** [Status Code]
- **User Message:** "[User-friendly message]"
- **Logging:** [What to log]
- **Recovery:** [How to recover/retry]

**Scenario 2: [Error Condition]**
[Repeat structure for each error scenario]

#### Error Handling Pattern

```[language]
try {
  // Implementation
} catch (error) {
  if (error instanceof [ErrorType]) {
    // Handle specific error
    throw new AppError('[message]', '[CODE]', [status]);
  }
  // Handle unknown errors
  logger.error('[context]', { error, [context] });
  throw new AppError('[message]', 'INTERNAL_ERROR', 500);
}
```

---

### Dependencies

#### Prerequisites
- [ ] [Prerequisite requirement or component]
- [ ] [Prerequisite requirement or component]

#### External Dependencies
- **[Library/Service Name]:** v[version]
  - Purpose: [Why needed]
  - Installation: `[command]`
  - Configuration: [Details]

#### Internal Dependencies
- Depends on: [REQ-XXX] [Requirement Name]
- Blocks: [REQ-XXX] [Requirement Name]

---

### Testing Requirements

#### Unit Tests

**Test File:** `[path/to/test-file.test.ts]`

**Test Cases:**
```[language]
describe('[Component/Function]', () => {
  describe('[method or functionality]', () => {
    it('should [expected behavior] when [condition]', () => {
      // Arrange
      [setup]
      
      // Act
      [execution]
      
      // Assert
      expect([result]).to[assertion];
    });
    
    it('should throw [ErrorType] when [invalid condition]', () => {
      // Test error case
    });
    
    it('should handle [edge case]', () => {
      // Test edge case
    });
  });
});
```

**Coverage Target:** [X]% for this component

#### Integration Tests

**Test File:** `[path/to/integration-test.test.ts]`

**Test Scenarios:**
- [ ] Happy path: [Description]
- [ ] Error path: [Description]
- [ ] Edge case: [Description]

```[language]
describe('[Feature] Integration', () => {
  it('should [complete workflow]', async () => {
    // Test complete integration flow
  });
});
```

#### E2E Tests (if applicable)

**Test File:** `[path/to/e2e-test.test.ts]`

**User Flow:**
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Verify outcome]

```[language]
describe('[User Flow]', () => {
  it('should allow user to [complete task]', async () => {
    // Test user interaction flow
  });
});
```

---

### Performance Requirements

#### Performance Targets
- Execution time: <[X]ms ([percentile])
- Memory usage: <[X]MB
- Database queries: <[X] per operation
- Cache hit rate: >[X]%

#### Performance Tests
```[language]
describe('[Performance]', () => {
  it('should [operation] in <[X]ms', async () => {
    const start = Date.now();
    await [operation]();
    const duration = Date.now() - start;
    expect(duration).toBeLessThan([X]);
  });
});
```

**Load Testing:**
- Concurrent users: [number]
- Expected throughput: [requests/second]
- Success rate: >[X]%

---

### Security Considerations

#### Security Requirements
- [ ] [Specific security requirement]
- [ ] [Specific security requirement]
- [ ] [Specific security requirement]

#### Threat Model
- **Threat:** [Description of threat]
  - **Mitigation:** [How it's addressed]
  - **Validation:** [How to verify mitigation]

#### Security Testing
```[language]
describe('[Security]', () => {
  it('should prevent [security threat]', async () => {
    // Test security measure
  });
});
```

---

### Documentation Requirements

#### Code Documentation
```[language]
/**
 * [Function description]
 * 
 * [Detailed explanation if needed]
 * 
 * @param {[type]} [name] - [description]
 * @param {[type]} [name] - [description]
 * @returns {[type]} [description]
 * @throws {[ErrorType]} [when condition]
 * 
 * @example
 * ```[language]
 * [example usage]
 * ```
 */
```

#### API Documentation
- Endpoint: `[METHOD] [/api/path]`
- Description: [What it does]
- Authentication: [Required/Optional]
- Rate Limiting: [Limits]
- Example request/response in OpenAPI format

#### User Documentation
- [ ] Update user guide
- [ ] Add examples
- [ ] Document limitations
- [ ] Include screenshots/diagrams (if applicable)

---

### Success Metrics

#### Functional Metrics
- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Code review approved

#### Technical Metrics
- [ ] Test coverage ≥[X]%
- [ ] Performance benchmarks met
- [ ] No linting errors
- [ ] No type errors
- [ ] Security scan passes

#### Business Metrics (if applicable)
- [Metric]: [Target value]
- [Metric]: [Target value]

---

### Verification Checklist

Before marking this requirement complete, verify:

- [ ] Implementation matches specification
- [ ] All acceptance criteria met
- [ ] All tests written and passing
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Performance benchmarks met
- [ ] Security requirements satisfied
- [ ] No regressions introduced
- [ ] Edge cases handled
- [ ] Error messages user-friendly

**If any item is unchecked, document the blocker:** [Blocker description]

---

### Implementation Notes

#### Assumptions Made
- [Assumption 1 and justification]
- [Assumption 2 and justification]

#### Design Decisions
- [Decision 1 and rationale]
- [Decision 2 and rationale]

#### Alternative Approaches Considered
- **Approach 1:** [Description]
  - Pros: [Benefits]
  - Cons: [Drawbacks]
  - Why not chosen: [Reason]

---

### Rollback Plan

#### How to Rollback
1. [Step 1 to revert changes]
2. [Step 2 to revert changes]
3. [Verification step]

#### Rollback Criteria
Rollback if:
- [ ] [Critical condition]
- [ ] [Critical condition]
- [ ] [Critical condition]

---

### Related Requirements

#### Depends On
- [REQ-XXX]: [Requirement name and relationship]

#### Blocks
- [REQ-XXX]: [Requirement name and relationship]

#### Related
- [REQ-XXX]: [Requirement name and relationship]

---

### Timeline

**Estimated Start:** [Date]  
**Estimated Completion:** [Date]  
**Actual Start:** [Date] (fill in during implementation)  
**Actual Completion:** [Date] (fill in during implementation)  

**Blockers/Delays:** [Document any blockers or delays]

---

### Change Log

#### Version History
- **v1.0** ([Date]): Initial requirement specification
- **v1.1** ([Date]): [Changes made]
- **v1.2** ([Date]): [Changes made]

---

### References

#### Internal Documentation
- Main PRD: `@docs/prd-main.md`
- Phase Documentation: `@docs/phase-[N].md`
- Related Requirements: `@docs/requirements/`

#### Code References
- Pattern to follow: `@[file-path]`
- Example implementation: `@[file-path]`

#### External Resources
- [Resource name]: [URL]
- [Resource name]: [URL]

---

### Questions and Clarifications

[Document any questions or needed clarifications during implementation]

**Q:** [Question]  
**A:** [Answer] ([Date])

**Q:** [Question]  
**A:** [Answer] ([Date])
