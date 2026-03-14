/**
 * webgpu-compute-demo.js
 *
 * Demonstrates WebGPU compute shaders for tensor operations.
 * Includes feature detection, fallbacks, and performance benchmarking.
 *
 * Usage:
 *   import { WebGPUCompute } from './webgpu-compute-demo.js';
 *   const gpu = await WebGPUCompute.create();
 *   const result = await gpu.relu(new Float32Array([-1, 0, 1, 2, -3]));
 */

// ─────────────────────────────────────────────────────────
// SHADERS
// ─────────────────────────────────────────────────────────

const RELU_SHADER = /* wgsl */ `
@group(0) @binding(0) var<storage, read> input: array<f32>;
@group(0) @binding(1) var<storage, read_write> output: array<f32>;

@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) id: vec3u) {
  let i = id.x;
  if (i >= arrayLength(&input)) { return; }
  output[i] = max(0.0, input[i]);
}
`;

const MATMUL_SHADER = /* wgsl */ `
struct Dimensions {
  M: u32,
  N: u32,
  K: u32,
}

@group(0) @binding(0) var<storage, read> A: array<f32>;  // M x K
@group(0) @binding(1) var<storage, read> B: array<f32>;  // K x N
@group(0) @binding(2) var<storage, read_write> C: array<f32>;  // M x N
@group(0) @binding(3) var<uniform> dims: Dimensions;

@compute @workgroup_size(16, 16)
fn main(@builtin(global_invocation_id) id: vec3u) {
  let row = id.y;
  let col = id.x;
  
  if (row >= dims.M || col >= dims.N) { return; }
  
  var sum = 0.0f;
  for (var k = 0u; k < dims.K; k++) {
    sum += A[row * dims.K + k] * B[k * dims.N + col];
  }
  C[row * dims.N + col] = sum;
}
`;

const SOFTMAX_SHADER = /* wgsl */ `
@group(0) @binding(0) var<storage, read> input: array<f32>;
@group(0) @binding(1) var<storage, read_write> output: array<f32>;
@group(0) @binding(2) var<uniform> length: u32;

var<workgroup> maxVal: atomic<u32>;  // reinterpret as f32
var<workgroup> sumExp: f32;

@compute @workgroup_size(256)
fn main(@builtin(global_invocation_id) gid: vec3u,
        @builtin(local_invocation_id) lid: vec3u) {
  let i = gid.x;
  if (i >= length) { return; }
  
  // Simple (non-workgroup-optimized) softmax for clarity
  // Find max for numerical stability
  var maxV = input[0];
  for (var j = 1u; j < length; j++) {
    maxV = max(maxV, input[j]);
  }
  
  // Sum of exp
  var expSum = 0.0f;
  for (var j = 0u; j < length; j++) {
    expSum += exp(input[j] - maxV);
  }
  
  output[i] = exp(input[i] - maxV) / expSum;
}
`;

// ─────────────────────────────────────────────────────────
// MAIN CLASS
// ─────────────────────────────────────────────────────────

export class WebGPUCompute {
  /** @type {GPUDevice} */
  device = null;
  /** @type {Map<string, GPUComputePipeline>} */
  pipelineCache = new Map();

  /**
   * Create and initialize a WebGPUCompute instance.
   * Throws if WebGPU is not available.
   */
  static async create({ powerPreference = 'high-performance', compatibilityMode = false } = {}) {
    const instance = new WebGPUCompute();
    await instance._init({ powerPreference, compatibilityMode });
    return instance;
  }

  /**
   * Check if WebGPU is available on this device.
   * @returns {{ available: boolean, reason?: string, info?: object }}
   */
  static async checkSupport() {
    if (!navigator.gpu) {
      return { available: false, reason: 'navigator.gpu not present' };
    }
    
    const adapter = await navigator.gpu.requestAdapter();
    if (!adapter) {
      return { available: false, reason: 'No WebGPU adapter found (unsupported GPU)' };
    }
    
    const info = await adapter.requestAdapterInfo();
    const features = [...adapter.features];
    
    return {
      available: true,
      vendor: info.vendor,
      architecture: info.architecture,
      device: info.device,
      hasFloat16: features.includes('shader-f16'),
      hasTimestampQuery: features.includes('timestamp-query'),
      maxBufferSize: adapter.limits.maxBufferSize,
    };
  }

  async _init({ powerPreference, compatibilityMode }) {
    if (!navigator.gpu) throw new Error('WebGPU not supported in this browser');

    const requestOptions = { powerPreference };
    if (compatibilityMode) {
      requestOptions.featureLevel = 'compatibility'; // Chrome 146+, supports OpenGL/D3D11
    }

    const adapter = await navigator.gpu.requestAdapter(requestOptions);
    if (!adapter) throw new Error('Failed to get WebGPU adapter. Try enabling in chrome://flags');

    this.device = await adapter.requestDevice({
      // Request optional features
      requiredFeatures: adapter.features.has('timestamp-query') ? ['timestamp-query'] : [],
    });

    // Handle device loss
    this.device.lost.then(({ reason, message }) => {
      console.error(`WebGPU device lost (${reason}):`, message);
      this.device = null;
    });
  }

  // ─────────────────────────────────────────────────────
  // PIPELINE MANAGEMENT
  // ─────────────────────────────────────────────────────

  async _getPipeline(key, shaderCode) {
    if (this.pipelineCache.has(key)) return this.pipelineCache.get(key);

    const pipeline = await this.device.createComputePipelineAsync({
      layout: 'auto',
      compute: {
        module: this.device.createShaderModule({ code: shaderCode }),
        entryPoint: 'main',
      },
    });

    this.pipelineCache.set(key, pipeline);
    return pipeline;
  }

  // ─────────────────────────────────────────────────────
  // BUFFER HELPERS
  // ─────────────────────────────────────────────────────

  _createStorageBuffer(data, writable = false) {
    const buffer = this.device.createBuffer({
      size: data.byteLength,
      usage: GPUBufferUsage.STORAGE | (writable ? GPUBufferUsage.COPY_SRC : GPUBufferUsage.COPY_DST),
      mappedAtCreation: !writable,
    });

    if (!writable) {
      new Float32Array(buffer.getMappedRange()).set(data);
      buffer.unmap();
    }

    return buffer;
  }

  _createOutputBuffer(size) {
    return this.device.createBuffer({
      size,
      usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_SRC,
    });
  }

  async _readBuffer(buffer, size) {
    const readback = this.device.createBuffer({
      size,
      usage: GPUBufferUsage.COPY_DST | GPUBufferUsage.MAP_READ,
    });

    const encoder = this.device.createCommandEncoder();
    encoder.copyBufferToBuffer(buffer, 0, readback, 0, size);
    this.device.queue.submit([encoder.finish()]);

    await readback.mapAsync(GPUMapMode.READ);
    const result = new Float32Array(readback.getMappedRange().slice());
    readback.unmap();
    readback.destroy();

    return result;
  }

  // ─────────────────────────────────────────────────────
  // COMPUTE OPERATIONS
  // ─────────────────────────────────────────────────────

  /**
   * Apply ReLU activation function: output[i] = max(0, input[i])
   */
  async relu(data) {
    const pipeline = await this._getPipeline('relu', RELU_SHADER);

    const inputBuf = this._createStorageBuffer(data);
    const outputBuf = this._createOutputBuffer(data.byteLength);

    const bindGroup = this.device.createBindGroup({
      layout: pipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: inputBuf } },
        { binding: 1, resource: { buffer: outputBuf } },
      ],
    });

    const encoder = this.device.createCommandEncoder();
    const pass = encoder.beginComputePass();
    pass.setPipeline(pipeline);
    pass.setBindGroup(0, bindGroup);
    pass.dispatchWorkgroups(Math.ceil(data.length / 64));
    pass.end();
    this.device.queue.submit([encoder.finish()]);

    const result = await this._readBuffer(outputBuf, data.byteLength);

    inputBuf.destroy();
    outputBuf.destroy();

    return result;
  }

  /**
   * Matrix multiplication: C = A × B
   * @param {Float32Array} A - Matrix A (M×K, row-major)
   * @param {Float32Array} B - Matrix B (K×N, row-major)
   * @param {number} M - Rows of A
   * @param {number} N - Cols of B
   * @param {number} K - Cols of A / Rows of B
   */
  async matmul(A, B, M, N, K) {
    if (A.length !== M * K) throw new Error(`A size mismatch: expected ${M * K}, got ${A.length}`);
    if (B.length !== K * N) throw new Error(`B size mismatch: expected ${K * N}, got ${B.length}`);

    const pipeline = await this._getPipeline('matmul', MATMUL_SHADER);

    const aBuf = this._createStorageBuffer(A);
    const bBuf = this._createStorageBuffer(B);
    const cBuf = this._createOutputBuffer(M * N * 4);

    const dimsData = new Uint32Array([M, N, K]);
    const dimsBuf = this.device.createBuffer({
      size: dimsData.byteLength,
      usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
      mappedAtCreation: true,
    });
    new Uint32Array(dimsBuf.getMappedRange()).set(dimsData);
    dimsBuf.unmap();

    const bindGroup = this.device.createBindGroup({
      layout: pipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: aBuf } },
        { binding: 1, resource: { buffer: bBuf } },
        { binding: 2, resource: { buffer: cBuf } },
        { binding: 3, resource: { buffer: dimsBuf } },
      ],
    });

    const encoder = this.device.createCommandEncoder();
    const pass = encoder.beginComputePass();
    pass.setPipeline(pipeline);
    pass.setBindGroup(0, bindGroup);
    pass.dispatchWorkgroups(Math.ceil(N / 16), Math.ceil(M / 16));
    pass.end();
    this.device.queue.submit([encoder.finish()]);

    const result = await this._readBuffer(cBuf, M * N * 4);

    aBuf.destroy();
    bBuf.destroy();
    cBuf.destroy();
    dimsBuf.destroy();

    return result;
  }

  /**
   * Softmax: output[i] = exp(input[i]) / sum(exp(input))
   */
  async softmax(data) {
    const pipeline = await this._getPipeline('softmax', SOFTMAX_SHADER);

    const inputBuf = this._createStorageBuffer(data);
    const outputBuf = this._createOutputBuffer(data.byteLength);

    const lenBuf = this.device.createBuffer({
      size: 4,
      usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
      mappedAtCreation: true,
    });
    new Uint32Array(lenBuf.getMappedRange())[0] = data.length;
    lenBuf.unmap();

    const bindGroup = this.device.createBindGroup({
      layout: pipeline.getBindGroupLayout(0),
      entries: [
        { binding: 0, resource: { buffer: inputBuf } },
        { binding: 1, resource: { buffer: outputBuf } },
        { binding: 2, resource: { buffer: lenBuf } },
      ],
    });

    const encoder = this.device.createCommandEncoder();
    const pass = encoder.beginComputePass();
    pass.setPipeline(pipeline);
    pass.setBindGroup(0, bindGroup);
    pass.dispatchWorkgroups(Math.ceil(data.length / 256));
    pass.end();
    this.device.queue.submit([encoder.finish()]);

    const result = await this._readBuffer(outputBuf, data.byteLength);

    inputBuf.destroy();
    outputBuf.destroy();
    lenBuf.destroy();

    return result;
  }

  // ─────────────────────────────────────────────────────
  // BENCHMARK
  // ─────────────────────────────────────────────────────

  async benchmark(size = 1024, iterations = 50) {
    const data = new Float32Array(size).map((_, i) => (i % 10) - 5);
    const results = {};

    // WebGPU ReLU
    await this.relu(data); // warmup
    const gpuStart = performance.now();
    for (let i = 0; i < iterations; i++) await this.relu(data);
    results.webgpu_relu_ms = (performance.now() - gpuStart) / iterations;

    // JavaScript ReLU
    const jsStart = performance.now();
    for (let i = 0; i < iterations; i++) {
      data.map((x) => Math.max(0, x));
    }
    results.js_relu_ms = (performance.now() - jsStart) / iterations;

    results.speedup = results.js_relu_ms / results.webgpu_relu_ms;
    return results;
  }

  destroy() {
    this.device?.destroy();
    this.pipelineCache.clear();
  }
}

// ─────────────────────────────────────────────────────────
// QUICK TEST (run directly in browser console or Node)
// ─────────────────────────────────────────────────────────

if (typeof window !== 'undefined') {
  window.testWebGPU = async () => {
    const support = await WebGPUCompute.checkSupport();
    console.log('WebGPU support:', support);

    if (!support.available) return;

    const gpu = await WebGPUCompute.create();

    // Test ReLU
    const input = new Float32Array([-3, -1, 0, 1, 3]);
    const relu = await gpu.relu(input);
    console.log('ReLU test:', Array.from(relu)); // [0, 0, 0, 1, 3]

    // Test MatMul (2×2 identity)
    const A = new Float32Array([1, 0, 0, 1]);
    const B = new Float32Array([5, 6, 7, 8]);
    const C = await gpu.matmul(A, B, 2, 2, 2);
    console.log('MatMul test:', Array.from(C)); // [5, 6, 7, 8]

    // Benchmark
    const bench = await gpu.benchmark(10000, 20);
    console.log('Benchmark:', bench);

    gpu.destroy();
  };
}
