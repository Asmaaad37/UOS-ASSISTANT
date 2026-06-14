# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Inbound Calling Agent for the University of Sargodha (UOS) — a voice-driven system that handles inbound calls in Urdu/English. Callers speak to the system, which transcribes their speech (STT), classifies intent (NLU), retrieves information from a Neo4j knowledge graph (GraphRAG), generates a response via GPT-4o-mini, and speaks the response back (TTS) via Twilio/SIP.

## Environment Variables

Required in `code/.env`:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<password>
OPENAI_API_KEY=<key>
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_PHONE_NUMBER=<number>
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

## Common Commands

### Python / GraphRAG (code/)
```bash
# Install Python dependencies
pip install neo4j-graphrag openai python-dotenv pdfplumber requests beautifulsoup4 streamlit

# Run the Streamlit RAG demo app
cd code
streamlit run graphrag_app.py

# Run the GraphRAG notebook (Jupyter)
jupyter notebook code/GraphRag.ipynb

# Format Python code
black code/

# Run tests
pytest
```

### Backend — Spring Boot (ca-be/)
```bash
cd ca-be
docker-compose up -d        # Start PostgreSQL + pgvector
./mvnw spring-boot:run      # Run Spring Boot app (Java 21)
```

### RAG Ingestion Service (rag-ingestion-app/)
```bash
cd rag-ingestion-app
./mvnw package
./mvnw spring-boot:run
```

### Android App (uosAssistant/)
Open in Android Studio and run on device/emulator. Requires Google STT/TTS credentials.

## Architecture

### Call Flow
```
Twilio/SIP → STT (Whisper/Google) → NLU (XLM-RoBERTa) → GraphRAG (Neo4j) → GPT-4o-mini → TTS → caller
```

### Module Map

| Directory | Language | Responsibility |
|-----------|----------|----------------|
| `code/` | Python | GraphRAG pipeline, web scraper, data generation scripts |
| `Areeba/` | Python | NLU — intent classification + NER with XLM-RoBERTa |
| `Fatima/` | Python | TTS — OpenAI speech synthesis |
| `Laiba Siraj/` | Python | STT — Whisper fine-tuning for Urdu |
| `ca-be/` | Java/Spring Boot | REST backend with PostgreSQL + pgvector for vector search |
| `rag-ingestion-app/` | Java/Maven | Ingests documents into the vector store |
| `uosAssistant/` | Kotlin/Compose | Android app with RTL Urdu UI and Google STT/TTS |
| `Asmaad/Documents/` | Data | Source CSVs and PDFs used to build the knowledge graph |

### Knowledge Graph (Neo4j + GraphRAG)

The graph is built from UOS documents (`Asmaad/Documents/`). Node types:
- **Academic**: Department, Program, Course, Semester, Faculty
- **Fees**: FeeStructure, FeeComponent, FeeType, StudyMode
- **Admission**: Eligibility, Requirement, Duration, CreditInfo

Building the graph is done inside `code/GraphRag.ipynb`:
1. Connect to Neo4j and clear existing nodes
2. Ingest PDFs (`CS-Prospectus-2025.pdf`, fee/eligibility/regulations PDFs) and CSVs
3. Create 1536-dim vector index (OpenAI `text-embedding-ada-002`)
4. Run hybrid retrieval: vector similarity + graph traversal

`code/GraphRag.py` contains the schema definitions (node/relationship types) used by the notebook.

### NLU Module (`Areeba/`)

Fine-tuned XLM-RoBERTa for Urdu intent classification (admission queries, fee inquiries, program info, etc.) and named entity recognition. The trained model weights are loaded at runtime and called before knowledge graph retrieval to route the query.

### TTS Module (`Fatima/`)

Wraps the OpenAI TTS API. Accepts text, returns an audio stream suitable for Twilio's `<Play>` verb or direct Android playback.

### STT Module (`Laiba Siraj/`)

Fine-tunes OpenAI Whisper on Urdu voice samples. Output is a transcript fed to the NLU module.

### Backend (`ca-be/`)

Spring Boot REST API backed by PostgreSQL with the `pgvector` extension. Provides a `/search` endpoint that performs approximate nearest-neighbor search on stored embeddings. Docker Compose file spins up both the DB and app containers.

## Key Data Files

All source data lives in `Asmaad/Documents/`:
- CSVs: `Curriculum.csv`, `Programs.csv`, `Department.csv`, `Faculty.csv`, `Fee_Structure.csv`, `FeeComponent.csv`, `FeeType.csv`, `StudyMode.csv`, `ProgramDepartment.csv`
- PDFs: `CS-Prospectus-2025.pdf`, `CS_Fee_Structure.pdf`, `CS_Eligibility.pdf`, semester regulation docs

Changes to these files require re-running the ingestion cells in `code/GraphRag.ipynb` to rebuild the knowledge graph.
