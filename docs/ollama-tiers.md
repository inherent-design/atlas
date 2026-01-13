# Ollama Model Tiers: Hardware-Based Selection Guide

**Version:** 1.0
**Date:** 2026-01-06
**Purpose:** Help users select optimal Ollama models based on available VRAM

---

## Overview

Atlas uses a tiered approach to Ollama model selection, automatically recommending models based on your available VRAM. This document explains the tier system, provides model recommendations per capability, and includes quantization guidance for optimal memory usage.

### What Are Tiers?

Tiers group models by VRAM requirements, from ultra-lightweight (<1GB) to frontier-scale (32GB+). Each tier includes recommended models for specific capabilities:

- **text-completion**: General text generation and reasoning
- **code-completion**: Code generation and understanding
- **json-completion**: Structured output generation (includes QNTM key generation)
- **text-embedding**: Semantic search and RAG applications
- **extended-thinking**: Complex multi-step reasoning (DeepSeek-R1 family)

### Tier Summary

| Tier       | VRAM Range | Best For                                    | Example Models                               |
| ---------- | ---------- | ------------------------------------------- | -------------------------------------------- |
| **Tier 1** | <1GB       | Classification, embedded systems, QNTM keys | qwen2.5-coder:0.5b (398MB)                   |
| **Tier 2** | 1-4GB      | Edge deployment, mobile devices             | ministral-3:3b (1.8GB)                       |
| **Tier 3** | 4-8GB      | General purpose, balanced performance       | mistral:7b (4.4GB), qwen2.5-coder:7b (4.7GB) |
| **Tier 4** | 8-16GB     | Complex reasoning, production code          | deepseek-r1:14b (8GB), phi4:14b (9GB)        |
| **Tier 5** | 16-32GB    | Maximum quality, complex codebases          | qwen2.5-coder:32b (20GB)                     |
| **Tier 6** | 32GB+      | Frontier capability, research               | llama3.3:70b (43GB), deepseek-r1:70b (40GB)  |

---

## Tier Details

### Tier 1: Ultra-Lightweight (<1GB VRAM)

**Best for:** Classification, QNTM key generation, embedded systems, IoT devices

#### LLM Models

- `qwen2.5-coder:0.5b` (398MB) - Code-aware, surprisingly capable for size
- `tinyllama:1.1b` (700MB) - Quick prototyping, rapid iteration
- `smollm2:360m` (250MB) - Extreme edge deployment

#### Embedding Models

- `all-minilm:l6-v2` (46MB, 384 dims) - Fast semantic similarity
- `snowflake-arctic-embed:xs` (44MB, 384 dims) - Production-tested retrieval

#### Recommended Configuration

```typescript
{
  'json-completion': 'qwen2.5-coder:0.5b',  // QNTM key generation
  'text-embedding': 'all-minilm:l6-v2',     // Semantic search
}
```

#### Use Cases

- QNTM key generation (semantic compression)
- Lightweight classification tasks
- Embedded systems with minimal resources
- Quick prototyping and testing
- Edge devices with <1GB VRAM

---

### Tier 2: Small (1-4GB VRAM)

**Best for:** General text generation, edge deployment, mobile devices

#### LLM Models

- `ministral-3:3b` (1.8GB) - Mistral's lightweight model, good quality/size ratio
- `phi3:3.8b` (2.3GB) - Microsoft's efficient reasoning model
- `gemma2:2b` (1.6GB) - Google's conversational model
- `qwen2.5-coder:1.5b` (986MB) - Lightweight code completion

#### Embedding Models

- `nomic-embed-text` (262MB, 768 dims) - Most popular, 48.9M pulls
- `granite-embedding:30m` (60MB) - IBM's English-only model

#### Recommended Configuration

```typescript
{
  'text-completion': 'ministral-3:3b',
  'json-completion': 'ministral-3:3b',      // Also handles QNTM
  'text-embedding': 'nomic-embed-text',
}
```

#### Use Cases

- Edge devices with limited VRAM
- Mobile deployment (tablets, high-end phones)
- General text generation tasks
- Lightweight code completion
- Development environments with resource constraints

---

### Tier 3: Medium (4-8GB VRAM)

**Best for:** Code generation, general purpose, balanced performance

#### LLM Models

- `mistral:7b` (4.4GB) - Fast iterations, function calling, general purpose
- `qwen2.5-coder:7b` (4.7GB) - Strong code generation, 92+ languages
- `deepseek-r1:8b` (4.5GB) - Reasoning specialist, chain-of-thought
- `llama3.1:8b` (4.1GB) - Meta's general purpose, instruction following
- `qwen3:8b` (4.5GB) - Agentic workflows, tool integration

#### Embedding Models

- `mxbai-embed-large` (670MB, 1024 dims) - MTEB 64.68, SOTA for size
- `bge-large` (639MB, 1024 dims) - MTEB 63.98, English-focused

#### Recommended Configuration

```typescript
{
  'text-completion': 'llama3.1:8b',
  'code-completion': 'qwen2.5-coder:7b',
  'json-completion': 'mistral:7b',          // Also handles QNTM
  'text-embedding': 'mxbai-embed-large',
}
```

#### Use Cases

- Development machines (most common tier)
- Code generation and debugging
- General purpose AI assistant
- RAG applications with quality embeddings
- Multi-language code projects
- Function calling and tool use

#### Notes

- **Sweet spot for most users**: 7-8B models offer excellent quality without excessive VRAM
- RTX 3060 12GB, RTX 4060 Ti 16GB ideal for this tier
- Can run two models simultaneously (e.g., LLM + embedding)

---

### Tier 4: Large (8-16GB VRAM)

**Best for:** Complex reasoning, production code generation, enterprise applications

#### LLM Models

- `deepseek-r1:14b` (8GB) - Strong reasoning, distilled from 671B model
- `phi4:14b` (9GB) - Microsoft's reasoning + function calling, low latency
- `qwen2.5-coder:14b` (9GB) - Production-quality code generation
- `deepseek-coder-v2:16b` (9GB) - 160K context, 300+ languages

#### Embedding Models

- `bge-m3` (1.06GB, 1024 dims) - Multilingual, 8192 token context
- `qwen3-embedding:0.6b` (1.2GB) - Code + multilingual, 32K context

#### Recommended Configuration

```typescript
{
  'text-completion': 'deepseek-r1:14b',
  'code-completion': 'qwen2.5-coder:14b',
  'extended-thinking': 'deepseek-r1:14b',   // Multi-step reasoning
  'text-embedding': 'bge-m3',
}
```

#### Use Cases

- Complex multi-step reasoning tasks
- Production code generation
- Enterprise applications
- Long-context understanding (160K tokens with deepseek-coder-v2)
- Agentic workflows requiring extended thinking
- Software engineering agents

#### Notes

- RTX 4070 Ti Super 16GB, RTX 4080 16GB recommended
- Can run LLM + embedding model simultaneously
- DeepSeek-R1 14B approaches GPT-4 class reasoning

---

### Tier 5: XL (16-32GB VRAM)

**Best for:** Maximum quality, complex codebases, frontier-adjacent performance

#### LLM Models

- `qwen2.5-coder:32b` (20GB) - Code repair, architecture understanding
- `codellama:34b` (19GB) - Meta's production code generation
- `deepseek-r1:32b` (18GB) - Advanced reasoning approaching O1-mini
- `gemma2:27b` (16GB) - Outperforms models 2x its size

#### Embedding Models

- `qwen3-embedding:4b` (8GB) - 32K context, MTEB top tier

#### Recommended Configuration

```typescript
{
  'code-completion': 'qwen2.5-coder:32b',
  'extended-thinking': 'deepseek-r1:32b',
  'text-embedding': 'qwen3-embedding:4b',
}
```

#### Use Cases

- Complex codebase understanding
- Code repair and refactoring at scale
- Advanced reasoning requiring extended thinking
- Research and frontier experimentation
- Multi-file code generation
- Repository-scale semantic search (32K context)

#### Notes

- RTX 4090 24GB can handle 20GB model + small embedding model
- May require splitting VRAM between model + context cache
- Consider 32GB cards (A6000, RTX 6000 Ada) for comfortable headroom

---

### Tier 6: XXL (32GB+ VRAM)

**Best for:** Frontier capability, research, maximum quality requirements

#### LLM Models

- `llama3.3:70b` (43GB) - Matches Llama 3.1 405B performance, 128K context
- `qwen3:70b` (40GB) - Agentic workflows at maximum quality
- `deepseek-r1:70b` (40GB) - Frontier reasoning approaching O3 level
- `mistral-large:123b` (70GB) - Multimodal MoE, enterprise workloads

#### Embedding Models

- `qwen3-embedding:8b` (16GB) - MTEB multilingual #1 (70.58 score)

#### Recommended Configuration

```typescript
{
  'text-completion': 'llama3.3:70b',
  'code-completion': 'qwen3:70b',
  'extended-thinking': 'deepseek-r1:70b',
  'text-embedding': 'qwen3-embedding:8b',
}
```

#### Use Cases

- State-of-the-art AI research
- Frontier reasoning tasks
- Maximum quality requirements
- Enterprise applications where cost < quality
- Multimodal applications (Mistral Large)
- Multilingual semantic search at scale

#### Hardware Requirements

- Single GPU: RTX 6000 Ada 48GB, A6000 48GB, H100 80GB
- Multi-GPU: 2x RTX 4090 (48GB total), 2x A40 (96GB total)
- Consider A100 80GB for single-card 70B deployment

#### Notes

- 70B models require 40-43GB VRAM (Q4_K_M quantization)
- May need GPU pooling or CPU offloading for 43GB+ models on 48GB cards
- 123B models (Mistral Large) require 70GB minimum

---

## Quantization Guide

### Understanding Quantization

Quantization reduces model size by using fewer bits per weight. Atlas uses **Q4_K_M** as the default, offering the best balance of quality and size.

### Quantization Types

| Type       | Bits   | Memory Multiplier | Quality vs FP16 | Speed     | Recommendation              |
| ---------- | ------ | ----------------- | --------------- | --------- | --------------------------- |
| **FP16**   | 16-bit | 1.0x              | 100% (baseline) | Slowest   | Maximum quality only        |
| **Q8_0**   | 8-bit  | ~0.5x             | 99%             | Fast      | Near-original quality       |
| **Q6_K**   | 6-bit  | ~0.38x            | 97%             | Faster    | High quality + efficiency   |
| **Q5_K_M** | 5-bit  | ~0.34x            | 95%             | Faster    | Balanced quality/size       |
| **Q4_K_M** | 4-bit  | ~0.29x            | 92%             | Fastest   | **Default (best balance)**  |
| **Q3_K**   | 3-bit  | ~0.19x            | 85%             | Very fast | ⚠️ Significant quality loss |
| **Q2_K**   | 2-bit  | ~0.13x            | 70%             | Extreme   | ❌ Avoid                    |

### Memory Calculation Formula

**Base model VRAM:**

```
VRAM (GB) ≈ Parameters (B) × Quantization Multiplier

For Q4_K_M (default):
VRAM (GB) ≈ Parameters (B) × 0.57
```

**Examples:**

- 7B Q4_K_M: `7 × 0.57 ≈ 4.0 GB`
- 14B Q4_K_M: `14 × 0.57 ≈ 8.0 GB`
- 32B Q4_K_M: `32 × 0.57 ≈ 18.2 GB`
- 70B Q4_K_M: `70 × 0.57 ≈ 40 GB`

**Total VRAM needed:**

```
Total = Model Memory + KV Cache + Overhead

KV Cache (context-dependent):
- 8B @ 32K context (FP16): ~4.5 GB
- 8B @ 32K context (Q8_0 cache): ~2.3 GB
- 8B @ 32K context (Q4_0 cache): ~1.5 GB

Overhead:
- Add ~10-15% for processing
```

### Quantization Trade-offs

**Q4_K_M → Q5_K_M:**

- +15-20% VRAM
- +3% quality
- Decision: Usually not worth it (diminishing returns)

**Q5_K_M → Q8_0:**

- +50% VRAM
- +4% quality
- Decision: Worth it for final production deployment with VRAM headroom

**Q8_0 → FP16:**

- +100% VRAM
- +1% quality
- Decision: Rarely worth it (2x VRAM for minimal gain)

### Recommendations by Use Case

**Development/Prototyping:** Q4_K_M (fast iteration, good quality)
**Production (VRAM available):** Q5_K_M or Q8_0 (minimal quality loss)
**Resource-constrained:** Q4_K_M (avoid Q3/Q2)
**Maximum quality:** Q8_0 (skip FP16 unless abundant VRAM)

### What to Avoid

❌ **Q3_K and Q2_K**: Severe quality degradation, coherence loss
❌ **FP16**: 2x memory for <1% quality gain (only for research/benchmarking)

---

## Embedding Model Selection

### General Text Embedding (RAG, Semantic Search)

**Best balance (quality/speed/memory):**

1. **nomic-embed-text** (262MB, 768 dims, MTEB 53.01) - 48.9M pulls, very fast
2. **mxbai-embed-large** (670MB, 1024 dims, MTEB 64.68) - SOTA for size
3. **bge-large** (639MB, 1024 dims, MTEB 63.98) - English-only

**Budget option (extreme constraints):**

- **all-minilm:l6-v2** (46MB, 384 dims) - Very fast, acceptable quality
- **snowflake-arctic-embed:xs** (44MB, 384 dims) - Production-optimized

**Quality priority (VRAM available):**

- **bge-m3** (1.06GB, 1024 dims, 8192 context) - Multilingual, long context
- **qwen3-embedding:8b** (16GB, MTEB 70.58) - Multilingual #1

### Code Embedding & Technical Documentation

**Specialized code models:**

1. **jina-embeddings-v2-base-code** (768 dims, 8192 context) - 30 languages, 150M code pairs
2. **qwen3-embedding:4b/8b** (32K context) - Programming languages + multilingual

**Code-aware general models:**

1. **embeddinggemma** (<200MB with quantization) - Trained on code/technical docs
2. **qwen3-embedding** series - Explicit code retrieval optimization

### Multilingual Embedding

**Best multilingual models:**

1. **qwen3-embedding:8b** (16GB) - MTEB multilingual #1 (70.58), 100+ languages
2. **bge-m3** (1.06GB) - 100+ languages, 8192 context
3. **snowflake-arctic-embed2** (1.14GB) - Multilingual without English degradation
4. **embeddinggemma** (<200MB) - 100+ languages, on-device optimized

### Dimension Mapping

Atlas automatically detects embedding dimensions for common Ollama models:

| Model                       | Dimensions | Memory (fp16) |
| --------------------------- | ---------- | ------------- |
| `nomic-embed-text`          | 768        | 262MB         |
| `all-minilm:l6-v2`          | 384        | 46MB          |
| `all-minilm:l12-v2`         | 384        | 66MB          |
| `snowflake-arctic-embed:xs` | 384        | 44MB          |
| `snowflake-arctic-embed:s`  | 384        | 66MB          |
| `snowflake-arctic-embed:m`  | 768        | ~400MB        |
| `snowflake-arctic-embed:l`  | 1024       | 670MB         |
| `snowflake-arctic-embed2`   | 1024       | 1.14GB        |
| `mxbai-embed-large`         | 1024       | 670MB         |
| `bge-m3`                    | 1024       | 1.06GB        |
| `bge-large`                 | 1024       | 639MB         |
| `embeddinggemma`            | 768        | <200MB        |
| `qwen3-embedding:0.6b`      | (auto)     | 1.2GB         |
| `qwen3-embedding:4b`        | (auto)     | 8GB           |
| `qwen3-embedding:8b`        | (auto)     | 16GB          |

**Note:** Unknown models default to 768 dimensions (nomic-embed-text standard).

---

## Hardware Recommendations

### VRAM Tier → GPU Mapping

| Available VRAM | GPU Examples                  | Recommended Tier | Typical Models                        |
| -------------- | ----------------------------- | ---------------- | ------------------------------------- |
| **4-6GB**      | RTX 3050, RTX 3060            | Tier 2-3         | ministral-3:3b, mistral:7b            |
| **8-12GB**     | RTX 3060 Ti, RTX 4060 Ti      | Tier 3-4         | qwen2.5-coder:7b, deepseek-r1:8b      |
| **12-16GB**    | RTX 4070 Ti, RTX 4060 Ti 16GB | Tier 3-4         | phi4:14b, qwen2.5-coder:14b           |
| **16-24GB**    | RTX 4080, RTX 4090            | Tier 4-5         | deepseek-r1:32b, qwen2.5-coder:32b    |
| **24GB**       | RTX 4090, A5000               | Tier 5           | qwen2.5-coder:32b (comfortable)       |
| **32-48GB**    | RTX 6000 Ada, A6000           | Tier 5-6         | llama3.3:70b, deepseek-r1:70b         |
| **64GB+**      | 2x RTX 4090, A100 80GB        | Tier 6+          | deepseek-coder-v2:236b, llama3.1:405b |

### System RAM Requirements

**Minimum RAM = Model VRAM × 1.5**

When VRAM overflows to system RAM, expect **5-30x slowdown**.

**Examples:**

- 7B Q4_K_M (4GB VRAM) → 6GB+ system RAM recommended
- 70B Q4_K_M (40GB VRAM) → 60GB+ system RAM recommended
- Running without GPU: Model size × 2-3 in system RAM

### Performance Expectations

**Full VRAM (no overflow):**

- 7B Q4_K_M: 40+ tokens/s (RTX 3060 12GB)
- 8B Q4_K_M: 35-45 tokens/s (RTX 4060 Ti 16GB)
- 70B Q4_K_M: 15-25 tokens/s (RTX 4090 24GB)

**VRAM overflow (partial RAM usage):**

- 25/36 layers in VRAM: ~5-10x slowdown
- 50% overflow: ~10-20x slowdown
- Full RAM (no GPU): ~20-30x slowdown

---

## Usage Examples

### Basic Model Selection

```bash
# Tier 3 (4-8GB VRAM): General purpose
atlas ingest \
  --llm ollama:mistral:7b \
  --embedding ollama:mxbai-embed-large \
  file.md

# Tier 4 (8-16GB VRAM): Production code
atlas ingest \
  --llm ollama:qwen2.5-coder:14b \
  --embedding ollama:bge-m3 \
  src/

# Tier 1 (ultra-lightweight): QNTM keys only
atlas ingest \
  --llm ollama:qwen2.5-coder:0.5b \
  --embedding ollama:all-minilm:l6-v2 \
  notes.txt
```

### Auto-Pull Behavior

Atlas automatically pulls Ollama models if they don't exist locally:

```bash
# If snowflake-arctic-embed:xs not installed:
atlas ingest --embedding ollama:snowflake-arctic-embed:xs file.md

# Atlas will:
# 1. Detect model not available
# 2. Pull model from Ollama registry (45MB download)
# 3. Auto-detect dimensions (384)
# 4. Create Qdrant collection with correct dimensions
# 5. Proceed with ingestion
```

**Logs will show:**

```
[info] Model not available, attempting to pull... model=snowflake-arctic-embed:xs
[info] Pulling Ollama embedding model model=snowflake-arctic-embed:xs
[info] Embedding model pulled successfully model=snowflake-arctic-embed:xs
```

### Dimension Detection

Atlas automatically detects embedding dimensions for Qdrant collection creation:

```bash
# Automatic dimension detection examples:
atlas ingest --embedding ollama:all-minilm:l6-v2 file.md
# → Creates collection with 384 dimensions

atlas ingest --embedding ollama:mxbai-embed-large file.md
# → Creates collection with 1024 dimensions

atlas ingest --embedding ollama:snowflake-arctic-embed:xs file.md
# → Creates collection with 384 dimensions

atlas ingest --embedding ollama:qwen3-embedding:8b file.md
# → Creates collection with auto-detected dimensions from model
```

**Unknown models default to 768 dimensions** (nomic-embed-text standard).

---

## Model Compatibility Matrix

### Capability → Tier Recommendations

| Capability            | Tier 1             | Tier 2             | Tier 3            | Tier 4            | Tier 5             | Tier 6             |
| --------------------- | ------------------ | ------------------ | ----------------- | ----------------- | ------------------ | ------------------ |
| **json-completion**   | qwen2.5-coder:0.5b | ministral-3:3b     | mistral:7b        | deepseek-r1:14b   | —                  | —                  |
| **text-completion**   | tinyllama:1.1b     | ministral-3:3b     | llama3.1:8b       | deepseek-r1:14b   | —                  | llama3.3:70b       |
| **code-completion**   | qwen2.5-coder:0.5b | qwen2.5-coder:1.5b | qwen2.5-coder:7b  | qwen2.5-coder:14b | qwen2.5-coder:32b  | qwen3:70b          |
| **text-embedding**    | all-minilm:l6-v2   | nomic-embed-text   | mxbai-embed-large | bge-m3            | qwen3-embedding:4b | qwen3-embedding:8b |
| **extended-thinking** | —                  | —                  | deepseek-r1:8b    | deepseek-r1:14b   | deepseek-r1:32b    | deepseek-r1:70b    |

### License Compatibility

**Fully Open (Commercial Use):**

- Apache 2.0: Qwen, Mistral (most), Phi, Gemma, StarCoder2, Granite
- MIT: DeepSeek (all models)

**Commercial with Restrictions:**

- Llama License: Llama 3.x (revenue cap for large companies)

**Commercial License Required:**

- Mistral Commercial: Codestral, Mistral Large

---

## Troubleshooting

### Model Not Found

```bash
Error: Model 'qwen2.5-coder:14b' not found
```

**Solution:** Atlas auto-pulls models. If pull fails:

1. Check Ollama is running: `ollama list`
2. Manually pull: `ollama pull qwen2.5-coder:14b`
3. Check network connectivity (Ollama downloads from registry)

### Wrong Dimensions

```bash
Error: Dimension mismatch: collection expects 768, got 384
```

**Solution:** Collection was created with different embedding model. Either:

1. Drop collection: `atlas ingest --force ...` (re-creates collection)
2. Switch to model matching existing dimensions
3. Create new collection for new embedding model

### VRAM Overflow

```bash
Warning: Model too large, offloading to RAM (slow)
```

**Solution:** Choose smaller model from lower tier, or:

1. Reduce context window: `--context-size 8192` (smaller KV cache)
2. Use Q4_K_M quantization (default, already optimal)
3. Close other GPU applications
4. Upgrade GPU or use multi-GPU setup

### Slow Inference

```bash
Generation taking >5 seconds per token
```

**Check:**

1. Is model fully loaded in VRAM? (use `nvidia-smi` or `ollama ps`)
2. Is model quantized to Q4_K_M? (check `ollama show MODEL`)
3. Are multiple models loaded? (Ollama caches models, may evict if memory tight)
4. Is system RAM being used? (VRAM overflow → 10-30x slowdown)

---

## Advanced Configuration

### Custom Model Selection (config.yml)

```yaml
backends:
  text-completion: ollama:llama3.1:8b
  code-completion: ollama:qwen2.5-coder:14b
  json-completion: ollama:mistral:7b
  text-embedding: ollama:mxbai-embed-large
  extended-thinking: ollama:deepseek-r1:14b

ollama:
  host: http://localhost:11434
  timeout: 300000 # 5 minutes for large model loads
```

### Per-Command Overrides

```bash
# Override for single command
atlas ingest \
  --llm ollama:deepseek-r1:32b \
  --embedding ollama:qwen3-embedding:4b \
  large-codebase/

# Use default config
atlas ingest file.md
```

### Multi-GPU Setup

```bash
# Ollama automatically uses all available GPUs
# Split 70B model across 2x RTX 4090 (48GB total)
ollama run llama3.3:70b

# Force specific GPU (Linux/Unix)
CUDA_VISIBLE_DEVICES=0 ollama serve  # Use GPU 0 only
CUDA_VISIBLE_DEVICES=1 ollama serve  # Use GPU 1 only
CUDA_VISIBLE_DEVICES=0,1 ollama serve  # Use both GPUs
```

---

## Resources

### Official Documentation

- [Ollama Library](https://ollama.com/library) - Browse all available models
- [Ollama Model Tags](https://ollama.com/library/MODEL/tags) - View quantization variants
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md) - Integration guide

### Atlas-Specific Research

- `/Users/zer0cell/.atlas/connector/reports/atlas/ollama-llm-models-2025-12-31.md` - LLM catalog
- `/Users/zer0cell/.atlas/connector/reports/atlas/ollama-embedding-models-2025-12-31.md` - Embedding catalog
- `/Users/zer0cell/.atlas/integrator/reports/atlas/ollama-autopull-2026-01-01.md` - Auto-pull implementation

### External Benchmarks

- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) - Embedding model rankings
- [Aider Benchmark](https://aider.chat/docs/leaderboards/) - Code generation rankings
- [LocalLLM VRAM Calculator](https://localllm.in/blog/interactive-vram-calculator) - Memory planning tool

---

## Quick Reference

### Model Pull Commands

```bash
# Tier 1
ollama pull qwen2.5-coder:0.5b        # 398MB
ollama pull all-minilm:l6-v2          # 46MB

# Tier 2
ollama pull ministral-3:3b            # 1.8GB
ollama pull nomic-embed-text          # 262MB

# Tier 3
ollama pull mistral:7b                # 4.4GB
ollama pull qwen2.5-coder:7b          # 4.7GB
ollama pull mxbai-embed-large         # 670MB

# Tier 4
ollama pull deepseek-r1:14b           # 8GB
ollama pull phi4:14b                  # 9GB
ollama pull bge-m3                    # 1.06GB

# Tier 5
ollama pull qwen2.5-coder:32b         # 20GB
ollama pull deepseek-r1:32b           # 18GB

# Tier 6
ollama pull llama3.3:70b              # 43GB
ollama pull deepseek-r1:70b           # 40GB
ollama pull qwen3-embedding:8b        # 16GB
```

### Dimension Quick Reference

```bash
# 384-dimensional models
all-minilm:l6-v2, snowflake-arctic-embed:xs/s/m

# 768-dimensional models
nomic-embed-text, snowflake-arctic-embed:m, embeddinggemma

# 1024-dimensional models
mxbai-embed-large, bge-m3, bge-large, snowflake-arctic-embed:l/2
```

---

**Last Updated:** 2026-01-06
**Atlas Version:** 0.1.0
**Document Version:** 1.0
