# Security-by-Design Reference

## Table of Contents
1. Security Architecture Principles
2. Authentication Foundation
3. Authorization Patterns
4. API Security
5. Data Protection
6. Zero Trust Service Mesh
7. Secrets Management
8. Security Checklist by Stage
9. Threat Modeling Lightweight Process

---

## 1. Security Architecture Principles

These principles come from Saltzer & Schroeder (1975), OWASP, and NIST SP 800-160. They've stood the test of 50 years because they are fundamental truths about secure systems.

### Economy of Mechanism
Keep security designs as simple as possible. Complex security is broken security — it's harder to verify, harder to maintain, and more likely to contain flaws. Prefer well-understood, battle-tested security libraries over custom implementations.

### Fail-Safe Defaults
Base access decisions on permission (allowlist), not exclusion (denylist). When a system fails or encounters an unexpected state, it should deny access by default. A user should have no access until explicitly granted.

### Complete Mediation
Check authorization on every access to every resource. Don't cache authorization decisions longer than necessary. Don't assume that because a user was authorized for request N, they're authorized for request N+1.

### Least Privilege
Every component, service, user, and process should operate with the minimum permissions necessary. Database connections should use read-only credentials when only reading. Services should only have access to the specific resources they need.

### Defense in Depth
Never rely on a single security control. Layer your defenses: input validation at the edge AND in the service, authentication at the API gateway AND verified in the service, encryption in transit AND at rest.

### Secure by Default
The default configuration of any system should be secure. Insecure behavior should require explicit opt-in with clear documentation of the risks. Configuration files, APIs, and frameworks should produce secure behavior when used with default settings.

### Don't Trust Services
External services (and even internal ones) should be treated as potentially compromised. Validate all input from other services. Use mTLS for service-to-service communication. Apply rate limiting even to internal APIs.

---

## 2. Authentication Foundation

Authentication answers: "Who are you?" Get this right early — retrofitting authentication is painful and error-prone.

### Recommended Approach by Stage

**Stage 0–1 (most projects)**: Use a managed identity provider.
- Auth0, Clerk, Firebase Auth, AWS Cognito, or Supabase Auth
- Why: Authentication is a solved problem with critical security implications. Don't build your own unless you have a specific, justified reason.
- Implement: OAuth 2.0 / OpenID Connect for user-facing auth, API keys or JWT for service-to-service

**Stage 2+ (if needed)**: Self-hosted identity (Keycloak, Ory) for control and compliance.
- Only when regulatory requirements or scale demands justify the operational cost

### JWT Best Practices
- Use short-lived access tokens (5–15 minutes) with longer-lived refresh tokens
- Store refresh tokens server-side (not in localStorage — use httpOnly cookies)
- Include only necessary claims in the token (user ID, roles — not full profile)
- Validate tokens on every request (signature, expiration, issuer, audience)
- Use RS256 (asymmetric) for tokens that cross service boundaries; HS256 (symmetric) only for single-service scenarios
- Implement token revocation for compromised tokens (blocklist or short token lifetime)

### MFA / Passwordless
- Require MFA for admin and high-privilege operations from day one
- Support TOTP (authenticator apps) as baseline; WebAuthn/passkeys as modern option
- Consider passwordless (magic links, passkeys) for better UX and security

---

## 3. Authorization Patterns

Authorization answers: "What are you allowed to do?" This is where most security bugs live.

### Role-Based Access Control (RBAC)
**When**: Most applications. Clear roles with predictable permissions.
```
Roles: admin, editor, viewer
Permissions: create_post, edit_post, delete_post, view_post
Mapping: admin → all, editor → create/edit/view, viewer → view
```
- Keep roles coarse-grained (under 10 roles)
- Map permissions to roles, then assign roles to users
- Check permissions in code, not roles (if user.has_permission("edit_post"), not if user.role == "admin")

### Attribute-Based Access Control (ABAC)
**When**: Complex authorization with contextual rules (user department, resource owner, time of day).
```
Rule: user.department == resource.department AND user.clearance >= resource.classification
```
- More flexible than RBAC but harder to audit and reason about
- Consider a policy engine (Open Policy Agent, Cedar) for complex rules

### Row-Level Security
**When**: Multi-tenant applications where users should only see their own data.
- Implement at the database level (PostgreSQL RLS policies) as a backstop
- Also enforce in the application layer — defense in depth
- Every query should include a tenant/owner filter, enforced by middleware or base repository

### Authorization Architecture
```
[API Gateway] → Authentication (verify token)
     │
     v
[Service] → Authorization middleware (check permissions for this endpoint)
     │
     v
[Data Layer] → Row-level security (filter by tenant/owner)
```

---

## 4. API Security

### Input Validation
- Validate ALL input at the trust boundary (where external data enters your system)
- Use schema validation (JSON Schema, Zod, Pydantic) — not manual checks
- Validate type, format, length, range, and allowed values
- Reject unexpected fields (don't silently ignore them)
- Sanitize output to prevent XSS (escape HTML in responses)

### Rate Limiting
- Apply rate limiting at the API gateway level
- Use token bucket or sliding window algorithms
- Different limits for different endpoints (login attempts: strict; read endpoints: lenient)
- Return 429 Too Many Requests with Retry-After header
- Consider per-user AND per-IP limits

### CORS
- Never use `Access-Control-Allow-Origin: *` in production
- Allowlist specific origins
- Restrict allowed methods and headers

### API Authentication
- Public APIs: API keys (for identification) + OAuth 2.0 (for authorization)
- Service-to-service: mTLS or signed tokens (JWT with service identity)
- Never pass secrets in URL query parameters (they appear in logs)
- Use HTTPS everywhere — no exceptions

---

## 5. Data Protection

### Encryption in Transit
- TLS 1.2+ everywhere. No exceptions. No "internal network so it's fine."
- Use mTLS for service-to-service communication in production
- Terminate TLS at the load balancer or API gateway, then re-encrypt to backend services
- HSTS headers for web applications

### Encryption at Rest
- Encrypt sensitive data at the database level (column-level encryption for PII, full-disk for everything else)
- Use cloud KMS (AWS KMS, GCP KMS, Azure Key Vault) for key management
- Rotate encryption keys on a schedule (annually minimum)
- Never store encryption keys alongside encrypted data

### Data Classification
Classify all data and apply controls accordingly:
- **Public**: No restrictions (marketing content, public APIs)
- **Internal**: Access limited to authenticated users (user-generated content)
- **Confidential**: Access limited to authorized users (PII, financial data)
- **Restricted**: Strictest controls (passwords, payment cards, health records)

### PII Handling
- Minimize collection — don't collect what you don't need
- Implement data retention policies — delete what you no longer need
- Log access to PII (audit trail)
- Support data export and deletion (GDPR, CCPA compliance)
- Pseudonymize or anonymize PII in non-production environments

---

## 6. Zero Trust Service Mesh

In a zero-trust architecture, no service trusts any other service by default, even within the same network. Every request must be authenticated and authorized.

### Implementation Pattern
```
[Service A] → mTLS → [Service Mesh Sidecar] → mTLS → [Service Mesh Sidecar] → [Service B]
                         │                                    │
                         └── Policy: A can call B endpoint X  ┘
                             with methods GET, POST
                             during business hours
```

### Key Components
- **Service Identity**: Each service has a cryptographic identity (certificate)
- **Mutual TLS (mTLS)**: Both sides of every connection verify identity
- **Policy Engine**: Defines which services can communicate and how
- **Audit Logging**: All service-to-service calls are logged

### Practical Implementation
- **Stage 1**: Start with API keys or JWTs for service-to-service auth
- **Stage 2**: Introduce mTLS with a service mesh (Istio, Linkerd) or Consul Connect
- **Stage 3**: Full zero-trust with policy-as-code, continuous verification, and automated certificate rotation

---

## 7. Secrets Management

### Rules
1. **Never commit secrets to version control.** Not even in "private" repos. Not even "temporarily."
2. **Never hardcode secrets in application code.** Not even in configuration files.
3. **Use a secrets manager.** HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault.
4. **Rotate secrets on a schedule.** Automate rotation where possible.
5. **Audit secret access.** Know who accessed what secret and when.
6. **Use different secrets per environment.** Development, staging, and production should never share secrets.

### Pattern for Applications
```
Application starts
  → Reads secret reference from environment variable (e.g., SECRET_ARN)
  → Fetches actual secret from secrets manager at runtime
  → Caches in memory (not on disk) with TTL
  → Refreshes before expiration
```

### Emergency Procedures
- Leaked secret? Rotate immediately, then investigate.
- Compromised service? Revoke its credentials, rotate all secrets it had access to.
- Always have a documented procedure for secret rotation that can be executed in under 15 minutes.

---

## 8. Security Checklist by Stage

### Stage 0: MVP
- [ ] HTTPS everywhere (Let's Encrypt makes this free)
- [ ] Managed auth provider (don't build your own)
- [ ] Input validation on all user input
- [ ] Parameterized queries (prevent SQL injection)
- [ ] Secrets in environment variables (not code)
- [ ] Dependencies scanned for known vulnerabilities
- [ ] CORS configured (not wildcard)
- [ ] Rate limiting on authentication endpoints

### Stage 1: Product-Market Fit
- [ ] Everything in Stage 0, plus:
- [ ] MFA for admin accounts
- [ ] Row-level security for multi-tenant data
- [ ] Structured audit logging for security events
- [ ] Automated dependency vulnerability scanning in CI
- [ ] Security headers (HSTS, CSP, X-Frame-Options)
- [ ] Backup encryption and access controls
- [ ] Incident response plan documented

### Stage 2: Growth
- [ ] Everything in Stage 1, plus:
- [ ] Service-to-service authentication (mTLS or signed tokens)
- [ ] API gateway with centralized auth and rate limiting
- [ ] Penetration testing (annual minimum)
- [ ] Secret rotation automation
- [ ] Data classification and handling procedures
- [ ] Security monitoring and alerting (SIEM or equivalent)
- [ ] Compliance framework alignment (SOC 2, GDPR, etc.)

### Stage 3: Mass Scale
- [ ] Everything in Stage 2, plus:
- [ ] Zero-trust service mesh
- [ ] Automated threat detection and response
- [ ] Bug bounty program
- [ ] Regular red team exercises
- [ ] Supply chain security (SBOM, signed builds)
- [ ] Chaos engineering for security scenarios

---

## 9. Threat Modeling Lightweight Process

For every new feature or significant architecture change, spend 30 minutes on lightweight threat modeling using STRIDE:

### STRIDE Categories
- **S**poofing: Can an attacker pretend to be someone/something they're not?
- **T**ampering: Can an attacker modify data in transit or at rest?
- **R**epudiation: Can a user deny they performed an action? (Do we have audit logs?)
- **I**nformation Disclosure: Can an attacker access data they shouldn't?
- **D**enial of Service: Can an attacker make the system unavailable?
- **E**levation of Privilege: Can a user gain more access than they should?

### Process
1. Draw the data flow diagram (even a rough sketch)
2. Identify trust boundaries (where data crosses from trusted to untrusted, or between different trust levels)
3. For each trust boundary crossing, ask all 6 STRIDE questions
4. For each identified threat, decide: mitigate, accept (with documentation), or transfer (insurance, SLA)
5. Document the results in the design doc or as a dedicated threat model document

This doesn't replace a full threat model for high-risk systems, but it catches the most common architectural security gaps in 30 minutes.
