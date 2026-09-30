import React, { useEffect, useRef, useState, useCallback } from "react";
import {
  sendChat,
  getMessages,
} from "../api/client";
import type { Message, ChatResponse } from "../api/client";
import { ChatMessage } from "../components/ChatMessage";
import { ChatInput } from "../components/ChatInput";
import "./ChatPage.css";

interface ChatPageProps {
  conversationId: number | null;
  onConversationCreated: (id: number) => void;
  onConversationsChanged: () => void;
}

const EXAMPLE_PROMPTS = [
  { icon: "🔐", text: "How should I investigate repeated failed SSH logins?" },
  { icon: "📋", text: "What logs should I review after a suspicious successful login?" },
  { icon: "🔑", text: "Explain password spraying using my security documents." },
  { icon: "🔍", text: "What evidence should be preserved during incident triage?" },
];

export const ChatPage: React.FC<ChatPageProps> = ({
  conversationId,
  onConversationCreated,
  onConversationsChanged,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversationId === null) {
      setMessages([]);
      return;
    }
    getMessages(conversationId)
      .then(setMessages)
      .catch(() => setMessages([]));
  }, [conversationId]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = useCallback(
    async (question: string) => {
      setError(null);
      setLoading(true);

      // Optimistically add the user message to the list
      const tempUserMsg: Message = {
        id: -1,
        conversation_id: conversationId ?? -1,
        role: "user",
        content: question,
        retrieval_meta: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, tempUserMsg]);

      try {
        const result: ChatResponse = await sendChat(
          question,
          conversationId ?? undefined
        );

        // If this was a new conversation, notify parent
        if (conversationId === null) {
          onConversationCreated(result.conversation_id);
        }

        // Build a Message from the response
        const assistantMsg: Message = {
          id: result.message_id,
          conversation_id: result.conversation_id,
          role: "assistant",
          content: result.answer,
          retrieval_meta: {
            sources: result.sources,
            retrieval_stats: result.retrieval_stats,
            low_confidence: result.low_confidence,
            provider_info: result.provider_info,
          },
          created_at: new Date().toISOString(),
        };

        setMessages((prev) => [
          ...prev.filter((m) => m.id !== -1), // remove optimistic user msg
          { ...tempUserMsg, id: result.message_id > 0 ? result.message_id - 1 : Date.now() },
          assistantMsg,
        ]);

        onConversationsChanged();
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Unknown error";
        setError(message);
        // Turn the optimistic message into a failed state or keep it visible
        setMessages((prev) => [
          ...prev.filter((m) => m.id !== -1),
          { ...tempUserMsg, id: Date.now() },
          {
            id: Date.now() + 1,
            conversation_id: conversationId ?? -1,
            role: "assistant",
            content: `❌ **Error Encountered:** ${message}\n\nPlease try again or check service status in the System Status dashboard.`,
            retrieval_meta: null,
            created_at: new Date().toISOString(),
          }
        ]);
      } finally {
        setLoading(false);
      }
    },
    [conversationId, onConversationCreated, onConversationsChanged]
  );

  const isEmpty = messages.length === 0 && !loading && !error;

  return (
    <div className="chat-page">
      {/* Header */}
      <div className="chat-header">
        <div>
          <h1 className="chat-title">Enterprise Security Assistant</h1>
          <p className="chat-subtitle">Private · Local · RAG-powered</p>
        </div>
        <div className="chat-header-badges">
          <span className="badge badge-green">🔒 LOCAL MODE</span>
          <span className="badge badge-blue">TF-IDF</span>
          <span className="badge badge-purple">Foundry Local</span>
        </div>
      </div>

      {/* Message area */}
      <div className="chat-messages">
        {isEmpty ? (
          <div className="chat-empty">
            <div className="chat-empty-icon">🛡️</div>
            <h2 className="chat-empty-title">Enterprise Security Assistant</h2>
            <p className="chat-empty-sub">
              Upload enterprise security policies and incident playbooks to the Knowledge Base, then ask
              questions. All data stays local — no cloud LLM required.
            </p>
            <div className="chat-empty-examples">
              {EXAMPLE_PROMPTS.map((p, i) => (
                <button
                  key={i}
                  className="chat-empty-prompt"
                  onClick={() => handleSend(p.text)}
                >
                  <span className="prompt-icon">{p.icon}</span>
                  <span>{p.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <ChatMessage key={i} message={msg} />
            ))}
            {loading && (
              <div className="chat-loading">
                <div className="chat-loading-dots">
                  <span />
                  <span />
                  <span />
                </div>
                <span className="chat-loading-text">Retrieving context and generating response…</span>
              </div>
            )}
            {error && (
              <div className="chat-error">
                ⚠️ {error}
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={loading} />
    </div>
  );
};
