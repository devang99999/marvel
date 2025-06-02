import { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import ChatMessage from "./ChatMessage.jsx";
import ChatInput from "./ChatInput.jsx";
import ChatSidebar from "./ChatSidebar.jsx";
import DarkModeToggle from "./DarkModeToggle.jsx";
import ContextRecommendations from "./ContextRecommendations.jsx";

import { getRecommendations, getChatResponse } from "../api/chatapi.js";

import "bootstrap/dist/css/bootstrap.min.css";
import "../index.css";
const BASE_URL = import.meta.env.VITE_API_URL;

function Chat() {
  const navigate = useNavigate();
  const location = useLocation();

  const [chatHistory, setChatHistory] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedChat, setSelectedChat] = useState("");
  const [darkMode, setDarkMode] = useState(true);

  const chatBottomRef = useRef(null);

  // Get chatId from query string
  const getChatIdFromQuery = () => {
    const query = new URLSearchParams(location.search);
    return query.get("c");
  };

  // On mount: determine chatId (from query string, localStorage, or create new)
  useEffect(() => {
    const paramChatId = getChatIdFromQuery();

    if (paramChatId) {
      setSelectedChat(paramChatId);
      localStorage.setItem("chatId", paramChatId);
    } else {
      const storedChatId = localStorage.getItem("chatId");
      if (storedChatId) {
        setSelectedChat(storedChatId);
        navigate(`/c?c=${storedChatId}`, { replace: true });
      } else {
        const newChatId = crypto.randomUUID();
        setSelectedChat(newChatId);
        localStorage.setItem("chatId", newChatId);
        navigate(`/c?c=${newChatId}`, { replace: true });
      }
    }
  }, [location.search, navigate]);

  // Fetch chat history from backend
  useEffect(() => {
    const fetchHistory = async () => {
      if (!selectedChat) return;
      const userId = localStorage.getItem("userId");
      if (!userId) return;

      try {
        const res = await fetch(
          `${BASE_URL}/chat/${selectedChat}/${userId}`
        );
        if (!res.ok) throw new Error("Chat not found");
        const data = await res.json();
        setChatHistory(data.messages);
      } catch (error) {
        console.error("Failed to load chat history:", error);
        setChatHistory([]);
      }
    };

    fetchHistory();
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
    if (!msg.trim()) return;

    const newEntry = { role: "user", content: msg };
    const updatedChat = [...chatHistory, newEntry];
    setChatHistory(updatedChat);

    try {
      const res = await getChatResponse(updatedChat, selectedChat);
      const responseEntry = { role: "assistant", content: res.answer };
      const finalChat = [...updatedChat, responseEntry];
      setChatHistory(finalChat);

      const recs = await getRecommendations(finalChat);
      setRecommendations(recs);
    } catch (error) {
      console.error("Error during chat:", error);
    }
  };

  // Start new chat
  const startNewChat = () => {
    const newId = crypto.randomUUID();
    setSelectedChat(newId);
    localStorage.setItem("chatId", newId);
    setChatHistory([]);
    setRecommendations([]);
    navigate(`/c?c=${newId}`);
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
        onSelect={(chatId) => {
          setSelectedChat(chatId);
          localStorage.setItem("chatId", chatId);
          navigate(`/c?c=${chatId}`);
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
          <ChatMessage messages={chatHistory} />
          {/* <ContextRecommendations recommendations={recommendations} darkMode={darkMode} /> */}
          <div ref={chatBottomRef} />
        </div>

        <div className="border-top p-3">
          <ChatInput darkMode={darkMode} onSend={handleSend} />
        </div>
      </main>
    </div>
  );
}

export default Chat;
