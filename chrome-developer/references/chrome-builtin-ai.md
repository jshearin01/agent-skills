# Chrome Built-in AI (Gemini Nano) — Complete Reference

## Table of Contents
1. [Setup & Requirements](#1-setup--requirements)
2. [Availability & Graceful Degradation](#2-availability--graceful-degradation)
3. [Prompt API (LanguageModel)](#3-prompt-api-languagemodel)
4. [Summarizer API](#4-summarizer-api)
5. [Writer API](#5-writer-api)
6. [Rewriter API](#6-rewriter-api)
7. [Translator & Language Detector APIs](#7-translator--language-detector-apis)
8. [Proofreader API](#8-proofreader-api)
9. [Using in Chrome Extensions](#9-using-in-chrome-extensions)
10. [Hybrid Cloud + Local Strategy](#10-hybrid-cloud--local-strategy)
11. [Token Management](#11-token-management)
12. [Privacy & Security Considerations](#12-privacy--security-considerations)
13. [Debugging & Diagnostics](#13-debugging--diagnostics)

---

## 1. Setup & Requirements

### Hardware & Software Requirements

| Requirement | Minimum |
|-------------|---------|
| OS | Windows 10/11, macOS 13+ (Ventura+), Linux, ChromeOS (Chromebook Plus) |
| Chrome Version | 138+ (Dev/Canary for early access, stable rollout ongoing) |
| Free Storage | 22GB on Chrome profile volume |
| GPU VRAM | Strictly >4GB VRAM (for GPU path) |
| RAM (CPU path) | 16GB RAM + 4+ CPU cores |
| Network | Unmetered for initial model download |

**Not supported on:** Mobile (Android/iOS), non-Chromebook Plus ChromeOS

### Flags for Local Development

Navigate to `chrome://flags` and enable:
- `#optimization-guide-on-device-model` → **Enabled BypassPerfRequirement**
- `#prompt-api-for-gemini-nano` → **Enabled** (or **Enabled multilingual** for multi-language)

For multilingual support (Spanish, Japanese added in Chrome 140+):
- `#prompt-api-for-gemini-nano` → **Enabled multilingual**

### Verify Model Download

```
chrome://on-device-internals → Model Status tab
```

Or in DevTools console:
```js
await LanguageModel.availability(); // should return 'available'
```

### TypeScript Types

```bash
npm install @types/dom-chromium-ai
```

---

## 2. Availability & Graceful Degradation

### Always Check Availability First

```js
// Availability states
// 'available'    — model downloaded, ready immediately
// 'downloadable' — supported, model not yet downloaded
// 'downloading'  — model currently downloading
// 'unavailable'  — not supported on this device/browser

async function checkAIAvailability() {
  if (!('LanguageModel' in globalThis)) {
    return { status: 'not_supported', reason: 'API not present' };
  }
  const status = await LanguageModel.availability();
  return { status };
}
```

### Progressive Enhancement Pattern

```js
class AIFeature {
  async initialize() {
    // Tier 1: Chrome Built-in AI (free, private, offline)
    if ('LanguageModel' in globalThis) {
      const status = await LanguageModel.availability();
      if (status === 'available') {
        this.backend = 'gemini-nano';
        this.session = await LanguageModel.create({ systemPrompt: this.systemPrompt });
        return;
      }
      if (status === 'downloadable') {
        this.backend = 'gemini-nano-pending';
        // Optionally trigger download
        return;
      }
    }
    
    // Tier 2: Local WASM/WebGPU model (offline, larger)
    if (await this.checkWebGPUAvailable()) {
      this.backend = 'transformers-webgpu';
      // Load Transformers.js model
      return;
    }
    
    // Tier 3: Cloud API (requires network, may cost money)
    this.backend = 'cloud-api';
  }
  
  async run(prompt) {
    switch (this.backend) {
      case 'gemini-nano':
        return this.session.prompt(prompt);
      case 'transformers-webgpu':
        return this.localModel(prompt);
      case 'cloud-api':
        return this.callCloudAPI(prompt);
      default:
        throw new Error('AI unavailable');
    }
  }
}
```

### Triggering Model Download with Progress

```js
async function downloadModelWithProgress(onProgress) {
  const session = await LanguageModel.create({
    monitor(monitor) {
      monitor.addEventListener('downloadprogress', (event) => {
        const pct = Math.round((event.loaded / event.total) * 100);
        onProgress(pct, event.loaded, event.total);
      });
    }
  });
  return session;
}

// Usage with UI
const session = await downloadModelWithProgress((pct) => {
  progressBar.style.width = `${pct}%`;
  statusText.textContent = `Downloading AI model: ${pct}%`;
});
```

---

## 3. Prompt API (LanguageModel)

### Session Creation Options

```js
const session = await LanguageModel.create({
  // System prompt — sets context/persona
  systemPrompt: 'You are a coding assistant. Respond only with code.',
  
  // Initial conversation history
  initialPrompts: [
    { role: 'user', content: 'Remember: always use TypeScript' },
    { role: 'assistant', content: 'Understood, I will use TypeScript.' }
  ],
  
  // Sampling parameters
  temperature: 0.7,      // 0=deterministic, 1=creative (default: model-defined)
  topK: 40,              // top-K sampling
  
  // Download progress callback
  monitor(m) {
    m.addEventListener('downloadprogress', e => console.log(e.loaded / e.total));
  }
});
```

### Prompt Methods

```js
// Full response (waits for completion)
const response = await session.prompt('Explain closures in JavaScript');

// Streaming response (real-time token output)
const stream = session.promptStreaming('Write a haiku about bugs');
let result = '';
for await (const chunk of stream) {
  result += chunk;
  updateUI(result);
}

// Multimodal (image + text) — Prompt API only
const imageResponse = await session.prompt([
  { role: 'user', content: [
    { type: 'text', text: 'What is in this image?' },
    { type: 'image', image: imageBlob }  // Blob, ImageData, or ImageBitmap
  ]}
]);

// With AbortSignal (cancel long requests)
const controller = new AbortController();
cancelButton.onclick = () => controller.abort();

const stream = session.promptStreaming('Generate a long story', {
  signal: controller.signal
});
try {
  for await (const chunk of stream) { updateUI(chunk); }
} catch (e) {
  if (e.name === 'AbortError') console.log('Request cancelled');
}
```

### Session Management

```js
// Clone session (preserve conversation history, fork context)
const clonedSession = await session.clone();

// Multi-turn conversation
const chat = await LanguageModel.create({ systemPrompt: 'You are helpful.' });
const r1 = await chat.prompt('My name is Alice');
const r2 = await chat.prompt('What is my name?');  // remembers context

// ALWAYS destroy sessions when done (frees GPU/RAM)
try {
  const result = await session.prompt(userInput);
  return result;
} finally {
  session.destroy();
}
```

---

## 4. Summarizer API

```js
// Availability check (separate from LanguageModel)
const summarizerStatus = await Summarizer.availability();

const summarizer = await Summarizer.create({
  type: 'key-points',  // 'tl;dr' | 'key-points' | 'teaser' | 'headline'
  format: 'markdown',  // 'plain-text' | 'markdown'
  length: 'medium',    // 'short' | 'medium' | 'long'
  
  // Optional context
  sharedContext: 'This is a technical blog post about WebGPU.',
});

// Non-streaming
const summary = await summarizer.summarize(longArticleText, {
  context: 'Focus on the practical implications for developers.'
});

// Streaming
const stream = summarizer.summarizeStreaming(longArticleText);
for await (const chunk of stream) {
  summaryEl.textContent += chunk;
}

summarizer.destroy();
```

### Type Descriptions

| Type | Output |
|------|--------|
| `tl;dr` | Short paragraph summarizing the whole text |
| `key-points` | Bulleted list of main points |
| `teaser` | Engaging excerpt to draw readers in |
| `headline` | Single-line headline |

---

## 5. Writer API

```js
const writerStatus = await Writer.availability();

const writer = await Writer.create({
  tone: 'professional',  // 'formal' | 'neutral' | 'professional' | 'casual'
  format: 'markdown',    // 'plain-text' | 'markdown'
  length: 'medium',      // 'short' | 'medium' | 'long'
  
  sharedContext: 'Writing for a technical audience. Use precise language.'
});

// Write from scratch
const article = await writer.write(
  'Write an introduction to WebGPU compute shaders',
  { context: 'Audience: web developers familiar with JavaScript' }
);

// Streaming write
const stream = writer.writeStreaming(
  'Write a product announcement for our new WebGPU library',
  { context: 'Product name: GpuFast. Target: game developers.' }
);
for await (const chunk of stream) { outputEl.textContent += chunk; }

writer.destroy();
```

---

## 6. Rewriter API

```js
const rewriter = await Rewriter.create({
  tone: 'casual',         // 'as-is' | 'more-formal' | 'more-casual' | 'casual' | 'formal'
  format: 'plain-text',
  length: 'shorter',      // 'as-is' | 'shorter' | 'longer'
  
  sharedContext: 'Converting formal technical docs to user-friendly content.'
});

const rewritten = await rewriter.rewrite(formalText, {
  context: 'This is for a beginner audience'
});

// Use case: A/B test different tones
const tones = ['formal', 'casual', 'professional'];
const variants = await Promise.all(
  tones.map(tone => Rewriter.create({ tone }).then(r => r.rewrite(text)))
);

rewriter.destroy();
```

---

## 7. Translator & Language Detector APIs

### Language Detector

```js
const detector = await LanguageDetector.create();

const results = await detector.detect('Hola, ¿cómo estás?');
// results: [{ detectedLanguage: 'es', confidence: 0.97 }, ...]

// Most likely language
const [best] = results;
console.log(best.detectedLanguage, best.confidence);

// Available languages: ISO 639-1 codes (e.g., 'en', 'es', 'ja', 'fr', 'de', ...)
```

### Translator

```js
// Check if translation pair is available
const translatorStatus = await Translator.availability({
  sourceLanguage: 'en',
  targetLanguage: 'es'
});
// 'available' | 'downloadable' | 'downloading' | 'unavailable'

const translator = await Translator.create({
  sourceLanguage: 'en',
  targetLanguage: 'ja'
});

const translated = await translator.translate('Hello, world!');
// Returns: 'こんにちは、世界！'

// Batch translation
const texts = ['Hello', 'How are you?', 'Goodbye'];
const translations = await Promise.all(texts.map(t => translator.translate(t)));

translator.destroy();
```

**Note:** Translator and Language Detector use lightweight expert models, not Gemini Nano.
They work on Chrome desktop only (not mobile).

---

## 8. Proofreader API

```js
const proofreaderStatus = await Proofreader.availability();

const proofreader = await Proofreader.create({
  // No options currently required
});

const corrections = await proofreader.proofread(
  'Their are many mistake in this sentance that need fixing.'
);
// Returns corrected text with explanations

const stream = proofreader.proofreadStreaming(longDocument);
for await (const chunk of stream) { outputEl.textContent += chunk; }

proofreader.destroy();
```

---

## 9. Using in Chrome Extensions

### Manifest Configuration

```json
{
  "manifest_version": 3,
  "permissions": [],
  "host_permissions": [],
  
  // For origin trial (if API not yet in stable):
  "trial_tokens": ["YOUR_ORIGIN_TRIAL_TOKEN"]
}
```

### In Service Worker

```js
// background.js
// LanguageModel API is available in extension service workers
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'summarize') {
    summarizePage(msg.content).then(sendResponse);
    return true; // async response
  }
});

async function summarizePage(content) {
  const status = await Summarizer.availability();
  if (status === 'unavailable') return null;
  
  const summarizer = await Summarizer.create({ type: 'key-points', length: 'short' });
  try {
    return await summarizer.summarize(content);
  } finally {
    summarizer.destroy();
  }
}
```

### In Content Script

```js
// content.js
async function extractAndSummarize() {
  const pageText = document.body.innerText.slice(0, 10000); // token budget
  
  // Send to background (which has LanguageModel access)
  const summary = await chrome.runtime.sendMessage({
    action: 'summarize',
    content: pageText
  });
  
  if (summary) showSummaryUI(summary);
}
```

### In Popup / Options Page

```js
// popup.js — full access to all Built-in AI APIs
document.addEventListener('DOMContentLoaded', async () => {
  const status = await LanguageModel.availability();
  
  if (status !== 'available') {
    document.getElementById('ai-status').textContent = 
      status === 'unavailable' ? 'AI not available on this device' : 'AI model downloading...';
    return;
  }
  
  const session = await LanguageModel.create({
    systemPrompt: 'Analyze web page content and provide insights.'
  });
  
  sendBtn.addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const [{ result: pageContent }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.body.innerText.slice(0, 8000)
    });
    
    const stream = session.promptStreaming(`Analyze: ${pageContent}`);
    outputEl.textContent = '';
    for await (const chunk of stream) { outputEl.textContent += chunk; }
  });
});
```

---

## 10. Hybrid Cloud + Local Strategy

### Decision Logic

```js
class SmartAI {
  constructor({ cloudApiKey, systemPrompt }) {
    this.cloudApiKey = cloudApiKey;
    this.systemPrompt = systemPrompt;
    this.localSession = null;
  }
  
  async init() {
    if ('LanguageModel' in globalThis) {
      const status = await LanguageModel.availability();
      if (status === 'available') {
        this.localSession = await LanguageModel.create({
          systemPrompt: this.systemPrompt
        });
      }
    }
  }
  
  async complete(prompt, options = {}) {
    const {
      requiresAccuracy = false,   // use cloud for accuracy-critical tasks
      maxTokens = 500,
      preferLocal = true,
    } = options;
    
    // Estimate complexity
    const tokenCount = this.localSession 
      ? await this.localSession.countPromptTokens(prompt)
      : Infinity;
    
    const useLocal = this.localSession && 
                     preferLocal && 
                     !requiresAccuracy && 
                     tokenCount < this.localSession.tokensLeft;
    
    if (useLocal) {
      return { text: await this.localSession.prompt(prompt), source: 'local' };
    }
    
    return { text: await this.callCloud(prompt, maxTokens), source: 'cloud' };
  }
  
  async callCloud(prompt, maxTokens) {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': this.cloudApiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: maxTokens,
        system: this.systemPrompt,
        messages: [{ role: 'user', content: prompt }]
      })
    });
    const data = await response.json();
    return data.content[0].text;
  }
  
  destroy() {
    this.localSession?.destroy();
  }
}
```

### Cost-Aware Routing

```js
// Use local for cheap/frequent tasks, cloud for complex/rare tasks
const ai = new SmartAI({ cloudApiKey: 'sk-...' });

// ✅ Use local: simple classification, extraction, short summaries
await ai.complete('Is this spam: "Buy cheap meds"?', { preferLocal: true });

// ☁️ Use cloud: complex reasoning, precise factual queries, long-form
await ai.complete('Explain quantum entanglement with mathematical formalism', { 
  requiresAccuracy: true 
});
```

---

## 11. Token Management

### Context Window

Gemini Nano has a limited context window (~6000 tokens in practice). Always check:

```js
const session = await LanguageModel.create({ systemPrompt: 'You are helpful.' });
console.log('Max tokens:', session.maxTokens);       // Total context window
console.log('Tokens used:', session.tokensSoFar);    // Used so far
console.log('Tokens left:', session.tokensLeft);     // Remaining budget

// Count before sending
const cost = await session.countPromptTokens(myPrompt);
if (cost > session.tokensLeft) {
  // Truncate, summarize, or start new session
  const summarized = await summarizePrevious(session);
  session.destroy();
  const newSession = await LanguageModel.create({ 
    systemPrompt: `Context: ${summarized}. Now answer questions.` 
  });
}
```

### Chunked Generation for Large Documents

```js
async function processLargeDocument(doc, question) {
  const CHUNK_SIZE = 3000;  // characters
  const chunks = [];
  for (let i = 0; i < doc.length; i += CHUNK_SIZE) {
    chunks.push(doc.slice(i, i + CHUNK_SIZE));
  }
  
  // Map-reduce: summarize each chunk, then synthesize
  const session = await LanguageModel.create({ systemPrompt: 'Summarize key points.' });
  const chunkSummaries = [];
  
  for (const chunk of chunks) {
    const summary = await session.prompt(`Summarize: ${chunk}`);
    chunkSummaries.push(summary);
  }
  session.destroy();
  
  // Final synthesis
  const synth = await LanguageModel.create({ systemPrompt: 'Answer questions from summaries.' });
  const answer = await synth.prompt(
    `Based on: ${chunkSummaries.join('\n---\n')}\n\nQuestion: ${question}`
  );
  synth.destroy();
  
  return answer;
}
```

---

## 12. Privacy & Security Considerations

### Data Locality

- **All Built-in AI inference happens on-device** — no data sent to Google servers during generation
- The model is downloaded once via Chrome's component updater infrastructure
- Suitable for processing PII, confidential business data, personal documents

### What Google Collects

- Model download metrics (not your prompts)
- Usage statistics (API call frequency, not content)
- Review Google's Generative AI Prohibited Uses Policy before deployment

### Security in Extensions

```js
// Sanitize user input before sending to AI
function sanitizeForAI(input) {
  // Truncate to reasonable length
  const truncated = input.slice(0, 8000);
  
  // Remove potential prompt injection
  const sanitized = truncated
    .replace(/ignore previous instructions/gi, '[removed]')
    .replace(/system:/gi, '[removed]');
  
  return sanitized;
}

// Don't expose session.prompt directly to untrusted content
chrome.runtime.onMessage.addListener((msg, sender) => {
  // Verify sender is from your extension's content scripts
  if (!sender.tab) return; // reject non-tab messages
  
  const sanitized = sanitizeForAI(msg.content);
  // proceed with sanitized input
});
```

### When NOT to Use Built-in AI

- Accuracy-critical tasks (factual queries, legal/medical advice)
- Tasks requiring knowledge after model training cutoff
- Languages other than English/Spanish/Japanese (Chrome 140+)
- Mobile users (not supported)
- Privacy-sensitive analytics that require logging

---

## 13. Debugging & Diagnostics

### Chrome Internal Pages

```
chrome://on-device-internals     — Model download status, version, size
chrome://flags                   — Enable/disable experimental AI features
chrome://components              — Force update "Optimization Guide On Device Model"
```

### DevTools Diagnostics

```js
// Check all API availability at once
const apis = ['LanguageModel', 'Summarizer', 'Writer', 'Rewriter', 
               'Translator', 'LanguageDetector', 'Proofreader'];

const status = Object.fromEntries(
  await Promise.all(
    apis
      .filter(api => api in globalThis)
      .map(async api => [api, await globalThis[api].availability()])
  )
);
console.table(status);
```

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `LanguageModel is not defined` | API not enabled or Chrome too old | Enable flags, update Chrome |
| `availability()` returns `'unavailable'` | Hardware too old, not enough VRAM | Check GPU, try BypassPerfRequirement flag |
| Model stuck at `'downloading'` | Slow connection, storage full | Check `chrome://on-device-internals` |
| Context window exceeded | Prompt too long | Use `countPromptTokens()` before sending |
| Session `destroy()` not called | Memory leak | Always destroy in `finally` block |
| Extension can't access API | Origin trial needed | Register for Chrome Origin Trial |
