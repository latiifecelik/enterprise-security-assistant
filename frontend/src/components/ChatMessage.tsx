import React, { useState } from "react";
import type { Message, SourceCitation, RetrievedChunk } from "../api/client";
import "./ChatMessage.css";

interface ChatMessageProps {
  message: Message;
}

interface SourceCardProps {
  source: SourceCitation;
  index: number;
}

const SourceCard: React.FC<SourceCardProps> = ({ source, index }) => {
  const [expanded, setExpanded] = useState(false);
  const scoreColor =
    source.score >= 0.4 ? "#3fb950" : source.score >= 0.2 ? "#d29922" : "#8b949e";

  return (
    <div className="source-card" onClick={() => setExpanded(!expanded)}>
      <div className="source-card-header">
        <span className="source-rank">[{index + 1}]</span>
        <span className="source-name">{source.document_name}</span>
        {source.page_number && (
          <span className="source-page">Page {source.page_number}</span>
        )}
        <span className="source-score" style={{ color: scoreColor }}>
          {(source.score * 100).toFixed(0)}% match
        </span>
        <span className="source-expand">{expanded ? "▲" : "▼"}</span>
      </div>
      {expanded && (
        <div className="source-content">
          <p className="source-preview">{source.content}</p>
        </div>
      )}
    </div>
  );
};

interface ContextPanelProps {
  chunks: RetrievedChunk[];
  onClose: () => void;
}

const ContextPanel: React.FC<ContextPanelProps> = ({ chunks, onClose }) => (
  <div className="context-panel">
    <div className="context-panel-header">
      <span>🔍 Retrieved Context ({chunks.length} chunks)</span>
      <button className="context-panel-close" onClick={onClose}>✕</button>
    </div>
    <div className="context-panel-body">
      {chunks.map((chunk, i) => (
        <div key={i} className="context-chunk">
          <div className="context-chunk-meta">
            <span className="context-rank">#{chunk.rank}</span>
            <span className="context-doc">{chunk.document_name}</span>
            {chunk.page_number && (
              <span className="context-page">Page {chunk.page_number}</span>
            )}
            <span className="context-score" style={{
              color: chunk.score >= 0.4 ? "#3fb950" : chunk.score >= 0.2 ? "#d29922" : "#8b949e"
            }}>
              Score: {chunk.score.toFixed(4)}
            </span>
          </div>
          <p className="context-text">{chunk.content}</p>
        </div>
      ))}
    </div>
  </div>
);

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [showContext, setShowContext] = useState(false);
  const isAssistant = message.role === "assistant";
  const meta = message.retrieval_meta;

  // Format markdown-style bold text in the answer
  const formatContent = (text: string) => {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className={`message-row ${isAssistant ? "assistant" : "user"}`}>
      <div className="message-avatar">
        {isAssistant ? "🛡️" : "👤"}
      </div>
      <div className="message-body">
        <div className={`message-bubble ${isAssistant ? "assistant-bubble" : "user-bubble"}`}>
          <div className="message-content">
            {isAssistant
              ? <>{formatContent(message.content)}</>
              : message.content
            }
          </div>

          {/* Mock warning */}
          {isAssistant && (meta?.provider_info as Record<string, unknown>)?.is_mock === true && (
            <div className="message-mock-warning">
              ⚠️ Development Mock Provider — not real AI inference
            </div>
          )}

          {/* Low confidence warning */}
          {isAssistant && meta?.low_confidence && (meta?.provider_info as Record<string, unknown>)?.is_mock !== true && (
            <div className="message-low-confidence">
              ⚠️ Low knowledge-base confidence — limited supporting documents found
            </div>
          )}
        </div>

        {/* Sources */}
        {isAssistant && meta?.sources && meta.sources.length > 0 && (
          <div className="message-sources">
            <div className="sources-header">
              <span>📎 Sources ({meta.sources.length})</span>
              <button
                className="view-context-btn"
                onClick={() => setShowContext(!showContext)}
              >
                {showContext ? "Hide" : "View"} Retrieved Context
              </button>
            </div>
            <div className="sources-list">
              {meta.sources.map((src, i) => (
                <SourceCard key={i} source={src} index={i} />
              ))}
            </div>
          </div>
        )}

        {/* Retrieved Context panel */}
        {showContext && meta?.sources && meta.sources.length > 0 && (
          <ContextPanel
            chunks={meta.sources as unknown as RetrievedChunk[]}
            onClose={() => setShowContext(false)}
          />
        )}

        {/* Retrieval stats */}
        {isAssistant && meta?.retrieval_stats && (
          <div className="message-stats">
            <span>⏱ {meta.retrieval_stats.total_ms}ms</span>
            <span>📄 {meta.retrieval_stats.chunk_count} chunks retrieved</span>
            <span>🎯 Best score: {(meta.retrieval_stats.best_score * 100).toFixed(0)}%</span>
            <span>🤖 {(meta.provider_info as any)?.provider ?? "AI"}</span>
          </div>
        )}
      </div>
    </div>
  );
};
