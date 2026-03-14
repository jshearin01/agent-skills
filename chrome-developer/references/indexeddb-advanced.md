# IndexedDB Advanced — Multi-Paradigm Browser Database

## Table of Contents
1. [Core API & the `idb` Library](#1-core-api--the-idb-library)
2. [Schema Design & Upgrades](#2-schema-design--upgrades)
3. [Indexes & Compound Queries](#3-indexes--compound-queries)
4. [Transactions & Atomicity](#4-transactions--atomicity)
5. [Cursor Patterns (Aggregation, Bulk)](#5-cursor-patterns)
6. [Vector Store — Cosine Similarity Search](#6-vector-store--cosine-similarity-search)
7. [Graph Database Patterns](#7-graph-database-patterns)
8. [Full-Text Search](#8-full-text-search)
9. [Quota Management & Storage Estimation](#9-quota-management--storage-estimation)
10. [Workers & Service Workers](#10-workers--service-workers)
11. [Migration Patterns](#11-migration-patterns)
12. [PGlite — Full PostgreSQL in Browser](#12-pglite--full-postgresql-in-browser)

---

## 1. Core API & the `idb` Library

### Why use `idb` (npm: `idb`)

The raw IDB API uses events/callbacks which are error-prone. The `idb` library wraps everything in promises with a clean, modern API. **Always use it.**

```bash
npm install idb
```

```js
import { openDB, deleteDB, wrap, unwrap } from 'idb';

// Basic open
const db = await openDB('my-database', 1, {
  upgrade(db, oldVersion, newVersion, transaction) {
    // Run on version bump — create/modify object stores
    if (oldVersion < 1) {
      db.createObjectStore('users', { keyPath: 'id' });
    }
  },
  blocked() { console.warn('IDB blocked by older tab'); },
  blocking() { console.warn('This tab is blocking a newer version'); },
  terminated() { console.error('IDB connection terminated unexpectedly'); },
});
```

### CRUD Operations

```js
// Create / Update
await db.put('users', { id: '1', name: 'Alice', age: 30 });
await db.add('users', { id: '2', name: 'Bob', age: 25 }); // fails if key exists

// Read
const user = await db.get('users', '1');
const all = await db.getAll('users');
const keys = await db.getAllKeys('users');
const count = await db.count('users');

// Delete
await db.delete('users', '1');
await db.clear('users');

// Key range queries
const range = IDBKeyRange.bound('a', 'z');          // inclusive
const half = IDBKeyRange.lowerBound('m');           // >= 'm'
const limited = await db.getAll('users', range, 10); // max 10 results
```

---

## 2. Schema Design & Upgrades

### Versioned Migrations

```js
const db = await openDB('app-db', 3, {
  upgrade(db, oldVersion, newVersion, tx) {
    // Always use if-chains, never switch fallthrough
    if (oldVersion < 1) {
      // v1: initial schema
      const users = db.createObjectStore('users', { keyPath: 'id' });
      users.createIndex('by-email', 'email', { unique: true });
    }
    if (oldVersion < 2) {
      // v2: add posts store
      const posts = db.createObjectStore('posts', { keyPath: 'id', autoIncrement: true });
      posts.createIndex('by-author', 'authorId');
      posts.createIndex('by-created', 'createdAt');
    }
    if (oldVersion < 3) {
      // v3: add index to existing store (access via transaction)
      tx.objectStore('users').createIndex('by-age', 'age');
    }
  }
});
```

### Key Path Options

```js
// keyPath: 'id'          — property of stored object is the key
// keyPath: ['a', 'b']   — compound key from two properties
// autoIncrement: true   — auto-increment integer key (keyPath must be empty or 'id')
// no keyPath            — explicit key required in put/add calls

// Examples:
db.createObjectStore('docs', { keyPath: 'id' });
db.createObjectStore('events', { keyPath: ['type', 'timestamp'] }); // compound
db.createObjectStore('blobs', { autoIncrement: true });             // auto id
db.createObjectStore('kvStore');                                     // explicit key
await db.put('kvStore', { data: 'value' }, 'my-key');
```

---

## 3. Indexes & Compound Queries

### Creating Indexes

```js
// Simple index
store.createIndex('by-status', 'status');

// Unique index (prevents duplicate values)
store.createIndex('by-email', 'email', { unique: true });

// Multi-entry index (for array properties — indexes each element)
store.createIndex('by-tag', 'tags', { multiEntry: true });

// Compound index
store.createIndex('by-user-date', ['userId', 'createdAt']);

// Nested property index
store.createIndex('by-city', 'address.city');
```

### Querying Indexes

```js
// Exact match
const alice = await db.getFromIndex('users', 'by-email', 'alice@example.com');

// Range on index
const adults = await db.getAllFromIndex('users', 'by-age', IDBKeyRange.lowerBound(18));

// Multi-entry: find all docs with tag 'ai'
const aiDocs = await db.getAllFromIndex('docs', 'by-tag', 'ai');

// Compound index exact match
const userPosts = await db.getAllFromIndex('posts', 'by-user-date', ['user123']);

// Compound index range: user's posts in last 7 days
const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
const recentPosts = await db.getAllFromIndex(
  'posts',
  'by-user-date',
  IDBKeyRange.bound(['user123', weekAgo], ['user123', Date.now()])
);
```

---

## 4. Transactions & Atomicity

```js
// Single-store transaction (shorthand: db.get, db.put etc. auto-create transactions)
await db.put('users', updatedUser);

// Multi-store transaction (atomic across stores)
const tx = db.transaction(['users', 'posts'], 'readwrite');
const usersStore = tx.objectStore('users');
const postsStore = tx.objectStore('posts');

await usersStore.put({ id: 'u1', name: 'Alice', postCount: 5 });
await postsStore.add({ title: 'Hello', authorId: 'u1', createdAt: Date.now() });
await tx.done; // waits for all operations in this transaction

// Error handling — transaction auto-aborts on error
try {
  const tx2 = db.transaction('users', 'readwrite');
  await tx2.store.put({ id: 'u2', email: 'existing@email.com' }); // might throw if unique
  await tx2.done;
} catch (e) {
  console.error('Transaction failed and was rolled back:', e);
}
```

---

## 5. Cursor Patterns

Cursors allow iterating records without loading everything into memory — essential for large stores.

```js
// Iterate all records
let cursor = await db.transaction('posts').store.openCursor();
while (cursor) {
  console.log(cursor.key, cursor.value);
  cursor = await cursor.continue();
}

// Iterate with index, specific range, direction
const index = db.transaction('posts').store.index('by-created');
let c = await index.openCursor(
  IDBKeyRange.lowerBound(weekAgo),
  'prev' // newest first
);
const results = [];
while (c && results.length < 20) {
  results.push(c.value);
  c = await c.continue();
}

// Aggregation — COUNT + SUM without loading all data
async function aggregatePostStats() {
  let count = 0, totalLength = 0;
  let cursor = await db.transaction('posts').store.openCursor();
  while (cursor) {
    count++;
    totalLength += cursor.value.content?.length ?? 0;
    cursor = await cursor.continue();
  }
  return { count, avgLength: count ? totalLength / count : 0 };
}

// Bulk update (update in place without re-inserting)
async function markAllRead(userId) {
  const tx = db.transaction('posts', 'readwrite');
  const index = tx.store.index('by-author');
  let cursor = await index.openCursor(userId);
  while (cursor) {
    if (!cursor.value.read) {
      cursor.update({ ...cursor.value, read: true }); // update in place
    }
    cursor = await cursor.continue();
  }
  await tx.done;
}
```

---

## 6. Vector Store — Cosine Similarity Search

### Schema

```js
const db = await openDB('vector-store', 2, {
  upgrade(db, old) {
    if (old < 1) {
      const v = db.createObjectStore('vectors', { keyPath: 'id', autoIncrement: true });
      v.createIndex('by-collection', 'collection');
      v.createIndex('by-collection-created', ['collection', 'createdAt']);
    }
    if (old < 2) {
      // Add metadata filtering support
      db.transaction('vectors').objectStore('vectors')
        .createIndex('by-tag', 'tags', { multiEntry: true });
    }
  }
});
```

### Insert & Search

```js
// Similarity functions
const cosineSim = (a, b) => {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i]*b[i]; na += a[i]**2; nb += b[i]**2; }
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
};

const euclideanDist = (a, b) => {
  let sum = 0;
  for (let i = 0; i < a.length; i++) sum += (a[i]-b[i])**2;
  return Math.sqrt(sum);
};

// Insert
async function vectorInsert(collection, text, embedding, metadata = {}) {
  return db.add('vectors', {
    collection,
    text,
    embedding: Array.from(embedding), // Float32Array → plain array for IDB serialization
    metadata,
    tags: metadata.tags ?? [],
    createdAt: Date.now()
  });
}

// Brute-force cosine search (fast up to ~50K vectors in JS; use WebGPU for larger)
async function vectorSearch(queryEmbedding, collection, {
  topK = 5,
  minScore = 0.5,
  filter = null   // optional: { tag: 'science' }
} = {}) {
  let candidates;
  if (filter?.tag) {
    candidates = await db.getAllFromIndex('vectors', 'by-tag', filter.tag);
    candidates = candidates.filter(c => c.collection === collection);
  } else {
    candidates = await db.getAllFromIndex('vectors', 'by-collection', collection);
  }

  return candidates
    .map(doc => ({ ...doc, score: cosineSim(queryEmbedding, doc.embedding) }))
    .filter(doc => doc.score >= minScore)
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

// WebGPU-accelerated batch similarity (for >50K vectors)
async function gpuSimilaritySearch(device, queryEmbedding, allEmbeddings, topK = 10) {
  const dim = queryEmbedding.length;
  const n = allEmbeddings.length;

  // Flatten all embeddings into one buffer
  const flat = new Float32Array(n * dim);
  allEmbeddings.forEach((e, i) => flat.set(e, i * dim));

  const queryBuf = device.createBuffer({ size: dim * 4, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST, mappedAtCreation: true });
  new Float32Array(queryBuf.getMappedRange()).set(queryEmbedding);
  queryBuf.unmap();

  // ... dispatch compute shader to compute all cosine similarities in parallel
  // Returns Float32Array of scores, then pick topK on CPU
  // See scripts/indexeddb-patterns.js for full GPU similarity shader
}
```

### Approximate Nearest Neighbor with PGlite + pgvector

```js
import { PGlite } from '@electric-sql/pglite';
import { vector } from '@electric-sql/pglite/vector';

const db = new PGlite({ extensions: { vector } });
await db.exec(`
  CREATE EXTENSION IF NOT EXISTS vector;
  CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT,
    embedding vector(384)
  );
  CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
`);

// Insert
await db.query(
  'INSERT INTO documents (content, embedding) VALUES ($1, $2)',
  ['My document text', embedding.join(',')]
);

// ANN search (HNSW — much faster than brute force for large collections)
const results = await db.query(
  'SELECT content, 1 - (embedding <=> $1::vector) as score FROM documents ORDER BY embedding <=> $1::vector LIMIT 5',
  [queryEmbedding.join(',')]
);
```

---

## 7. Graph Database Patterns

### Schema

```js
const db = await openDB('graph', 1, {
  upgrade(db) {
    db.createObjectStore('nodes', { keyPath: 'id' });
    const e = db.createObjectStore('edges', { keyPath: 'id', autoIncrement: true });
    e.createIndex('by-from', 'from');
    e.createIndex('by-to', 'to');
    e.createIndex('by-type', 'type');
    e.createIndex('by-from-type', ['from', 'type']);
  }
});
```

### Graph Operations

```js
// Add node / edge
const addNode = (id, labels, props = {}) => db.put('nodes', { id, labels, ...props });
const addEdge = (from, to, type, weight = 1, props = {}) =>
  db.add('edges', { from, to, type, weight, ...props });

// Get edges by type from a node (e.g., FOLLOWS, LIKES)
const getEdgesByType = (nodeId, type) =>
  db.getAllFromIndex('edges', 'by-from-type', [nodeId, type]);

// BFS with visited set
async function bfs(startId, maxDepth = 4, edgeType = null) {
  const visited = new Set([startId]);
  const layers = [[startId]];

  for (let depth = 0; depth < maxDepth; depth++) {
    const current = layers[depth];
    if (!current.length) break;
    const next = [];
    for (const id of current) {
      const edges = edgeType
        ? await db.getAllFromIndex('edges', 'by-from-type', [id, edgeType])
        : await db.getAllFromIndex('edges', 'by-from', id);
      for (const edge of edges) {
        if (!visited.has(edge.to)) {
          visited.add(edge.to);
          next.push(edge.to);
        }
      }
    }
    layers.push(next);
  }
  return layers;
}

// PageRank (simplified, single iteration)
async function computePageRank(dampingFactor = 0.85, iterations = 10) {
  const allNodes = await db.getAll('nodes');
  const scores = Object.fromEntries(allNodes.map(n => [n.id, 1 / allNodes.length]));

  for (let iter = 0; iter < iterations; iter++) {
    const newScores = {};
    for (const node of allNodes) {
      const inEdges = await db.getAllFromIndex('edges', 'by-to', node.id);
      let sum = 0;
      for (const edge of inEdges) {
        const outCount = (await db.getAllFromIndex('edges', 'by-from', edge.from)).length;
        sum += (scores[edge.from] ?? 0) / (outCount || 1);
      }
      newScores[node.id] = (1 - dampingFactor) / allNodes.length + dampingFactor * sum;
    }
    Object.assign(scores, newScores);
  }
  return scores;
}
```

---

## 8. Full-Text Search

IDB has no built-in FTS. Common approaches:

```js
// Option 1: Inverted index (fast, manual)
async function buildInvertedIndex(docId, text) {
  const tokens = text.toLowerCase().match(/\b\w+\b/g) ?? [];
  const unique = [...new Set(tokens)];
  const tx = db.transaction('inverted-index', 'readwrite');
  for (const token of unique) {
    const existing = await tx.store.get(token) ?? { token, docIds: [] };
    if (!existing.docIds.includes(docId)) {
      existing.docIds.push(docId);
      tx.store.put(existing);
    }
  }
  await tx.done;
}

async function ftsSearch(query) {
  const tokens = query.toLowerCase().match(/\b\w+\b/g) ?? [];
  const sets = await Promise.all(tokens.map(async t => {
    const entry = await db.get('inverted-index', t);
    return new Set(entry?.docIds ?? []);
  }));
  // Intersection (AND search)
  if (!sets.length) return [];
  const result = [...sets[0]].filter(id => sets.every(s => s.has(id)));
  return Promise.all(result.map(id => db.get('docs', id)));
}

// Option 2: Use FlexSearch (npm: flexsearch) with IDB persistence
import { Document } from 'flexsearch';
const index = new Document({ document: { id: 'id', index: ['title', 'content'] } });
// serialize/deserialize to IDB for persistence
```

---

## 9. Quota Management & Storage Estimation

```js
// Check available storage
async function checkStorageQuota() {
  const estimate = await navigator.storage.estimate();
  return {
    usedMB: (estimate.usage / 1e6).toFixed(1),
    quotaMB: (estimate.quota / 1e6).toFixed(1),
    percentUsed: ((estimate.usage / estimate.quota) * 100).toFixed(1),
    breakdown: estimate.usageDetails // Chrome 61+: breakdown by type
  };
}

// Request persistent storage (prevents eviction under storage pressure)
async function requestPersistentStorage() {
  if (navigator.storage?.persist) {
    const granted = await navigator.storage.persist();
    console.log('Persistent storage:', granted ? 'granted' : 'denied');
    return granted;
  }
  return false;
}

// IDB-specific size check
async function estimateIDBSize(dbName) {
  // Indirect: compare storage before/after
  const before = await navigator.storage.estimate();
  const db = await openDB(dbName, 1);
  db.close();
  const after = await navigator.storage.estimate();
  return (after.usage - before.usage) / 1e6; // MB (approximate)
}

// Eviction strategy: remove oldest entries when quota is tight
async function evictOldEntries(storeName, maxCount = 10000) {
  const count = await db.count(storeName);
  if (count <= maxCount) return 0;

  const toDelete = count - maxCount;
  const tx = db.transaction(storeName, 'readwrite');
  const index = tx.store.index('by-created');
  let cursor = await index.openCursor(); // oldest first
  let deleted = 0;
  while (cursor && deleted < toDelete) {
    await cursor.delete();
    cursor = await cursor.continue();
    deleted++;
  }
  await tx.done;
  return deleted;
}
```

---

## 10. Workers & Service Workers

IDB works in web workers and service workers — critical for extensions and offline PWAs.

```js
// In a service worker — cache model files AND use IDB for structured data
self.addEventListener('install', (event) => {
  event.waitUntil(
    openDB('sw-cache', 1, {
      upgrade(db) { db.createObjectStore('config'); }
    }).then(db => db.put('config', { version: '1.0', installed: Date.now() }, 'app'))
  );
});

// In a web worker — full IDB access
// worker.js
import { openDB } from 'idb';
self.onmessage = async ({ data }) => {
  const db = await openDB('worker-db', 1, { upgrade(db) { db.createObjectStore('cache'); } });
  await db.put('cache', data.payload, data.key);
  self.postMessage({ type: 'stored', key: data.key });
};

// NOTE: IDB connections must be opened per worker context — don't share handles across workers
```

---

## 11. Migration Patterns

```js
// Safe migration with data transformation
const db = await openDB('app', 4, {
  async upgrade(db, oldVersion, newVersion, tx) {
    if (oldVersion < 3) {
      // Migrate: add 'status' field with default to all existing records
      const store = tx.objectStore('posts');
      let cursor = await store.openCursor();
      while (cursor) {
        cursor.update({ ...cursor.value, status: cursor.value.status ?? 'published' });
        cursor = await cursor.continue();
      }
    }
    if (oldVersion < 4) {
      // Rename store: copy old → new, delete old
      const old = tx.objectStore('posts');
      const newStore = db.createObjectStore('articles', { keyPath: 'id' });
      newStore.createIndex('by-author', 'authorId');
      let cursor = await old.openCursor();
      while (cursor) {
        newStore.add({ ...cursor.value, migratedAt: Date.now() });
        cursor = await cursor.continue();
      }
      db.deleteObjectStore('posts');
    }
  }
});
```

---

## 12. PGlite — Full PostgreSQL in Browser

PGlite runs the actual PostgreSQL engine in WASM, with full SQL support + pgvector.
Persists to IndexedDB. Perfect for complex relational queries.

```js
import { PGlite } from '@electric-sql/pglite';

// Persisted to IDB
const db = new PGlite('idb://my-app-db');
await db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title TEXT,
    body TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id);
`);

// Full SQL including JOINs, aggregates, window functions
const result = await db.query(`
  SELECT u.name, COUNT(p.id) AS post_count
  FROM users u
  LEFT JOIN posts p ON p.user_id = u.id
  GROUP BY u.id, u.name
  ORDER BY post_count DESC
  LIMIT 10
`);

// With pgvector (requires @electric-sql/pglite/vector extension)
import { vector } from '@electric-sql/pglite/vector';
const dbVec = new PGlite({ extensions: { vector } });
await dbVec.exec(`
  CREATE EXTENSION vector;
  CREATE TABLE embeddings (id SERIAL, content TEXT, vec vector(384));
  CREATE INDEX ON embeddings USING hnsw (vec vector_cosine_ops);
`);
// ANN search: finds semantically similar rows at scale
const similar = await dbVec.query(
  `SELECT content, 1-(vec <=> $1::vector) AS sim FROM embeddings ORDER BY vec <=> $1::vector LIMIT 5`,
  [`[${queryEmbedding.join(',')}]`]
);
```

PGlite tradeoffs vs raw IDB:
- ✅ Full SQL (JOINs, GROUP BY, window functions, CTEs, pgvector HNSW)
- ✅ ACID transactions with savepoints
- ❌ Larger bundle size (~5MB WASM)
- ❌ Slower startup than raw IDB
- ✅ Best for complex relational + vector workloads
