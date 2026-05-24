# Code Slop Reference: React, Frontend & Backend Architecture

## Table of Contents
1. [React Component Anti-Patterns](#1-react-component-anti-patterns)
2. [React Hooks Anti-Patterns](#2-react-hooks-anti-patterns)
3. [State Management Slop](#3-state-management-slop)
4. [Backend / API Anti-Patterns](#4-backend--api-anti-patterns)
5. [Architecture Anti-Patterns](#5-architecture-anti-patterns)
6. [Security Slop — Critical](#6-security-slop--critical)
7. [Performance Slop](#7-performance-slop)
8. [Code Quality Tells](#8-code-quality-tells)
9. [Remediation Principles](#9-remediation-principles)
10. [Before / After Examples](#10-before--after-examples)

---

## 1. React Component Anti-Patterns

### 1.1 God Components (The Monolith)
AI generates single components handling data fetching, business logic, formatting, and rendering simultaneously. Often 200–600+ lines. OX Security's 2025 analysis of 300 AI-generated codebases found 80–90% contained god components.

**Slop signals:**
- Component file over 150 lines
- Multiple `useEffect` hooks in one component (more than 2)
- Component fetches data AND renders it AND handles all interactions
- `// Handle everything` style comments

```tsx
// ❌ AI slop — god component
function UserDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [page, setPage] = useState(1);
  const [selectedUser, setSelectedUser] = useState(null);

  useEffect(() => {
    fetch('/api/users').then(r => r.json()).then(setUsers);
  }, []);
  // 300+ more lines...
}

// ✅ Fixed — separation of concerns
// hooks/useUsers.ts      — data fetching
// components/UserList.tsx — rendering list
// components/UserCard.tsx — individual item
// components/UserFilters.tsx — filter UI
// UserDashboard.tsx      — composition only (< 30 lines)
function UserDashboard() {
  const { users, loading, error } = useUsers();
  return <UserList users={users} loading={loading} error={error} />;
}
```

### 1.2 Components Defined Inside Components
AI frequently nests component definitions inside parent functions, recreating the child definition on every render, breaking memoization.

```tsx
// ❌ AI slop — Item is a new function reference every render
function List({ items }) {
  const Item = ({ label }) => <li>{label}</li>;
  return <ul>{items.map(i => <Item key={i.id} label={i.name} />)}</ul>;
}

// ✅ Fixed — Item defined at module scope
const Item = ({ label }: { label: string }) => <li>{label}</li>;

function List({ items }) {
  return <ul>{items.map(i => <Item key={i.id} label={i.name} />)}</ul>;
}
```

### 1.3 Array Index as Key
```tsx
// ❌ AI slop — breaks reconciliation on sort/filter/splice
{items.map((item, index) => <Card key={index} {...item} />)}

// ✅ Fixed — stable, unique identity
{items.map(item => <Card key={item.id} {...item} />)}
```

### 1.4 No Error Boundary
AI generates component trees with no `ErrorBoundary`. One runtime exception crashes the entire app.

```tsx
// ✅ Add ErrorBoundary around feature sections
class ErrorBoundary extends React.Component<
  { fallback: ReactNode; children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(err: Error) { logger.error(err); }

  render() {
    return this.state.hasError ? this.props.fallback : this.props.children;
  }
}

// Wrap sections, not the whole app
<ErrorBoundary fallback={<DashboardError />}>
  <Dashboard />
</ErrorBoundary>
```

### 1.5 Spreading All Props onto DOM Elements
```tsx
// ❌ AI slop — unknown props (isActive, onToggle) reach DOM
function Button({ isActive, onToggle, ...props }) {
  return <button style={{ color: isActive ? 'blue' : 'gray' }} {...props} />;
}

// ✅ Fixed — forward only valid HTML attributes
function Button({ isActive, className, children, onClick }: ButtonProps) {
  return (
    <button className={cn(className, isActive && 'active')} onClick={onClick}>
      {children}
    </button>
  );
}
```

---

## 2. React Hooks Anti-Patterns

### 2.1 Derived State via useState + useEffect (Most Common AI Hooks Mistake)
```tsx
// ❌ AI slop — synchronizing derived state
function FullName({ firstName, lastName }) {
  const [fullName, setFullName] = useState('');
  useEffect(() => {
    setFullName(`${firstName} ${lastName}`);
  }, [firstName, lastName]);
  return <span>{fullName}</span>;
}

// ✅ Fixed — computed during render, no effect needed
function FullName({ firstName, lastName }) {
  const fullName = `${firstName} ${lastName}`;
  return <span>{fullName}</span>;
}
```

**Rule**: If a value can be derived from props or existing state without any async operation, compute it inline. No useState. No useEffect.

### 2.2 useEffect Without Cleanup (Memory Leaks)
AI almost never writes cleanup functions. Causes memory leaks and "state update on unmounted component" errors.

```tsx
// ❌ AI slop — no cleanup, potential leak
useEffect(() => {
  const handler = () => setScrolled(window.scrollY > 100);
  window.addEventListener('scroll', handler);
}, []); // missing cleanup!

// ✅ Fixed
useEffect(() => {
  const handler = () => setScrolled(window.scrollY > 100);
  window.addEventListener('scroll', handler);
  return () => window.removeEventListener('scroll', handler); // cleanup
}, []);

// ✅ Fetch with AbortController
useEffect(() => {
  const controller = new AbortController();
  fetch(`/api/user/${id}`, { signal: controller.signal })
    .then(r => r.json())
    .then(setUser)
    .catch(err => { if (err.name !== 'AbortError') setError(err); });
  return () => controller.abort();
}, [id]);
```

### 2.3 Hooks After Conditional Returns (Rules Violation)
```tsx
// ❌ AI slop — hook is conditional, violates Rules of Hooks
function Panel({ isReady }) {
  if (!isReady) return <Spinner />;
  const [open, setOpen] = useState(false); // ERROR: hook after return
  return <div onClick={() => setOpen(o => !o)}>{open ? 'Open' : 'Closed'}</div>;
}

// ✅ Fixed — hooks before any conditional returns
function Panel({ isReady }) {
  const [open, setOpen] = useState(false); // always called
  if (!isReady) return <Spinner />;
  return <div onClick={() => setOpen(o => !o)}>{open ? 'Open' : 'Closed'}</div>;
}
```

### 2.4 Pointless Memoization
AI over-memoizes trivial values, adding complexity with no benefit.

```tsx
// ❌ Pointless — memoizing constants and string interpolation
const count = useMemo(() => 42, []);
const label = useMemo(() => `Hello ${name}`, [name]);

// ✅ When to actually use useMemo:
// 1. Genuinely expensive computation (sorting large arrays, complex transforms)
// 2. Result passed to a React.memo'd component as a prop
// 3. Result used as a useEffect dependency

// ✅ When to actually use useCallback:
// 1. Function passed to a React.memo'd child
// 2. Function used as a useEffect dependency
// Not: every click handler in every component
```

---

## 3. State Management Slop

### 3.1 Prop Drilling (4+ Levels Deep)
```tsx
// ❌ AI slop — Navbar and NavLinks don't use theme
<App theme="dark">
  <Navbar theme="dark">
    <NavLinks theme="dark">
      <NavButton theme="dark" /> {/* finally uses it */}
    </NavLinks>
  </Navbar>
</App>

// ✅ Fixed — Context for cross-cutting values
const ThemeCtx = createContext<'light' | 'dark'>('light');

function App() {
  return (
    <ThemeCtx.Provider value="dark">
      <Navbar /> {/* no prop threading */}
    </ThemeCtx.Provider>
  );
}
function NavButton() {
  const theme = useContext(ThemeCtx); // reads directly
}
```

### 3.2 Monolithic Context (Everything in One Provider)
AI puts all app state in one context, causing the entire app to re-render on any change.

```tsx
// ❌ AI slop — changing cart re-renders everything
const GlobalCtx = createContext();
const [user, setUser] = useState(null);
const [theme, setTheme] = useState('light');
const [cart, setCart] = useState([]);
const [notifications, setNotifications] = useState([]);
// All in one provider — cart change = full re-render

// ✅ Fixed — split by change frequency
// UserContext   — changes rarely (login/logout)
// ThemeContext  — changes rarely
// CartContext   — changes frequently, isolated
// NotifContext  — changes frequently, isolated
```

### 3.3 Impossible State Machines (Parallel Boolean Flags)
```tsx
// ❌ AI slop — loading=true AND error=true is reachable (impossible state)
const [loading, setLoading] = useState(false);
const [data, setData] = useState(null);
const [error, setError] = useState(null);

// ✅ Fixed — discriminated union, no impossible states
type FetchState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; message: string };

const [state, dispatch] = useReducer(fetchReducer, { status: 'idle' });
```

---

## 4. Backend / API Anti-Patterns

### 4.1 No Input Validation (Critical)
```ts
// ❌ AI slop — raw body used directly (injection, type errors, data corruption)
app.post('/users', async (req, res) => {
  const user = await prisma.user.create({ data: req.body });
  res.json(user);
});

// ✅ Fixed — validate with Zod at the edge
import { z } from 'zod';
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(['user', 'admin']).default('user'),
});

app.post('/users', async (req, res) => {
  const result = CreateUserSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ errors: result.error.issues });
  }
  const user = await prisma.user.create({ data: result.data });
  res.status(201).json(user);
});
```

### 4.2 N+1 Query Problem
AI loops with a DB query per iteration instead of batching. GitClear data shows this is the most common backend performance issue in AI-generated code.

```ts
// ❌ AI slop — fires 1 + N queries
const posts = await prisma.post.findMany(); // 1 query
for (const post of posts) {
  post.author = await prisma.user.findById(post.authorId); // N queries!
}

// ✅ Fixed — single query with JOIN
const posts = await prisma.post.findMany({
  include: { author: true }, // 1 query total
});
```

### 4.3 Unbounded Queries (No Pagination)
```ts
// ❌ AI slop — returns ALL records, DoS risk
const users = await prisma.user.findMany();

// ✅ Fixed — cursor pagination
const { cursor, limit = 20 } = req.query;
const users = await prisma.user.findMany({
  take: Math.min(Number(limit), 100), // hard cap
  cursor: cursor ? { id: String(cursor) } : undefined,
  orderBy: { createdAt: 'desc' },
});
res.json({
  data: users,
  nextCursor: users.length === Number(limit)
    ? users[users.length - 1].id
    : null,
});
```

### 4.4 No Resource Ownership Check (Broken Object Level Authorization)
```ts
// ❌ AI slop — any authenticated user can access any document
app.get('/documents/:id', requireAuth, async (req, res) => {
  const doc = await prisma.document.findById(req.params.id);
  // Missing: does req.user own this document?
  res.json(doc);
});

// ✅ Fixed — scope query to authenticated user
app.get('/documents/:id', requireAuth, async (req, res) => {
  const doc = await prisma.document.findFirst({
    where: { id: req.params.id, userId: req.user.id }, // ownership check in query
  });
  if (!doc) return res.status(404).json({ error: 'Not found' });
  res.json(doc);
});
```

### 4.5 Async Routes Without Error Handling
```ts
// ❌ AI slop — unhandled rejection crashes the process
app.get('/item/:id', async (req, res) => {
  const item = await db.getItem(req.params.id); // throws = crash
  res.json(item);
});

// ✅ Fixed — use global async error wrapper
const asyncHandler = (fn) => (req, res, next) => fn(req, res, next).catch(next);

app.get('/item/:id', asyncHandler(async (req, res) => {
  const item = await db.getItem(req.params.id);
  if (!item) return res.status(404).json({ error: 'Not found' });
  res.json(item);
}));

// Global error handler
app.use((err, req, res, next) => {
  logger.error({ err, url: req.url });
  res.status(err.status ?? 500).json({ error: 'Internal server error', requestId: req.id });
});
```

---

## 5. Architecture Anti-Patterns

### 5.1 No Layer Separation
AI generates route handlers that contain business logic and raw SQL/ORM calls in the same function — untestable and unmaintainable.

```
❌ AI slop architecture:
route handler → business logic + SQL → format response
(all in one 80-line async function)

✅ Clean layers:
routes/       HTTP: parse request, call service, format response
services/     Business logic: rules, orchestration, validation
repositories/ Data access: all DB queries, no business logic
types/        Shared types, schemas, constants
```

### 5.2 Architecture Drift (The Vibe Coding Tax)
AI generates three different approaches to the same problem in the same codebase because it has no memory between prompts.

**Slop signals:**
- `fetch()` in some components, `axios` in others, `react-query` in a third
- Error handling done differently in every route
- State managed with Context in feature A, Zustand in feature B, raw useState in feature C

**Fix**: Document your canonical approach in `AGENTS.md` or `ARCHITECTURE.md`. Before each AI generation session, include the document in context. Audit for drift before merging.

### 5.3 Hardcoded / Unvalidated Environment Variables
```ts
// ❌ AI slop — crashes obscurely when var is missing
const stripe = new Stripe(process.env.STRIPE_KEY!);

// ✅ Fixed — validate all env vars at startup
import { z } from 'zod';
const envSchema = z.object({
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
  DATABASE_URL: z.string().url(),
  NODE_ENV: z.enum(['development', 'test', 'production']),
  PORT: z.coerce.number().default(3000),
});
export const env = envSchema.parse(process.env); // fails loudly at boot
```

### 5.4 Magic Numbers Everywhere
```ts
// ❌ AI slop
if (user.planId === 3) allowFeature = true;
setTimeout(refresh, 30000);
if (text.length > 280) truncate(text);

// ✅ Fixed — named constants
const PLAN_IDS = { free: 1, pro: 2, enterprise: 3 } as const;
const REFRESH_INTERVAL_MS = 30_000;
const TWEET_MAX_LENGTH = 280;

if (user.planId === PLAN_IDS.enterprise) allowFeature = true;
```

### 5.5 Missing Database Indexes
```prisma
// ❌ AI slop — no indexes on frequently queried columns
model User {
  id    String @id
  email String       // queried for login — full table scan!
  posts Post[]
}

// ✅ Fixed
model User {
  id        String   @id @default(cuid())
  email     String   @unique              // @unique creates index automatically
  createdAt DateTime @default(now())
  posts     Post[]

  @@index([createdAt])    // for time-range queries
}
```

---

## 6. Security Slop — Critical

All of the following are 🚨 Critical severity. Ship any of these to production and you have a security incident.

### 6.1 Hardcoded Credentials in Source
```ts
// ❌ CRITICAL — AI does this frequently
const openai = new OpenAI({ apiKey: "sk-proj-abc123xyz..." });
const db = new Client({ password: "mySecretPassword123" });

// ✅ Fixed — always from environment
const openai = new OpenAI({ apiKey: env.OPENAI_API_KEY });
```

### 6.2 SQL Injection via Template Literals
```ts
// ❌ CRITICAL — classic injection
const result = await db.query(
  `SELECT * FROM users WHERE email = '${email}'`
);

// ✅ Fixed — parameterized query
const result = await db.query(
  'SELECT * FROM users WHERE email = $1',
  [email]
);
```

### 6.3 Missing Supabase Row Level Security
```sql
-- ❌ AI creates tables without RLS — any user can read/write any row
CREATE TABLE documents (id uuid, user_id uuid, content text);

-- ✅ Fixed — enable RLS and add policies
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own their documents"
  ON documents FOR ALL
  USING (auth.uid() = user_id);
```

### 6.4 No Rate Limiting on Public Endpoints
```ts
// ✅ Always add rate limiting to any public or auth endpoint
import rateLimit from 'express-rate-limit';

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 10, // 10 auth attempts per 15 min
  standardHeaders: true,
  message: { error: 'Too many attempts. Try again in 15 minutes.' },
});
app.use('/auth/', authLimiter);

const apiLimiter = rateLimit({ windowMs: 60_000, max: 100 });
app.use('/api/', apiLimiter);
```

---

## 7. Performance Slop

### 7.1 Rendering Huge Lists Without Virtualization
```tsx
// ❌ AI slop — renders 10,000 DOM nodes
{allItems.map(item => <ItemRow key={item.id} item={item} />)}

// ✅ Fixed — windowed rendering
import { FixedSizeList } from 'react-window';
<FixedSizeList height={600} itemCount={allItems.length} itemSize={52} width="100%">
  {({ index, style }) => (
    <ItemRow style={style} item={allItems[index]} />
  )}
</FixedSizeList>
```

### 7.2 Sequential Fetches (Waterfall)
```ts
// ❌ AI slop — 2× slower, sequential
const user = await getUser(id);
const posts = await getUserPosts(user.id);

// ✅ Fixed — parallel when independent
const [user, posts] = await Promise.all([getUser(id), getUserPosts(id)]);
```

### 7.3 No Loading / Error States in Data Fetching
```tsx
// ❌ AI slop — null render during load, no error recovery
function Profile({ id }) {
  const [user, setUser] = useState(null);
  useEffect(() => {
    fetch(`/api/users/${id}`).then(r => r.json()).then(setUser);
  }, [id]);
  if (!user) return null; // invisible blank screen
  return <UserCard user={user} />;
}

// ✅ Fixed — all states handled
function Profile({ id }) {
  const { data: user, isLoading, error } = useQuery(['user', id], () => api.getUser(id));
  if (isLoading) return <UserCardSkeleton />;
  if (error) return <ErrorMessage error={error} retry={() => refetch()} />;
  return <UserCard user={user} />;
}
```

---

## 8. Code Quality Tells

### AI Comment Patterns to Flag
```ts
// ❌ Comments restating the code (delete these)
const count = 0; // Initialize count to zero
setCount(prev => prev + 1); // Increment count by 1

// ❌ Vague TODOs (make specific or file an issue)
// TODO: Handle edge cases
// TODO: Add error handling
// TODO: Optimize this later

// ❌ AI disclaimer comments (remove entirely)
// Note: This is a simplified implementation
// Note: In production, you would want to add...
// This is just for demonstration purposes

// ✅ Good comments explain WHY
// Using exponential backoff here because the API rate limits at 100/min
// and linear retry causes thundering herd on recovery
```

### TypeScript Slop
```ts
// ❌ Common AI TypeScript anti-patterns
function process(data: any): any { ... }      // defeats TypeScript
const user = getUser()!;                       // unchecked assertion
const config: { [key: string]: any } = {};    // index signature + any

// ✅ Be specific
function process(data: ProcessInput): ProcessResult { ... }
const user = getUser() ?? redirect('/login'); // handle null explicitly
const config: Record<ConfigKey, ConfigValue> = {}; // typed record
```

### Test Slop
```ts
// ❌ AI test anti-patterns
it('calls setUser when fetch completes') // tests implementation, not behavior
it('should submit successfully') // happy path only, no failure cases

// ✅ Behavior-focused tests with failure cases
describe('login form', () => {
  it('redirects to /dashboard on valid credentials');
  it('shows specific error message on wrong password');
  it('disables submit button while loading');
  it('locks the form after 5 failed attempts');
  it('clears password field on failed attempt');
});
```

---

## 9. Remediation Principles

### The Senior Engineer Test
OX Security's 2025 research: AI code is "highly functional but systematically lacking architectural judgment." Ask: would a senior engineer approve this PR without changes? If not, list exactly what they'd comment on.

### The Security Audit Checklist (Every AI-generated endpoint)
```
☐ Authentication required (if resource is private)?
☐ Authorization: does this user own this resource?
☐ All inputs validated with a schema?
☐ Rate limiting applied?
☐ Error messages don't expose internals or stack traces?
☐ No secrets, keys, or credentials in code?
☐ Pagination/limits on any collection endpoint?
```

### The Architecture Consistency Test
Before merging AI code:
- Does it introduce a 3rd way to do something already done 2 ways?
- Does it skip the defined layer separation (route → service → repo)?
- Does it have magic numbers instead of named constants?
- Does it import from a layer it shouldn't know about?

### The Refactoring Signal
Google's DORA 2025 report: AI adoption correlated with refactoring dropping from 25% to 10% of changes. If the AI added a feature without improving the surrounding code, the codebase is accumulating debt. Push back and request refactoring alongside new features.

---

## 10. Before / After Examples

### Example 1: Data Fetching Component

**BEFORE (AI slop):**
```tsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/users/${userId}`)
      .then(r => r.json())
      .then(data => { setUser(data); setLoading(false); })
      .catch(err => { setError(err.message); setLoading(false); });
  }, [userId]); // no cleanup, impossible states, no empty state
}
```

**AFTER:**
```tsx
// hooks/useUser.ts
const useUser = (userId: string) =>
  useQuery({ queryKey: ['user', userId], queryFn: () => api.users.getById(userId) });

// components/UserProfile.tsx
function UserProfile({ userId }: { userId: string }) {
  const { data: user, isLoading, error, refetch } = useUser(userId);

  if (isLoading) return <UserProfileSkeleton />;
  if (error) return <ErrorState error={error} onRetry={refetch} />;
  if (!user) return <EmptyState message="User not found" />;

  return <UserCard user={user} />;
}
```

### Example 2: API Route

**BEFORE (AI slop):**
```ts
app.post('/api/posts', async (req, res) => {
  try {
    const post = await prisma.post.create({ data: req.body }); // no validation, no auth
    res.json(post);
  } catch (e) {
    res.status(500).json({ error: 'Something went wrong' });
  }
});
```

**AFTER:**
```ts
const CreatePostSchema = z.object({
  title: z.string().min(1).max(200),
  content: z.string().min(1),
  published: z.boolean().default(false),
});

app.post('/api/posts',
  requireAuth,
  rateLimiter({ max: 10, windowMs: 60_000 }),
  validateBody(CreatePostSchema),
  asyncHandler(async (req, res) => {
    const post = await prisma.post.create({
      data: { ...req.validatedBody, authorId: req.user.id },
    });
    res.status(201).json(post);
  })
);
```
