import React from "react";
import "./AboutPage.css";

export const AboutPage: React.FC = () => (
  <div className="about-page">
    <div className="about-header">
      <span className="about-logo">🛡️</span>
      <h1>Enterprise Security Assistant</h1>
      <p className="about-tagline">
        Privacy-Preserving Enterprise Cybersecurity RAG Assistant
      </p>
      <div className="about-badges">
        <span className="badge badge-green">🔒 LOCAL MODE</span>
        <span className="badge badge-blue">TF-IDF RAG</span>
        <span className="badge badge-purple">Foundry Local</span>
        <span className="badge badge-orange">SQLite</span>
      </div>
    </div>

    <div className="about-grid">
      {/* What it is */}
      <div className="about-card">
        <h2>🎯 What This Is</h2>
        <p>
          An offline AI assistant designed to help enterprise security teams and SOC
          analysts search, investigate, and understand local cybersecurity documentation.
          It uses Retrieval-Augmented Generation (RAG) to ground AI responses
          in your own documents — without sending sensitive data to any cloud service.
        </p>
      </div>

      {/* How RAG works */}
      <div className="about-card">
        <h2>⚙️ How RAG Works</h2>
        <ol className="about-steps">
          <li>You upload a cybersecurity document</li>
          <li>Text is extracted, normalised, and split into chunks</li>
          <li>Chunks are indexed using TF-IDF (scikit-learn)</li>
          <li>Your question is vectorised in the same space</li>
          <li>Cosine similarity ranks the most relevant chunks</li>
          <li>Top-K chunks are injected into the AI prompt as context</li>
          <li>Foundry Local generates a grounded response</li>
          <li>Sources are cited with similarity scores</li>
        </ol>
      </div>

      {/* Architecture */}
      <div className="about-card">
        <h2>🏗️ Five-Layer Architecture</h2>
        <div className="arch-layers">
          {[
            { icon: "🖥️", name: "Layer 1 — Client", desc: "React + TypeScript UI" },
            { icon: "🔌", name: "Layer 2 — Server", desc: "FastAPI REST API" },
            { icon: "🔍", name: "Layer 3 — RAG Pipeline", desc: "TF-IDF + Chunker + Prompt Builder" },
            { icon: "💾", name: "Layer 4 — Data", desc: "SQLite local database" },
            { icon: "🤖", name: "Layer 5 — AI", desc: "Microsoft Foundry Local SDK" },
          ].map((layer) => (
            <div key={layer.name} className="arch-layer">
              <span>{layer.icon}</span>
              <div>
                <div className="arch-layer-name">{layer.name}</div>
                <div className="arch-layer-desc">{layer.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Privacy */}
      <div className="about-card">
        <h2>🔒 Privacy</h2>
        <ul className="about-list">
          <li>✅ Documents stored in local SQLite database</li>
          <li>✅ TF-IDF retrieval runs entirely on-device</li>
          <li>✅ AI inference runs locally via Foundry Local</li>
          <li>✅ No cloud LLM is used during normal operation</li>
          <li>✅ Conversations stored locally in SQLite</li>
          <li>⚠️ Initial model download may require internet access</li>
          <li>⚠️ Network activity during model download is expected</li>
        </ul>
      </div>

      {/* Why TF-IDF */}
      <div className="about-card">
        <h2>📐 Why TF-IDF?</h2>
        <div className="about-compare">
          <div>
            <div className="compare-label green">✅ Advantages</div>
            <ul className="about-list">
              <li>No embedding model required</li>
              <li>Runs entirely on CPU</li>
              <li>Fully interpretable matches</li>
              <li>Fast index build and query</li>
              <li>Works offline immediately</li>
            </ul>
          </div>
          <div>
            <div className="compare-label orange">⚠️ Limitations vs Embeddings</div>
            <ul className="about-list">
              <li>Lexical only — no semantic meaning</li>
              <li>"SSH brute force" ≠ "repeated login"</li>
              <li>Dense embeddings capture context better</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Tech stack */}
      <div className="about-card">
        <h2>🛠️ Technology Stack</h2>
        <div className="tech-grid">
          {[
            { name: "FastAPI", desc: "Python REST backend" },
            { name: "SQLite", desc: "Local database" },
            { name: "scikit-learn", desc: "TF-IDF vectoriser" },
            { name: "pdfplumber", desc: "PDF text extraction" },
            { name: "Foundry Local SDK", desc: "Local AI inference" },
            { name: "React + TypeScript", desc: "Frontend UI" },
            { name: "Vite", desc: "Frontend tooling" },
            { name: "Python 3.13", desc: "Backend runtime" },
          ].map((t) => (
            <div key={t.name} className="tech-item">
              <div className="tech-name">{t.name}</div>
              <div className="tech-desc">{t.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>

    <div className="about-footer">
      Built as a portfolio project demonstrating offline AI, RAG, and cybersecurity tooling.
      All inference is local — no data leaves your machine during normal operation.
    </div>
  </div>
);
