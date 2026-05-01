# Trading KB - Multimodal Embedding Architecture

## Overview

This system extracts knowledge from YouTube videos using:
- Transcript analysis
- Visual content extraction
- OCR / on-screen text
- LLM understanding
- Vector retrieval in ChromaDB

## Architecture Components

```
Input Layer
    ↓
Browser-based extraction (transcript, frames)
    ↓
Multimodal Fusion (transcript + OCR + visual summary)
    ↓
Embedding Service → LiteLLM Proxy (nv-embedqa-mistral-7b-v2)
    ↓
Vector Storage (ChromaDB)
    ↓
Retrieval + LLM Answering
```

## Configuration

### LiteLLM Proxy

**Currently configured in:** `/home/ml/.hermes/config.yaml`

- Base URL: `http://127.0.0.1:4000`
- Models available:
  - `qwen3-coder-next-awq-4bit` (Qwen - for LLM tasks)
  - `gemma-4-31B-it-AWQ-4bit` (Gemma - for LLM tasks)
  - `nv-embedqa-mistral-7b-v2` (NVIDIA embedding model - **working!**)

### Embedding Service

**File:** `src/embeddings/litellm_embed.py`

#### Key Parameters for NVIDIA Embeddings:
- `input_type`: `passage` (for documents) or `query` (for search queries)
- `encoding_format`: `float`

```python
from embeddings.litellm_embed import LiteLMEmbeddingService

service = LiteLMEmbeddingService()

# Single embedding (passage)
embedding = service.embed("text to embed", input_type="passage")

# Single embedding (query)
embedding = service.embed("What is gradient descent?", input_type="query")

# Batch embeddings
embeddings = service.embed_batch(["text1", "text2", "text3"], input_type="passage")
```

### ChromaDB Vector Store

**File:** `src/embeddings/chroma_store.py`

```python
from embeddings.chroma_store import ChromaVectorStore, SEGMENT_METADATA_SCHEMA

store = ChromaVectorStore()
store.create_collection("trading_kb")

# Add a segment
store.add_segment(
    segment_id="seg_001",
    document="Multimodal summary text",
    metadata={
        "video_id": "test001",
        "chapter": "Introduction",
        "start_sec": 0,
        "end_sec": 60,
        "visual_type": "slide"
    },
    embedding=[0.1, 0.2, ...]  # 4096-dim embedding from NVIDIA model
)
```

## Metadata Schema

Each segment includes:

| Field | Type | Description |
|-------|------|-------------|
| video_id | str | Video identifier |
| video_title | str | Full video title |
| chapter | str | Chapter/section title |
| start_sec | int | Start time in seconds |
| end_sec | int | End time in seconds |
| transcript | str | Transcript text |
| ocr_text | str | OCR from frames |
| visual_type | str | Type: slide, code, demo, speaker, diagram |
| concepts | str | Comma-separated concepts |
| tags | str | Comma-separated tags |
| has_ocr | bool | Whether OCR was extracted |
| summary | str | Multimodal summary text |

## Embedding Input Format

**Best practice:** Create merged multimodal text per segment:

```
Chapter: Choosing the Learning Rate
Time: 08:10-09:02

Transcript:
If the learning rate is too high, the optimization process may overshoot the minimum.

OCR:
learning rate
convergence
overshoot
loss

Visual summary:
A slide shows three loss curves for small, optimal, and large learning rates.

Merged text for embedding:
This segment explains how learning rate affects optimization convergence, 
with a chart showing underpowered progress, stable convergence, and overshooting.
```

**Use `input_type="passage"` for segments**

For search queries, use `input_type="query"`:
```
Query: What is gradient descent?
Query embedding: service.embed("What is gradient descent?", input_type="query")
```

## Current Status

### ✅ Working

1. **ChromaDB Store** - Fully functional
2. **LiteLLM Proxy** - Running on port 4000
3. **Qwen/Gemma LLM Models** - Available via proxy
4. **NVIDIA Embedding Model** - `nv-embedqa-mistral-7b-v2` working with correct parameters
   - Embedding dimension: **4096**
   - Required parameters: `input_type="passage"|"query"`, `encoding_format="float"`

### Fixed Issues

| Issue | Solution |
|-------|----------|
| Embedding returns 404 | Updated `input_type` parameter required by NVIDIA |
| Embedding returns 400 | Added `encoding_format: float` parameter |

## Next Steps

1. **Implement Full Ingestion Pipeline**
   - YouTube URL input → browser extraction
   - Transcribe + capture frames
   - OCR + vision summary
   - Merge multimodal text
   - Embed and store

2. **Build Query Pipeline**
   - User query → embed with `input_type="query"`
   - Search ChromaDB for similar segments
   - Pass context to LLM for answer generation
   - Return timestamped responses with evidence

3. **Integration Tests**
   - End-to-end video processing
   - Query → answer with grounding

## Usage Example

```python
import sys
sys.path.insert(0, '/home/ml/trading_kb/src')

from embeddings.litellm_embed import LiteLMEmbeddingService
from embeddings.chroma_store import ChromaVectorStore

# Initialize services
embedding_service = LiteLMEmbeddingService()
vector_store = ChromaVectorStore()
vector_store.create_collection("trading_kb")

# Process a segment
segment_text = """Chapter: Gradient Descent
Time: 08:10-09:02
Transcript: Learning rate affects convergence...
OCR: learning rate, convergence, overshoot"""

# Embed the text
embedding = embedding_service.embed(segment_text, input_type="passage")

# Store in ChromaDB
vector_store.add_segment(
    segment_id="seg_001",
    document=segment_text,
    metadata={
        "video_id": "video001",
        "chapter": "Gradient Descent",
        "start_sec": 490,
        "end_sec": 542,
        "visual_type": "slide"
    },
    embedding=embedding
)

# Query with embedding
query = "What is gradient descent?"
query_embedding = embedding_service.embed(query, input_type="query")
results = vector_store.query(query_embedding, n_results=5)
```

## API Reference

### LiteLMEmbeddingService

| Method | Description |
|--------|-------------|
| `embed(text, input_type="passage")` | Embed single text string |
| `embed_batch(texts, input_type="passage")` | Embed multiple texts |
| `get_model_info()` | Get model metadata |
| `_check_health()` | Check endpoint availability |

### ChromaVectorStore

| Method | Description |
|--------|-------------|
| `create_collection(name)` | Create/get a collection |
| `add_segment(id, doc, metadata, embedding)` | Add single segment |
| `add_batch(segments)` | Add multiple segments |
| `query(embedding, n_results)` | Search for similar segments |
| `get_segment(id)` | Get single segment |
| `get_stats()` | Get collection statistics |

## Embedding Parameters (NVIDIA nv-embedqa-mistral-7b-v2)

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `input_type` | ✓ | `passage`, `query` | Document type for retrieval |
| `encoding_format` | ✓ | `float` | Output format |
| `model` | ✓ | `nv-embedqa-mistral-7b-v2` | Model name |
| `input` | ✓ | string or list | Text to embed |
