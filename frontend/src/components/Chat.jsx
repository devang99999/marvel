import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import ChatMessage from "./ChatMessage.jsx";
import ChatInput from "./ChatInput.jsx";
import ChatSidebar from "./ChatSidebar.jsx";
import DarkModeToggle from "./DarkModeToggle.jsx";
import ContextRecommendations from "./ContextRecommendations.jsx";

import { getRecommendations, getChatResponse, getChatHistory } from "../api/chatapi.js";

import "bootstrap/dist/css/bootstrap.min.css";
import "../index.css";

function Chat() {
  const navigate = useNavigate();
  const { chatId: urlChatId } = useParams();

  const [chatHistory, setChatHistory] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedChat, setSelectedChat] = useState("");
  const [darkMode, setDarkMode] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarRefresh, setSidebarRefresh] = useState(0);

  const chatBottomRef = useRef(null);

  // Sync selectedChat from URL (dynamic route /chat/:chatId)
  useEffect(() => {
    if (urlChatId) {
      setSelectedChat(urlChatId);
      localStorage.setItem("chatId", urlChatId);
    } else {
      const storedChatId = localStorage.getItem("chatId");
      if (storedChatId) {
        navigate(`/chat/${storedChatId}`, { replace: true });
      } else {
        const newChatId = crypto.randomUUID();
        setSelectedChat(newChatId);
        localStorage.setItem("chatId", newChatId);
        navigate(`/chat/${newChatId}`, { replace: true });
      }
    }
  }, [urlChatId, navigate]);

  // Load chat history when switching to a chat
  useEffect(() => {
    if (!selectedChat) {
      setChatHistory([]);
      return;
    }
    let cancelled = false;
    getChatHistory(selectedChat)
      .then((messages) => {
        if (!cancelled) setChatHistory(messages || []);
      })
      .catch(() => {
        if (!cancelled) setChatHistory([]);
      });
    return () => { cancelled = true; };
  }, [selectedChat]);

  // Scroll to bottom when chat updates
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  // Dark mode toggle
  useEffect(() => {
    document.body.classList.toggle("bg-dark", darkMode);
    document.body.classList.toggle("text-white", darkMode);
    document.body.classList.toggle("bg-white", !darkMode);
    document.body.classList.toggle("text-dark", !darkMode);
  }, [darkMode]);

  // Handle sending a new message
  const handleSend = async (msg) => {
    if (!msg.trim() || isLoading) return;

    const newEntry = { role: "user", content: msg };
    const updatedChat = [...chatHistory, newEntry];
    setChatHistory(updatedChat);
    setIsLoading(true);

    try {
      const res = await getChatResponse(updatedChat, selectedChat);
      const responseEntry = {
        role: "assistant",
        content: res.answer,
        source: res.source ?? null,
        chunksUsed: res.chunksUsed ?? 0,
      };
      const finalChat = [...updatedChat, responseEntry];
      setChatHistory(finalChat);
      setSidebarRefresh((n) => n + 1);

      const recs = await getRecommendations(finalChat);
      setRecommendations(recs);
    } catch (error) {
      console.error("Error during chat:", error);
      const errorEntry = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again or check your connection."
      };
      setChatHistory([...updatedChat, errorEntry]);
    } finally {
      setIsLoading(false);
    }
  };

  // Start new chat
  const startNewChat = () => {
    const newId = crypto.randomUUID();
    setSelectedChat(newId);
    localStorage.setItem("chatId", newId);
    setChatHistory([]);
    setRecommendations([]);
    navigate(`/chat/${newId}`);
  };

  // Logout
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("chatId");
    localStorage.removeItem("userId");
    window.location.reload();
  };

  return (
    <div className="d-flex vh-100 overflow-hidden">
      <ChatSidebar
        darkMode={darkMode}
        refreshTrigger={sidebarRefresh}
        onSelect={(chatId) => {
          setSelectedChat(chatId);
          localStorage.setItem("chatId", chatId);
          navigate(`/chat/${chatId}`);
        }}
      />

      <main className="d-flex flex-column flex-grow-1">
        <div className="d-flex align-items-center justify-content-between p-3 border-bottom">
          <h1 className="h4 fw-bold">🦸‍♂️ Marvel Chatbot</h1>
          <div className="d-flex align-items-center gap-3">
            <button
              className="btn btn-outline-primary btn-sm"
              onClick={startNewChat}
            >
              + New Chat
            </button>
            <DarkModeToggle darkMode={darkMode} setDarkMode={setDarkMode} />
            <button
              className="btn btn-outline-danger btn-sm"
              onClick={handleLogout}
            >
              Logout
            </button>
          </div>
        </div>

        <div className="flex-grow-1 overflow-auto p-3">
          <ChatMessage messages={chatHistory} darkMode={darkMode} />
          {isLoading && (
            <div className="text-center my-3">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-2">Thinking...</p>
            </div>
          )}
          {/* <ContextRecommendations recommendations={recommendations} darkMode={darkMode} /> */}
          <div ref={chatBottomRef} />
        </div>

        <div className="border-top p-3">
          <ChatInput darkMode={darkMode} onSend={handleSend} disabled={isLoading} />
        </div>
      </main>
    </div>
  );
}

export default Chat;
