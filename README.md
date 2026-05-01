# Trading Video Knowledge Base (Graph-first)

A local-first multimodal knowledge base system that converts trading education videos into a structured knowledge graph with GraphRAG capabilities.

## Architecture

```
Raw Trading Videos
    |
    v
Audio/Frame Extraction (ffmpeg, PySceneDetect)
    |
    v
Multimodal Extraction
    |
    |-- Audio -> faster-whisper -> transcript
    |-- Frames -> PaddleOCR -> text
    |-- Frames -> Gemma4 31B -> visual descriptions
    |
    v
Segment Builder (timestamped multimodal chunks)
    |
    v
Knowledge Extraction (Qwen3 Next 80B)
    |
    |-- Entities: Strategy, Concept, Indicator, Rule, Condition
    |-- Relationships: HAS_RULE, USES, SUPPORTS, etc.
    |
    v
Storage
    |
    |-- Neo4j Graph DB
    |-- ChromaDB Vector DB
    |-- SQLite Metadata DB
    |
    v
GraphRAG Agent
    |-- Semantic retrieval
    |-- Graph traversal
    |-- Strategy completeness validation
    |-- Strategy draft generation
    |-- Platform-neutral bot spec
```

## Quick Start

### Prerequisites

- Python 3.10+
- Neo4j (local or remote)
- Ollama for local models (recommended) or any OpenAI-compatible API

### Installation

```bash
# Clone or navigate to the project
cd trading_kb

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Running the System

```bash
# Initialize databases
python scripts/init_db.py

# Ingest a video
python scripts/ingest_video.py --file data/videos/video_001.mp4 --title "RSI Strategy"

# Build knowledge base from ingested video
python scripts/build_kb.py --video-id video_001

# Query the agent
python scripts/query_agent.py --query "Create a bot strategy using RSI divergence and support resistance"
```

## Configuration

Edit `.env` with your settings:

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Ollama/OpenAI-compatible API
QWEN_API_BASE=http://localhost:11434/v1
QWEN_API_KEY=local
QWEN_MODEL=qwen3-next-80b

GEMMA_API_BASE=http://localhost:11434/v1
GEMMA_API_KEY=local
GEMMA_MODEL=gemma4-31b

# Processing settings
FRAME_INTERVAL_SECONDS=5
SEGMENT_MIN_SECONDS=60
SEGMENT_MAX_SECONDS=180
```

## Project Structure

```
trading_kb/
├── README.md
├── .env.example
├── requirements.txt
├── config.yaml
│
├── data/
│   ├── videos/          # Input video files
│   ├── extracted/       # Extracted audio, frames, OCR
│   └── processed/       # Multimodal segments, extracted knowledge
│
├── db/
│   ├── chroma/          # ChromaDB vectors
│   └── metadata.sqlite  # SQLite metadata
│
├── src/
│   ├── main.py
│   ├── config/
│   │   └── settings.py
│   ├── storage/
│   │   ├── sqlite_store.py
│   │   ├── chroma_store.py
│   │   ├── neo4j_store.py
│   │   └── file_store.py
│   ├── ingestion/
│   │   ├── register_video.py
│   │   ├── extract_audio.py
│   │   ├── extract_frames.py
│   │   ├── transcribe_audio.py
│   │   ├── run_ocr.py
│   │   ├── describe_frames.py
│   │   └── build_segments.py
│   ├── extraction/
│   │   ├── knowledge_extractor.py
│   │   └── entity_normalizer.py
│   ├── graph/
│   │   ├── graph_schema.py
│   │   ├── graph_loader.py
│   │   └── graph_queries.py
│   ├── rag/
│   │   ├── vector_retriever.py
│   │   ├── graph_retriever.py
│   │   ├── graphrag_agent.py
│   │   └── completeness_checker.py
│   ├── bot/
│   │   ├── strategy_draft.py
│   │   ├── bot_spec.py
│   │   └── code_generator.py
│   ├── models/
│   │   ├── base.py
│   │   ├── qwen_client.py
│   │   └── gemma_client.py
│   └── prompts/
│       ├── visual_description_prompt.md
│       ├── knowledge_extraction_prompt.md
│       ├── entity_normalization_prompt.md
│       ├── strategy_generation_prompt.md
│       └── bot_spec_prompt.md
│
└── scripts/
    ├── init_db.py
    ├── ingest_video.py
    ├── build_kb.py
    └── query_agent.py
```

## Key Features

- **Local-first**: Runs entirely on your machine
- **Multimodal extraction**: Audio + visual + OCR
- **Graph-first**: Neo4j knowledge graph with relationships
- **GraphRAG**: Combines semantic retrieval with graph traversal
- **Bot-readiness classification**: Knows which rules are machine-executable
- **Completeness validation**: Can't build bots from incomplete strategies

## Development Status

- ✅ Project structure
- 🔄 Phase 1: Core storage and ingestion
- ⏳ Phase 2: Gemma visual descriptions
- ⏳ Phase 3: Qwen extraction
- ⏳ Phase 4: GraphRAG agent
- ⏳ Phase 5: Code generation

## License

Private project - personal use only
