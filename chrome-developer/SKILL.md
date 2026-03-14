---
name: chrome-developer
description: >
  Expert Chrome developer skill covering advanced browser APIs and capabilities. Use this skill whenever
  working on Chrome extensions (Manifest V3), WebAssembly (Wasm 3.0), WebGPU (graphics and compute),
  WebNN (neural network inference), Chrome Built-in AI (Gemini Nano Prompt API, Summarizer, Translator),
  local ML model inference in the browser, IndexedDB (as SQL/NoSQL/vector/graph database), downloading
  and running HuggingFace models locally with WebGPU, or any advanced Chrome platform feature.
  Trigger this skill for requests about: building Chrome extensions, MV3 service workers, offscreen
  documents, declarativeNetRequest, running LLMs or ML models client-side (Qwen3, Llama, Phi, Gemma,
  Mistral, SmolLM), GPU compute shaders, WGSL shader language, WebAssembly SIMD/threads/GC, on-device
  AI without server infrastructure, browser performance optimization with WASM/GPU, WebGPU for
  machine learning, ONNX Runtime Web, Transformers.js v3, WebLLM, model quantization (q4/q4f16/fp16),
  IndexedDB as a database (key-value, relational patterns, vector similarity search, graph traversal,
  semantic RAG), caching ML models in IndexedDB/Cache API, or any task involving Chrome's advanced
  platform APIs. Also use for DevTools advanced usage, Chrome flags, performance profiling, and
  Chromium internals.
---

# Chrome Developer — Advanced Platform Skill

You are an expert Chrome platform developer with deep knowledge of all advanced browser capabilities
as of 2026. You write production-quality code and give concrete, accurate guidance.

## Capability Map

| Domain | Key APIs / Tools | Maturity |
|--------|-----------------|----------|
| Chrome Extensions | MV3, Service Workers, Offscreen Documents, declarativeNetRequest | ✅ Stable |
| WebAssembly | Wasm 3.0, SIMD, Threads, GC, Memory64, Emscripten, wasm-bindgen | ✅ Stable |
| WebGPU | Compute Shaders, WGSL, Dawn, Render Bundles, Compatibility Mode | ✅ Stable (all browsers) |
| WebNN | MLContext, MLGraphBuilder, NPU/GPU/CPU routing | 🧪 Origin Trial (Chrome 146+) |
| Built-in AI | Gemini Nano, Prompt API, Summarizer, Writer, Translator, Rewriter | 🧪 Chrome 138+ (desktop) |
| Local ML Inference | ONNX Runtime Web, Transformers.js v3, WebLLM, TensorFlow.js | ✅ Stable |
| HF Models + WebGPU | Qwen3, Llama-3.2, Phi-4, Gemma-3, SmolLM2 — download & run | ✅ Stable |
| IndexedDB | NoSQL, SQL patterns, Vector DB, Graph DB, RAG store | ✅ Stable |

---

## 1. Chrome Extensions (Manifest V3)

### Architecture Overview

MV3 extensions use a **service worker** as the background context (replaces persistent background pages).
Key constraints: no DOM access, terminates when idle, no global state persistence.

```json
// manifest.json skeleton
{
  "manifest_version": 3,
  "name": "My Extension",
  "version": "1.0.0",
  "permissions": ["storage", "alarms", "offscreen"],
  "host_permissions": ["https://*/*"],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [{
    "matches": ["<all_urls>"],
    "js": ["content.js"]
  }],
  "action": { "default_popup": "popup.html" }
}
```

### Service Worker Patterns

**State persistence** — service workers terminate; always persist to `chrome.storage`:
```js
// ❌ WRONG: Global state lost on termination
let counter = 0;

// ✅ CORRECT: Persist to storage
async function increment() {
  const { counter = 0 } = await chrome.storage.local.get('counter');
  await chrome.storage.local.set({ counter: counter + 1 });
}
```

**Keep-alive strategies** (Chrome 116+):
- Active WebSocket connections reset the idle timer
- Messages from offscreen documents reset the timer
- Active `chrome.debugger` sessions keep the worker alive
- `chrome.alarms` minimum 30-second interval

**Register listeners synchronously** — async registration is not guaranteed:
```js
// ❌ WRONG
chrome.storage.local.get(['ready'], () => {
  chrome.runtime.onMessage.addListener(handler); // may be missed
});

// ✅ CORRECT — top-level registration
chrome.runtime.onMessage.addListener(handler);
chrome.alarms.onAlarm.addListener(alarmHandler);
```

### Offscreen Documents

Use when you need DOM APIs inside an extension (audio, clipboard, canvas, workers, localStorage):

```js
// background.js — create offscreen document
async function ensureOffscreen() {
  const existing = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT']
  });
  if (existing.length > 0) return;
  await chrome.offscreen.createDocument({
    url: 'offscreen.html',
    reasons: ['DOM_SCRAPING'],   // must match actual use
    justification: 'Parse HTML content from page'
  });
}

// Send data to offscreen doc
await ensureOffscreen();
chrome.runtime.sendMessage({ type: 'process', data: payload });
```

Available `reasons`: `AUDIO_PLAYBACK`, `CLIPBOARD`, `DOM_PARSER`, `DOM_SCRAPING`,
`IFRAME_SCRIPTING`, `LOCAL_STORAGE`, `MATCH_MEDIA`, `WORKERS`, `GEOLOCATION`, `BATTERY_STATUS`

### Network Interception (declarativeNetRequest)

Replaces blocking `webRequest`. Performant, privacy-preserving:
```json
// rules.json
[{
  "id": 1,
  "priority": 1,
  "action": { "type": "block" },
  "condition": {
    "urlFilter": "||ads.example.com^",
    "resourceTypes": ["script", "image"]
  }
}]
```

```js
// Dynamic rules at runtime
await chrome.declarativeNetRequest.updateDynamicRules({
  addRules: [{ id: 2, priority: 1, action: { type: 'redirect',
    redirect: { url: 'https://safe.example.com' }}, condition: { ... }}],
  removeRuleIds: [1]
});
```

### Message Passing Patterns

```js
// From content script to background
const response = await chrome.runtime.sendMessage({ action: 'getData' });

// Long-lived connection (resets service worker timer)
const port = chrome.runtime.connect({ name: 'stream' });
port.onMessage.addListener(msg => console.log(msg));
port.postMessage({ type: 'start' });

// Background receiving messages
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'getData') {
    fetchData().then(sendResponse);
    return true; // keep channel open for async response
  }
});
```

> 📖 See `references/chrome-extensions-mv3.md` for complete API reference, storage types, permissions guide, testing patterns, and Chrome Web Store publishing checklist.

---

## 2. WebAssembly (Wasm 3.0)

### What's New in Wasm 3.0 (Standardized Sept 2025)

| Feature | Description | Use Case |
|---------|-------------|----------|
| **GC** | Browser-native garbage collection | Java, Kotlin, Dart, Python → Wasm |
| **Memory64** | 64-bit address space (>4GB) | Large datasets, ML models |
| **SIMD (relaxed)** | Hardware-optimized vector ops | Signal processing, ML inference |
| **Threads** | SharedArrayBuffer + atomics | Parallel compute, workers |
| **Tail Calls** | Stack-safe recursion | Functional languages, interpreters |
| **Exception Handling** | Native try/catch with exnref | C++, Rust panic propagation |
| **Multi-memory** | Multiple independent linear memories | Isolation, modular design |

### Toolchain Selection

```
Rust    → wasm-pack / wasm-bindgen (best ergonomics, no GC needed)
C/C++   → Emscripten (most compatible, WebGPU via emdawnwebgpu)
Kotlin  → KotlinJS / K2/Wasm (leverages browser GC)
Go      → TinyGo or standard Go (tinygo better for size)
Python  → Pyodide (ships CPython to browser)
```

### Rust + wasm-bindgen Example

```rust
// src/lib.rs
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn process_image(pixels: &[u8], width: u32, height: u32) -> Vec<u8> {
    // SIMD-accelerated image processing
    pixels.chunks(4)
        .flat_map(|px| {
            let gray = (0.299 * px[0] as f32 + 0.587 * px[1] as f32 
                       + 0.114 * px[2] as f32) as u8;
            [gray, gray, gray, px[3]]
        })
        .collect()
}
```

```bash
wasm-pack build --target web --release
```

```js
// main.js — consuming the WASM module
import init, { process_image } from './pkg/my_module.js';

const wasm = await init();
const result = process_image(pixelData, width, height);
```

### Threading with SharedArrayBuffer

```js
// Requires COOP/COEP headers:
// Cross-Origin-Opener-Policy: same-origin
// Cross-Origin-Embedder-Policy: require-corp

const worker = new Worker('worker.js');
const sharedBuffer = new SharedArrayBuffer(1024 * 1024);
const sharedArray = new Float32Array(sharedBuffer);

worker.postMessage({ buffer: sharedBuffer });
```

### Performance Patterns

- **Minimize JS↔Wasm boundary crossings** — batch operations, pass typed arrays
- **Use `WebAssembly.compileStreaming`** — compile in parallel with download
- **Memory management** — use `Memory64` for models >4GB, free explicitly in linear memory langs
- **Feature detection** — use `wasm-feature-detect` library before relying on Wasm 3.0 features

> 📖 See `references/webgpu-webnn-webassembly.md` for WGSL shader patterns, Emscripten build flags, and WASM↔WebGPU interop.

---

## 3. WebGPU

### Core Concepts

WebGPU is available in all major browsers (Chrome 113+, Firefox 141+, Safari 26+). It exposes
modern GPU capabilities: compute shaders, render pipelines, GPU buffers, and textures.

```js
// Initialization
const adapter = await navigator.gpu.requestAdapter();
const device = await adapter.requestDevice();

// For older GPUs (OpenGL/D3D11), use compatibility mode (Chrome 146+):
const adapter = await navigator.gpu.requestAdapter({ featureLevel: 'compatibility' });
```

### Compute Shader (WGSL) — ML-style tensor operation

```wgsl
// shader.wgsl
@group(0) @binding(0) var<storage, read> input: array<f32>;
@group(0) @binding(1) var<storage, read_write> output: array<f32>;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) id: vec3u) {
    let i = id.x;
    if (i >= arrayLength(&input)) { return; }
    // ReLU activation
    output[i] = max(0.0, input[i]);
}
```

```js
// Running the compute shader
const pipeline = await device.createComputePipelineAsync({
  layout: 'auto',
  compute: { module: device.createShaderModule({ code: shaderWGSL }), entryPoint: 'main' }
});

const inputBuffer = device.createBuffer({
  size: data.byteLength,
  usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST,
});
device.queue.writeBuffer(inputBuffer, 0, data);

const outputBuffer = device.createBuffer({
  size: data.byteLength,
  usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC,
});

const bindGroup = device.createBindGroup({
  layout: pipeline.getBindGroupLayout(0),
  entries: [
    { binding: 0, resource: { buffer: inputBuffer } },
    { binding: 1, resource: { buffer: outputBuffer } },
  ]
});

const encoder = device.createCommandEncoder();
const pass = encoder.beginComputePass();
pass.setPipeline(pipeline);
pass.setBindGroup(0, bindGroup);
pass.dispatchWorkgroups(Math.ceil(data.length / 64));
pass.end();
device.queue.submit([encoder.finish()]);
```

### WebGPU + ML Frameworks

```js
// ONNX Runtime Web with WebGPU backend
import * as ort from 'onnxruntime-web';

ort.env.wasm.wasmPaths = '/wasm/';
const session = await ort.InferenceSession.create('./model.onnx', {
  executionProviders: ['webgpu', 'wasm'],  // GPU with CPU fallback
});

const feeds = { input: new ort.Tensor('float32', inputData, [1, 3, 224, 224]) };
const results = await session.run(feeds);
```

```js
// Transformers.js with WebGPU
import { pipeline } from '@huggingface/transformers';

const classifier = await pipeline('text-classification', 'Xenova/distilbert-base-uncased-finetuned-sst-2-english', {
  device: 'webgpu',
});
const result = await classifier('I love this!');
```

> 📖 See `references/webgpu-webnn-webassembly.md` for render pipeline patterns, texture formats, and performance profiling.

---

## 4. WebNN (Web Neural Network API)

WebNN abstracts ML hardware (CPU/GPU/NPU) through a unified graph-based API. In Chrome 146+ origin trial.

```js
// Feature detection
if (!('ml' in navigator)) {
  console.warn('WebNN not supported — fallback to ONNX/WebGPU');
}

// Create context (routes to best available hardware)
const context = await navigator.ml.createContext({ deviceType: 'gpu' });
// deviceType options: 'cpu' | 'gpu' | 'npu'

const builder = new MLGraphBuilder(context);

// Define graph (example: matmul + relu)
const inputDesc = { dataType: 'float32', dimensions: [1, 784] };
const weightsData = new Float32Array(784 * 128); // pre-loaded weights
const biasData = new Float32Array(128);

const input = builder.input('input', inputDesc);
const weights = builder.constant({ dataType: 'float32', dimensions: [784, 128] }, weightsData);
const bias = builder.constant({ dataType: 'float32', dimensions: [128] }, biasData);
const matmul = builder.matmul(input, weights);
const biased = builder.add(matmul, bias);
const output = builder.relu(biased);

const graph = await builder.build({ output });

// Run inference
const inputTensor = new Float32Array(784);
const outputTensor = new Float32Array(128);
await context.compute(graph, { input: inputTensor }, { output: outputTensor });
```

**Hardware routing:** Windows uses DirectML, macOS uses Core ML, Linux uses vendor drivers.
Always feature-detect and degrade to WebGPU or Wasm.

> 📖 See `references/webgpu-webnn-webassembly.md` for complete MLGraphBuilder ops reference.

---

## 5. Chrome Built-in AI (Gemini Nano)

Available on Chrome 138+ desktop (Windows 10/11, macOS 13+, Linux). Requires 22GB free storage,
4GB+ VRAM or 16GB RAM.

### Availability Check (always do this first)

```js
const status = await LanguageModel.availability();
// Returns: 'available' | 'downloadable' | 'downloading' | 'unavailable'

if (status === 'unavailable') {
  // Fallback to cloud API or ONNX/WebGPU
}
if (status === 'downloadable') {
  // Trigger download, show progress UI
  const session = await LanguageModel.create({
    monitor(m) { m.addEventListener('downloadprogress', e => {
      console.log(`${Math.round(e.loaded / e.total * 100)}%`);
    }); }
  });
}
```

### Prompt API

```js
const session = await LanguageModel.create({
  systemPrompt: 'You are a helpful assistant that responds concisely.',
  temperature: 0.7,
  topK: 40,
});

// Check context window before sending
const tokenCount = await session.countPromptTokens(userInput);
if (tokenCount > session.tokensLeft) {
  // Chunk or summarize input
}

// Streaming response
const stream = session.promptStreaming(userInput);
for await (const chunk of stream) {
  outputElement.textContent += chunk;
}

// Always clean up
session.destroy();
```

### Specialized APIs

```js
// Summarizer
const summarizer = await Summarizer.create({ type: 'key-points', length: 'short' });
const summary = await summarizer.summarize(longText);

// Translator
const translator = await Translator.create({ sourceLanguage: 'en', targetLanguage: 'es' });
const translated = await translator.translate(text);

// Writer
const writer = await Writer.create({ tone: 'professional', length: 'medium' });
const draft = await writer.write('Write a product announcement for...', { context: 'B2B SaaS' });

// Rewriter
const rewriter = await Rewriter.create({ tone: 'casual' });
const rewritten = await rewriter.rewrite(formalText);

// Language Detector
const detector = await LanguageDetector.create();
const results = await detector.detect(text);
// results[0].detectedLanguage, results[0].confidence
```

### Using Built-in AI in Extensions

```js
// In extension service worker or content script
// Note: Must register for origin trial in manifest if not in stable
const session = await LanguageModel.create({
  systemPrompt: 'Extract structured data from web pages as JSON.'
});

// Multimodal (image input) — available in Prompt API
const imageBlob = await fetch(imageUrl).then(r => r.blob());
const response = await session.prompt([
  { role: 'user', content: [
    { type: 'text', text: 'Describe this image:' },
    { type: 'image', image: imageBlob }
  ]}
]);
```

> 📖 See `references/chrome-builtin-ai.md` for full API surface, graceful degradation patterns,
> and hybrid cloud+local strategies.

---

## 6. Local ML Model Inference — Framework Guide

### Framework Selection Matrix

| Framework | Best For | Backend | Bundle Size |
|-----------|----------|---------|-------------|
| **Transformers.js** | NLP, vision, audio (HF models) | WebGPU/Wasm | ~2MB + model |
| **ONNX Runtime Web** | Any ONNX model, production | WebGPU/Wasm | ~5MB + model |
| **WebLLM** | Full LLM chat (Llama, Mistral) | WebGPU | ~10MB + model |
| **TensorFlow.js** | TF models, transfer learning | WebGPU/Wasm | ~3MB + model |
| **MediaPipe** | Vision tasks, hand/face tracking | Wasm/WebGL | ~1MB + model |

### Model Loading Strategies

```js
// Cache models in Cache API for offline use
import { pipeline } from '@huggingface/transformers';

// Custom cache config
const model = await pipeline('text-classification', 'Xenova/bert-base-uncased', {
  device: 'webgpu',
  cache_dir: '/models/',  // Service Worker caches this
  progress_callback: (progress) => {
    console.log(`Loading: ${Math.round(progress.progress)}%`);
  }
});

// Service Worker caching of WASM/model files
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/models/')) {
    event.respondWith(caches.match(event.request).then(cached => 
      cached || fetch(event.request).then(response => {
        const clone = response.clone();
        caches.open('ml-models-v1').then(c => c.put(event.request, clone));
        return response;
      })
    ));
  }
});
```

---

## 7. Performance & Debugging

### Chrome DevTools for Advanced APIs

```
chrome://gpu                    — GPU info, WebGPU/WebGL status
chrome://flags                  — Enable experimental APIs
chrome://on-device-internals    — Gemini Nano model status
chrome://tracing                — Deep performance profiling
Shift+Esc                       — Task Manager (per-tab GPU/memory)
DevTools → Application → IndexedDB   — Browse IDB stores, clear data
DevTools → Application → Cache Storage — Inspect cached model shards
```

### WebGPU Performance Profiling

```js
// Use render bundles for repeated draw calls (up to 10x faster)
const bundle = device.createRenderBundle(descriptor);
renderPass.executeBundles([bundle]);

// GPU timing queries
const querySet = device.createQuerySet({ type: 'timestamp', count: 2 });
// ... record timestamps in command encoder
```

### Extension Debugging

```
chrome://extensions/           — Load unpacked, inspect service worker
DevTools → Application → Service Workers
Background page console: inspect service worker directly
```

---

## 8. IndexedDB — Multi-Paradigm Browser Database

IndexedDB is the primary persistent storage for web apps and extensions. It supports storing
arbitrary JS values (including typed arrays for vectors), indexes for fast querying, and
transactions for atomicity. Quota is large (often GB-scale, bounded by disk).

### Core API Patterns

```js
// Open/upgrade database
function openDB(name, version, upgradeCallback) {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(name, version);
    req.onupgradeneeded = (e) => upgradeCallback(e.target.result);
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = (e) => reject(e.target.error);
  });
}

// Promisified helper (or use the `idb` npm package — recommended)
const idbPut = (db, storeName, value, key) =>
  new Promise((res, rej) => {
    const tx = db.transaction(storeName, 'readwrite');
    const req = tx.objectStore(storeName).put(value, key);
    req.onsuccess = () => res(req.result);
    req.onerror = () => rej(req.error);
  });
```

**Always prefer the `idb` wrapper library** (`npm install idb`) — it wraps the callback API in clean promises and avoids common pitfalls.

### IDB as NoSQL Document Store

```js
import { openDB } from 'idb';

const db = await openDB('my-app', 1, {
  upgrade(db) {
    const store = db.createObjectStore('docs', { keyPath: 'id', autoIncrement: true });
    store.createIndex('by-type', 'type');          // query by type
    store.createIndex('by-created', 'createdAt');  // query by date
    store.createIndex('by-tag', 'tags', { multiEntry: true }); // array index
  }
});

// CRUD
await db.put('docs', { type: 'note', title: 'Hello', tags: ['work', 'ai'], createdAt: Date.now() });
const all = await db.getAll('docs');
const notes = await db.getAllFromIndex('docs', 'by-type', 'note');
const recent = await db.getAllFromIndex('docs', 'by-created', IDBKeyRange.lowerBound(Date.now() - 86400000));
```

### IDB as SQL-style Relational Store

IndexedDB is key-value + indexes, so SQL JOIN patterns require manual implementation:

```js
// Schema: users + posts (one-to-many)
const db = await openDB('relational-demo', 1, {
  upgrade(db) {
    db.createObjectStore('users', { keyPath: 'id' });
    const posts = db.createObjectStore('posts', { keyPath: 'id', autoIncrement: true });
    posts.createIndex('by-user', 'userId');        // FK index
    posts.createIndex('by-user-date', ['userId', 'createdAt']); // compound index
  }
});

// JOIN: get all posts by a user (equivalent to SELECT * FROM posts WHERE userId = ?)
async function getPostsByUser(userId) {
  return db.getAllFromIndex('posts', 'by-user', userId);
}

// Range query (equivalent to WHERE createdAt BETWEEN ? AND ?)
async function getPostsInRange(userId, from, to) {
  const range = IDBKeyRange.bound([userId, from], [userId, to]);
  return db.getAllFromIndex('posts', 'by-user-date', range);
}

// Transaction across stores (equivalent to BEGIN; INSERT ...; INSERT ...; COMMIT)
async function createUserWithPost(user, post) {
  const tx = db.transaction(['users', 'posts'], 'readwrite');
  await tx.objectStore('users').put(user);
  await tx.objectStore('posts').put({ ...post, userId: user.id });
  await tx.done;
}

// Aggregation (COUNT, SUM) — no built-in SQL, iterate with cursor
async function countPostsByUser() {
  const counts = {};
  let cursor = await db.transaction('posts').store.index('by-user').openCursor();
  while (cursor) {
    counts[cursor.key] = (counts[cursor.key] || 0) + 1;
    cursor = await cursor.continue();
  }
  return counts;
}
```

### IDB as Vector Database (Semantic Search / RAG)

Store embeddings as `Float32Array` alongside documents. Cosine similarity computed in JS (or via WASM/WebGPU for scale).

```js
const db = await openDB('vector-store', 1, {
  upgrade(db) {
    const store = db.createObjectStore('vectors', { keyPath: 'id', autoIncrement: true });
    store.createIndex('by-collection', 'collection');
  }
});

// Insert document + pre-computed embedding
async function insertVector(collection, text, embedding, metadata = {}) {
  return db.add('vectors', {
    collection,
    text,
    embedding: Array.from(embedding), // store as plain array (IDB serializes Float32Array)
    metadata,
    createdAt: Date.now()
  });
}

// Cosine similarity
function cosineSimilarity(a, b) {
  let dot = 0, normA = 0, normB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dot / (Math.sqrt(normA) * Math.sqrt(normB));
}

// Similarity search — brute force (fine up to ~100K vectors)
async function similaritySearch(queryEmbedding, collection, topK = 5) {
  const all = await db.getAllFromIndex('vectors', 'by-collection', collection);
  const scored = all.map(doc => ({
    ...doc,
    score: cosineSimilarity(queryEmbedding, doc.embedding)
  }));
  return scored
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

// Full RAG pipeline: embed query → search → inject into LLM prompt
async function ragQuery(userQuestion, model, llmSession) {
  const queryEmbedding = await generateEmbedding(model, userQuestion);
  const hits = await similaritySearch(queryEmbedding, 'knowledge', 3);
  const context = hits.map(h => h.text).join('\n\n');
  return llmSession.prompt(`Context:\n${context}\n\nQuestion: ${userQuestion}`);
}
```

### IDB as Graph Database

Model graphs as nodes + edges stores. Traverse with BFS/DFS using cursor-based lookups.

```js
const db = await openDB('graph-store', 1, {
  upgrade(db) {
    db.createObjectStore('nodes', { keyPath: 'id' });
    const edges = db.createObjectStore('edges', { keyPath: 'id', autoIncrement: true });
    edges.createIndex('by-from', 'from');
    edges.createIndex('by-to', 'to');
    edges.createIndex('by-type', 'type');
  }
});

// Add nodes and edges
const addNode = (id, data) => db.put('nodes', { id, ...data });
const addEdge = (from, to, type, data = {}) =>
  db.add('edges', { from, to, type, ...data });

// Get neighbors (1-hop)
async function getNeighbors(nodeId, direction = 'out') {
  const index = direction === 'out' ? 'by-from' : 'by-to';
  const key = direction === 'out' ? 'to' : 'from';
  const edges = await db.getAllFromIndex('edges', index, nodeId);
  return Promise.all(edges.map(e => db.get('nodes', e[key])));
}

// BFS traversal
async function bfs(startId, maxDepth = 3) {
  const visited = new Set([startId]);
  const queue = [{ id: startId, depth: 0 }];
  const result = [];
  while (queue.length) {
    const { id, depth } = queue.shift();
    const node = await db.get('nodes', id);
    result.push({ ...node, depth });
    if (depth < maxDepth) {
      const neighbors = await getNeighbors(id, 'out');
      for (const n of neighbors) {
        if (n && !visited.has(n.id)) {
          visited.add(n.id);
          queue.push({ id: n.id, depth: depth + 1 });
        }
      }
    }
  }
  return result;
}

// Shortest path (Dijkstra)
async function shortestPath(startId, endId) {
  const dist = { [startId]: 0 };
  const prev = {};
  const queue = [startId];
  while (queue.length) {
    const current = queue.shift();
    if (current === endId) break;
    const edges = await db.getAllFromIndex('edges', 'by-from', current);
    for (const edge of edges) {
      const weight = edge.weight ?? 1;
      const newDist = dist[current] + weight;
      if (newDist < (dist[edge.to] ?? Infinity)) {
        dist[edge.to] = newDist;
        prev[edge.to] = current;
        queue.push(edge.to);
      }
    }
  }
  // Reconstruct path
  const path = [];
  let cur = endId;
  while (cur) { path.unshift(cur); cur = prev[cur]; }
  return { path, distance: dist[endId] };
}
```

### IDB for ML Model Caching

Transformers.js and WebLLM automatically cache model shards in Cache API / IDB.
For manual model caching (e.g., custom ONNX files):

```js
// Store model binary in IDB (survives service worker restarts)
async function cacheModel(modelId, arrayBuffer) {
  const db = await openDB('model-cache', 1, {
    upgrade(db) { db.createObjectStore('models'); }
  });
  await db.put('models', arrayBuffer, modelId);
  console.log(`Cached ${(arrayBuffer.byteLength / 1e6).toFixed(1)}MB model: ${modelId}`);
}

async function loadCachedModel(modelId) {
  const db = await openDB('model-cache', 1);
  return db.get('models', modelId); // returns ArrayBuffer or undefined
}

// Check if model is cached before downloading
async function getOrFetchModel(modelId, remoteUrl) {
  const cached = await loadCachedModel(modelId);
  if (cached) { console.log('Model loaded from IDB cache'); return cached; }

  console.log('Downloading model...');
  const resp = await fetch(remoteUrl);
  const buf = await resp.arrayBuffer();
  await cacheModel(modelId, buf);
  return buf;
}
```

> 📖 See `references/indexeddb-advanced.md` for full IDB API, quota management, migration patterns, worker usage, and PGlite (full PostgreSQL in-browser) integration.

---

## 9. HuggingFace Models + WebGPU — Download & Run

When Chrome Built-in AI (Gemini Nano) is unavailable, download and run open models directly
via Transformers.js v3 (ONNX-based) or WebLLM (MLC-compiled). Both cache to IndexedDB/Cache API
after first download.

### Model Selection Guide

| Model | VRAM (q4f16) | Use Case | Transformers.js ID |
|-------|-------------|----------|-------------------|
| **SmolLM2-135M** | ~0.1GB | Ultra-light classification/chat | `HuggingFaceTB/SmolLM2-135M-Instruct` |
| **SmolLM2-360M** | ~0.3GB | Fast on-device chat | `HuggingFaceTB/SmolLM2-360M-Instruct` |
| **Qwen3-0.6B** | ~0.5GB | Reasoning, tool use, multilingual | `onnx-community/Qwen3-0.6B-ONNX` |
| **SmolLM2-1.7B** | ~1GB | Good balance quality/size | `HuggingFaceTB/SmolLM2-1.7B-Instruct` |
| **Qwen3-1.7B** | ~1.2GB | Coding, reasoning | `onnx-community/Qwen3-1.7B-ONNX` |
| **Phi-4-mini (3.8B)** | ~2.5GB | Strong reasoning, STEM | `onnx-community/Phi-4-mini-instruct-ONNX` |
| **Qwen3-4B** | ~2.8GB | Best quality <5GB VRAM | `onnx-community/Qwen3-4B-ONNX` |
| **Llama-3.2-3B** | ~2GB | General chat | `onnx-community/Llama-3.2-3B-Instruct-ONNX` |
| **Gemma-3-4B** | ~2.7GB | Multilingual, vision | via WebLLM |
| **Qwen3-8B** | ~5.5GB | Near-GPT-4 quality tasks | via WebLLM |

**Rule of thumb:** `q4f16` = 4-bit weights + fp16 activations. Fits in ~0.6 × param_count GB. For a 4B model: ~2.4–3GB VRAM. Always prefer `q4f16` over `q4` on WebGPU for better accuracy.

### Transformers.js v3 — Download & Run with WebGPU

```js
import { pipeline, env, TextStreamer } from '@huggingface/transformers';

// Configuration
env.allowRemoteModels = true;
env.useBrowserCache = true;        // caches to Cache API (persists across sessions)
env.backends.onnx.wasm.proxy = false;

// Load a Qwen3 4B model on WebGPU
const generator = await pipeline(
  'text-generation',
  'onnx-community/Qwen3-4B-ONNX',
  {
    device: 'webgpu',
    dtype: 'q4f16',               // recommended for WebGPU — 4-bit weights, fp16 activations
    // dtype: 'q4' if GPU memory is tight; 'fp16' for maximum quality
    progress_callback(p) {
      if (p.status === 'downloading') {
        const pct = Math.round(p.progress ?? 0);
        console.log(`Downloading ${p.file}: ${pct}%`);
        updateProgressUI(pct, p.file);
      }
    }
  }
);

// Chat-style generation with streaming
const messages = [
  { role: 'system', content: 'You are a helpful assistant.' },
  { role: 'user', content: 'Explain WebGPU in 2 sentences.' }
];

const streamer = new TextStreamer(generator.tokenizer, {
  skip_prompt: true,
  callback_function: (token) => outputEl.textContent += token,
});

const output = await generator(messages, {
  max_new_tokens: 512,
  do_sample: false,
  streamer,
});
```

### Run in a Web Worker (keeps UI responsive)

**Always run model inference in a Worker** — it prevents UI freezes during loading and inference.

```js
// worker.js
import { pipeline, TextStreamer } from '@huggingface/transformers';

let generator = null;

self.onmessage = async ({ data }) => {
  if (data.type === 'load') {
    generator = await pipeline('text-generation', data.modelId, {
      device: 'webgpu',
      dtype: 'q4f16',
      progress_callback: (p) => self.postMessage({ type: 'progress', progress: p }),
    });
    self.postMessage({ type: 'ready' });
  }

  if (data.type === 'generate') {
    const streamer = new TextStreamer(generator.tokenizer, {
      skip_prompt: true,
      callback_function: (token) => self.postMessage({ type: 'token', token }),
    });
    const result = await generator(data.messages, {
      max_new_tokens: data.maxTokens ?? 512,
      streamer,
    });
    self.postMessage({ type: 'done', result });
  }
};

// main.js
const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });

worker.postMessage({ type: 'load', modelId: 'onnx-community/Qwen3-4B-ONNX' });
worker.onmessage = ({ data }) => {
  if (data.type === 'progress') updateUI(data.progress);
  if (data.type === 'ready') enableChatInput();
  if (data.type === 'token') appendToken(data.token);
};
```

### WebLLM — Larger Models (Qwen3-8B+)

WebLLM is better for larger models (3B+). It uses MLC-compiled WebGPU kernels with
FlashAttention and PagedAttention for efficient KV cache management.

```js
import { CreateMLCEngine } from '@mlc-ai/web-llm';

// Current best models for browser (as of 2026)
const WEBLLM_MODELS = {
  fast_small:   'SmolLM2-1.7B-Instruct-q4f16_1-MLC',   // 1GB, very fast
  balanced:     'Qwen3-4B-Instruct-q4f16_1-MLC',         // 3GB, great quality
  quality:      'Qwen3-8B-Instruct-q4f16_1-MLC',         // 6GB, near-cloud quality
  reasoning:    'Phi-4-mini-instruct-q4f16_1-MLC',        // 2.5GB, strong reasoning
  coding:       'Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC', // 5GB, best browser coder
};

const engine = await CreateMLCEngine(WEBLLM_MODELS.balanced, {
  initProgressCallback: ({ progress, text }) => {
    console.log(`[${Math.round(progress * 100)}%] ${text}`);
    updateLoadingUI(progress);
  },
});

// OpenAI-compatible API
const response = await engine.chat.completions.create({
  messages: [
    { role: 'system', content: 'You are a coding assistant.' },
    { role: 'user', content: 'Write a binary search in JavaScript.' }
  ],
  temperature: 0.7,
  max_tokens: 1024,
  stream: true,
});

for await (const chunk of response) {
  const delta = chunk.choices[0]?.delta?.content || '';
  outputEl.textContent += delta;
}

// Structured JSON output
const jsonResponse = await engine.chat.completions.create({
  messages: [{ role: 'user', content: 'List 3 fruits as JSON array' }],
  response_format: { type: 'json_object' },
});
const data = JSON.parse(jsonResponse.choices[0].message.content);
```

### Model Download + Cache Strategy

Models are large (0.5–6GB). Always handle caching properly:

```js
// Transformers.js caches to Cache API automatically (checkable in DevTools → Cache Storage)
// WebLLM caches to Cache API under key: webllm/<model-id>/

// Check if model is already cached
async function isModelCached(modelId) {
  const cacheName = `webllm/${modelId}`;
  const cache = await caches.open(cacheName);
  const keys = await cache.keys();
  return keys.length > 0;
}

// Estimate VRAM before loading
function estimateVRAM(paramBillions, dtype = 'q4f16') {
  const multipliers = { 'fp32': 4, 'fp16': 2, 'q8': 1, 'q4f16': 0.6, 'q4': 0.5 };
  return paramBillions * (multipliers[dtype] ?? 1); // GB
}

// Check GPU memory before loading
async function canRunModel(paramBillions, dtype = 'q4f16') {
  const adapter = await navigator.gpu?.requestAdapter();
  if (!adapter) return false;
  const needed = estimateVRAM(paramBillions, dtype) * 1e9;
  // adapter.limits.maxBufferSize is a proxy for available GPU memory
  return adapter.limits.maxBufferSize >= needed * 0.8;
}

// Smart model selection based on available hardware
async function selectBestModel() {
  const adapter = await navigator.gpu?.requestAdapter();
  if (!adapter) return null; // No WebGPU

  const maxBuf = adapter.limits.maxBufferSize / 1e9; // GB

  if (maxBuf >= 6) return 'onnx-community/Qwen3-8B-ONNX';
  if (maxBuf >= 3) return 'onnx-community/Qwen3-4B-ONNX';
  if (maxBuf >= 1.5) return 'onnx-community/Qwen3-1.7B-ONNX';
  return 'onnx-community/Qwen3-0.6B-ONNX';
}
```

### Embedding Models (for RAG / Vector Search)

```js
// Small, fast embedding models (pair with IDB vector store above)
const embedder = await pipeline(
  'feature-extraction',
  'Xenova/all-MiniLM-L6-v2',     // 384-dim, 22MB, excellent quality/size ratio
  // alternatives:
  // 'Xenova/bge-small-en-v1.5'  — 384-dim, better retrieval
  // 'Xenova/bge-m3'             — 1024-dim, multilingual
  // 'Xenova/nomic-embed-text-v1' — 768-dim, long context
  { device: 'webgpu', dtype: 'fp16' }
);

async function generateEmbedding(text) {
  const output = await embedder(text, { pooling: 'mean', normalize: true });
  return output.data; // Float32Array
}

// Batch embeddings (more efficient than one-at-a-time)
async function batchEmbed(texts, batchSize = 32) {
  const embeddings = [];
  for (let i = 0; i < texts.length; i += batchSize) {
    const batch = texts.slice(i, i + batchSize);
    const outputs = await embedder(batch, { pooling: 'mean', normalize: true });
    embeddings.push(...outputs.map(o => o.data));
  }
  return embeddings;
}
```

### Converting Custom HuggingFace Models to ONNX

```bash
# Convert any HF model to ONNX + quantize for browser use
pip install optimum[exporters] transformers

# Basic conversion
python -m optimum.exporters.onnx --model Qwen/Qwen3-4B ./qwen3-4b-onnx/

# With quantization (q4 = 4-bit)
python -m optimum.exporters.onnx \
  --model Qwen/Qwen3-4B \
  --task text-generation-with-past \
  --fp16 \
  --optimize O2 \
  ./qwen3-4b-onnx/

# Upload to HuggingFace Hub with transformers.js tag for browser use
huggingface-cli upload your-username/Qwen3-4B-ONNX ./qwen3-4b-onnx/
```

> 📖 See `references/hf-webgpu-models.md` for complete model catalog, quantization guide,
> Worker patterns, IndexedDB caching integration, and RAG pipeline examples.

---

## Reference Files

Read these for deeper detail:

- **`references/chrome-extensions-mv3.md`** — Complete MV3 API reference, permissions guide, 
  content security policy, storage comparison, native messaging, testing patterns, Chrome Web Store publishing

- **`references/webgpu-webnn-webassembly.md`** — WebGPU render pipelines, WGSL language reference,
  WebNN ops catalog, Wasm 3.0 feature flags, Emscripten build recipes, interop patterns

- **`references/chrome-builtin-ai.md`** — Full Gemini Nano API surface, graceful degradation strategies,
  hybrid cloud/local patterns, privacy considerations, token management, all built-in AI API examples

- **`references/indexeddb-advanced.md`** — Complete IDB API, quota/migration, idb library, cursor patterns,
  compound indexes, PGlite (PostgreSQL in-browser), HNSW approximate nearest-neighbor indexing

- **`references/hf-webgpu-models.md`** — HuggingFace model catalog for browsers, dtype/quantization guide,
  Transformers.js v3 & WebLLM advanced configuration, RAG pipelines, ONNX conversion recipes

## Scripts

- **`scripts/extension-boilerplate/`** — Complete MV3 extension template with service worker,
  offscreen document, content script, and popup

- **`scripts/webgpu-compute-demo.js`** — Runnable WebGPU compute shader for tensor operations
  with feature detection and fallbacks

- **`scripts/local-inference-demo.js`** — Multi-backend ML inference with Built-in AI + Transformers.js +
  ONNX Runtime Web + WebLLM graceful degradation chain

- **`scripts/indexeddb-patterns.js`** — Full IDB pattern library: NoSQL store, SQL-style relational
  patterns, vector similarity search, graph BFS/Dijkstra, model caching

- **`scripts/hf-webgpu-inference.js`** — Complete HuggingFace + WebGPU pipeline: smart model selection,
  Worker-based inference, streaming generation, RAG with IDB vector store

