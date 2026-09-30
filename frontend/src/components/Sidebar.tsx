import React, { useState } from "react";
import type { Conversation } from "../api/client";
import "./Sidebar.css";

interface SidebarProps {
  conversations: Conversation[];
  activeConvId: number | null;
  onSelectConversation: (id: number) => void;
  onNewChat: () => void;
  onDeleteConversation: (id: number) => void;
  activePage: string;
  onNavigate: (page: string) => void;
  aiStatus: { ready: boolean; is_mock: boolean; status_text: string; provider: string } | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  activeConvId,
  onSelectConversation,
  onNewChat,
  onDeleteConversation,
  activePage,
  onNavigate,
  aiStatus,
}) => {
  const [hoveredId, setHoveredId] = useState<number | null>(null);

  const navItems = [
    { id: "chat", label: "Chat", icon: "💬" },
    { id: "documents", label: "Documents", icon: "📂" },
    { id: "status", label: "System Status", icon: "📊" },
    { id: "about", label: "About", icon: "ℹ️" },
  ];

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <span className="sidebar-logo-icon">🛡️</span>
        <div>
          <div className="sidebar-logo-title">Enterprise Security</div>
          <div className="sidebar-logo-sub">AI Defense Assistant</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`sidebar-nav-item ${activePage === item.id ? "active" : ""}`}
            onClick={() => onNavigate(item.id)}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      {/* New Chat button */}
      {activePage === "chat" && (
        <>
          <div className="sidebar-section-label">Chats</div>
          <button className="sidebar-new-chat" onClick={onNewChat}>
            <span>＋</span> New Chat
          </button>

          {/* Conversation list */}
          <div className="sidebar-conv-list">
            {conversations.length === 0 ? (
              <div className="sidebar-empty">No conversations yet</div>
            ) : (
              conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`sidebar-conv-item ${activeConvId === conv.id ? "active" : ""}`}
                  onClick={() => onSelectConversation(conv.id)}
                  onMouseEnter={() => setHoveredId(conv.id)}
                  onMouseLeave={() => setHoveredId(null)}
                >
                  <span className="sidebar-conv-title">{conv.title}</span>
                  {hoveredId === conv.id && (
                    <button
                      className="sidebar-conv-delete"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conv.id);
                      }}
                      title="Delete conversation"
                    >
                      🗑
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}

      {/* AI Status indicator at bottom */}
      <div className="sidebar-status">
        {aiStatus ? (
          <span className={`sidebar-status-dot ${aiStatus.ready ? "green" : aiStatus.is_mock ? "orange" : "red"}`}>
            ●
          </span>
        ) : (
          <span className="sidebar-status-dot grey">●</span>
        )}
        <span className="sidebar-status-text">
          {aiStatus ? aiStatus.provider : "Connecting…"}
        </span>
        <span className={`badge ${aiStatus?.ready ? "badge-green" : aiStatus?.is_mock ? "badge-orange" : "badge-red"}`}>
          {aiStatus?.ready ? "Ready" : aiStatus?.is_mock ? "Mock" : "Offline"}
        </span>
      </div>
    </aside>
  );
};
