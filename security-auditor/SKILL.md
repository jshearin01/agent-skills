---
name: security-auditor
description: >
  Expert security audit and penetration testing skill for evaluating frontend and backend
  code repositories. Use this skill whenever a user wants to audit code for security
  vulnerabilities, find exposed secrets or API keys, check for OWASP Top 10 issues,
  review authentication/authorization flaws, identify injection vulnerabilities, assess
  dependency risks, or generate a security report. Trigger on any mention of "security
  audit", "pen test", "penetration test", "security review", "find vulnerabilities",
  "exposed keys", "hardcoded secrets", "security scan", "code security", "OWASP check",
  "security flaws", or whenever the user shares code and asks if it is secure. Also
  trigger when users ask to "check my repo", "review my code for security", or "find
  security issues" even without explicitly naming it a security audit.
---

# Security Auditor — Code Repository Penetration Testing Skill

## Overview

This skill performs systematic security audits of frontend and backend code repositories,
mimicking the methodology of a professional penetration tester and AppSec engineer. It covers:

- **Secrets detection** — hardcoded API keys, tokens, passwords, credentials
- **OWASP Top 10 (2025)** — the most critical web application security risks
- **Frontend vulnerabilities** — XSS, CSRF, insecure storage, CSP gaps
- **Backend vulnerabilities** — injection, broken auth, access control, cryptography flaws
- **Dependency auditing** — known CVEs in third-party libraries
- **Infrastructure and config** — exposed config files, insecure headers, misconfigurations
- **Severity-rated findings** with remediation guidance and a structured final report

**Standards referenced:** OWASP Top 10 (2025), CWE Top 25, NIST SP 800-92.

## Audit Methodology

Follow this 6-phase approach. Adapt depth based on available code.

1. **Reconnaissance** — understand the stack, entry points, data flows
2. **Secrets Detection** — scan for leaked credentials FIRST
3. **Frontend Audit** — client-side vulnerabilities
4. **Backend Audit** — server-side vulnerabilities
5. **Dependency and Supply Chain** — third-party risks
6. **Report Generation** — severity-rated findings with remediation steps

When given a code repository or files, scan ALL files including tests, docs, and configs.
Note the tech stack early. Flag both confirmed vulnerabilities and suspicious patterns.

## Phase 1: Reconnaissance and Repository Triage

Map the attack surface before diving into vulnerabilities.

**Identify the tech stack:**
- Frontend: React/Vue/Angular/plain JS, which bundler
- Backend: Node/Python/Java/Go/PHP/Ruby and framework
- Database: SQL (Postgres/MySQL) or NoSQL (MongoDB/Redis)
- Auth mechanism: JWT, OAuth, sessions, or custom
- Infrastructure: Docker, Kubernetes, cloud provider

**High-value targets to locate immediately:**
- .env, .env.local, .env.production, .env.* files
- config.js, config.ts, settings.py, application.properties
- docker-compose.yml and docker-compose.override.yml
- .aws/credentials, id_rsa, *.pem, *.key files
- terraform.tfvars, *.tfstate files
- .github/workflows/ and .gitlab-ci.yml (CI/CD configs)
- package.json, requirements.txt, Gemfile, pom.xml (dependency files)

**Pre-audit questions to answer:**
- Where does user input enter the system?
- What authenticates and authorizes users?
- Where is sensitive data stored and transmitted?
- What external services or APIs are integrated?
- Is there file upload functionality?
- Are there admin-only endpoints?

## Phase 2: Secrets and Exposed Credentials Detection

This is always the FIRST scan. Exposed secrets are highest-impact, easiest-to-exploit.

### Secret Patterns to Find

Scan ALL files — including comments, tests, and documentation:

| Secret Type | Detection Pattern | Notes |
|---|---|---|
| AWS Access Key | AKIA[0-9A-Z]{16} | e.g., AKIAIOSFODNN7EXAMPLE |
| AWS Secret Key | 40-char alphanum after aws_secret | wJalrXUtnFEMI/K7MDENG/... |
| GitHub Token | ghp_[a-zA-Z0-9]{36} or github_pat_ | |
| Google API Key | AIza[0-9A-Za-z_-]{35} | AIzaSyDdI0hCZtE6... |
| Stripe Live Key | sk_live_[0-9a-zA-Z]{24,} | pk_live_ is also sensitive |
| Slack Token | xox[baprs]-[0-9a-zA-Z]{10,} | |
| Twilio | SK[0-9a-fA-F]{32} | |
| JWT Token | eyJ[A-Za-z0-9_-]+.eyJ[A-Za-z0-9_-]+. | Decode and check alg/exp |
| Private Key | -----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY----- | |
| Database URL | postgres://user:pass@host or mysql://user:pass@host | |
| Generic password | password = "somevalue" (non-placeholder) | |
| Generic API key | api_key = "somevalue" (non-placeholder) | |

**Also look for:**
- Tokens hardcoded in Authorization headers inside source code
- Credentials embedded in URLs: https://user:password@host
- Secrets inside comments: // TODO: remove this key: sk_live_...
- Base64-encoded secrets near keywords "key", "secret", "token"
- .env files accidentally committed (check .gitignore covers them)
- SSH keys or PEM certificates in the repository

### File and Location Scanning Commands

```bash
# Find .env files (should never be committed)
find . -name "*.env" -o -name ".env*" | grep -v node_modules | grep -v ".env.example"

# Find common secret assignments
grep -rn "password\s*=" . --include="*.js" --include="*.ts" --include="*.py"
grep -rn "api_key\s*=" . | grep -v "YOUR_API_KEY\|PLACEHOLDER\|EXAMPLE"
grep -rn "secret\s*=" . | grep -v test

# Find hardcoded database URLs
grep -rn "mongodb+srv://\|postgresql://\|mysql://" .

# Find AWS access keys
grep -rn "AKIA[0-9A-Z]" .

# Find private key material
grep -rn "BEGIN PRIVATE KEY\|BEGIN RSA PRIVATE" .
find . -name "*.pem" -o -name "id_rsa" | grep -v node_modules

# Verify .gitignore protects sensitive files
cat .gitignore | grep -E "\.env|secret|credential"
```

**Critical:** If .env is NOT in .gitignore, flag as HIGH — it is a data leak waiting to happen.

### Git History Audit

Secrets deleted in a later commit are still exposed in git history:

```bash
# Search entire git history for secrets
git log --all --full-history -p | grep -E "(password|api_key|secret|token)\s*="

# Find deleted files that may have contained secrets
git log --all --diff-filter=D --name-only --pretty=format: | grep -i "secret\|key\|env\|config"

# Find commits mentioning secret removal (reveals what was there)
git log --all --oneline | grep -i "remove\|delete\|secret\|key\|password"
```

IMPORTANT: A secret found only in git history is still CRITICAL if the key has not been
rotated. Removing a secret from code does NOT revoke access to the service it unlocks.

## Phase 3: Frontend Security Audit

### XSS — Cross-Site Scripting (CWE-79)

XSS is the most prevalent frontend vulnerability with 30,000+ CVEs.

**Flag these as CRITICAL or HIGH:**
```javascript
// Direct innerHTML with user data — CRITICAL
element.innerHTML = userInput;
document.write(userInput);

// eval with any external data — CRITICAL
eval(userInput);
new Function(userInput)();
setTimeout(userInput, 100);    // string form of setTimeout

// React escape hatch — HIGH (needs sanitization)
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// jQuery unsafe methods — HIGH
$(element).html(userInput);
$(element).append(userInput);  // when userInput contains HTML
```

**DOM-based XSS sources — dangerous if written unsanitized to DOM:**
- location.hash, location.search, location.href
- document.referrer, window.name
- postMessage handlers — verify event.origin is validated before use

**Safe patterns to confirm:** textContent/innerText instead of innerHTML, DOMPurify
sanitization before any HTML insertion, React JSX default rendering (safe by default).

### Security Headers and CSP

**Check HTTP response headers. Flag missing or weak values:**

| Header | Required Value | Risk if Missing/Weak |
|---|---|---|
| Content-Security-Policy | Restrictive policy | HIGH — XSS amplification |
| X-Frame-Options | DENY or SAMEORIGIN | HIGH — clickjacking |
| X-Content-Type-Options | nosniff | MEDIUM — MIME sniffing |
| Strict-Transport-Security | max-age=31536000; includeSubDomains | HIGH — SSL stripping |
| Referrer-Policy | strict-origin-when-cross-origin | LOW — data leakage |
| Permissions-Policy | Restrict unneeded browser features | LOW-MEDIUM |

**CSP weaknesses to flag:**
- Missing CSP entirely — HIGH
- script-src * or default-src * — HIGH (allows any script source)
- unsafe-inline in script-src — MEDIUM (allows inline scripts)
- unsafe-eval in script-src — MEDIUM (allows eval)

### Authentication and Session Management (Frontend)

**Token storage — flag insecure patterns:**
```javascript
// INSECURE: localStorage accessible to any JS code; XSS can steal tokens
localStorage.setItem("token", jwtToken);         // HIGH
localStorage.setItem("authToken", bearerToken);  // HIGH

// SECURE: HttpOnly cookies are not accessible to JS
// Backend must set: Set-Cookie: token=...; HttpOnly; Secure; SameSite=Strict
```

**CSRF protection checklist:**
- CSRF tokens on all state-changing forms
- SameSite=Strict or SameSite=Lax on session cookies
- Custom request headers on AJAX calls (e.g., X-Requested-With)

**JWT issues to flag:**
- JWTs stored in localStorage — HIGH
- alg: none accepted by server — CRITICAL
- No expiry (exp claim) validation — HIGH
- Sensitive PII in JWT payload — MEDIUM (payload is base64, NOT encrypted)

### Sensitive Data Exposure in Client Code

```javascript
// CRITICAL: secrets visible to all users in browser dev tools
const API_KEY = "AIzaSy...";
const STRIPE_KEY = "sk_live_...";
const DB_PASSWORD = "password123";

// HIGH: internal infrastructure exposed to clients
const INTERNAL_API = "http://10.0.0.5:8080/internal";
```

**Framework-specific env var exposure:**
- React (CRA): REACT_APP_* vars are bundled into client JS — never put secrets here
- Vite: VITE_* vars end up in client bundle — never put secrets here
- Next.js: NEXT_PUBLIC_* vars are browser-visible — never put secrets here
- Flag any process.env.DATABASE_URL or process.env.JWT_SECRET in frontend code — CRITICAL

### Third-Party Dependencies (Frontend)

```bash
npm audit --audit-level=high    # Check for known CVEs
npm outdated                     # Check for outdated packages
yarn audit                       # Yarn equivalent
```

**Manual checks:**
- CDN-loaded scripts missing Subresource Integrity (SRI) hashes — MEDIUM
  Good: script src="cdn.example.com/lib.js" integrity="sha384-abc123..."
  Bad: script src="cdn.example.com/lib.js" (no integrity attribute)
- Typosquatted package names: lodahs, recat, expres — CRITICAL
- Post-install scripts that make network requests — review carefully

## Phase 4: Backend Security Audit

### Injection Vulnerabilities

**SQL Injection (CWE-89) — highest-impact injection risk:**
```python
# VULNERABLE: string concatenation in queries — CRITICAL
query = "SELECT * FROM users WHERE id = " + user_id
cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")

# SAFE: parameterized queries
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
# ORM: User.objects.get(id=user_id), User.query.filter_by(id=user_id)
```

```javascript
// VULNERABLE in Node — CRITICAL
db.query("SELECT * FROM users WHERE email = '" + req.body.email + "'")

// SAFE
db.query("SELECT * FROM users WHERE email = ?", [req.body.email])
```

**NoSQL Injection (MongoDB) — HIGH:**
```javascript
// VULNERABLE: user-controlled operators
db.users.find({ username: req.body.username })  // username = { $gt: "" } bypasses auth

// SAFE: cast input to expected type
db.users.find({ username: String(req.body.username) })
```

**Command Injection (CWE-78) — CRITICAL:**
```python
# VULNERABLE
os.system("ping " + user_input)
subprocess.call("ls " + directory, shell=True)

# SAFE
subprocess.call(["ping", user_input])   # List form, no shell=True
```

**Server-Side Template Injection (SSTI) — CRITICAL (leads to RCE):**
```python
# VULNERABLE
render_template_string("Hello " + username)   # Jinja2 SSTI possible
```

### Authentication and Authorization

**Password storage — flag these immediately:**
```python
# CRITICAL: plaintext
user.password = password

# CRITICAL: broken hashing algorithms for passwords
hashlib.md5(password).hexdigest()    # MD5 is broken
hashlib.sha1(password).hexdigest()   # SHA1 is broken for passwords

# SAFE
from passlib.hash import bcrypt
hashed = bcrypt.hash(password)        # Use bcrypt, argon2, or scrypt
```

**JWT security:**
```javascript
// CRITICAL: no algorithm specification allows "none" attack
jwt.verify(token, secret)

// SAFE
jwt.verify(token, secret, { algorithms: ["HS256"] })

// CRITICAL: weak secrets
const JWT_SECRET = "secret"     // Too short, common word
const JWT_SECRET = "changeme"   // Default placeholder

// Verify: secret is at least 256 bits / 32 chars
// Verify: exp claim is enforced
// Verify: tokens are invalidated on logout
```

**Session management checklist:**
- Session IDs are cryptographically random (not sequential integers)
- Session regenerated after login (prevents session fixation CWE-384)
- Session invalidated on logout
- Absolute timeout (2-8 hours) AND idle timeout (15-30 min) enforced

### Broken Access Control (OWASP #1 Risk 2025)

```javascript
// CRITICAL IDOR: any user ID accessible without ownership check
app.get("/api/users/:id", async (req, res) => {
  const user = await User.findById(req.params.id);  // No ownership check!
  res.json(user);
});

// SAFE: verify requester owns or is authorized to access the resource
app.get("/api/users/:id", requireAuth, async (req, res) => {
  if (req.params.id !== req.user.id && !req.user.isAdmin) {
    return res.status(403).json({ error: "Forbidden" });
  }
  const user = await User.findById(req.params.id);
  res.json(user);
});
```

**Mass assignment (parameter pollution) — HIGH:**
```javascript
// VULNERABLE: user can set any field including isAdmin
const user = new User(req.body);

// SAFE: explicit allowlist of accepted fields
const user = new User({
  name: req.body.name,
  email: req.body.email
});
```

**Access control checklist:**
- All endpoints require authentication (no accidental @PermitAll or public routes)
- Authorization checked on every request, not just at login
- Admin-only endpoints have role checks beyond just authentication
- IDOR: resource IDs validated against requesting user's ownership
- Directory listing disabled on web server
- Sensitive API endpoints not publicly discoverable

### Cryptography and Data Protection

**Flag these cryptographic weaknesses:**

| Issue | Severity | Fix |
|---|---|---|
| MD5 or SHA1 for passwords | CRITICAL | Use bcrypt/argon2/scrypt |
| DES or 3DES encryption | CRITICAL | Use AES-256-GCM |
| AES-ECB mode | HIGH | Use AES-GCM or AES-CBC with HMAC |
| Hardcoded encryption key | CRITICAL | Use key management service |
| HTTP for sensitive data transmission | HIGH | Enforce HTTPS/TLS 1.2+ |
| verify=False in HTTPS requests | CRITICAL | Never disable cert verification |
| Math.random() for security tokens | HIGH | Use crypto.randomBytes or secrets module |

```python
# CRITICAL: disabling SSL/TLS verification
requests.get(url, verify=False)

# CRITICAL: weak random for security tokens
import random
token = str(random.random())   # Not cryptographically secure

# SAFE
import secrets
token = secrets.token_urlsafe(32)   # 256-bit cryptographically secure token
```

### Security Misconfiguration

**Framework-specific flags:**
```python
# Django — flag in production settings
DEBUG = True                          # CRITICAL: exposes full stack traces
ALLOWED_HOSTS = ["*"]                 # HIGH: accepts any hostname
SECRET_KEY = "django-insecure-..."   # CRITICAL: change default/insecure key
CORS_ALLOW_ALL_ORIGINS = True         # HIGH: allows cross-origin from anywhere
```

```javascript
// Express/Node — flag
app.use(cors())                        # HIGH: allows all origins by default
app.use(cors({ origin: "*" }))        # HIGH: explicit wildcard
```

**Database security flags:**
- Connection strings or credentials hardcoded in code — CRITICAL
- Database directly accessible from internet (no VPC/firewall) — CRITICAL
- App DB user has DROP, CREATE, or ALTER permissions — HIGH
- Principle of least privilege not applied to DB user — MEDIUM

**Docker/container:**
```dockerfile
# HIGH: running container as root (no USER directive)
FROM node:18
# Should include: USER node

# CRITICAL: secrets baked into image layers
ARG API_KEY=secret123
ENV DATABASE_URL=postgres://user:pass@host/db
# Use --secret mount or runtime env vars instead
```

### API Security

**REST API checklist:**
- Rate limiting on all public endpoints (prevents brute force and scraping)
- Rate limiting on auth endpoints specifically (prevents credential stuffing)
- Input validation on ALL parameters: type, length, format, range
- Output filtering: API never returns more fields than requested/needed
- Pagination limits enforced (no LIMIT 99999 or unbounded queries)
- HTTP method enforcement (PUT /users should reject GET)

**GraphQL specific issues:**
- Introspection enabled in production — MEDIUM (exposes schema to attackers)
- No query depth limiting — HIGH (enables DoS via deeply nested queries)
- No query complexity limiting — HIGH
- Batching attacks possible without rate limiting — HIGH

**Verbose error messages — flag as MEDIUM:**
```json
// BAD: internal details leaked in error responses
{ "error": "SQLSTATE[42000]: Syntax error near 'id'..." }
{ "error": "Cannot read property 'id' at /app/routes/user.js:42" }

// GOOD: generic error message
{ "error": "An internal error occurred. Please try again." }
```

### File Upload and Path Traversal

**File upload vulnerabilities:**
```python
# CRITICAL: no type validation, user-controlled filename
filename = request.files["file"].filename   # Path traversal: "../../etc/passwd"
file.save(os.path.join(UPLOAD_DIR, filename))

# SAFE approach:
import uuid, magic
safe_filename = str(uuid.uuid4()) + get_validated_extension(file)
# Validate file type by magic bytes (not just extension)
# Store outside web root
# Regenerate filename server-side
```

**Path traversal (CWE-22) — CRITICAL:**
```python
# VULNERABLE
open(BASE_DIR + "/" + user_input)   # user_input = "../../etc/passwd"

# SAFE: resolve and verify path stays within base
real_path = os.path.realpath(os.path.join(BASE_DIR, user_input))
if not real_path.startswith(os.path.realpath(BASE_DIR) + os.sep):
    raise PermissionError("Path traversal detected")
```

### Logging and Error Handling

```python
# CRITICAL: logging credentials or tokens
logger.info(f"Login: user={username}, password={password}")
logger.debug(f"Auth token: {jwt_token}")

# HIGH: logging PII unnecessarily
logger.info(f"User SSN {user.ssn} accessed resource")
```

**Logging checklist:**
- Failed login attempts logged with timestamp, IP, and username
- Successful logins logged
- Authorization failures logged
- Passwords, tokens, PII, and card numbers NEVER logged (CWE-532)
- Log injection prevented (user input sanitized before logging)
- Error messages shown to users are generic — no stack traces in production

## Phase 5: Dependency and Supply Chain Security

OWASP A06 (2021) / A03 (2025): Software Supply Chain Failures.

```bash
# Node.js
npm audit --audit-level=critical
npx snyk test

# Python
pip-audit
safety check -r requirements.txt

# Ruby
bundle audit

# Java
mvn dependency-check:check

# Go
govulncheck ./...
```

**Manual dependency review:**
- Flag packages abandoned for 2+ years with no security updates
- Verify package-lock.json or yarn.lock is committed (reproducible builds)
- Flag * or latest version pins — unpredictable, potentially insecure updates
- Inspect post-install scripts in package.json that make network requests
- Watch for typosquatted package names (lodahs, recat, expres, etc.)
- Transitive dependencies: trace with npm ls <package>

**Supply chain attack indicators:**
- Package recently transferred to a new maintainer
- Sudden major version bump with minimal changelog
- Post-install or preinstall scripts that are undocumented

## Phase 6: Infrastructure and Configuration Checks

**Cloud IaC (Terraform/CloudFormation) — flag:**
- acl = "public-read" on S3 buckets — HIGH
- cidr_blocks = ["0.0.0.0/0"] with wide port ranges — CRITICAL
- Secrets stored in tfvars files committed to repo — CRITICAL
- Security groups allowing 0.0.0.0/0 on port 22 or 3389 — CRITICAL

**Docker/container security checklist:**
- Base images pinned to specific digest, not "latest"
- USER directive present (non-root)
- No secrets in ENV, ARG, or image layers
- .dockerignore excludes .env, .git, credentials, id_rsa
- Multi-stage builds minimize final image size and attack surface

**CI/CD pipeline security:**
- Secrets stored in CI secrets manager, not in YAML files in repo
- Third-party GitHub Actions pinned to commit SHA (not tag):
  Risky:  uses: actions/checkout@v3
  Safe:   uses: actions/checkout@8e5e7e5ab8b370d6c329ec480221332ada57f0ab
- GITHUB_TOKEN permissions scoped to minimum needed
- Pull request workflows cannot access production secrets

**Web server configuration:**
- Server version header hidden (server_tokens off in nginx)
- Directory browsing disabled
- Sensitive paths blocked: .git, .env, phpinfo.php, /.git/config
- TLS 1.0 and TLS 1.1 disabled (TLS 1.2+ only)
- HTTPS redirect active for all HTTP traffic

## Producing the Security Report

### Severity Classification

| Severity | CVSS | Description | Example | SLA |
|---|---|---|---|---|
| CRITICAL | 9-10 | Direct path to full compromise | Hardcoded prod secret, RCE via injection | Immediate |
| HIGH | 7-8.9 | Significant data breach or system risk | SQLi, stored XSS, broken auth | 7 days |
| MEDIUM | 4-6.9 | Partial access or data exposure | Missing CSRF, weak crypto, verbose errors | 30 days |
| LOW | 1-3.9 | Defense-in-depth gap | Missing security header | 90 days |
| INFO | 0 | Best practice recommendation | Logging improvement | Backlog |

### Report Template

Use this structure for every finding:

```
Finding #N: [Descriptive Title]
Severity:   CRITICAL / HIGH / MEDIUM / LOW / INFO
Category:   OWASP A0X:2025 — [Name] / CWE-XXX
Location:   path/to/file.py:42 (or endpoint/component)
Description:
  What the vulnerability is and why it is dangerous.
Evidence:
  [Relevant code snippet showing the vulnerable pattern]
Impact:
  What an attacker can achieve if this is exploited.
Remediation:
  Step-by-step fix with corrected code example.
References:
  CWE-N: https://cwe.mitre.org/data/definitions/N.html
  OWASP: https://owasp.org/...
```

**Report summary — always open with this:**
```
SECURITY AUDIT SUMMARY
======================
Repository : [name]
Date       : [date]
Stack      : [tech stack identified]

FINDINGS OVERVIEW
  Critical : X    High : X    Medium : X    Low : X    Info : X
  Total    : X

TOP 3 PRIORITY ACTIONS
  1. [Most critical finding — action required]
  2. [Second finding — action required]
  3. [Third finding — action required]

POSITIVE SECURITY FINDINGS
  - [Acknowledge good practices found, e.g., "Parameterized queries used consistently"]
  - [e.g., "HTTPS enforced site-wide"]
  - [e.g., "Dependency audit passing with no critical CVEs"]
```

Always include positive findings. Security audits that only list problems are less
effective. Teams are more receptive to security work when good practices are acknowledged.

## Quick Grep Reference

Copy-paste these commands when auditing a repository:

```bash
# === SECRETS ===
find . -name ".env*" -not -path "*/node_modules/*" -not -name ".env.example"
grep -rn "AKIA[0-9A-Z]" . --include="*.js" --include="*.ts" --include="*.py" --include="*.yml"
grep -rn "password\s*=" . | grep -v "test\|spec\|example\|#\|YOUR_"
grep -rn "api_key\s*=" . | grep -v "PLACEHOLDER\|YOUR_API_KEY\|EXAMPLE"
grep -rn "BEGIN PRIVATE KEY\|BEGIN RSA PRIVATE" .
grep -rn "mongodb+srv://\|postgresql://\|mysql://" . | grep -v test
find . -name "*.pem" -o -name "id_rsa" 2>/dev/null | grep -v node_modules

# === INJECTION ===
grep -rn "innerHTML\s*=" . --include="*.js" --include="*.jsx" --include="*.tsx"
grep -rn "dangerouslySetInnerHTML" .
grep -rn "eval(" . --include="*.js" --include="*.ts" | grep -v "test\|spec"
grep -rn "shell=True" . --include="*.py"
grep -rn "os\.system(" . --include="*.py"

# === AUTH ===
grep -rn "localStorage.*[Tt]oken\|localStorage.*[Aa]uth" . --include="*.js" --include="*.ts"
grep -rn "verify\s*=\s*False" . --include="*.py"
grep -rn "hashlib\.md5\|hashlib\.sha1" . --include="*.py"

# === CONFIG ===
grep -rn "DEBUG\s*=\s*True" . --include="*.py" --include="*.env"
grep -rn "CORS.*\*\|cors.*all" . --include="*.js" --include="*.ts"
grep -rn "0\.0\.0\.0/0" . --include="*.tf" --include="*.yml"

# === CRYPTO ===
grep -rn "Math\.random()" . --include="*.js" | grep -i "token\|secret\|key\|session"
grep -rn "random\.random()\|random\.randint" . --include="*.py" | grep -i "token\|secret"
```
