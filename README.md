# Enterprise Security Assistant 🛡️
> **Privacy-Preserving Cybersecurity RAG Assistant Powered by Microsoft Foundry Local**

An on-device, fully offline AI assistant designed for Enterprise Security teams and SOC analysts to investigate incidents, parse internal security policies and playbooks, and conduct threat triage with zero telemetry or cloud dependencies.

---

## 🌟 Key Features

- **100% Offline & Private:** Built with Microsoft Foundry Local SDK (`phi-3.5-mini`). Zero inference data leaves the host workstation.
- **5-Layer Architecture:** Clean decoupling across Client, REST API, RAG Engine, Data Persistence, and Neural Runtime.
- **Instant Retrieval-Augmented Generation (RAG):** Sublinear TF-IDF vectorization with sentence-aware chunking and cosine similarity.
- **Strict Defensive Guardrails:** Rejects off-topic queries (cooking, trivia, etc.) and incoherent noise/gibberish while providing helpful domain reminders.
- **Evidence-Based Grounding:** Hallucination controls force the model to explicitly cite local playbook sources (`[Source 1]`) with similarity confidence metrics.
- **Dark SOC Operations Dashboard:** Built with React 19 + TypeScript, responsive document management, and real-time inference telemetry.

---

## 🏗️ 5-Layer Architecture

```
[ Layer 1: Client ]       React + TypeScript + Vite (Port 5173)
        │
[ Layer 2: Server ]       FastAPI REST Service (Port 8000)
        │
[ Layer 3: RAG Engine ]   Sentence-Aware Chunker + TF-IDF Vectorizer + Guardrail Prompt Builder
        │
[ Layer 4: Data Layer ]   SQLite (WAL Mode) for Documents, Chunks, and Conversations
        │
[ Layer 5: AI Runtime ]   Microsoft Foundry Local SDK (phi-3.5-mini / ONNX CPU Runtime)
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.13)
- **Node.js 18+** & npm
- **Microsoft Foundry Local SDK**

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run Application
Start the backend server:
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend dashboard:
```bash
cd frontend
npm install
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## 📄 License
MIT License. Created for portfolio and educational demonstration.
