# WebGPU, WebNN & WebAssembly 3.0 — Deep Reference

## Table of Contents
1. [WebGPU: Render Pipeline](#1-webgpu-render-pipeline)
2. [WGSL Language Reference](#2-wgsl-language-reference)
3. [WebGPU for ML Workloads](#3-webgpu-for-ml-workloads)
4. [WebGPU Compatibility & Feature Detection](#4-webgpu-compatibility--feature-detection)
5. [WebNN: Complete API Reference](#5-webnn-complete-api-reference)
6. [WebAssembly 3.0 Features](#6-webassembly-30-features)
7. [Toolchain Recipes](#7-toolchain-recipes)
8. [WASM ↔ WebGPU Interop](#8-wasm--webgpu-interop)
9. [Performance Patterns](#9-performance-patterns)

---

## 1. WebGPU: Render Pipeline

### Full Render Pipeline Example (triangle)

```js
// Initialize WebGPU
const adapter = await navigator.gpu.requestAdapter({
  powerPreference: 'high-performance'
});
if (!adapter) throw new Error('WebGPU not supported');

const device = await adapter.requestDevice({
  requiredFeatures: [],
  requiredLimits: {}
});

// Configure canvas
const canvas = document.querySelector('canvas');
const context = canvas.getContext('webgpu');
const format = navigator.gpu.getPreferredCanvasFormat();
context.configure({ device, format, alphaMode: 'premultiplied' });

// Shaders
const shaderCode = `
@vertex
fn vs_main(@builtin(vertex_index) vi: u32) -> @builtin(position) vec4f {
  var pos = array<vec2f, 3>(
    vec2f(0.0, 0.5),
    vec2f(-0.5, -0.5),
    vec2f(0.5, -0.5)
  );
  return vec4f(pos[vi], 0.0, 1.0);
}

@fragment
fn fs_main() -> @location(0) vec4f {
  return vec4f(1.0, 0.0, 0.0, 1.0); // red
}
`;

const shaderModule = device.createShaderModule({ code: shaderCode });

const pipeline = device.createRenderPipeline({
  layout: 'auto',
  vertex: { module: shaderModule, entryPoint: 'vs_main' },
  fragment: {
    module: shaderModule,
    entryPoint: 'fs_main',
    targets: [{ format }]
  },
  primitive: { topology: 'triangle-list' }
});

// Render loop
function frame() {
  const encoder = device.createCommandEncoder();
  const pass = encoder.beginRenderPass({
    colorAttachments: [{
      view: context.getCurrentTexture().createView(),
      clearValue: { r: 0, g: 0, b: 0, a: 1 },
      loadOp: 'clear',
      storeOp: 'store'
    }]
  });
  pass.setPipeline(pipeline);
  pass.draw(3);
  pass.end();
  device.queue.submit([encoder.finish()]);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
```

### Vertex Buffers

```js
const vertices = new Float32Array([
  // x, y, r, g, b
  0.0, 0.5, 1.0, 0.0, 0.0,
  -0.5, -0.5, 0.0, 1.0, 0.0,
  0.5, -0.5, 0.0, 0.0, 1.0,
]);

const vertexBuffer = device.createBuffer({
  size: vertices.byteLength,
  usage: GPUBufferUsage.VERTEX | GPUBufferUsage.COPY_DST,
  mappedAtCreation: true,
});
new Float32Array(vertexBuffer.getMappedRange()).set(vertices);
vertexBuffer.unmap();

// In pipeline:
const pipeline = device.createRenderPipeline({
  vertex: {
    module: shaderModule,
    entryPoint: 'vs_main',
    buffers: [{
      arrayStride: 5 * 4,  // 5 floats × 4 bytes
      attributes: [
        { shaderLocation: 0, offset: 0, format: 'float32x2' },     // position
        { shaderLocation: 1, offset: 2 * 4, format: 'float32x3' }, // color
      ]
    }]
  },
  // ...
});
```

### Render Bundles (performance optimization)

```js
// Record once, replay many times — ~10x performance improvement (Babylon.js)
const bundleEncoder = device.createRenderBundleEncoder({
  colorFormats: [format]
});
bundleEncoder.setPipeline(pipeline);
bundleEncoder.setVertexBuffer(0, vertexBuffer);
bundleEncoder.draw(vertexCount);
const bundle = bundleEncoder.finish();

// In render loop:
renderPass.executeBundles([bundle]);
```

### Uniforms and Bind Groups

```js
// Uniform buffer (e.g., transformation matrix)
const uniformBuffer = device.createBuffer({
  size: 64,  // 4x4 matrix = 16 floats × 4 bytes
  usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
});

const bindGroupLayout = device.createBindGroupLayout({
  entries: [{
    binding: 0,
    visibility: GPUShaderStage.VERTEX,
    buffer: { type: 'uniform' }
  }]
});

const bindGroup = device.createBindGroup({
  layout: bindGroupLayout,
  entries: [{ binding: 0, resource: { buffer: uniformBuffer } }]
});

// Update each frame:
device.queue.writeBuffer(uniformBuffer, 0, modelViewProjectionMatrix);
```

---

## 2. WGSL Language Reference

### Types

```wgsl
// Scalar types
var a: bool = true;
var b: i32 = -42;
var c: u32 = 42u;
var d: f32 = 3.14;
var e: f16 = 1.0h;  // half precision (requires 'shader-f16' feature)

// Vector types
var v2: vec2f = vec2f(1.0, 2.0);
var v3: vec3<f32> = vec3f(1.0, 2.0, 3.0);
var v4: vec4f = vec4f(0.0, 0.0, 0.0, 1.0);

// Matrix types
var m4: mat4x4f;  // 4x4 float matrix

// Array
var arr: array<f32, 4> = array<f32, 4>(1.0, 2.0, 3.0, 4.0);

// Struct
struct Vertex {
  position: vec4f,
  color: vec4f,
}
```

### Address Spaces

```wgsl
// uniform — read-only, shared across workgroup
@group(0) @binding(0) var<uniform> ubo: MyUniforms;

// storage — read-write, large buffer
@group(0) @binding(1) var<storage, read> input: array<f32>;
@group(0) @binding(2) var<storage, read_write> output: array<f32>;

// workgroup — shared within a workgroup (FAST, ~100x faster than storage)
var<workgroup> shared_data: array<f32, 64>;

// function — local variable
var<function> temp: f32 = 0.0;

// private — per-invocation private variable
var<private> counter: u32 = 0u;
```

### Built-in Functions

```wgsl
// Math
abs(x), ceil(x), floor(x), round(x)
sqrt(x), pow(x, y), log(x), exp(x)
min(a, b), max(a, b), clamp(x, lo, hi)
sin(x), cos(x), tan(x), atan2(y, x)
mix(a, b, t)              // linear interpolation
step(edge, x)             // 0 if x < edge, else 1
smoothstep(lo, hi, x)     // smooth Hermite interpolation

// Vector
dot(a, b)                 // dot product
cross(a, b)               // cross product (vec3 only)
normalize(v)              // unit vector
length(v)                 // magnitude
distance(a, b)            // distance between points
reflect(i, n)             // reflection vector
refract(i, n, eta)        // refraction vector

// Texture
textureSample(t, s, uv)   // sample at UV coords
textureLoad(t, coord, 0)  // load texel by integer coord
textureDimensions(t)      // texture size
```

### Compute Shader Patterns

```wgsl
// Shared memory reduction (sum all elements in workgroup)
@group(0) @binding(0) var<storage, read> input: array<f32>;
@group(0) @binding(1) var<storage, read_write> output: array<f32>;

var<workgroup> partial: array<f32, 256>;

@compute @workgroup_size(256)
fn reduce(@builtin(global_invocation_id) gid: vec3u,
          @builtin(local_invocation_id) lid: vec3u,
          @builtin(workgroup_id) wgid: vec3u) {
  let i = gid.x;
  partial[lid.x] = select(0.0, input[i], i < arrayLength(&input));
  workgroupBarrier();  // sync all threads in workgroup
  
  // Parallel reduction
  var stride = 128u;
  while (stride > 0u) {
    if (lid.x < stride) {
      partial[lid.x] += partial[lid.x + stride];
    }
    workgroupBarrier();
    stride >>= 1u;
  }
  
  if (lid.x == 0u) {
    output[wgid.x] = partial[0];
  }
}
```

---

## 3. WebGPU for ML Workloads

### Matrix Multiplication (naive)

```wgsl
@group(0) @binding(0) var<storage, read> matA: array<f32>;
@group(0) @binding(1) var<storage, read> matB: array<f32>;
@group(0) @binding(2) var<storage, read_write> matC: array<f32>;
@group(0) @binding(3) var<uniform> dims: vec3u;  // M, N, K

@compute @workgroup_size(16, 16)
fn matmul(@builtin(global_invocation_id) gid: vec3u) {
  let row = gid.y;
  let col = gid.x;
  let M = dims.x; let N = dims.y; let K = dims.z;
  
  if (row >= M || col >= N) { return; }
  
  var sum = 0.0f;
  for (var k = 0u; k < K; k++) {
    sum += matA[row * K + k] * matB[k * N + col];
  }
  matC[row * N + col] = sum;
}
```

### Using ONNX Runtime Web

```js
import * as ort from 'onnxruntime-web';

// Configure WASM path
ort.env.wasm.wasmPaths = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.0/dist/';
ort.env.wasm.numThreads = navigator.hardwareConcurrency;

async function runModel(modelUrl, inputData) {
  const session = await ort.InferenceSession.create(modelUrl, {
    executionProviders: ['webgpu', 'wasm'],
    graphOptimizationLevel: 'all',
  });
  
  const inputNames = session.inputNames;
  const outputNames = session.outputNames;
  
  const feeds = {};
  feeds[inputNames[0]] = new ort.Tensor('float32', inputData, [1, 3, 224, 224]);
  
  const results = await session.run(feeds);
  return results[outputNames[0]].data;
}
```

### Using Transformers.js

```js
import { pipeline, env } from '@huggingface/transformers';

// Force local caching
env.allowRemoteModels = true;
env.useBrowserCache = true;
env.backends.onnx.wasm.proxy = false;

// Load model with WebGPU
const extractor = await pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2', {
  device: 'webgpu',
  dtype: 'fp32',
});

const output = await extractor('Your text here', { pooling: 'mean', normalize: true });
const embedding = output.data;  // Float32Array of 384 dimensions

// Available tasks:
// 'text-classification', 'token-classification', 'question-answering'
// 'feature-extraction', 'text-generation', 'translation', 'summarization'
// 'image-classification', 'object-detection', 'image-segmentation'
// 'automatic-speech-recognition', 'audio-classification'
```

### WebLLM (full LLM in browser)

```js
import * as webllm from '@mlc-ai/web-llm';

const engine = new webllm.MLCEngine();
engine.setInitProgressCallback((report) => {
  console.log(`Loading: ${report.text}`);
});

// Available models: Llama-3.2, Phi-3.5, Mistral, Gemma, Qwen, etc.
await engine.reload('Llama-3.2-1B-Instruct-q4f16_1-MLC');

const messages = [
  { role: 'system', content: 'You are a helpful assistant.' },
  { role: 'user', content: 'Hello! What can you do?' }
];

// Streaming
const chunks = await engine.chat.completions.create({
  messages,
  stream: true,
  temperature: 0.7,
});
for await (const chunk of chunks) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```

---

## 4. WebGPU Compatibility & Feature Detection

```js
// Full feature detection
async function getWebGPUCapabilities() {
  if (!navigator.gpu) return { supported: false };
  
  const adapter = await navigator.gpu.requestAdapter();
  if (!adapter) return { supported: false, reason: 'No adapter found' };
  
  const info = await adapter.requestAdapterInfo();
  const features = [...adapter.features];
  const limits = adapter.limits;
  
  return {
    supported: true,
    vendor: info.vendor,
    architecture: info.architecture,
    device: info.device,
    features,
    maxBufferSize: limits.maxBufferSize,
    maxComputeWorkgroupSizeX: limits.maxComputeWorkgroupSizeX,
    maxStorageBufferBindingSize: limits.maxStorageBufferBindingSize,
    hasFloat16: features.includes('shader-f16'),
    hasTimestampQuery: features.includes('timestamp-query'),
  };
}

// Compatibility mode for older GPUs (Chrome 146+)
const adapterCompat = await navigator.gpu.requestAdapter({
  featureLevel: 'compatibility'  // supports OpenGL 4.5 / D3D11
});
```

### Required HTTP Headers for Shared Memory / WASM Threads

```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

These headers are required for `SharedArrayBuffer` (used in WASM threads and some WebGPU patterns).

---

## 5. WebNN: Complete API Reference

### Context and Graph Building

```js
// DeviceType options: 'cpu', 'gpu', 'npu'
// PowerPreference: 'default', 'high-performance', 'low-power'
const context = await navigator.ml.createContext({
  deviceType: 'gpu',
  powerPreference: 'high-performance'
});

const builder = new MLGraphBuilder(context);
```

### Supported Operations (MLGraphBuilder)

```js
// Arithmetic
builder.add(a, b)          // element-wise addition
builder.sub(a, b)          // subtraction
builder.mul(a, b)          // multiplication
builder.div(a, b)          // division
builder.pow(a, b)          // power
builder.abs(x)             // absolute value
builder.neg(x)             // negation
builder.sqrt(x)            // square root
builder.exp(x)             // exponential
builder.log(x)             // natural log

// Matrix operations
builder.matmul(a, b)                   // matrix multiply
builder.gemm(a, b, options)            // general matrix multiply (a*b + c*alpha)
builder.conv2d(input, filter, options) // 2D convolution
builder.convTranspose2d(...)           // transposed convolution

// Pooling
builder.averagePool2d(input, options)
builder.maxPool2d(input, options)
builder.globalAveragePool(input)

// Normalization
builder.batchNormalization(input, mean, variance, options)
builder.instanceNormalization(input, options)
builder.layerNormalization(input, options)

// Activation
builder.relu(x)
builder.sigmoid(x)
builder.tanh(x)
builder.leakyRelu(x, options)
builder.softmax(x, axis)
builder.gelu(x)

// Tensor manipulation
builder.reshape(x, newShape)
builder.transpose(x, options)
builder.concat(inputs, axis)
builder.split(x, splits, axis)
builder.pad(x, beginningPadding, endingPadding, options)
builder.slice(x, starts, sizes)
builder.gather(input, indices, options)

// Recurrent
builder.lstm(input, weight, bias, hidden, cellState, options)
builder.gru(input, weight, bias, initialHiddenState, options)

// Misc
builder.clamp(x, options)     // min/max clamp
builder.cast(x, type)         // dtype cast
builder.argMax(x, axis, ...)
builder.argMin(x, axis, ...)
builder.constant(descriptor, data)
builder.input(name, descriptor)
```

### Full MobileNet-style Inference

```js
async function buildMobileNetGraph(builder, weights) {
  const input = builder.input('input', { dataType: 'float32', dimensions: [1, 224, 224, 3] });
  
  // Conv -> BN -> ReLU block
  function convBnRelu(x, w, b, mean, variance, gamma, beta, stride = 1) {
    const conv = builder.conv2d(x, builder.constant(w.desc, w.data), {
      padding: [1, 1, 1, 1], strides: [stride, stride], inputLayout: 'nhwc', filterLayout: 'ohwi'
    });
    const bn = builder.batchNormalization(conv, builder.constant(mean.desc, mean.data),
      builder.constant(variance.desc, variance.data), {
        scale: builder.constant(gamma.desc, gamma.data),
        bias: builder.constant(beta.desc, beta.data)
      });
    return builder.relu(bn);
  }
  
  // ... build layers ...
  const logits = /* final dense layer */ null;
  const output = builder.softmax(logits, 1);
  
  return builder.build({ output });
}
```

---

## 6. WebAssembly 3.0 Features

### Feature Detection

```js
import { wasmFeatureDetect } from 'wasm-feature-detect';

const features = {
  simd: await wasmFeatureDetect.simd(),
  relaxedSimd: await wasmFeatureDetect.relaxedSimd(),
  threads: await wasmFeatureDetect.threads(),
  gc: await wasmFeatureDetect.gc(),
  memory64: await wasmFeatureDetect.memory64(),
  tailCall: await wasmFeatureDetect.tailCall(),
  exceptionHandling: await wasmFeatureDetect.exceptionHandling(),
  multiMemory: await wasmFeatureDetect.multiMemory(),
};

console.log('Wasm 3.0 support:', features);
```

### Loading and Instantiation

```js
// Streaming compilation (fastest)
const module = await WebAssembly.compileStreaming(fetch('/module.wasm'));
const instance = await WebAssembly.instantiate(module, importObject);

// With error handling and fallback
async function loadWasm(url, imports = {}) {
  try {
    const { instance } = await WebAssembly.instantiateStreaming(fetch(url), imports);
    return instance.exports;
  } catch (e) {
    // Fallback: fetch then compile
    const bytes = await fetch(url).then(r => r.arrayBuffer());
    const { instance } = await WebAssembly.instantiate(bytes, imports);
    return instance.exports;
  }
}
```

### Memory Management

```js
// Create memory (optionally shared for threads)
const memory = new WebAssembly.Memory({
  initial: 256,    // 256 pages = 16MB
  maximum: 16384,  // 1GB max
  shared: true     // requires COOP/COEP headers
});

// Memory64 (Wasm 3.0) - for large data
const memory64 = new WebAssembly.Memory({
  initial: 256n,   // BigInt for 64-bit
  maximum: 65536n,
  index: 'i64'     // 64-bit addressing
});

// Access from JS
const heap = new Float32Array(memory.buffer);
heap[0] = 3.14;  // Write to Wasm memory
```

### Threading

```js
// main.js
const sharedMemory = new WebAssembly.Memory({ initial: 10, shared: true });
const sharedBuffer = sharedMemory.buffer;

// Start workers
for (let i = 0; i < 4; i++) {
  const worker = new Worker('worker.js');
  worker.postMessage({ memory: sharedMemory, workerId: i });
}

// worker.js
self.onmessage = async ({ data: { memory, workerId } }) => {
  const { instance } = await WebAssembly.instantiate(wasmModule, {
    env: { memory }
  });
  instance.exports.computeChunk(workerId);
};
```

### Wasm GC — Kotlin Wasm Example

```kotlin
// Kotlin code compiles to Wasm with GC support
@JsExport
fun processData(items: List<String>): String {
    return items.filter { it.isNotBlank() }
               .map { it.trim().uppercase() }
               .joinToString(", ")
}
```

```bash
# Build with Kotlin/Wasm
./gradlew wasmJsBrowserDistribution
```

---

## 7. Toolchain Recipes

### Emscripten (C/C++)

```bash
# Install
git clone https://github.com/emscripten-core/emsdk.git
./emsdk install latest && ./emsdk activate latest
source ./emsdk_env.sh

# Basic compile
emcc -O3 -s WASM=1 -s EXPORTED_FUNCTIONS='["_myFunc"]' \
     -s EXPORTED_RUNTIME_METHODS='["cwrap"]' \
     -o output.js input.c

# With WebGPU support
emcc -O3 -s WASM=1 \
     --use-port=emdawnwebgpu \
     -s ASYNCIFY=1 \
     -o app.html app.cpp

# With threads (requires COOP/COEP)
emcc -O3 -s WASM=1 -s USE_PTHREADS=1 \
     -s PTHREAD_POOL_SIZE=4 \
     -o app.js app.cpp
```

### wasm-pack (Rust)

```bash
# Install
cargo install wasm-pack

# Build for browser
wasm-pack build --target web --release

# Build for bundlers (webpack/vite)
wasm-pack build --target bundler --release

# Build for Node.js
wasm-pack build --target nodejs --release

# Output: pkg/ directory with .wasm, .js, .d.ts files
```

### wasm-opt (optimization)

```bash
# Optimize WASM binary (often 20-30% size reduction)
npm install -g binaryen
wasm-opt -O3 --enable-simd input.wasm -o output.wasm
```

### Vite + Rust/Wasm

```js
// vite.config.js
import { defineConfig } from 'vite';
import wasm from 'vite-plugin-wasm';
import topLevelAwait from 'vite-plugin-top-level-await';

export default defineConfig({
  plugins: [wasm(), topLevelAwait()],
  server: {
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    }
  }
});
```

---

## 8. WASM ↔ WebGPU Interop

### Emscripten + WebGPU (C++)

```cpp
// app.cpp
#include <webgpu/webgpu_cpp.h>
#include <emscripten.h>

wgpu::Device device;
wgpu::Queue queue;

extern "C" {
  void EMSCRIPTEN_KEEPALIVE runCompute(float* data, int size) {
    wgpu::BufferDescriptor bufDesc{};
    bufDesc.size = size * sizeof(float);
    bufDesc.usage = wgpu::BufferUsage::Storage | wgpu::BufferUsage::CopyDst;
    auto buffer = device.CreateBuffer(&bufDesc);
    queue.WriteBuffer(buffer, 0, data, bufDesc.size);
    // ... dispatch compute shader
  }
}
```

```bash
emcc -O2 app.cpp --use-port=emdawnwebgpu -s ASYNCIFY=1 -o app.js
```

### Rust + wgpu

```rust
// Access WebGPU through wgpu Rust library (compiles to WASM)
use wgpu;

pub async fn run_compute(data: &[f32]) -> Vec<f32> {
    let instance = wgpu::Instance::default();
    let adapter = instance.request_adapter(&Default::default()).await.unwrap();
    let (device, queue) = adapter.request_device(&Default::default(), None).await.unwrap();
    
    let buffer = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: None,
        contents: bytemuck::cast_slice(data),
        usage: wgpu::BufferUsages::STORAGE | wgpu::BufferUsages::COPY_SRC,
    });
    
    // ... dispatch and read back
    vec![]
}
```

---

## 9. Performance Patterns

### Minimize JS↔Wasm Boundary Crossings

```js
// ❌ BAD: Many small calls
for (let i = 0; i < 10000; i++) {
  wasmModule.processItem(i);
}

// ✅ GOOD: Single call with typed array
const inputArray = new Float32Array(10000).fill(0).map((_, i) => i);
const resultPtr = wasmModule.processArray(inputArray);
const result = new Float32Array(wasmModule.memory.buffer, resultPtr, 10000);
```

### GPU Buffer Read-back (async, non-blocking)

```js
// Reading GPU results back to CPU (async)
const readbackBuffer = device.createBuffer({
  size: outputBuffer.size,
  usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
});

const encoder = device.createCommandEncoder();
encoder.copyBufferToBuffer(outputBuffer, 0, readbackBuffer, 0, outputBuffer.size);
device.queue.submit([encoder.finish()]);

// Map buffer asynchronously (don't block main thread)
await readbackBuffer.mapAsync(GPUMapMode.READ);
const result = new Float32Array(readbackBuffer.getMappedRange().slice());
readbackBuffer.unmap();
```

### Pipeline Caching

```js
// Cache compiled pipelines (expensive to create)
const pipelineCache = new Map();

async function getOrCreatePipeline(key, descriptor) {
  if (pipelineCache.has(key)) return pipelineCache.get(key);
  const pipeline = await device.createComputePipelineAsync(descriptor);
  pipelineCache.set(key, pipeline);
  return pipeline;
}
```

### Benchmark WebGPU vs Wasm vs JS

```js
async function benchmark(fn, label, iterations = 100) {
  const start = performance.now();
  for (let i = 0; i < iterations; i++) await fn();
  const elapsed = performance.now() - start;
  console.log(`${label}: ${(elapsed / iterations).toFixed(2)}ms/iter`);
}

await benchmark(() => jsImplementation(data), 'JavaScript');
await benchmark(() => wasmImplementation(data), 'WebAssembly');
await benchmark(() => webgpuImplementation(data), 'WebGPU');
```
