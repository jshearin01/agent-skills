# HuggingFace Models + WebGPU — Complete Reference

## Table of Contents
1. [Model Catalog for Browser Inference](#1-model-catalog-for-browser-inference)
2. [Quantization & dtype Guide](#2-quantization--dtype-guide)
3. [Transformers.js v3 — Full API](#3-transformersjs-v3--full-api)
4. [WebLLM — Large Model Inference](#4-webllm--large-model-inference)
5. [Worker Patterns](#5-worker-patterns)
6. [Model Caching Architecture](#6-model-caching-architecture)
7. [RAG Pipeline with IDB](#7-rag-pipeline-with-idb)
8. [ONNX Conversion from HuggingFace](#8-onnx-conversion-from-huggingface)
9. [Performance Benchmarks & Tips](#9-performance-benchmarks--tips)
10. [Multimodal Models](#10-multimodal-models)

---

## 1. Model Catalog for Browser Inference

### LLM Chat / Instruction Models (Transformers.js + WebGPU)

| Model | Size | VRAM (q4f16) | Quality | Speed | HF ID |
|-------|------|-------------|---------|-------|-------|
| SmolLM2-135M | 135M | ~150MB | ⭐⭐ | ⚡⚡⚡⚡ | `HuggingFaceTB/SmolLM2-135M-Instruct` |
| SmolLM2-360M | 360M | ~300MB | ⭐⭐⭐ | ⚡⚡⚡⚡ | `HuggingFaceTB/SmolLM2-360M-Instruct` |
| **Qwen3-0.6B** | 0.6B | ~500MB | ⭐⭐⭐ | ⚡⚡⚡⚡ | `onnx-community/Qwen3-0.6B-ONNX` |
| SmolLM2-1.7B | 1.7B | ~1GB | ⭐⭐⭐⭐ | ⚡⚡⚡ | `HuggingFaceTB/SmolLM2-1.7B-Instruct` |
| **Qwen3-1.7B** | 1.7B | ~1.2GB | ⭐⭐⭐⭐ | ⚡⚡⚡ | `onnx-community/Qwen3-1.7B-ONNX` |
| Llama-3.2-1B | 1B | ~700MB | ⭐⭐⭐ | ⚡⚡⚡ | `onnx-community/Llama-3.2-1B-Instruct-ONNX` |
| Llama-3.2-3B | 3B | ~2GB | ⭐⭐⭐⭐ | ⚡⚡⚡ | `onnx-community/Llama-3.2-3B-Instruct-ONNX` |
| **Phi-4-mini** | 3.8B | ~2.5GB | ⭐⭐⭐⭐⭐ | ⚡⚡ | `onnx-community/Phi-4-mini-instruct-ONNX` |
| **Qwen3-4B** | 4B | ~2.8GB | ⭐⭐⭐⭐⭐ | ⚡⚡ | `onnx-community/Qwen3-4B-ONNX` |

### LLM Chat Models (WebLLM — MLC compiled, larger models)

| Model | VRAM | Quality | WebLLM Model ID |
|-------|------|---------|-----------------|
| SmolLM2-1.7B | ~1GB | ⭐⭐⭐ | `SmolLM2-1.7B-Instruct-q4f16_1-MLC` |
| **Qwen3-4B** | ~3GB | ⭐⭐⭐⭐⭐ | `Qwen3-4B-Instruct-q4f16_1-MLC` |
| Llama-3.2-3B | ~2GB | ⭐⭐⭐⭐ | `Llama-3.2-3B-Instruct-q4f16_1-MLC` |
| Phi-4-mini | ~2.5GB | ⭐⭐⭐⭐⭐ | `Phi-4-mini-instruct-q4f16_1-MLC` |
| **Qwen3-8B** | ~5.5GB | ⭐⭐⭐⭐⭐ | `Qwen3-8B-Instruct-q4f16_1-MLC` |
| Gemma-3-4B | ~2.7GB | ⭐⭐⭐⭐ | `gemma-3-4b-it-q4f16_1-MLC` |
| Qwen2.5-Coder-7B | ~5GB | ⭐⭐⭐⭐⭐ | `Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC` |
| Mistral-7B | ~5GB | ⭐⭐⭐⭐ | `Mistral-7B-Instruct-v0.3-q4f16_1-MLC` |

**Recommended picks (2026):**
- **Best quality <3GB VRAM:** `Phi-4-mini` or `Qwen3-4B` (both excellent)
- **Best speed <1GB VRAM:** `SmolLM2-1.7B` or `Qwen3-0.6B`
- **Best coding:** `Qwen2.5-Coder-7B` (6GB VRAM needed)
- **Best reasoning (thinking mode):** `Qwen3-4B` (enable thinking with `/think` prefix)

### Embedding Models (for vector search / RAG)

| Model | Dims | Size | Speed | Use Case |
|-------|------|------|-------|----------|
| `Xenova/all-MiniLM-L6-v2` | 384 | 22MB | ⚡⚡⚡ | General semantic search |
| `Xenova/bge-small-en-v1.5` | 384 | 33MB | ⚡⚡⚡ | Best small English retrieval |
| `Xenova/bge-m3` | 1024 | 570MB | ⚡⚡ | Multilingual, long context |
| `Xenova/nomic-embed-text-v1` | 768 | 137MB | ⚡⚡ | Long documents (8K context) |
| `Xenova/jina-embeddings-v2-base-en` | 768 | 136MB | ⚡⚡ | Long context (8K), strong quality |

### Vision Models

| Model | Task | Size | HF ID |
|-------|------|------|-------|
| `onnx-community/Florence-2-base-ft` | Image captioning, detection | 230MB | see HF |
| `Xenova/clip-vit-base-patch32` | Image embedding / CLIP | 150MB | see HF |
| `onnx-community/moondream2` | Visual Q&A | 450MB | see HF |
| `onnx-community/Qwen2-VL-2B-Instruct` | Multimodal chat | 2GB | see HF |

---

## 2. Quantization & dtype Guide

### dtype Options in Transformers.js v3

| dtype | Description | VRAM | Quality | Recommended For |
|-------|-------------|------|---------|-----------------|
| `fp32` | Full precision | 4× | Highest | Embedding models, small models |
| `fp16` | Half precision | 2× | High | Encoder models on WebGPU |
| `q8` | 8-bit quantization | 1× | Good | Default WASM fallback |
| `q4` | 4-bit quantization | 0.5× | OK | Low-memory situations |
| **`q4f16`** | 4-bit weights + fp16 activations | ~0.6× | Best tradeoff | **Recommended for LLMs on WebGPU** |
| `bnb4` | BitsAndBytes 4-bit | 0.5× | OK | Some models only |

### Per-Component dtype (Encoder-Decoder models)

For models like Whisper or Florence-2 with separate components:

```js
const model = await Florence2ForConditionalGeneration.from_pretrained(
  'onnx-community/Florence-2-base-ft',
  {
    dtype: {
      embed_tokens: 'fp16',    // embeddings: keep precision
      vision_encoder: 'fp16', // vision: keep precision
      encoder_model: 'q4',    // encoder body: quantize
      decoder_model_merged: 'q4', // decoder: quantize
    },
    device: 'webgpu',
  }
);
```

### VRAM Estimation Formula

```
VRAM (GB) ≈ param_count (B) × bytes_per_param × 1.1 (overhead)

bytes_per_param:
  fp32  → 4.0 bytes
  fp16  → 2.0 bytes
  q8    → 1.0 byte
  q4f16 → ~0.6 bytes (weights are 4-bit, activations fp16)
  q4    → ~0.5 bytes

Examples:
  Qwen3-4B q4f16  → 4 × 0.6 × 1.1 ≈ 2.6GB
  Qwen3-8B q4f16  → 8 × 0.6 × 1.1 ≈ 5.3GB
  Phi-4-mini q4f16 → 3.8 × 0.6 × 1.1 ≈ 2.5GB
```

---

## 3. Transformers.js v3 — Full API

### Pipeline API (Easiest)

```js
import { pipeline, env, TextStreamer } from '@huggingface/transformers';

// Global config
env.allowRemoteModels = true;
env.useBrowserCache = true;   // Cache API persistence
env.backends.onnx.wasm.proxy = false; // inline WASM, not shared worker

// Create pipeline
const pipe = await pipeline(task, modelId, {
  device: 'webgpu' | 'wasm' | 'cpu',
  dtype: 'q4f16' | 'q4' | 'fp16' | 'fp32' | 'q8',
  progress_callback: (p) => { /* { status, file, progress, loaded, total } */ }
});
```

### All Supported Tasks

```js
// NLP
pipeline('text-generation', ...)              // LLM, chat
pipeline('text2text-generation', ...)         // T5, BART
pipeline('feature-extraction', ...)          // embeddings
pipeline('text-classification', ...)         // sentiment, intent
pipeline('token-classification', ...)        // NER, POS tagging
pipeline('question-answering', ...)          // extractive QA
pipeline('summarization', ...)
pipeline('translation', ...)
pipeline('zero-shot-classification', ...)

// Vision
pipeline('image-classification', ...)
pipeline('object-detection', ...)
pipeline('image-segmentation', ...)
pipeline('depth-estimation', ...)
pipeline('image-to-text', ...)              // captioning

// Audio
pipeline('automatic-speech-recognition', ...) // Whisper
pipeline('audio-classification', ...)
pipeline('text-to-audio', ...)               // TTS
pipeline('zero-shot-audio-classification', ...)
```

### Low-Level API (More Control)

```js
import {
  AutoTokenizer, AutoModelForCausalLM,
  AutoProcessor, PreTrainedModel,
  TextStreamer, StoppingCriteria
} from '@huggingface/transformers';

// Load model and tokenizer separately
const tokenizer = await AutoTokenizer.from_pretrained('onnx-community/Qwen3-4B-ONNX');
const model = await AutoModelForCausalLM.from_pretrained('onnx-community/Qwen3-4B-ONNX', {
  device: 'webgpu',
  dtype: 'q4f16',
});

// Tokenize with chat template
const messages = [
  { role: 'system', content: 'You are helpful.' },
  { role: 'user', content: 'Hello!' }
];
const text = tokenizer.apply_chat_template(messages, { tokenize: false, add_generation_prompt: true });
const inputs = tokenizer(text, { return_tensors: 'pt' });

// Generate with streaming
const streamer = new TextStreamer(tokenizer, {
  skip_prompt: true,
  callback_function: (text) => process.stdout.write(text),
});

const output = await model.generate({
  ...inputs,
  max_new_tokens: 512,
  do_sample: true,
  temperature: 0.7,
  top_p: 0.9,
  streamer,
});

const decoded = tokenizer.decode(output[0], { skip_special_tokens: true });
```

### Qwen3 Thinking Mode

Qwen3 supports a "thinking" mode for deeper reasoning (uses more tokens):

```js
// Enable thinking mode by prepending /think or using the chat template
const messages = [
  { role: 'system', content: 'You are a helpful assistant. /think' },
  // or add <think> tokens manually:
  { role: 'user', content: 'Solve: if x^2 + 3x - 4 = 0, find x' }
];

// The model will generate <think>...</think> blocks before the answer
// Strip thinking from output if you only want the final answer:
function stripThinking(text) {
  return text.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
}
```

---

## 4. WebLLM — Large Model Inference

### Engine Setup with Web Worker

```js
// WebLLM in a Web Worker for non-blocking UI
// worker.js
import { MLCEngine } from '@mlc-ai/web-llm';

const engine = new MLCEngine();

self.onmessage = async ({ data }) => {
  switch (data.type) {
    case 'load':
      engine.setInitProgressCallback((report) => {
        self.postMessage({ type: 'progress', ...report });
      });
      await engine.reload(data.modelId, data.engineConfig);
      self.postMessage({ type: 'loaded' });
      break;

    case 'chat':
      const stream = await engine.chat.completions.create({
        messages: data.messages,
        stream: true,
        temperature: data.temperature ?? 0.7,
        max_tokens: data.maxTokens ?? 1024,
        response_format: data.responseFormat,
      });
      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content || '';
        if (content) self.postMessage({ type: 'chunk', content });
      }
      const stats = await engine.runtimeStatsText();
      self.postMessage({ type: 'done', stats });
      break;

    case 'embed':
      // WebLLM also supports embeddings for some models
      const embeddings = await engine.embeddings.create({ input: data.texts, model: data.model });
      self.postMessage({ type: 'embeddings', data: embeddings.data });
      break;

    case 'reset':
      await engine.resetChat();
      self.postMessage({ type: 'reset' });
      break;
  }
};
```

### WebLLM Structured JSON Output

```js
// Get guaranteed JSON output
const response = await engine.chat.completions.create({
  messages: [{
    role: 'user',
    content: 'Extract: name, email, and phone from: "Call John Smith at john@acme.com, 555-0100"'
  }],
  response_format: {
    type: 'json_object',
    schema: JSON.stringify({
      type: 'object',
      properties: {
        name: { type: 'string' },
        email: { type: 'string' },
        phone: { type: 'string' }
      },
      required: ['name', 'email', 'phone']
    })
  }
});
const extracted = JSON.parse(response.choices[0].message.content);
```

### WebLLM Custom Models

```js
import { CreateMLCEngine, prebuiltAppConfig } from '@mlc-ai/web-llm';

// Add a custom model not in the default list
const appConfig = {
  ...prebuiltAppConfig,
  model_list: [
    ...prebuiltAppConfig.model_list,
    {
      model: 'https://your-cdn.com/models/my-custom-model/',
      model_id: 'MyCustomModel-q4f16_1-MLC',
      model_lib: 'https://your-cdn.com/models/my-custom-model/model.wasm',
      low_resource_required: true,
      vram_required_MB: 2048,
    }
  ]
};

const engine = await CreateMLCEngine('MyCustomModel-q4f16_1-MLC', { appConfig });
```

---

## 5. Worker Patterns

### Singleton Worker Pattern

```js
// model-worker.js — reusable singleton pattern
class ModelWorker {
  static _instance = null;
  static _loading = null;
  _worker = null;
  _callbacks = new Map();
  _msgId = 0;

  static getInstance() {
    if (!ModelWorker._instance) {
      if (!ModelWorker._loading) {
        ModelWorker._loading = new Promise(async (resolve) => {
          const w = new ModelWorker();
          await w._init();
          ModelWorker._instance = w;
          resolve(w);
        });
      }
      return ModelWorker._loading;
    }
    return Promise.resolve(ModelWorker._instance);
  }

  async _init() {
    this._worker = new Worker(new URL('./inference.worker.js', import.meta.url), { type: 'module' });
    this._worker.onmessage = ({ data }) => {
      const cb = this._callbacks.get(data.id);
      if (cb) cb(data);
    };
  }

  request(type, payload) {
    const id = ++this._msgId;
    return new Promise((resolve) => {
      this._callbacks.set(id, (data) => {
        this._callbacks.delete(id);
        resolve(data);
      });
      this._worker.postMessage({ id, type, ...payload });
    });
  }
}

// Usage anywhere in app
const worker = await ModelWorker.getInstance();
const result = await worker.request('generate', { messages, maxTokens: 512 });
```

### Transferable Objects for Zero-Copy

```js
// Pass large Float32Array to worker without copying
const embedding = new Float32Array(384);

// Transfer ownership (zero-copy, but embedding is no longer usable in main thread)
worker.postMessage({ type: 'store', embedding }, [embedding.buffer]);

// Clone (slower but keeps original)
worker.postMessage({ type: 'store', embedding: embedding.slice() });
```

---

## 6. Model Caching Architecture

Transformers.js and WebLLM use Cache API (not IndexedDB) for model shards. This is intentional — Cache API handles large binary files better and integrates with Service Workers.

```js
// Inspect cached models
const caches_list = await caches.keys();
console.log('Cached items:', caches_list);

// Check if a specific model is cached
async function isModelCached(modelId) {
  const keys = await caches.keys();
  for (const key of keys) {
    if (key.includes(modelId)) return true;
  }
  const cache = await caches.open(`transformers-cache`);
  const match = await cache.match(`https://huggingface.co/${modelId}/resolve/main/config.json`);
  return !!match;
}

// Pre-fetch model in Service Worker (for offline PWA)
// sw.js
const MODEL_CACHE = 'ml-models-v1';
const MODELS_TO_PREFETCH = [
  // Pre-cache model manifest; actual weights are large and fetched on-demand
  'https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/config.json',
  'https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/tokenizer.json',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(MODEL_CACHE).then(c => c.addAll(MODELS_TO_PREFETCH)));
});

self.addEventListener('fetch', e => {
  if (e.request.url.includes('huggingface.co') && e.request.url.includes('.onnx')) {
    e.respondWith(
      caches.open(MODEL_CACHE).then(cache =>
        cache.match(e.request).then(cached =>
          cached || fetch(e.request).then(resp => {
            cache.put(e.request, resp.clone());
            return resp;
          })
        )
      )
    );
  }
});

// Force clear model cache (for updates)
async function clearModelCache() {
  const keys = await caches.keys();
  await Promise.all(keys.filter(k => k.startsWith('transformers-')).map(k => caches.delete(k)));
  await Promise.all(keys.filter(k => k.includes('webllm')).map(k => caches.delete(k)));
}

// Show download size before caching
async function estimateModelSize(modelId) {
  // Fetch config to determine model structure
  const config = await fetch(`https://huggingface.co/${modelId}/resolve/main/config.json`).then(r => r.json());
  // Rough estimate based on parameters
  const params = config.num_parameters ?? config.n_params;
  return params ? `~${(params * 0.6 / 1e9).toFixed(1)}GB (q4f16)` : 'unknown';
}
```

---

## 7. RAG Pipeline with IDB

Complete Retrieval-Augmented Generation with IndexedDB as the knowledge base:

```js
import { pipeline } from '@huggingface/transformers';
import { CreateMLCEngine } from '@mlc-ai/web-llm';
import { openDB } from 'idb';

class BrowserRAG {
  constructor() {
    this.embedder = null;
    this.llm = null;
    this.db = null;
  }

  async init({ embeddingModel = 'Xenova/all-MiniLM-L6-v2', llmModel = 'Qwen3-4B-Instruct-q4f16_1-MLC' } = {}) {
    // Init IDB
    this.db = await openDB('rag-knowledge', 1, {
      upgrade(db) {
        const s = db.createObjectStore('chunks', { keyPath: 'id', autoIncrement: true });
        s.createIndex('by-source', 'source');
        s.createIndex('by-collection', 'collection');
      }
    });

    // Load embedding model (small, fast)
    this.embedder = await pipeline('feature-extraction', embeddingModel, {
      device: 'webgpu', dtype: 'fp16'
    });

    // Load LLM
    this.llm = await CreateMLCEngine(llmModel, {
      initProgressCallback: (r) => console.log(`LLM: ${Math.round(r.progress * 100)}%`)
    });
  }

  // Chunk and index documents
  async ingest(text, source, collection = 'default', chunkSize = 512, overlap = 64) {
    const chunks = this._chunk(text, chunkSize, overlap);
    for (const chunk of chunks) {
      const embOutput = await this.embedder(chunk, { pooling: 'mean', normalize: true });
      const embedding = Array.from(embOutput.data);
      await this.db.add('chunks', { text: chunk, source, collection, embedding, createdAt: Date.now() });
    }
    console.log(`Indexed ${chunks.length} chunks from ${source}`);
  }

  // Retrieve relevant chunks
  async retrieve(query, collection = 'default', topK = 5) {
    const qOut = await this.embedder(query, { pooling: 'mean', normalize: true });
    const qVec = Array.from(qOut.data);

    const allChunks = await this.db.getAllFromIndex('chunks', 'by-collection', collection);
    const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
    const norm = (a) => Math.sqrt(a.reduce((s, v) => s + v * v, 0));

    return allChunks
      .map(c => ({ ...c, score: dot(qVec, c.embedding) / (norm(qVec) * norm(c.embedding)) }))
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }

  // Full RAG query
  async query(question, collection = 'default', { streaming = false } = {}) {
    const chunks = await this.retrieve(question, collection, 5);
    const context = chunks.map((c, i) => `[${i+1}] ${c.text}`).join('\n\n');

    const messages = [
      { role: 'system', content: 'Answer questions based solely on the provided context. If the context does not contain enough information, say so.' },
      { role: 'user', content: `Context:\n${context}\n\nQuestion: ${question}` }
    ];

    return this.llm.chat.completions.create({ messages, stream: streaming, max_tokens: 1024 });
  }

  _chunk(text, size = 512, overlap = 64) {
    const words = text.split(/\s+/);
    const chunks = [];
    for (let i = 0; i < words.length; i += size - overlap) {
      chunks.push(words.slice(i, i + size).join(' '));
      if (i + size >= words.length) break;
    }
    return chunks;
  }
}

// Usage
const rag = new BrowserRAG();
await rag.init();
await rag.ingest(longDocumentText, 'docs/manual.pdf');
const answer = await rag.query('How do I configure WebGPU?');
```

---

## 8. ONNX Conversion from HuggingFace

### Convert Any HF Model to Browser-Compatible ONNX

```bash
# Install dependencies
pip install optimum[exporters,onnxruntime] transformers torch

# Basic conversion (generates fp32 + q8 quantized)
python -m optimum.exporters.onnx \
  --model Qwen/Qwen3-4B \
  --task text-generation-with-past \
  ./qwen3-4b-onnx/

# With fp16 + additional quantizations
python -m optimum.exporters.onnx \
  --model Qwen/Qwen3-4B \
  --task text-generation-with-past \
  --fp16 \
  --device cuda \
  ./qwen3-4b-onnx/

# Or use Optimum directly in Python
from optimum.exporters.onnx import main_export
main_export(
    model_name_or_path="Qwen/Qwen3-4B",
    output="./qwen3-4b-onnx/",
    task="text-generation-with-past",
    optimize="O2",
)
```

### JavaScript-Side Loading of Custom ONNX

```js
import { AutoTokenizer, AutoModelForCausalLM } from '@huggingface/transformers';

// Load from local file or custom URL (not HF Hub)
env.allowLocalModels = true;
env.localModelPath = '/models/';  // served from your static files

const tokenizer = await AutoTokenizer.from_pretrained('qwen3-4b-custom/');
const model = await AutoModelForCausalLM.from_pretrained('qwen3-4b-custom/', {
  device: 'webgpu',
  dtype: 'q4f16',
  // model_file_name: 'decoder_model_merged' // if non-standard filename
});
```

### Upload to HuggingFace Hub

```bash
# Install HF CLI
pip install huggingface_hub

# Login
huggingface-cli login

# Upload converted model
huggingface-cli upload your-username/Qwen3-4B-ONNX ./qwen3-4b-onnx/

# Add transformers.js tag (makes it discoverable)
# Go to HF model page → Edit model card → Add tags: transformers.js
```

---

## 9. Performance Benchmarks & Tips

### Typical Token Generation Speeds (2026)

| Model | Hardware | tokens/sec |
|-------|----------|------------|
| SmolLM2-1.7B q4f16 | RTX 3060 | ~80 t/s |
| Qwen3-4B q4f16 | RTX 3060 | ~40 t/s |
| Qwen3-4B q4f16 | M2 Pro (18GB) | ~35 t/s |
| Qwen3-8B q4f16 | RTX 3080 (10GB) | ~30 t/s |
| Phi-4-mini q4f16 | RTX 3060 | ~45 t/s |
| SmolLM2-360M fp16 | Any WebGPU | ~150+ t/s |

### Optimization Tips

```js
// 1. Always use Web Workers — prevents UI freezing
// 2. Reuse engine/pipeline across requests — model loading takes seconds
// 3. Use streaming — better perceived performance
// 4. Limit max_new_tokens — each token costs time
// 5. Use q4f16 not q4 on WebGPU — better quality, nearly same size
// 6. Prefill (KV cache) is faster than generation — keep system prompts short

// Measure prefill vs generation speed
const start = performance.now();
const reply = await engine.chat.completions.create({ messages, stream: false });
const total = performance.now() - start;
const stats = await engine.runtimeStatsText(); // includes prefill and decode tps
console.log(stats);
// e.g.: "prefill: 120 tokens/s, decode: 42 tokens/s"
```

---

## 10. Multimodal Models

### Vision + Text with Transformers.js

```js
import {
  Qwen2VLForConditionalGeneration,
  AutoProcessor,
  TextStreamer,
  RawImage,
} from '@huggingface/transformers';

const model_id = 'onnx-community/Qwen2-VL-2B-Instruct';

const processor = await AutoProcessor.from_pretrained(model_id);
const model = await Qwen2VLForConditionalGeneration.from_pretrained(model_id, {
  dtype: { embed_tokens: 'fp16', vision_encoder: 'fp16', decoder_model_merged: 'q4' },
  device: 'webgpu',
});

// Process image + question
const image = await RawImage.fromURL('https://example.com/photo.jpg');
const conversation = [
  { role: 'user', content: [
    { type: 'image' },
    { type: 'text', text: 'What is in this image?' }
  ]}
];

const text = processor.apply_chat_template(conversation, { add_generation_prompt: true });
const inputs = await processor(text, image, { padding: true });

const streamer = new TextStreamer(processor.tokenizer, { skip_prompt: true });
await model.generate({ ...inputs, max_new_tokens: 128, streamer });
```

### Audio Transcription with Whisper WebGPU

```js
import { pipeline } from '@huggingface/transformers';

const transcriber = await pipeline(
  'automatic-speech-recognition',
  'onnx-community/whisper-large-v3-turbo',
  {
    device: 'webgpu',
    dtype: { encoder_model: 'fp16', decoder_model_merged: 'q4' }, // q4 decoder for size
  }
);

// From File
const result = await transcriber(audioFile, {
  language: 'en',                   // or null for auto-detect
  task: 'transcribe',               // or 'translate' → English
  chunk_length_s: 30,               // chunk long audio
  stride_length_s: 5,               // overlap between chunks
  return_timestamps: 'word',        // word-level timestamps
});
console.log(result.text);
```
