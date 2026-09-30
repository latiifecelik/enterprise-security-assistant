import React, { useEffect, useState } from "react";
import { getSystemStatus, downloadModel } from "../api/client";
import type { SystemStatus } from "../api/client";
import "./StatusPage.css";

export const StatusPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [downloadMsg, setDownloadMsg] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const s = await getSystemStatus();
      setStatus(s);
    } catch {
      /* show cached if available */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, 10000); // refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const handleDownloadModel = async () => {
    setDownloading(true);
    setDownloadMsg(null);
    try {
      const result = await downloadModel();
      setDownloadMsg(result.message);
      await load();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Download failed.";
      setDownloadMsg(`Error: ${msg}`);
    } finally {
      setDownloading(false);
    }
  };

  const StatusDot = ({ ok }: { ok: boolean }) => (
    <span className={`status-dot ${ok ? "green" : "red"}`}>●</span>
  );

  if (loading && !status) {
    return (
      <div className="status-page">
        <div className="status-loading">Loading system status…</div>
      </div>
    );
  }

  return (
    <div className="status-page">
      <div className="status-header">
        <h1>System Status</h1>
        <button className="refresh-btn" onClick={load} disabled={loading}>
          {loading ? "Refreshing…" : "↻ Refresh"}
        </button>
      </div>

      <div className="status-grid">
        {/* AI Runtime */}
        <div className="status-card">
          <div className="status-card-header">
            <span className="status-card-icon">🤖</span>
            <span className="status-card-title">AI Runtime</span>
            {status && <StatusDot ok={status.ai.ready} />}
          </div>
          <div className="status-card-body">
            <div className="status-row">
              <span>Provider</span>
              <span className={status?.ai.is_mock ? "text-orange" : "text-primary"}>
                {status?.ai.provider ?? "—"}
              </span>
            </div>
            <div className="status-row">
              <span>Status</span>
              <span className={status?.ai.ready ? "text-green" : "text-muted"}>
                {status?.ai.status_text ?? "Unknown"}
              </span>
            </div>
            {status?.ai.model && (
              <div className="status-row">
                <span>Model</span>
                <span className="text-primary">{status.ai.model}</span>
              </div>
            )}
            {status?.ai.is_mock && (
              <div className="status-warn">
                ⚠️ Development mock provider active — not real AI inference
              </div>
            )}
            {status?.ai.error && (
              <div className="status-error">{status.ai.error}</div>
            )}
            {!status?.ai.ready && !status?.ai.is_mock && (
              <button
                className="download-model-btn"
                onClick={handleDownloadModel}
                disabled={downloading}
              >
                {downloading ? "Downloading…" : "⬇ Download Model"}
              </button>
            )}
            {downloadMsg && (
              <div className="download-msg">{downloadMsg}</div>
            )}
          </div>
        </div>

        {/* Database */}
        <div className="status-card">
          <div className="status-card-header">
            <span className="status-card-icon">🗄️</span>
            <span className="status-card-title">Database</span>
            {status && <StatusDot ok={status.database.connected} />}
          </div>
          <div className="status-card-body">
            <div className="status-row">
              <span>Type</span>
              <span className="text-primary">{status?.database.type ?? "—"}</span>
            </div>
            <div className="status-row">
              <span>Path</span>
              <span className="text-muted">{status?.database.path ?? "—"}</span>
            </div>
            <div className="status-row">
              <span>Status</span>
              <span className={status?.database.connected ? "text-green" : "text-red"}>
                {status?.database.connected ? "Connected" : "Error"}
              </span>
            </div>
          </div>
        </div>

        {/* RAG Retriever */}
        <div className="status-card">
          <div className="status-card-header">
            <span className="status-card-icon">🔍</span>
            <span className="status-card-title">RAG Retriever</span>
            {status && <StatusDot ok={status.retriever.ready} />}
          </div>
          <div className="status-card-body">
            <div className="status-row">
              <span>Algorithm</span>
              <span className="text-primary">{status?.retriever.type ?? "—"}</span>
            </div>
            <div className="status-row">
              <span>Indexed Chunks</span>
              <span className="text-primary">{status?.retriever.chunk_count ?? 0}</span>
            </div>
            <div className="status-row">
              <span>TF-IDF Features</span>
              <span className="text-primary">{status?.retriever.feature_count ?? 0}</span>
            </div>
            <div className="status-row">
              <span>Status</span>
              <span className={status?.retriever.ready ? "text-green" : "text-muted"}>
                {status?.retriever.ready ? "Ready" : "Empty (no documents)"}
              </span>
            </div>
          </div>
        </div>

        {/* Knowledge Base */}
        <div className="status-card">
          <div className="status-card-header">
            <span className="status-card-icon">📚</span>
            <span className="status-card-title">Knowledge Base</span>
            {status && <StatusDot ok={(status.knowledge_base.document_count ?? 0) > 0} />}
          </div>
          <div className="status-card-body">
            <div className="status-row">
              <span>Documents</span>
              <span className="text-primary">{status?.knowledge_base.document_count ?? 0}</span>
            </div>
            <div className="status-row">
              <span>Total Chunks</span>
              <span className="text-primary">{status?.knowledge_base.chunk_count ?? 0}</span>
            </div>
            <div className="status-row">
              <span>Conversations</span>
              <span className="text-primary">{status?.knowledge_base.conversation_count ?? 0}</span>
            </div>
          </div>
        </div>

        {/* Privacy */}
        <div className="status-card full-width">
          <div className="status-card-header">
            <span className="status-card-icon">🔒</span>
            <span className="status-card-title">Privacy & Data Flow</span>
            <span className="badge badge-green">LOCAL MODE</span>
          </div>
          <div className="status-card-body">
            <div className="privacy-grid">
              <div className="privacy-item">
                <span className="privacy-icon">💾</span>
                <div>
                  <div className="privacy-label">Storage</div>
                  <div className="privacy-value">{status?.privacy.storage ?? "Local SQLite"}</div>
                </div>
              </div>
              <div className="privacy-item">
                <span className="privacy-icon">🧠</span>
                <div>
                  <div className="privacy-label">Inference</div>
                  <div className="privacy-value">{status?.privacy.inference ?? "Local / On-device"}</div>
                </div>
              </div>
              <div className="privacy-item">
                <span className="privacy-icon">☁️</span>
                <div>
                  <div className="privacy-label">Cloud LLM</div>
                  <div className="privacy-value text-green">None — all inference is local</div>
                </div>
              </div>
              <div className="privacy-item">
                <span className="privacy-icon">🌐</span>
                <div>
                  <div className="privacy-label">Internet Required</div>
                  <div className="privacy-value">{status?.privacy.internet_required}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
