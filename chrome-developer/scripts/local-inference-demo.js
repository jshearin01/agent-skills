/**
 * local-inference-demo.js
 *
 * Demonstrates multi-backend ML inference with graceful degradation:
 *   1. Chrome Built-in AI (Gemini Nano) — free, private, zero latency
 *   2. Transformers.js with WebGPU — local, larger models, offline
 *   3. ONNX Runtime Web — production, custom models
 *   4. Cloud API fallback — always available
 *
 * Usage:
 *   import { LocalInference } from './local-inference-demo.js';
 *   const ai = new LocalInference({ task: 'summarization' });
 *   await ai.init();
 *   const result = await ai.run('Text to process...');
 *
 * Dependencies (install as needed):
 *   npm install @huggingface/transformers onnxruntime-web @mlc-ai/web-llm
 */

// ─────────────────────────────────────────────────────────
// BACKEND DETECTOR
// ─────────────────────────────────────────────────────────

export class BackendDetector {
  static async getAvailableBackends() {
    const backends = [];

    // 1. Chrome Built-in AI
    if ('LanguageModel' in globalThis) {
      const status = await LanguageModel.availability().catch(() => 'unavailable');
      backends.push({
        name: 'chrome-builtin-ai',
        available: status === 'available',
        downloadable: status === 'downloadable',
        label: `Chrome Built-in AI (Gemini Nano) — ${status}`,
        cost: 'free',
        privacy: 'on-device',
        latency: 'low',
      });
    }

    // 2. WebGPU (for Transformers.js / ONNX Runtime Web)
    const webgpuAvailable = !!(navigator.gpu && await navigator.gpu.requestAdapter());
    backends.push({
      name: 'webgpu',
      available: webgpuAvailable,
      label: `WebGPU — ${webgpuAvailable ? 'available' : 'unavailable'}`,
      cost: 'free',
      privacy: 'on-device',
      latency: 'medium',
    });

    // 3. WebAssembly (always available as CPU fallback)
    backends.push({
      name: 'wasm',
      available: typeof WebAssembly !== 'undefined',
      label: 'WebAssembly (CPU) — available',
      cost: 'free',
      privacy: 'on-device',
      latency: 'high',
    });

    // 4. WebNN
    if ('ml' in navigator) {
      const ctx = await navigator.ml.createContext({ deviceType: 'gpu' }).catch(() => null);
      backends.push({
        name: 'webnn',
        available: !!ctx,
        label: `WebNN — ${ctx ? 'available' : 'unavailable'}`,
        cost: 'free',
        privacy: 'on-device',
        latency: 'low',
      });
    }

    return backends;
  }

  static async report() {
    const backends = await this.getAvailableBackends();
    console.table(backends.map(b => ({
      backend: b.name,
      available: b.available ? '✅' : '❌',
      privacy: b.privacy,
      latency: b.latency,
    })));
    return backends;
  }
}

// ─────────────────────────────────────────────────────────
// CHROME BUILT-IN AI BACKEND
// ─────────────────────────────────────────────────────────

class ChromeBuiltinAIBackend {
  name = 'chrome-builtin-ai';
  session = null;

  async init(task, systemPrompt) {
    if (!('LanguageModel' in globalThis)) throw new Error('Built-in AI not available');

    const status = await LanguageModel.availability();
    if (status === 'unavailable') throw new Error('Gemini Nano not supported on this device');

    if (status === 'downloadable' || status === 'downloading') {
      console.log('[chrome-ai] Downloading Gemini Nano model...');
    }

    this.session = await LanguageModel.create({
      systemPrompt: systemPrompt || this._getSystemPrompt(task),
      monitor(m) {
        m.addEventListener('downloadprogress', (e) => {
          console.log(`[chrome-ai] Download: ${Math.round(e.loaded / e.total * 100)}%`);
        });
      }
    });

    console.log(`[chrome-ai] Ready. Tokens available: ${this.session.tokensLeft}`);
  }

  _getSystemPrompt(task) {
    const prompts = {
      summarization: 'Summarize the following text concisely in 2-3 sentences.',
      classification: 'Classify the following text. Respond with only the category name.',
      extraction: 'Extract key information from the following text as a JSON object.',
      qa: 'Answer the following question based on the provided context.',
      translation: 'Translate the following text accurately.',
      default: 'Process the following text and provide a helpful response.',
    };
    return prompts[task] || prompts.default;
  }

  async run(input, options = {}) {
    if (!this.session) throw new Error('Not initialized');

    const { stream = false, signal } = options;

    // Check token budget
    const tokenCost = await this.session.countPromptTokens(input);
    if (tokenCost > this.session.tokensLeft) {
      // Truncate input to fit
      const ratio = this.session.tokensLeft / tokenCost * 0.9;
      input = input.slice(0, Math.floor(input.length * ratio));
      console.warn('[chrome-ai] Input truncated to fit token budget');
    }

    if (stream) {
      return this.session.promptStreaming(input, { signal });
    }

    return this.session.prompt(input, { signal });
  }

  async summarize(text) {
    const summarizer = await Summarizer.create({ type: 'key-points', length: 'short' });
    try {
      return await summarizer.summarize(text);
    } finally {
      summarizer.destroy();
    }
  }

  destroy() {
    this.session?.destroy();
    this.session = null;
  }
}

// ─────────────────────────────────────────────────────────
// TRANSFORMERS.JS BACKEND
// ─────────────────────────────────────────────────────────

class TransformersJSBackend {
  name = 'transformers-js';
  pipeline = null;

  // Model recommendations by task
  static MODELS = {
    summarization: 'Xenova/distilbart-cnn-6-6',
    classification: 'Xenova/distilbert-base-uncased-finetuned-sst-2-english',
    ner: 'Xenova/bert-base-NER',
    qa: 'Xenova/distilbert-base-uncased-distilled-squad',
    translation_en_fr: 'Xenova/opus-mt-en-fr',
    'feature-extraction': 'Xenova/all-MiniLM-L6-v2',
    'text-generation': 'Xenova/gpt2',
    zero_shot: 'Xenova/nli-deberta-v3-small',
  };

  async init(task, modelOverride = null, progressCallback = null) {
    // Dynamic import — only load if needed
    const { pipeline, env } = await import('@huggingface/transformers');

    env.allowRemoteModels = true;
    env.useBrowserCache = true;

    const model = modelOverride || TransformersJSBackend.MODELS[task] ||
      TransformersJSBackend.MODELS['feature-extraction'];

    const device = await this._selectDevice();
    console.log(`[transformers-js] Loading ${model} on ${device}...`);

    this.pipeline = await pipeline(task, model, {
      device,
      dtype: device === 'webgpu' ? 'fp32' : 'q8',
      progress_callback: progressCallback || ((p) => {
        if (p.status === 'progress') {
          console.log(`[transformers-js] ${p.file}: ${Math.round(p.progress)}%`);
        }
      }),
    });

    console.log(`[transformers-js] Model loaded on ${device}`);
  }

  async _selectDevice() {
    if (navigator.gpu && await navigator.gpu.requestAdapter()) return 'webgpu';
    return 'wasm';
  }

  async run(input, options = {}) {
    if (!this.pipeline) throw new Error('Not initialized');
    return this.pipeline(input, options);
  }
}

// ─────────────────────────────────────────────────────────
// ONNX RUNTIME WEB BACKEND
// ─────────────────────────────────────────────────────────

class ONNXBackend {
  name = 'onnx-runtime-web';
  session = null;

  async init(modelUrl, options = {}) {
    const ort = await import('onnxruntime-web');

    ort.env.wasm.wasmPaths = options.wasmPaths || 'https://cdn.jsdelivr.net/npm/onnxruntime-web@latest/dist/';
    ort.env.wasm.numThreads = navigator.hardwareConcurrency || 4;

    this.session = await ort.InferenceSession.create(modelUrl, {
      executionProviders: ['webgpu', 'wasm'],
      graphOptimizationLevel: 'all',
      ...options.sessionOptions,
    });

    console.log('[onnx] Session created. Inputs:', this.session.inputNames);
  }

  async run(feeds) {
    if (!this.session) throw new Error('Not initialized');
    return this.session.run(feeds);
  }

  async runClassification(inputData, shape) {
    const ort = await import('onnxruntime-web');
    const tensor = new ort.Tensor('float32', inputData, shape);
    const feeds = { [this.session.inputNames[0]]: tensor };
    const output = await this.session.run(feeds);
    return output[this.session.outputNames[0]].data;
  }
}

// ─────────────────────────────────────────────────────────
// WEBLLM BACKEND (Full LLM Chat)
// ─────────────────────────────────────────────────────────

class WebLLMBackend {
  name = 'web-llm';
  engine = null;

  // Available models (see https://github.com/mlc-ai/web-llm for full list)
  static MODELS = {
    small: 'Llama-3.2-1B-Instruct-q4f16_1-MLC',
    medium: 'Llama-3.2-3B-Instruct-q4f16_1-MLC',
    large: 'Llama-3.1-8B-Instruct-q4f16_1-MLC',
    phi: 'Phi-3.5-mini-instruct-q4f16_1-MLC',
    gemma: 'gemma-2-2b-it-q4f16_1-MLC',
    mistral: 'Mistral-7B-Instruct-v0.3-q4f16_1-MLC',
  };

  async init(modelSize = 'small', onProgress = null) {
    const { MLCEngine } = await import('@mlc-ai/web-llm');

    this.engine = new MLCEngine();
    if (onProgress) {
      this.engine.setInitProgressCallback((report) => onProgress(report));
    }

    const model = WebLLMBackend.MODELS[modelSize] || modelSize;
    console.log(`[webllm] Loading ${model}...`);
    await this.engine.reload(model);
    console.log('[webllm] Model ready');
  }

  async chat(messages, options = {}) {
    if (!this.engine) throw new Error('Not initialized');

    const { stream = false, temperature = 0.7, maxTokens = 1000 } = options;

    const completion = await this.engine.chat.completions.create({
      messages,
      stream,
      temperature,
      max_tokens: maxTokens,
    });

    if (stream) return completion;
    return completion.choices[0]?.message?.content;
  }

  async simplePrompt(userMessage, systemMessage = 'You are a helpful assistant.') {
    return this.chat([
      { role: 'system', content: systemMessage },
      { role: 'user', content: userMessage },
    ]);
  }
}

// ─────────────────────────────────────────────────────────
// UNIFIED INFERENCE API (with degradation chain)
// ─────────────────────────────────────────────────────────

export class LocalInference {
  /**
   * @param {object} options
   * @param {string} options.task - 'summarization' | 'classification' | 'chat' | 'embedding'
   * @param {string} [options.systemPrompt] - Override system prompt for Built-in AI
   * @param {string} [options.cloudApiUrl] - Fallback cloud API endpoint
   * @param {string} [options.cloudApiKey] - Fallback cloud API key
   */
  constructor(options = {}) {
    this.task = options.task || 'chat';
    this.systemPrompt = options.systemPrompt;
    this.cloudApiUrl = options.cloudApiUrl;
    this.cloudApiKey = options.cloudApiKey;
    this.activeBackend = null;
    this.backendName = null;
  }

  async init(onProgress = null) {
    const errors = [];

    // Try backends in order of preference
    const chain = [
      () => this._tryBuiltinAI(),
      () => this._tryTransformersJS(onProgress),
      () => this._tryWasm(),
    ];

    for (const tryBackend of chain) {
      try {
        await tryBackend();
        return; // Success
      } catch (e) {
        errors.push(e.message);
        console.warn(`[inference] Backend failed: ${e.message}`);
      }
    }

    if (this.cloudApiUrl) {
      console.log('[inference] Using cloud API fallback');
      this.backendName = 'cloud';
      return;
    }

    throw new Error(`All backends failed:\n${errors.join('\n')}`);
  }

  async _tryBuiltinAI() {
    if (!('LanguageModel' in globalThis)) throw new Error('Built-in AI API not present');
    const backend = new ChromeBuiltinAIBackend();
    await backend.init(this.task, this.systemPrompt);
    this.activeBackend = backend;
    this.backendName = 'chrome-builtin-ai';
    console.log('[inference] Using Chrome Built-in AI (Gemini Nano)');
  }

  async _tryTransformersJS(onProgress) {
    const backend = new TransformersJSBackend();
    await backend.init(this.task, null, onProgress);
    this.activeBackend = backend;
    this.backendName = 'transformers-js';
    console.log('[inference] Using Transformers.js');
  }

  async _tryWasm() {
    // Minimal WASM fallback — just basic text processing
    if (typeof WebAssembly === 'undefined') throw new Error('WebAssembly not supported');
    this.backendName = 'wasm-basic';
    console.log('[inference] Using minimal WASM fallback');
  }

  async run(input, options = {}) {
    if (this.backendName === 'cloud') {
      return this._runCloud(input);
    }

    if (!this.activeBackend) throw new Error('Not initialized. Call init() first.');

    return this.activeBackend.run(input, options);
  }

  async runStream(input) {
    if (this.backendName === 'chrome-builtin-ai') {
      return this.activeBackend.run(input, { stream: true });
    }
    // Fallback: run non-streaming and yield once
    const result = await this.run(input);
    return (async function* () { yield result; })();
  }

  async _runCloud(input) {
    if (!this.cloudApiUrl || !this.cloudApiKey) {
      throw new Error('Cloud API credentials not configured');
    }

    const response = await fetch(this.cloudApiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.cloudApiKey}`,
      },
      body: JSON.stringify({ input, task: this.task }),
    });

    if (!response.ok) throw new Error(`Cloud API error: ${response.status}`);
    const data = await response.json();
    return data.output || data.result || data.text;
  }

  get backend() {
    return this.backendName;
  }

  destroy() {
    this.activeBackend?.destroy?.();
    this.activeBackend = null;
  }
}

// Re-export individual backends for direct use
export { ChromeBuiltinAIBackend, TransformersJSBackend, ONNXBackend, WebLLMBackend };

// ─────────────────────────────────────────────────────────
// DEMO (run in browser console: await window.demoInference())
// ─────────────────────────────────────────────────────────

if (typeof window !== 'undefined') {
  window.demoInference = async () => {
    console.log('=== Backend Detection ===');
    await BackendDetector.report();

    console.log('\n=== Initializing LocalInference ===');
    const ai = new LocalInference({
      task: 'summarization',
      systemPrompt: 'Summarize the following text in 1-2 sentences.',
    });

    await ai.init((progress) => {
      if (progress.status === 'progress') {
        console.log(`Loading model: ${progress.file} (${Math.round(progress.progress)}%)`);
      }
    });

    console.log(`Active backend: ${ai.backend}`);

    console.log('\n=== Running Inference ===');
    const sampleText = `
      WebGPU is a new graphics and compute API for the web that provides access to modern GPU 
      features. Unlike WebGL, WebGPU supports compute shaders, allowing developers to run 
      general-purpose GPU computations directly in the browser. This enables AI workloads, 
      physics simulations, and complex visualizations to run at near-native speeds.
    `;

    const result = await ai.run(sampleText);
    console.log('Result:', result);

    ai.destroy();
    return result;
  };
}
