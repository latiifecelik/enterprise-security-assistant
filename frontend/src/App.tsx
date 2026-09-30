import { useEffect, useState, useCallback } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatPage } from "./pages/ChatPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { StatusPage } from "./pages/StatusPage";
import { AboutPage } from "./pages/AboutPage";
import {
  listConversations,
  deleteConversation,
  getSystemStatus,
} from "./api/client";
import type { Conversation } from "./api/client";
import "./App.css";

type Page = "chat" | "documents" | "status" | "about";

function App() {
  const [page, setPage] = useState<Page>("chat");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [aiStatus, setAiStatus] = useState<{
    ready: boolean;
    is_mock: boolean;
    status_text: string;
    provider: string;
  } | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      const convs = await listConversations();
      setConversations(convs);
    } catch {
      /* ignore — will retry */
    }
  }, []);

  const loadAIStatus = useCallback(async () => {
    try {
      const status = await getSystemStatus();
      setAiStatus({
        ready: status.ai.ready,
        is_mock: status.ai.is_mock,
        status_text: status.ai.status_text,
        provider: status.ai.provider,
      });
    } catch {
      setAiStatus(null);
    }
  }, []);

  useEffect(() => {
    loadConversations();
    loadAIStatus();
    // Refresh AI status every 15s to catch model loading completion
    const interval = setInterval(loadAIStatus, 15000);
    return () => clearInterval(interval);
  }, [loadConversations, loadAIStatus]);

  const handleNewChat = () => {
    setActiveConvId(null);
    setPage("chat");
  };

  const handleSelectConversation = (id: number) => {
    setActiveConvId(id);
    setPage("chat");
  };

  const handleConversationCreated = (id: number) => {
    setActiveConvId(id);
    loadConversations();
  };

  const handleDeleteConversation = async (id: number) => {
    await deleteConversation(id);
    if (activeConvId === id) setActiveConvId(null);
    await loadConversations();
  };

  const renderPage = () => {
    switch (page) {
      case "chat":
        return (
          <ChatPage
            conversationId={activeConvId}
            onConversationCreated={handleConversationCreated}
            onConversationsChanged={loadConversations}
          />
        );
      case "documents":
        return <DocumentsPage />;
      case "status":
        return <StatusPage />;
      case "about":
        return <AboutPage />;
      default:
        return null;
    }
  };

  return (
    <div className="app-layout">
      <Sidebar
        conversations={conversations}
        activeConvId={activeConvId}
        onSelectConversation={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteConversation={handleDeleteConversation}
        activePage={page}
        onNavigate={(p) => setPage(p as Page)}
        aiStatus={aiStatus}
      />
      <main className="app-main">{renderPage()}</main>
    </div>
  );
}

export default App;
