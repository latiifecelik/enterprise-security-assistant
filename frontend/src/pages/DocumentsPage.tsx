import React, { useState, useEffect, useCallback } from "react";
import {
  listDocuments,
  uploadDocument,
  deleteDocument,
} from "../api/client";
import type { Document } from "../api/client";
import "./DocumentsPage.css";

export const DocumentsPage: React.FC = () => {
  const [docs, setDocs] = useState<Document[]>([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const loadDocs = useCallback(async () => {
    try {
      const res = await listDocuments();
      setDocs(res.documents);
      setTotalChunks(res.total_chunks);
    } catch {
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadDocs(); }, [loadDocs]);

  const handleUpload = async (file: File) => {
    setError(null);
    setSuccess(null);
    setUploading(true);
    try {
      const res = await uploadDocument(file);
      setSuccess(
        `✅ "${res.filename}" ingested successfully — ${res.chunk_count} chunks created.`
      );
      await loadDocs();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed.";
      setError(`❌ ${msg}`);
    } finally {
      setUploading(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleUpload(file);
    e.target.value = "";
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleUpload(file);
  };

  const handleDelete = async (id: number, filename: string) => {
    if (!confirm(`Delete "${filename}" and its chunks?`)) return;
    try {
      await deleteDocument(id);
      setSuccess(`Deleted "${filename}".`);
      await loadDocs();
    } catch {
      setError("Failed to delete document.");
    }
  };

  const formatBytes = (b: number) => {
    if (b < 1024) return `${b} B`;
    if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
    return `${(b / 1024 / 1024).toFixed(1)} MB`;
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString("en-US", {
      month: "short", day: "numeric", year: "numeric",
    });

  const FILE_ICONS: Record<string, string> = {
    ".pdf": "📄",
    ".txt": "📝",
    ".md": "📋",
    ".docx": "📃",
  };

  return (
    <div className="docs-page">
      <div className="docs-header">
        <div>
          <h1 className="docs-title">Knowledge Base</h1>
          <p className="docs-subtitle">Upload and manage your cybersecurity documents</p>
        </div>
        <div className="docs-stats">
          <div className="docs-stat">
            <span className="docs-stat-value">{docs.length}</span>
            <span className="docs-stat-label">Documents</span>
          </div>
          <div className="docs-stat">
            <span className="docs-stat-value">{totalChunks}</span>
            <span className="docs-stat-label">Chunks indexed</span>
          </div>
        </div>
      </div>

      {/* Upload zone */}
      <div
        className={`upload-zone ${dragOver ? "drag-over" : ""} ${uploading ? "uploading" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <div className="upload-icon">📤</div>
        <div className="upload-text">
          {uploading
            ? "Processing document…"
            : "Drop a file here, or click to browse"}
        </div>
        <div className="upload-types">Supported: PDF · TXT · MD · DOCX</div>
        <label className="upload-btn">
          {uploading ? "Uploading…" : "Choose File"}
          <input
            type="file"
            accept=".pdf,.txt,.md,.docx"
            onChange={handleFileInput}
            disabled={uploading}
            hidden
          />
        </label>
      </div>

      {/* Status messages */}
      {success && (
        <div className="docs-alert success">
          {success}
          <button onClick={() => setSuccess(null)}>✕</button>
        </div>
      )}
      {error && (
        <div className="docs-alert error">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}

      {/* Document table */}
      <div className="docs-table-wrap">
        {loading ? (
          <div className="docs-loading">Loading documents…</div>
        ) : docs.length === 0 ? (
          <div className="docs-empty">
            <span>📂</span>
            <p>No documents yet. Upload a cybersecurity document to get started.</p>
          </div>
        ) : (
          <table className="docs-table">
            <thead>
              <tr>
                <th>Document</th>
                <th>Type</th>
                <th>Chunks</th>
                <th>Size</th>
                <th>Added</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((doc) => (
                <tr key={doc.id}>
                  <td className="doc-name">
                    <span className="doc-icon">
                      {FILE_ICONS[doc.file_type] ?? "📄"}
                    </span>
                    <span>{doc.title}</span>
                  </td>
                  <td>
                    <span className="badge badge-blue">{doc.file_type}</span>
                  </td>
                  <td className="doc-chunks">{doc.chunk_count}</td>
                  <td className="doc-size">{formatBytes(doc.file_size)}</td>
                  <td className="doc-date">{formatDate(doc.created_at)}</td>
                  <td>
                    <button
                      className="doc-delete-btn"
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      title="Delete document"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
