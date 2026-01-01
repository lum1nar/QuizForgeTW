# 📘 QuizForgeTW

[Chinese Version](/README.md)

![demo](./static/demo.png)

**Using agentic RAG technology to effortlessly generate Taiwan-style high school English exam questions. From PDF exam papers to ready-to-use questions, QuizForgeTW integrates intelligence, context, and exam expertise into a single streamlined workflow.**

### ✨ Key Features

- **🧠 Intelligent RAG Decision**
  The system automatically determines whether retrieval is necessary before generation—avoiding wasted prompts or irrelevant information.

- **📄 Exam-Aware Semantic Chunking**
  Uses LLMs to segment content based on exam structure and context, rather than arbitrary fixed-size splits.

- **📚 Grammar- and Exam-Style Retrieval**
  Precisely retrieves questions that match semantic intent and grammatical focus, closely aligned with Taiwan junior and senior high school exam styles.

- **📝 Realistic Exam Question Generation**
  Supports cloze tests, grammar questions, and reading comprehension—generated questions are highly similar to real exams.

- **⚡ Offline Indexing, Online Real-Time Generation**
  All embedding and indexing work is completed offline, enabling fast and stable online question generation.

### 📔 Exam Discriminative Power

Please refer to Question 8 in the [Sample Questions](./demo_output.pdf).  
If a student believes that both options (A) and (B) are correct,  
it indicates that the student has not yet mastered the concept of **non-restrictive relative clauses**.

> Since the question generation process heavily incorporates historical exam archives, the system is able to test students on the **classic trap questions** commonly found in Taiwan junior and senior high school exams.

![Q8](./static/q8.png)

## 🧠 Models Used

| Purpose               | Model                     |
| --------------------- | ------------------------- |
| Chunking & Generation | `gpt-oss:120b` (ncku)     |
| RAG Query Generation  | `gpt-oss:20b` (ncku)      |
| Lightweight Control   | `gemma3:4b` (ncku)        |
| Text Embedding        | `embeddinggemma` (Ollama) |
| Vector Database       | FAISS                     |

## 🏗️ System Workflow Overview

```mermaid
flowchart TD
    %% =========================
    %% Offline: PDF → VectorDB
    %% =========================

    A[PDF Files]
        -->|Extract Raw Text| B[pdfplumber]

    B -->|LLM Intelligent Chunking| C[gpt-oss:120b]

    C -->|Output JSON chunks| D[Chunk Validator]

    D -->|Valid Chunks| E[all_chunks.json]

    E -->|Record Processed PDFs| F[chunked_pdf.json]

    %% Embedding
    E -->|Embed Text + metadata| G[ollama embeddinggamma]

    G -->|Build Vector Index| H[FAISS VectorDB]

    G -->|Backup metadata| I[exam_chunks_meta.json]

    %% =========================
    %% Online: User → Question Generation
    %% =========================

    J[User Request]
        -->|Decide Whether RAG Is Needed| K[gemma3:4b]

    K -->|Not Needed| L[Direct Question Generation]

    K -->|Needed| M[RAG Cloze Query Generator <br> gpt-oss:20b<br>]

    M -->|Query Embedding| N[embeddinggamma]

    N -->|Vector Similarity Search| O[FAISS]

    O -->|Retrieve Relevant Chunks| P[Grammar + metadata]

    P -->|Supplement Reading Queries| Q[RAG Reading Query Generator <br> gpt-oss:20b<br>]

    Q --> |Query Embedding| N

    P -->|Integrate Content to Generate Questions| S[gpt-oss:120b]

    S --> T[Final Exam Questions]
```

## 🚀 Quick Start (Linux)

### 0. System Requirements

- Python 3.12
- [Ollama](https://ollama.com/) (must be installed)
- Ollama model: `embeddinggamma`

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull embeddinggamma
ollama serve
```

### 1. Install Dependencies

```bash
# Optional: create a virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux / Mac
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root directory and fill in the API Key:

```env
# .env
API_KEY=your_api_key_here
```

### 3. Prepare PDFs

```bash
cd pdf
# Put exam PDF files into ./pdf
```

### 4. Offline Chunking & Indexing

```bash
# PDF chunking and organization
python3 chunking.py

# Build vector embeddings
python3 embedding.py
```

### 5. Start the Agent (Server Mode)

```bash
# Start FastAPI / Uvicorn server
uvicorn server:app --host 0.0.0.0 --port 8000
```

- Open a browser and visit: [http://localhost:8000](http://localhost:8000)
- Enter prompts in the frontend to start interacting.

## 📂 Project Structure

```bash
.
├── pdf/                    # Original exam PDFs
├── prompts/                # Prompt templates
├── json/                   # Chunk and metadata outputs
├── exam_chunks.faiss       # FAISS index
├── chunking.py             # Offline chunking
├── embedding.py            # Offline embedding
├── agent.py                # Question generation
├── utils.py
├── server.py               # Local web server
```
