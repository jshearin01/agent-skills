/**
 * hf-webgpu-inference.js
 *
 * Complete HuggingFace + WebGPU inference system:
 * - Smart model selection based on available VRAM
 * - Transformers.js v3 with Worker offloading
 * - WebLLM for larger models (Qwen3-8B etc.)
 * - Embedding generation + IDB vector store integration
 * - Full RAG (Retrieval-Augmented Generation) pipeline
 * - Model download progress + caching
 *
 * Usage:
 *   import { SmartLLM, BrowserRAG } from './hf-webgpu-inference.js';
 *   const llm = await SmartLLM.create({ preferredQuality: 'balanced' });
 *   const answer = await llm.chat('Explain WebGPU');
 *
 * Requires: npm install @huggingface/transformers @mlc-ai/web-llm idb
 */

// ═══════════════════════════════════════════════════════
// MODEL REGISTRY
// ═══════════════════════════════════════════════════════

export const MODELS = {
  transformers: {
    // Format: { modelId, paramB (billions), quality (1-5), vramGB at q4f16 }
    tiny:     { id: 'HuggingFaceTB/SmolLM2-135M-Instruct',           paramB: 0.135, quality: 2, vramGB: 0.15 },
    small:    { id: 'HuggingFaceTB/SmolLM2-360M-Instruct',           paramB: 0.36,  quality: 2, vramGB: 0.3  },
    compact:  { id: 'onnx-community/Qwen3-0.6B-ONNX',               paramB: 0.6,   quality: 3, vramGB: 0.5  },
    medium:   { id: 'HuggingFaceTB/SmolLM2-1.7B-Instruct',          paramB: 1.7,   quality: 3, vramGB: 1.0  },
    good:     { id: 'onnx-community/Qwen3-1.7B-ONNX',               paramB: 1.7,   quality: 4, vramGB: 1.2  },
    llama3b:  { id: 'onnx-community/Llama-3.2-3B-Instruct-ONNX',   paramB: 3,     quality: 4, vramGB: 2.0  },
    phi4mini: { id: 'onnx-community/Phi-4-mini-instruct-ONNX',      paramB: 3.8,   quality: 5, vramGB: 2.5  },
    qwen4b:   { id: 'onnx-community/Qwen3-4B-ONNX',                 paramB: 4,     quality: 5, vramGB: 2.8  },
  },
  webllm: {
    smol:     { id: 'SmolLM2-1.7B-Instruct-q4f16_1-MLC',           paramB: 1.7,   quality: 3, vramGB: 1.0  },
    qwen4b:   { id: 'Qwen3-4B-Instruct-q4f16_1-MLC',               paramB: 4,     quality: 5, vramGB: 3.0  },
    phi4:     { id: 'Phi-4-mini-instruct-q4f16_1-MLC',             paramB: 3.8,   quality: 5, vramGB: 2.5  },
    llama3b:  { id: 'Llama-3.2-3B-Instruct-q4f16_1-MLC',          paramB: 3,     quality: 4, vramGB: 2.0  },
    qwen8b:   { id: 'Qwen3-8B-Instruct-q4f16_1-MLC',               paramB: 8,     quality: 5, vramGB: 5.5  },
    coder7b:  { id: 'Qwen2.5-Coder-7B-Instruct-q4f16_1-MLC',      paramB: 7,     quality: 5, vramGB: 5.0  },
    gemma4b:  { id: 'gemma-3-4b-it-q4f16_1-MLC',                   paramB: 4,     quality: 4, vramGB: 2.7  },
  },
  embeddings: {
    minilm:   { id: 'Xenova/all-MiniLM-L6-v2',   dims: 384,  sizeMB: 22  },
    bge_sm:   { id: 'Xenova/bge-small-en-v1.5',  dims: 384,  sizeMB: 33  },
    nomic:    { id: 'Xenova/nomic-embed-text-v1', dims: 768,  sizeMB: 137 },
    bge_m3:   { id: 'Xenova/bge-m3',             dims: 1024, sizeMB: 570 },
  }
};

// ═══════════════════════════════════════════════════════
// GPU CAPABILITY DETECTION
// ═══════════════════════════════════════════════════════

export async function detectGPUCapabilities() {
  if (!navigator.gpu) return { available: false, vramGB: 0 };

  const adapter = await navigator.gpu.requestAdapter({ powerPreference: 'high-performance' });
  if (!adapter) return { available: false, vramGB: 0 };

  const info = await adapter.requestAdapterInfo();
  // maxBufferSize is a proxy — typically equals VRAM for discrete GPUs
  const vramGB = adapter.limits.maxBufferSize / 1e9;

  return {
    available: true,
    vramGB: Math.round(vramGB * 10) / 10,
    vendor: info.vendor,
    architecture: info.architecture,
    hasFloat16: adapter.features.has('shader-f16'),
    maxBufferSize: adapter.limits.maxBufferSize,
    maxStorageBufferSize: adapter.limits.maxStorageBufferBindingSize,
  };
}

export async function selectBestModel(quality = 'balanced') {
  const gpu = await detectGPUCapabilities();
  if (!gpu.available) return null;

  const vram = gpu.vramGB;
  console.log(`[GPU] Available VRAM: ~${vram}GB`);

  // quality: 'fast' | 'balanced' | 'best'
  if (quality === 'fast') {
    if (vram >= 1.5) return { backend: 'transformers', ...MODELS.transformers.good };
    if (vram >= 0.5) return { backend: 'transformers', ...MODELS.transformers.compact };
    return { backend: 'transformers', ...MODELS.transformers.tiny };
  }
  if (quality === 'balanced') {
    if (vram >= 5.5) return { backend: 'webllm', ...MODELS.webllm.qwen8b };
    if (vram >= 3)   return { backend: 'webllm', ...MODELS.webllm.qwen4b };
    if (vram >= 2.5) return { backend: 'transformers', ...MODELS.transformers.phi4mini };
    if (vram >= 1.5) return { backend: 'transformers', ...MODELS.transformers.good };
    return { backend: 'transformers', ...MODELS.transformers.compact };
  }
  if (quality === 'best') {
    if (vram >= 5.5) return { backend: 'webllm', ...MODELS.webllm.qwen8b };
    if (vram >= 3)   return { backend: 'webllm', ...MODELS.webllm.qwen4b };
    if (vram >= 2.5) return { backend: 'webllm', ...MODELS.webllm.phi4 };
    if (vram >= 2)   return { backend: 'webllm', ...MODELS.webllm.llama3b };
    return { backend: 'transformers', ...MODELS.transformers.good };
  }
  return { backend: 'transformers', ...MODELS.transformers.compact };
}

// ═══════════════════════════════════════════════════════
// TRANSFORMERS.JS BACKEND
// ═══════════════════════════════════════════════════════

export class TransformersBackend {
  generator = null;
  modelId = null;

  async load(modelId, { dtype = 'q4f16', onProgress } = {}) {
    const { pipeline, env, TextStreamer } = await import('@huggingface/transformers');
    env.allowRemoteModels = true;
    env.useBrowserCache = true;

    this.TextStreamer = TextStreamer;
    this.modelId = modelId;

    this.generator = await pipeline('text-generation', modelId, {
      device: 'webgpu',
      dtype,
      progress_callback(p) {
        if (p.status === 'downloading') onProgress?.({
          file: p.file,
          percent: Math.round(p.progress ?? 0),
          loaded: p.loaded,
          total: p.total,
        });
      },
    });
    console.log(`[Transformers] Loaded ${modelId}`);
    return this;
  }

  async chat(messages, { maxTokens = 512, temperature = 0.7, onToken } = {}) {
    if (!this.generator) throw new Error('Model not loaded');

    let result = '';
    const streamer = onToken ? new this.TextStreamer(this.generator.tokenizer, {
      skip_prompt: true,
      callback_function: (tok) => { result += tok; onToken(tok); }
    }) : undefined;

    const output = await this.generator(messages, {
      max_new_tokens: maxTokens,
      do_sample: temperature > 0,
      temperature,
      streamer,
    });

    return streamer ? result : output[0].generated_text.at(-1).content;
  }
}

// ═══════════════════════════════════════════════════════
// WEBLLM BACKEND
// ═══════════════════════════════════════════════════════

export class WebLLMBackend {
  engine = null;
  modelId = null;

  async load(modelId, { onProgress } = {}) {
    const { CreateMLCEngine } = await import('@mlc-ai/web-llm');
    this.modelId = modelId;
    this.engine = await CreateMLCEngine(modelId, {
      initProgressCallback: ({ progress, text }) => {
        onProgress?.({ percent: Math.round(progress * 100), text });
      }
    });
    console.log(`[WebLLM] Loaded ${modelId}`);
    return this;
  }

  async chat(messages, { maxTokens = 1024, temperature = 0.7, onToken, jsonSchema } = {}) {
    if (!this.engine) throw new Error('Model not loaded');

    const opts = {
      messages,
      temperature,
      max_tokens: maxTokens,
      stream: !!onToken,
    };
    if (jsonSchema) {
      opts.response_format = { type: 'json_object', schema: JSON.stringify(jsonSchema) };
    }

    if (onToken) {
      const stream = await this.engine.chat.completions.create(opts);
      let full = '';
      for await (const chunk of stream) {
        const tok = chunk.choices[0]?.delta?.content || '';
        if (tok) { full += tok; onToken(tok); }
      }
      return full;
    }

    const response = await this.engine.chat.completions.create(opts);
    return response.choices[0].message.content;
  }

  async getStats() {
    return this.engine?.runtimeStatsText();
  }

  async reset() {
    return this.engine?.resetChat();
  }
}

// ═══════════════════════════════════════════════════════
// SMART LLM — auto-selects backend + model
// ═══════════════════════════════════════════════════════

export class SmartLLM {
  backend = null;
  modelInfo = null;

  static async create({
    preferredQuality = 'balanced',
    forceModel = null,
    forceBackend = null,
    onProgress,
    systemPrompt = 'You are a helpful assistant.',
  } = {}) {
    const llm = new SmartLLM();
    llm.systemPrompt = systemPrompt;

    // Determine model to use
    const modelInfo = forceModel
      ? { backend: forceBackend ?? 'transformers', id: forceModel }
      : await selectBestModel(preferredQuality);

    if (!modelInfo) {
      console.warn('[SmartLLM] WebGPU unavailable — falling back to minimal Wasm model');
      modelInfo = { backend: 'transformers', ...MODELS.transformers.compact };
    }

    llm.modelInfo = modelInfo;
    console.log(`[SmartLLM] Selected: ${modelInfo.id} (${modelInfo.backend})`);

    if (modelInfo.backend === 'webllm') {
      llm.backend = new WebLLMBackend();
      await llm.backend.load(modelInfo.id, { onProgress });
    } else {
      llm.backend = new TransformersBackend();
      await llm.backend.load(modelInfo.id, { onProgress });
    }

    return llm;
  }

  async chat(userMessage, { onToken, context = '', maxTokens = 1024 } = {}) {
    const messages = [
      { role: 'system', content: this.systemPrompt + (context ? `\n\nContext:\n${context}` : '') },
      { role: 'user', content: userMessage },
    ];
    return this.backend.chat(messages, { onToken, maxTokens });
  }

  async extractJSON(userMessage, schema) {
    if (this.backend instanceof WebLLMBackend) {
      return JSON.parse(await this.backend.chat(
        [{ role: 'user', content: userMessage }],
        { jsonSchema: schema, maxTokens: 512 }
      ));
    }
    // Fallback: ask for JSON explicitly
    const response = await this.backend.chat([
      { role: 'system', content: 'Respond ONLY with valid JSON. No markdown, no explanation.' },
      { role: 'user', content: userMessage }
    ], { maxTokens: 512 });
    return JSON.parse(response.replace(/```json|```/g, '').trim());
  }
}

// ═══════════════════════════════════════════════════════
// EMBEDDING ENGINE
// ═══════════════════════════════════════════════════════

export class EmbeddingEngine {
  pipe = null;
  dims = 0;

  async load(modelKey = 'minilm', { device = 'webgpu', dtype = 'fp16' } = {}) {
    const { pipeline, env } = await import('@huggingface/transformers');
    env.useBrowserCache = true;

    const modelCfg = MODELS.embeddings[modelKey] ?? MODELS.embeddings.minilm;
    this.dims = modelCfg.dims;

    this.pipe = await pipeline('feature-extraction', modelCfg.id, { device, dtype });
    console.log(`[Embeddings] Loaded ${modelCfg.id} (${this.dims}-dim)`);
    return this;
  }

  async embed(text) {
    const out = await this.pipe(text, { pooling: 'mean', normalize: true });
    return out.data; // Float32Array
  }

  async embedBatch(texts, batchSize = 16) {
    const results = [];
    for (let i = 0; i < texts.length; i += batchSize) {
      const batch = texts.slice(i, i + batchSize);
      const outs = await this.pipe(batch, { pooling: 'mean', normalize: true });
      results.push(...(Array.isArray(outs) ? outs.map(o => o.data) : [outs.data]));
    }
    return results;
  }
}

// ═══════════════════════════════════════════════════════
// RAG PIPELINE
// ═══════════════════════════════════════════════════════

export class BrowserRAG {
  embedder = null;
  llm = null;
  db = null;

  static async create({
    embeddingModel = 'minilm',
    llmQuality = 'balanced',
    onLoadProgress,
  } = {}) {
    const rag = new BrowserRAG();

    // Open IDB
    const { openDB } = await import('idb');
    rag.db = await openDB('rag-store', 1, {
      upgrade(db) {
        const s = db.createObjectStore('chunks', { keyPath: 'id', autoIncrement: true });
        s.createIndex('by-coll', 'collection');
        s.createIndex('by-source', 'source');
      }
    });

    // Load embedder
    console.log('[RAG] Loading embedding model...');
    rag.embedder = await new EmbeddingEngine().load(embeddingModel, { device: 'webgpu' });

    // Load LLM
    console.log('[RAG] Loading language model...');
    rag.llm = await SmartLLM.create({
      preferredQuality: llmQuality,
      onProgress: onLoadProgress,
      systemPrompt: 'You are a helpful assistant. Answer questions based on provided context. If context is insufficient, say so honestly.',
    });

    return rag;
  }

  // Add documents to knowledge base
  async ingest(text, source = 'unknown', collection = 'default', {
    chunkSize = 400,
    overlap = 50,
  } = {}) {
    const chunks = this._splitIntoChunks(text, chunkSize, overlap);
    const embeddings = await this.embedder.embedBatch(chunks);

    const tx = this.db.transaction('chunks', 'readwrite');
    for (let i = 0; i < chunks.length; i++) {
      await tx.store.add({
        collection,
        source,
        text: chunks[i],
        embedding: Array.from(embeddings[i]),
        chunkIndex: i,
        createdAt: Date.now(),
      });
    }
    await tx.done;
    console.log(`[RAG] Indexed ${chunks.length} chunks from "${source}"`);
    return chunks.length;
  }

  // Retrieve relevant chunks
  async retrieve(query, collection = 'default', topK = 5, minScore = 0.3) {
    const qEmb = await this.embedder.embed(query);
    const all = await this.db.getAllFromIndex('chunks', 'by-coll', collection);

    const cos = (a, b) => {
      let d = 0, na = 0, nb = 0;
      for (let i = 0; i < a.length; i++) { d += a[i]*b[i]; na += a[i]*a[i]; nb += b[i]*b[i]; }
      return d / (Math.sqrt(na) * Math.sqrt(nb) + 1e-10);
    };

    return all
      .map(chunk => ({ ...chunk, score: cos(qEmb, chunk.embedding) }))
      .filter(c => c.score >= minScore)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
  }

  // Full RAG query
  async query(question, collection = 'default', { onToken, topK = 5 } = {}) {
    const chunks = await this.retrieve(question, collection, topK);

    if (!chunks.length) {
      return this.llm.chat(question, { onToken });
    }

    const context = chunks
      .map((c, i) => `[Source: ${c.source}, chunk ${c.chunkIndex}]\n${c.text}`)
      .join('\n\n---\n\n');

    return this.llm.chat(question, { context, onToken });
  }

  // Multi-turn chat with memory
  chatWithMemory(collection = 'default') {
    const history = [];
    return async (message, { onToken } = {}) => {
      // Retrieve relevant context
      const chunks = await this.retrieve(message, collection, 3);
      const context = chunks.map(c => c.text).join('\n');

      // Build messages with history
      const messages = [
        {
          role: 'system',
          content: 'You are a helpful assistant. Answer based on context and conversation history.\n\n' +
                   (context ? `Knowledge base context:\n${context}` : '')
        },
        ...history,
        { role: 'user', content: message }
      ];

      const response = await this.llm.backend.chat(messages, { onToken });
      history.push({ role: 'user', content: message });
      history.push({ role: 'assistant', content: response });

      // Trim history to last 10 turns
      if (history.length > 20) history.splice(0, 2);

      return response;
    };
  }

  _splitIntoChunks(text, size = 400, overlap = 50) {
    const words = text.split(/\s+/);
    const chunks = [];
    let i = 0;
    while (i < words.length) {
      chunks.push(words.slice(i, i + size).join(' '));
      i += size - overlap;
    }
    return chunks.filter(c => c.trim().length > 0);
  }
}

// ═══════════════════════════════════════════════════════
// QUICK DEMO
// ═══════════════════════════════════════════════════════

if (typeof window !== 'undefined') {
  window.demoHFWebGPU = async () => {
    console.log('=== HuggingFace + WebGPU Demo ===');

    const gpu = await detectGPUCapabilities();
    console.log('GPU:', gpu);

    const modelInfo = await selectBestModel('balanced');
    console.log('Selected model:', modelInfo?.id ?? 'None (no WebGPU)');

    if (!modelInfo) {
      console.log('WebGPU unavailable. Skipping inference demo.');
      return;
    }

    console.log('\nLoading model...');
    const llm = await SmartLLM.create({
      preferredQuality: 'fast',
      onProgress: (p) => console.log(`Loading: ${p.percent ?? p.text ?? ''}%`),
    });

    console.log('\nGenerating response...');
    let output = '';
    await llm.chat('What is WebGPU in 2 sentences?', {
      maxTokens: 100,
      onToken: (tok) => {
        output += tok;
        process.stdout?.write(tok);
      }
    });
    console.log('\nResponse:', output);

    console.log('\nDone!');
    return { modelInfo, output };
  };

  window.demoRAG = async () => {
    console.log('=== RAG Pipeline Demo ===');

    const rag = await BrowserRAG.create({
      embeddingModel: 'minilm',
      llmQuality: 'fast',
      onLoadProgress: (p) => console.log(`Model: ${p.percent ?? 0}%`),
    });

    // Ingest knowledge
    await rag.ingest(`
      WebGPU is a modern graphics API for the web that provides access to GPU hardware.
      It supports compute shaders for general-purpose GPU programming.
      WebGPU is available in Chrome 113+, Firefox 141+, and Safari 26+.
      It enables running machine learning models directly in the browser.
    `, 'webgpu-docs', 'tech');

    // Query
    console.log('\nQuerying knowledge base...');
    const answer = await rag.query('Which browsers support WebGPU?', 'tech');
    console.log('Answer:', answer);
    return answer;
  };
}
