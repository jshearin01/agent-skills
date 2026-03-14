# Phase [N]: [Phase Name]

**Estimated Effort:** [X hours/days]  
**Dependencies:** Phase [N-1] must be complete  
**Target Completion:** [Date]

---

## Phase Overview

**Goal:** [1-2 sentence description of what this phase accomplishes]

**Why This Phase:** [Why this phase exists in the sequence - what foundation it builds]

---

## Scope Definition

### Will Implement (In Scope)
- [ ] [Feature/capability with specific details]
- [ ] [Feature/capability with specific details]
- [ ] [Feature/capability with specific details]
- [ ] [Feature/capability with specific details]

### Will NOT Implement (Explicit Exclusions)
- ❌ [Feature/capability] (Reason: Phase [N] / Future / Not planned)
- ❌ [Feature/capability] (Reason: Phase [N] / Future / Not planned)
- ❌ [Feature/capability] (Reason: Phase [N] / Future / Not planned)

**Rationale for Exclusions:** [Brief explanation of why these are excluded]

---

## Prerequisites

Must be complete before starting this phase:

### Previous Phases
- [ ] Phase [N-1]: [Name] - Status: [Complete/In Progress]

### Infrastructure
- [ ] [Infrastructure requirement] installed/configured
- [ ] [Infrastructure requirement] installed/configured

### Documentation
- [ ] [Documentation] available at [location]
- [ ] [Documentation] available at [location]

### Environment Setup
- [ ] Environment variables configured (see below)
- [ ] Database migrations applied
- [ ] Dependencies installed

---

## Dependencies

### External Services
- **[Service Name]:** v[version] or higher
  - Purpose: [Why needed]
  - Documentation: [URL]
  - Authentication: [Requirements]

### Libraries/Packages
- **[Package Name]:** v[version]
  - Installation: `[install command]`
  - Purpose: [Why needed]
  - Configuration: [Location/details]

### Database Requirements
- **Tables:** [List of tables needed]
- **Migrations:** [Migration files to run]
- **Indexes:** [Specific indexes required]

---

## Environment Configuration

### Environment Variables
Required in `.env` file:

```bash
# [Category]
[VAR_NAME]=[example-value]        # Description
[VAR_NAME]=[example-value]        # Description

# [Category]
[VAR_NAME]=[example-value]        # Description
```

### Configuration Files
Additional configuration needed:

**[config-file.json]:**
```json
{
  "key": "value",
  "nested": {
    "key": "value"
  }
}
```

---

## Requirements

### [REQ-[N]-001] [Requirement Title] (MUST/SHOULD/MAY)

**Description:**  
[Detailed description of what needs to be implemented]

**Acceptance Criteria:**
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

**Implementation Details:**
```[language]
// Expected structure/pattern
[code example or pseudocode]
```

**Reference:** Follow pattern in `@[file-path]`

**Test Requirements:**
- Unit tests: [Specific test scenarios]
- Integration tests: [Specific test scenarios]
- Test file: `[path/to/test.spec.ts]`
- Command: `[test command]`

**Success Metric:** [How to measure completion]

**Estimated Effort:** [X hours]

---

### [REQ-[N]-002] [Requirement Title] (MUST/SHOULD/MAY)

[Repeat structure above for each requirement]

---

## Technical Implementation

### File Changes

#### New Files to Create
```
[path/to/new-file.ext]           # Purpose: [Description]
[path/to/new-file.ext]           # Purpose: [Description]
[path/to/new-file.ext]           # Purpose: [Description]
```

#### Existing Files to Modify
```
[path/to/existing-file.ext]      # Changes: [Description]
[path/to/existing-file.ext]      # Changes: [Description]
```

#### Files to Reference (Don't Modify)
```
[path/to/reference-file.ext]     # Use as pattern/example
[path/to/reference-file.ext]     # Use as pattern/example
```

### Database Changes

**Migration File:** `migrations/[NNN]-[description].sql`

```sql
-- Add your migration SQL here
CREATE TABLE IF NOT EXISTS [table_name] (
    [column] [type] [constraints],
    [column] [type] [constraints]
);

CREATE INDEX [index_name] ON [table_name]([column]);
```

**Rollback:**
```sql
-- Rollback SQL
DROP INDEX IF EXISTS [index_name];
DROP TABLE IF EXISTS [table_name];
```

### API Endpoints

#### New Endpoints
```
[METHOD]  [/api/path]
  Purpose: [Description]
  Auth: [Required/Optional]
  Request: [Body/Params format]
  Response: [Format]
  Status Codes: [200, 400, 401, etc.]
```

#### Modified Endpoints
```
[METHOD]  [/api/path]
  Changes: [What's changing]
  Breaking: [Yes/No - explain if yes]
```

---

## Implementation Plan

### Step-by-Step Implementation

**Step 1: [Description]**
- Create: `[file-path]`
- Implement: [Specific functionality]
- Test: `[test command]`
- Verify: [What to check]

**Step 2: [Description]**
- Modify: `[file-path]`
- Add: [Specific functionality]
- Test: `[test command]`
- Verify: [What to check]

**Step 3: [Description]**
[Continue for all steps]

### Implementation Order
```
1. [First task] → Enables [capability]
2. [Second task] → Builds on [previous task]
3. [Third task] → Completes [feature]
```

---

## Testing Strategy

### Unit Tests

**Coverage Target:** [X]% for this phase

**Test Files:**
```
tests/unit/[feature].test.ts
tests/unit/[feature].test.ts
```

**Key Test Scenarios:**
```[language]
describe('[Feature]', () => {
  describe('[Method]', () => {
    it('should [expected behavior] when [condition]', () => {
      // Test implementation
    });
    
    it('should throw [ErrorType] when [invalid condition]', () => {
      // Test implementation
    });
  });
});
```

### Integration Tests

**Test Files:**
```
tests/integration/[feature]-integration.test.ts
```

**Test Scenarios:**
- [ ] [End-to-end scenario]
- [ ] [Error scenario]
- [ ] [Edge case]

### Performance Tests

**Benchmarks:**
```[language]
describe('[Performance]', () => {
  it('should complete [operation] in <[X]ms', async () => {
    // Benchmark implementation
  });
});
```

**Acceptance Criteria:**
- [ ] [Operation]: <[X]ms
- [ ] [Operation]: <[X]ms

---

## Quality Verification

### Code Quality Checks
```bash
# Run all quality checks
npm run lint           # Must pass with 0 errors, 0 warnings
npm run typecheck      # Must pass with 0 errors
npm run test           # Must pass with [X]% coverage
npm run build          # Must succeed
```

### Manual Verification
- [ ] [Specific manual test]
- [ ] [Specific manual test]
- [ ] [Specific manual test]

### Security Checks
```bash
npm audit              # Must have 0 HIGH/CRITICAL vulnerabilities
npm run security-scan  # Must pass all checks
```

---

## Success Criteria

### Functional Success
- [ ] All requirements (REQ-[N]-001 through REQ-[N]-XXX) implemented
- [ ] All acceptance criteria met
- [ ] All tests passing

### Technical Success
- [ ] Code coverage ≥[X]%
- [ ] Build time <[X] minutes
- [ ] API response time <[X]ms ([percentile])
- [ ] No linting errors/warnings
- [ ] No type errors
- [ ] Security scan passes

### Documentation Success
- [ ] All new APIs documented
- [ ] README updated
- [ ] Migration guide written (if breaking changes)
- [ ] Architecture decisions recorded

---

## Breaking Changes

### Identified Breaking Changes
[If none, state "None"]

**Change 1: [Description]**
- **Impact:** [Who/what is affected]
- **Migration Path:** [How to upgrade]
- **Version:** [Version number]

**Change 2: [Description]**
[Repeat as needed]

### Backward Compatibility
- [ ] No breaking changes in this phase
- [ ] Breaking changes documented and communicated
- [ ] Migration guide available
- [ ] Feature flags in place for gradual rollout

---

## Rollback Strategy

### How to Rollback This Phase

**Step 1: Code Rollback**
```bash
git revert [commit-hash]  # Revert code changes
git push
```

**Step 2: Database Rollback**
```bash
npm run migrate:rollback  # Rollback migrations
```

**Step 3: Configuration Rollback**
- Revert environment variables to previous values
- Restore configuration files from backup

**Step 4: Verification**
- [ ] Application starts successfully
- [ ] All tests pass
- [ ] No errors in logs

### Rollback Decision Criteria
Rollback if:
- [ ] Critical bugs discovered
- [ ] Performance degradation >[X]%
- [ ] Security vulnerabilities found
- [ ] Data integrity issues
- [ ] Unable to complete within [timeframe]

---

## Monitoring and Observability

### Metrics to Track
- **Performance:**
  - [Metric name]: Target <[value]
  - [Metric name]: Target <[value]

- **Errors:**
  - Error rate: Target <[X]%
  - [Specific error type]: Target <[X]/hour

- **Usage:**
  - [Feature usage metric]
  - [Feature usage metric]

### Alerts to Configure
- Alert when [metric] exceeds [threshold]
- Alert when [error rate] exceeds [threshold]
- Alert when [condition] occurs

### Logging
Log these events:
- [Event type] with [context]
- [Event type] with [context]

---

## Post-Implementation

### Documentation Updates Required
- [ ] Update `README.md` with new features
- [ ] Update API documentation
- [ ] Create/update architecture diagrams
- [ ] Document architecture decisions in `docs/adr/`

### Communication
- [ ] Notify team of completion
- [ ] Update project status
- [ ] Share lessons learned
- [ ] Update sprint board

### Lessons Learned
[Fill in after implementation]
- What went well:
- What could be improved:
- What to remember for next phase:

---

## Next Phase Preview

**Phase [N+1]: [Name]**
- Builds on this phase by: [Description]
- Prerequisites from this phase: [What must be complete]
- Estimated start: [Date]

---

## References

### Documentation
- Main PRD: `@docs/prd-main.md`
- Architecture: `@docs/architecture.md`
- Standards: `@.ai/standards/`

### Code References
- Pattern to follow: `@[file-path]`
- Example implementation: `@[file-path]`

### External Resources
- [Resource name]: [URL]
- [Resource name]: [URL]
