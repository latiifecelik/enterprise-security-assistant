// API client — all backend calls live here so they're easy to find and modify.
// We use native fetch() — no extra HTTP library needed.

const API_BASE = "http://127.0.0.1:8000/api";

// ── Types ──────────────────────────────────────────────────────────────────

export interface SourceCitation {
  rank: number;
  chunk_id: number | null;
  document_id: number | null;
  document_name: string;
  document_title: string;
  page_number: number | null;
  score: number;
  content_preview: string;
  content: string;
}

export interface RetrievalStats {
  chunk_count: number;
  best_score: number;
  retrieve_ms: number;
  generate_ms: number;
  total_ms: number;
}

export interface RetrievedChunk {
  rank: number;
  chunk_id: number | null;
  document_id: number | null;
  document_name: string;
  document_title: string;
  chunk_index: number;
  page_number: number | null;
  content: string;
  score: number;
}

export interface ChatResponse {
  message_id: number;
  conversation_id: number;
  answer: string;
  sources: SourceCitation[];
  retrieved_chunks: RetrievedChunk[];
  retrieval_stats: RetrievalStats;
  low_confidence: boolean;
  provider_info: {
    provider: string;
    model: string | null;
    is_mock: boolean;
    inference_ms?: number;
  };
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant";
  content: string;
  retrieval_meta: {
    sources: SourceCitation[];
    retrieval_stats: RetrievalStats;
    low_confidence: boolean;
    provider_info: Record<string, unknown>;
  } | null;
  created_at: string;
}

export interface Document {
  id: number;
  filename: string;
  file_type: string;
  title: string;
  file_size: number;
  chunk_count: number;
  created_at: string;
}

export interface SystemStatus {
  ai: {
    provider: string;
    ready: boolean;
    model: string | null;
    status_text: string;
    is_mock: boolean;
    state: string | null;
    error: string | null;
  };
  database: {
    connected: boolean;
    path: string;
    type: string;
    error: string | null;
  };
  retriever: {
    ready: boolean;
    type: string;
    chunk_count: number;
    feature_count: number;
  };
  knowledge_base: {
    document_count: number;
    chunk_count: number;
    conversation_count: number;
  };
  privacy: {
    inference: string;
    storage: string;
    internet_required: string;
    cloud_llm: boolean;
  };
}

// ── API helpers ────────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ── Health ─────────────────────────────────────────────────────────────────

export const getHealth = () =>
  request<{ status: string }>("/health");

// ── System ─────────────────────────────────────────────────────────────────

export const getSystemStatus = () =>
  request<SystemStatus>("/system/status");

export const downloadModel = () =>
  request<{ success: boolean; message: string }>("/system/download-model", {
    method: "POST",
  });

export const getRetrievalDebug = (query: string, topK = 5) =>
  request<{ query: string; results: RetrievedChunk[] }>(
    `/retrieval/debug?query=${encodeURIComponent(query)}&top_k=${topK}`
  );

// ── Conversations ──────────────────────────────────────────────────────────

export const listConversations = () =>
  request<Conversation[]>("/conversations");

export const createConversation = (title = "New Chat") =>
  request<Conversation>("/conversations", {
    method: "POST",
    body: JSON.stringify({ title }),
  });

export const deleteConversation = (id: number) =>
  request<void>(`/conversations/${id}`, { method: "DELETE" });

export const getMessages = (conversationId: number) =>
  request<Message[]>(`/conversations/${conversationId}/messages`);

// ── Chat ───────────────────────────────────────────────────────────────────

export const sendChat = (
  question: string,
  conversationId?: number,
  topK?: number
) =>
  request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
      top_k: topK,
    }),
  });

// ── Documents ──────────────────────────────────────────────────────────────

export const listDocuments = () =>
  request<{ documents: Document[]; total_count: number; total_chunks: number }>(
    "/documents"
  );

export const uploadDocument = async (
  file: File,
  title?: string
): Promise<{
  document_id: number;
  filename: string;
  chunk_count: number;
  message: string;
}> => {
  const form = new FormData();
  form.append("file", file);
  if (title) form.append("title", title);

  const res = await fetch(`${API_BASE}/documents`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
};

export const deleteDocument = (id: number) =>
  request<void>(`/documents/${id}`, { method: "DELETE" });
