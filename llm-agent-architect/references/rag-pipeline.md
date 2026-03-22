# RAG Pipeline Architecture

Reference file for `llm-agent-architect` skill. Read this when building retrieval-augmented generation systems, document Q&A, knowledge bases, or any system where agents need to query external data.

---

## RAG Pipeline Overview

```
INGESTION (offline)                  QUERYING (online)
─────────────────────────────────    ──────────────────────────────────
Documents                            User Query
    │                                    │
    ▼                                    ▼
Parse + Clean                       Query Understanding
    │                               (expansion, HyDE, decomposition)
    ▼                                    │
Chunk                                    ▼
    │                               Vector Search (dense)
    ▼                                    + BM25 Search (sparse)
Embed                                    │ Hybrid via RRF
    │                                    ▼
    ▼                               Rerank (cross-encoder)
Vector DB                               │
                                         ▼
                                    Context Assembly
                                         │
                                         ▼
                                    LLM Generation
```

---

## Stage 1: Document Ingestion & Parsing

Quality of parsing directly impacts retrieval accuracy. Poorly parsed documents can reduce retrieval accuracy by up to 45%.

**Parser selection by document type:**
| Document Type | Recommended Approach |
|-------------|---------------------|
| Plain text / Markdown | Direct splitting |
| PDFs (text-based) | PDFPlumber, PyMuPDF |
| PDFs (scanned) | OCR → text cleaning pipeline |
| HTML / Web | Trafilatura or Readability, strip nav/ads |
| Tables | Extract as structured data (CSV/JSON), not raw text |
| Code | Preserve syntax structure, split at function/class boundaries |
| Multimodal (images, charts) | Vision model → text description before embedding |

**Pre-processing checklist:**
- [ ] Remove headers, footers, page numbers, navigation elements
- [ ] Normalize whitespace and encoding
- [ ] Detect and handle duplicate documents
- [ ] Add metadata: source URL, document ID, creation date, section hierarchy
- [ ] Preserve document structure signals (headings, section boundaries) — they guide chunking

---

## Stage 2: Chunking Strategy

Chunking is the highest-leverage decision in any RAG pipeline. The wrong strategy creates up to a 9% gap in recall performance.

**The fundamental tension:**
- Smaller chunks (100–256 tokens): Better semantic precision for retrieval
- Larger chunks (512–1024+ tokens): More context for the LLM to reason from

**Start with the recommended default:**
```python
# RecursiveCharacterTextSplitter — good for most text content
chunk_size = 400-512 tokens
chunk_overlap = 10-20% (40-100 tokens)
separators = ["\n\n", "\n", ". ", " ", ""]
```

**When to upgrade your strategy:**
| Situation | Upgrade To |
|-----------|-----------|
| Documents with clear structure (headers) | Structure-aware/recursive splitting |
| Topics revisited across sections | Semantic/cluster chunking |
| Hierarchical content (docs with nested sections) | Hierarchical chunking |
| Dense technical or code content | Token-based splitting respecting syntax |

**Hierarchical chunking (parent-child):** Index small child chunks for precise retrieval, but return the larger parent chunk to the LLM for richer context. This resolves the precision-vs-context tension.

**Important:** A January 2026 systematic analysis found a "context cliff" around 2,500 tokens where response quality drops significantly. Keep chunks well below this limit when assembling final context.

**Cost vs. quality reality:**
- Semantic chunking only improves recall ~3–9% over recursive splitting
- But costs 10x more in compute (requires embedding every sentence to find split points)
- Test whether the improvement justifies the cost for your use case before defaulting to semantic

---

## Stage 3: Embedding Models

Embedding quality sets the ceiling on retrieval performance.

**Model selection:**
| Priority | Model | Notes |
|---------|-------|-------|
| Best quality (2025) | Voyage-3-large | +9.74% over OpenAI, 32K context, $0.06/M tokens |
| Best ecosystem fit | OpenAI text-embedding-3-large | Battle-tested, 256–3072 dim configurable |
| Self-hosted / open | nomic-embed-text-v1, BGE-large | Strong MTEB scores, free to run |

**Practical considerations:**
- Match embedding model between ingestion and query time — NEVER mix models in the same index
- Larger dimensions = better recall but higher storage cost (OpenAI 3072 vs 1024 for Voyage)
- Multi-modal indexes: consider using different embedding models per document type
- Refresh embeddings when the embedding model is upgraded

---

## Stage 4: Vector Database

**Selection guide:**
| Database | Best For | Trade-off |
|---------|---------|----------|
| Pinecone | Managed, zero-ops, production | Highest cost, least control |
| Weaviate | Hybrid search built-in, GraphQL API | Operational complexity |
| Qdrant | Performance, Rust-based, self-hosted | Less ecosystem support |
| Milvus | Extreme scale (billions of vectors) | Heavy infrastructure |
| pgvector | Already using Postgres, low scale | Performance ceilings |

**Critical features to require:**
- Hybrid search support (dense + sparse in one query)
- Metadata filtering (time, source, region, document type)
- Multi-tenancy (namespace isolation per user/org)
- Sub-50ms query latency at your target scale

---

## Stage 5: Retrieval

Never use single-strategy retrieval in production. Always combine multiple signals.

**Hybrid retrieval (required for production):**
```
Dense search (vector similarity)     → High semantic recall
    +
Sparse search (BM25/keyword)         → Catches exact tokens, rare strings, IDs
    =
Reciprocal Rank Fusion (RRF)         → Merges ranked lists optimally
    ↓
Final ranked candidates (top 20–50)
```

**Why hybrid matters:** Vector-only search misses exact token matches (names, codes, rare terms). BM25-only misses semantic equivalents. RRF is the standard fusion method.

**Query-time improvements:**
| Technique | What It Does | When to Use |
|-----------|-------------|------------|
| Query expansion | Add synonyms / related terms | When phrasing mismatch is a problem |
| HyDE | Generate hypothetical answer, embed it, search | When query is very short or abstract |
| Step-back prompting | Rephrase to more general query first | Multi-hop or complex questions |
| Multi-query | Generate 3–5 query variants, merge results | For ambiguous or broad queries |
| Decomposition | Break multi-part question into sub-queries | For questions requiring multiple retrievals |

**Metadata filtering:** Always implement time, source, and category filters. Without them, stale or irrelevant documents pollute results regardless of retrieval quality.

---

## Stage 6: Reranking

Reranking reorders the top-k retrieved candidates using a more expensive but more accurate model. It adds 10–30% precision improvement at a cost of 50–100ms latency.

**Pipeline:**
```
Vector search → top 25 candidates (fast, high recall)
    ↓
Cross-encoder reranker → top 5 candidates (slow, high precision)
    ↓
LLM receives top 5 with full text
```

**Reranker options:**
- Cohere Rerank API (managed, easy)
- cross-encoder/ms-marco-MiniLM (open-source, fast)
- Voyage AI reranker
- LLM-as-reranker (slow but highest quality for high-stakes applications)

**Skip reranking when:** Latency budget is <100ms, query volume is very high, or you already have strong signal from metadata filtering.

---

## Stage 7: Context Assembly & Generation

How you assemble retrieved chunks into the LLM's context significantly affects output quality.

**Context assembly rules:**
1. Sort by relevance score, not document order
2. Deduplicate overlapping chunks (parent-child strategy helps here)
3. Add source metadata to each chunk (document title, date, URL)
4. Stay within token budget — prefer 3–5 high-quality chunks over 10 mediocre ones
5. Don't drop the first or last retrieved item ("lost in the middle" effect is real but manageable)

**Generation prompt template:**
```
You are answering a question based on the provided context.

RULES:
- Answer only from the provided context
- If the context doesn't contain the answer, say so explicitly
- Cite your sources using [Doc N] notation
- Do not hallucinate facts not in the context

CONTEXT:
[Doc 1 - {source} - {date}]: {chunk_text}
[Doc 2 - {source} - {date}]: {chunk_text}
...

QUESTION: {user_query}

ANSWER:
```

---

## Advanced RAG Patterns

**GraphRAG:** Build a knowledge graph (entity-relation extraction) during ingestion. At query time, traverse graph relationships to retrieve contextually connected chunks. Up to 99% search precision for structured domains. High build cost; worth it for domains with dense entity relationships.

**Agentic RAG:** Give an agent a retrieval tool. The agent iteratively retrieves, evaluates sufficiency, and retrieves again until it has enough context. Handles multi-hop questions that single-pass RAG cannot.

**Self-RAG / CRAG:** Add a lightweight judge after retrieval to evaluate whether retrieved context is relevant before passing to generation. Filters irrelevant context before it reaches the LLM.

---

## RAG Evaluation Metrics

Never ship a RAG system without measuring these:

| Metric | What It Measures | How to Compute |
|--------|-----------------|----------------|
| Recall@k | % of relevant docs in top-k | Ground truth labels + retrieval |
| Precision@k | % of top-k that are relevant | Same |
| Groundedness | Does the answer use the context? | LLM-as-judge |
| Context Relevance | Are retrieved chunks relevant to query? | LLM-as-judge |
| Answer Faithfulness | Does the answer contradict the context? | NLI model or LLM-as-judge |
| Latency (p50/p99) | End-to-end query time | Instrumentation |

**Baseline first:** Fix basic retrieval (good embeddings, sensible chunking, metadata) before adding complexity. Measure at each step.

---

## Common RAG Failures

| Failure | Diagnosis | Fix |
|---------|-----------|-----|
| Wrong documents retrieved | Low recall, embedding mismatch | Add hybrid search, tune chunk size |
| Right docs but bad answer | Context assembly issue | Check lost-in-middle, add reranking |
| Hallucination despite good retrieval | Prompt doesn't enforce grounding | Strengthen system prompt rules |
| Slow queries | Missing index, no filtering | Add metadata filters, check vector DB config |
| Stale answers | Index not updated | Implement incremental indexing pipeline |
| Cross-document reasoning fails | No graph connectivity | Consider GraphRAG |
