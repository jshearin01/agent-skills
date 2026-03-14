# LLM Coding Agents Context

Understanding different AI coding agents and their capabilities to optimize PRD specifications.

## Agent Autonomy Levels

### Level 1-2: Basic Autocomplete
- Single-line code completion
- Context: Few lines around cursor
- Examples: Basic GitHub Copilot, TabNine
- **PRD Optimization:** Not applicable (doesn't consume PRDs)

### Level 3: Supervised Agents
- Multi-file read/write capability
- Request permission at each step
- Human-in-the-loop for every action
- Examples: Cursor Agent Mode, Windsurf IDE, Cline
- **PRD Optimization:**
  - Clear step-by-step instructions
  - Explain each step's purpose
  - Include verification points
  - Specify when to ask for permission

### Level 4: Autonomous Agents
- Execute multi-step plans with minimal supervision
- Iterate on failures independently
- Complete entire features
- Humans review outcomes, not every action
- Examples: Claude Code, Aider, Devin AI
- **PRD Optimization:**
  - Phased specifications (30-50 requirements)
  - Explicit success criteria
  - Self-verification instructions
  - Clear boundaries and constraints

### Level 5: Experimental Fully Autonomous
- Operate for hours/days on complex projects
- Minimal human direction
- Not production-ready yet (context limitations, brittleness)
- **PRD Optimization:** Not recommended for production use

**Most practical tools in 2025: Level 3-4**

## Major Coding Agents

### Claude Code

**Type:** Terminal-first autonomous agent (Level 4)

**Key Capabilities:**
- 200k token context window (reliable, doesn't reduce)
- Deep codebase reasoning and navigation
- Multi-step autonomous workflows
- Excellent at tests and version control
- Plan Mode for complex tasks
- Extended Thinking for deep reasoning
- Subagents for specialized tasks

**Context System:**
- Reads CLAUDE.md files (hierarchical)
- Supports AGENTS.md (via symlink or directive)
- .claude/rules/ for path-specific instructions
- .claude/skills/ for reusable procedures
- Cascading context: enterprise → project → local

**PRD Optimization:**
```markdown
## For Claude Code

### Context Files
Create CLAUDE.md in project root:
```markdown
# Project Context

See @AGENTS.md for detailed project information.

## Quick Reference
- Tech stack: Node.js 20, TypeScript, PostgreSQL
- Test command: npm test
- Build command: npm run build
- Standards: See @.ai/standards/
```

### Leverage Strengths
- Multi-file refactoring: Specify all files to modify
- Test iteration: Let it run tests and fix failures
- Commit messages: Allow it to generate detailed commits
- Documentation: Have it update docs automatically

### Example PRD Section
```markdown
## Implementation Steps

1. Create database migration:
   - File: migrations/003-add-sessions.sql
   - Add sessions table with columns from @database/schema.sql

2. Create session model:
   - File: backend/models/session.ts
   - Follow pattern in @backend/models/user.ts

3. Implement session service:
   - File: backend/services/session.ts
   - Methods: create, validate, invalidate, cleanup
   - Tests: backend/services/session.test.ts

4. Add middleware:
   - File: backend/middleware/session.ts
   - Validate session on protected routes

5. Run tests and iterate until all pass
6. Generate commit with conventional commits format
```

**Execution:**
```bash
claude code  # In project directory
# Agent reads CLAUDE.md, understands context, executes plan
```

### Cursor

**Type:** IDE-integrated supervised agent (Level 3)

**Key Capabilities:**
- VS Code-based familiar interface
- 128K context (normal), 200K context (max mode - may reduce for performance)
- Agent modes: Ask, Manual, Agent
- Tab completion and inline edits
- Background agent execution
- GUI-first experience

**Context System:**
- Reads .cursorrules files
- Supports AGENTS.md
- .cursor/rules/ for path-specific rules (with frontmatter)
- Custom documentation injection
- RAG-like system on local filesystem

**PRD Optimization:**
```markdown
## For Cursor

### Context Files
Create .cursorrules in project root (or symlink to AGENTS.md):
```markdown
---
title: Project Rules
description: Core development standards
---

# Tech Stack
- Backend: Express.js + TypeScript
- Database: PostgreSQL with TypeORM
- Testing: Jest

# Standards
- See @.ai/standards/coding-standards.md
- All functions need JSDoc
- Use AppError for error handling

# Commands
- Test: npm test
- Build: npm run build
- Lint: npm run lint
```

### Leverage Strengths
- Visual file editing: Specify exact changes needed
- Inline completions: Provide examples to autocomplete
- GUI workflow: User can review changes in editor
- Quick iterations: Fast feedback loop

### Example PRD Section
```markdown
## File Modifications

### backend/api/routes/auth.ts
Add these routes after existing routes:
```typescript
router.post('/register', validateInput, authController.register);
router.post('/verify-email', authController.verifyEmail);
```

### backend/controllers/auth.ts
Add these controller methods:
```typescript
async register(req, res, next) {
  // Implementation follows pattern from login method above
  // 1. Validate input
  // 2. Check if user exists
  // 3. Hash password
  // 4. Create user
  // 5. Send verification email
  // 6. Return success
}
```

Expected output shows file diffs for review before accepting.
```

### Devin AI

**Type:** Fully autonomous software engineer (Level 4)

**Key Capabilities:**
- Natural language interface
- Plans, codes, tests, deploys complete features
- Multi-day autonomous execution
- Accessible to non-technical stakeholders
- Full-stack project handling

**Context System:**
- Natural language specifications
- Can access documentation
- Web research capability
- Integration with various tools

**Pricing:** ACU-based (starts ~$20/month prepaid)

**PRD Optimization:**
```markdown
## For Devin

### Natural Language Specification
Write PRDs in plain, descriptive language:

"Create a user authentication system with the following capabilities:

1. Users can register with email and password
2. Passwords must be at least 8 characters with uppercase, lowercase, and numbers
3. Send verification email after registration
4. Users can log in with verified accounts
5. Issue JWT tokens that expire after 24 hours
6. Protected endpoints require valid JWT

Technical requirements:
- Use PostgreSQL for data storage
- Use bcrypt for password hashing (12 rounds)
- Use nodemailer for emails
- Use jsonwebtoken for JWT
- Write tests with Jest (>85% coverage)
- Follow RESTful API design

Success criteria:
- All tests pass
- API responds in <200ms
- No security vulnerabilities
- Comprehensive documentation"

### Leverage Strengths
- High-level specifications work well
- Can research and choose implementations
- Handles full project lifecycle
- Good for stakeholder-driven development

### Considerations
- Higher cost than other agents
- Less control over implementation details
- Best for complete features vs. specific modifications
```

### Aider

**Type:** Terminal CLI autonomous agent (Level 4)

**Key Capabilities:**
- Editor-agnostic (works with any IDE)
- Supports multiple LLM backends (Claude, GPT-4, DeepSeek, local models)
- Git integration
- Mature open-source tool
- Cost-effective (pay only for LLM API usage)

**Context System:**
- Reads .aider.conf.yml for configuration
- Can use AGENTS.md
- Git integration for context
- Map/plan/edit workflow

**PRD Optimization:**
```markdown
## For Aider

### Configuration File
Create .aider.conf.yml:
```yaml
model: claude-opus-4
edit-format: diff
auto-commits: true
test-cmd: npm test
lint: true
```

### Leverage Strengths
- Git integration: Specify commit requirements
- Model flexibility: Use best model for task
- Terminal-native: Great for automation
- Open source: Customizable workflows

### Example PRD Section
```markdown
## Implementation Requirements

Run implementation in this order:
1. Create models: `aider --message "Create User model in models/user.ts following TypeORM patterns"`
2. Create service: `aider --message "Create UserService in services/user.ts with register and login methods"`
3. Add tests: `aider --message "Add comprehensive tests for UserService"`
4. Create API: `aider --message "Create /api/auth routes using the UserService"`

After each step, verify:
- Tests pass: `npm test`
- Linting passes: `npm run lint`
- Types check: `npm run typecheck`
```

## Context File Systems

### AGENTS.md (Universal Standard)

**Purpose:** Cross-tool standard for AI-specific instructions

**Supported By:** Claude Code, Cursor, GitHub Copilot, Gemini CLI, Codex

**Best Practices:**
```markdown
# AGENTS.md

## Project Overview
Brief description of the project and its purpose.

## Tech Stack
- List all technologies and versions
- Include framework choices
- Document build tools

## Project Structure
```
src/
  api/       # REST API endpoints
  services/  # Business logic
  models/    # Data models
  utils/     # Helper functions
```

## Development Commands
```bash
npm test           # Run all tests
npm run lint       # Check code quality
npm run build      # Production build
npm run dev        # Development server
```

## Coding Standards
- TypeScript strict mode
- ESLint with our config
- Prettier for formatting
- Conventional commits

## Testing Strategy
- Unit tests for all services
- Integration tests for APIs
- E2E tests for critical flows
- Coverage minimum: 85%

## Common Patterns
See @.ai/patterns/ for reusable code patterns.

## Architecture Decisions
See @docs/adr/ for architecture decision records.
```

**Progressive Disclosure:**
Use nested AGENTS.md files for module-specific context:
```
project/
  AGENTS.md                    # Root context
  backend/
    AGENTS.md                  # Backend-specific context
    api/
      AGENTS.md                # API-specific context
```

**Integration Pattern:**
```bash
# Create symlinks for multi-tool compatibility
ln -s AGENTS.md CLAUDE.md
ln -s AGENTS.md .cursorrules
```

### CLAUDE.md (Claude Code Specific)

**Purpose:** Hierarchical memory for Claude Code

**Structure:**
```markdown
# CLAUDE.md

See @AGENTS.md for project details.

## Claude Code Specific

### Skills
This project uses these Claude Code skills:
- authentication-patterns (@.claude/skills/auth/)
- testing-helpers (@.claude/skills/testing/)

### Subagents
Available specialized agents:
- @bugbot: Focuses on finding and fixing bugs
- @testbot: Writes comprehensive tests
- @docbot: Updates documentation

### Workflow
1. Read requirements from @docs/current-sprint.md
2. Implement following @.ai/standards/
3. Test with `npm test`
4. Commit using conventional commits
```

### .cursorrules (Cursor Specific)

**Purpose:** Cursor IDE configuration

**Format:** MDX with frontmatter
```markdown
---
title: Project Rules
description: Development standards for this project
tags: [typescript, nodejs, react]
auto-attach: "**/*.{ts,tsx,js,jsx}"
type: always
---

# Project Standards

## File Organization
- Components in `components/`
- Utilities in `utils/`
- Types in `types/`

## Naming Conventions
- Components: PascalCase
- Functions: camelCase
- Constants: UPPER_SNAKE_CASE

## Code Style
Follow @.ai/standards/code-style.md
```

**Path-Specific Rules:**
```
.cursor/
  rules/
    always/
      base-rules.md         # Always loaded
    auto-attach/
      api-*.md             # Loaded for API files
      component-*.md       # Loaded for components
    manual/
      advanced.md          # Load with @advanced
```

### Copilot Instructions

**Purpose:** GitHub Copilot configuration

**Location:** `.github/copilot-instructions.md`

**Format:**
```markdown
# GitHub Copilot Instructions

## Project Context
This is a Node.js backend API using TypeScript, Express, and PostgreSQL.

## Code Preferences
- Use async/await, not callbacks
- Prefer functional programming
- Use TypeScript strict mode
- Follow ESLint rules

## Test Preferences
- Use Jest for testing
- Write tests in .test.ts files
- Aim for >85% coverage
- Test both happy and error paths

## Common Patterns
Error handling:
```typescript
try {
  const result = await operation();
  return result;
} catch (error) {
  throw new AppError(error.message, 'ERROR_CODE', 500);
}
```
```

## Context Window Management

### Understanding Context Limits

**Frontier Models (2025):**
- Claude Opus/Sonnet: ~200k tokens
- GPT-4 Turbo: ~128k tokens
- Gemini Pro: ~1M tokens (highest)

**Effective Instruction Limit: 150-200 instructions**
- Beyond this, performance degrades
- Think of context as limited "attention budget"
- Retrieval performance decreases with each token

### Context Engineering Strategies

**1. Progressive Disclosure**
```markdown
Don't load everything at once. Instead:

"For database schema, see @database/schema.sql"
"For API patterns, reference @backend/api/users.ts"
"For auth implementation, read @.ai/guides/authentication.md"

The agent loads only when needed.
```

**2. Hierarchical Context**
```
project/
  AGENTS.md                 # High-level context (always loaded)
  .ai/
    standards/
      coding-standards.md   # Load when writing code
      api-design.md         # Load when creating APIs
      testing.md            # Load when writing tests
    patterns/
      authentication.md     # Load for auth features
      caching.md           # Load for caching features
    guides/
      setup.md             # Load for initial setup
```

**3. Context Compaction**
```markdown
# Instead of this (wasteful):
## Background
[5 paragraphs about company history]

## Previous Attempts
[Long story about past failures]

## Requirements
[Actual requirements]

# Do this (efficient):
## Requirements
[Detailed requirements]

## Additional Context
For background, see @docs/background.md (load only if needed)
```

**4. Clear Context Between Tasks**
```markdown
After completing Phase 1, start a new conversation for Phase 2.
This prevents Phase 1 context from cluttering Phase 2 implementation.

Or use:
- `/clear` command (Claude Code)
- New chat tab (Cursor)
```

**5. Reference Don't Duplicate**
```markdown
❌ Duplicate database schema in PRD
✅ "Use schema from @database/schema.sql"

❌ Copy entire coding standards
✅ "Follow @.ai/standards/coding-standards.md"

❌ Repeat API examples
✅ "Follow pattern in @backend/api/users.ts"
```

### Measuring Context Usage

**Approximate token counts:**
- 1 token ≈ 4 characters or 0.75 words
- Typical function: 100-300 tokens
- PRD phase: 1,000-3,000 tokens
- Large file: 5,000-10,000 tokens

**Context budget example (200k tokens):**
- System prompt: 20k tokens (10%)
- AGENTS.md: 2k tokens (1%)
- PRD current phase: 3k tokens (1.5%)
- Referenced files: 10k tokens (5%)
- Conversation history: 15k tokens (7.5%)
- **Available for work: 150k tokens (75%)**

## Tool Integration (MCP)

### Model Context Protocol

**Purpose:** Standardized protocol for LLM tool integration

**Enables:**
- Database queries
- API calls
- File system operations
- External service integration

**PRD Integration:**
```markdown
## Available Tools (MCP)

This project has MCP servers configured for:

### Database (PostgreSQL MCP)
Query database directly:
```
Available operations:
- SELECT queries (read-only by default)
- INSERT for test data
- Schema inspection

Rate limits: 100 queries/minute
```

### GitHub MCP
Interact with GitHub:
```
Available operations:
- Create issues
- Create PRs
- Search code
- Fetch file contents

Authentication: Uses GITHUB_TOKEN from environment
```

### Slack MCP
Send notifications:
```
Available operations:
- Post messages
- Send alerts
- Update status

When to use: Notify team when deployment completes
```

## When to Use
The agent can use these tools during implementation.
Specify when tools should be used:

"After successful deployment, use Slack MCP to notify #engineering channel"
"Use GitHub MCP to create issue if tests fail"
"Query database using MCP to verify migration succeeded"
```

## Agent Selection Guide

**Choose Claude Code when:**
- Terminal workflow preferred
- Complex multi-file refactoring needed
- Deep codebase understanding required
- Test-driven development approach
- Autonomous execution desired
- Cost-conscious (pay per use)

**Choose Cursor when:**
- IDE integration preferred
- Visual feedback desired
- Frequent human oversight needed
- Learning AI coding (supervised)
- Team uses VS Code

**Choose Devin when:**
- Non-technical stakeholders driving development
- Complete feature implementation needed
- Budget allows ($500+/month)
- Minimal technical oversight available
- Full lifecycle automation desired

**Choose Aider when:**
- Open source preferred
- Model flexibility needed (can use any LLM)
- Terminal workflow comfortable
- Budget constrained
- Customization needed

## Summary

**PRD optimization by agent type:**

**For Autonomous Agents (Claude Code, Aider, Devin):**
- Phased specifications (30-50 requirements)
- Explicit success criteria
- Self-verification steps
- Clear boundaries
- Reference documentation

**For Supervised Agents (Cursor, Cline):**
- Step-by-step instructions
- Verification points
- Visual file references
- Approval gates
- Detailed examples

**Universal best practices:**
- Use AGENTS.md for cross-tool compatibility
- Progressive context disclosure
- Reference don't duplicate
- Measure context usage
- Clear context between phases
