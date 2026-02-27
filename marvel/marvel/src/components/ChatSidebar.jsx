import { useEffect, useState } from "react";
import 'bootstrap-icons/font/bootstrap-icons.css';
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';


function ChatSidebar({ onSelect, darkMode, refreshTrigger = 0 }) {
  const [chatSessions, setChatSessions] = useState([]);
  const userId = localStorage.getItem("userId");

  useEffect(() => {
    async function fetchChatSessions() {
      if (!userId) return;
      try {
        const res = await fetch(`${BASE_URL}/chats/${userId}`);
        if (!res.ok) {
          setChatSessions([]);
          return;
        }
        const data = await res.json();
        setChatSessions(Array.isArray(data) ? data : []);
      } catch {
        setChatSessions([]);
      }
    }
    fetchChatSessions();
  }, [userId, refreshTrigger]);

  return (
    <aside
      className={`border-end p-3 ${darkMode ? 'bg-dark text-white' : 'bg-light text-dark'}`}
      style={{
        width: "250px",
        minWidth: "200px"
      }}
    >
      <h2 className="h6 fw-semibold mb-3 d-flex align-items-center">
        <i className="bi bi-chat-dots-fill me-2"></i>
        <span className="d-none d-md-inline">Chats</span>
      </h2>
      <ul className="list-unstyled d-flex flex-column gap-2" style={{ maxHeight: "80vh", overflowY: "auto" }}>
        {chatSessions.length === 0 && <li className="small">No chats yet</li>}

        {chatSessions.map(({ chat_id, title, last_updated }) => (
          <li key={chat_id}>
            <button
              className={`w-100 text-start btn btn-sm ${
                darkMode ? 'btn-secondary text-white' : 'btn-light text-dark'
              }`}
              onClick={() => onSelect(chat_id)}
              title={`Last updated: ${new Date(last_updated).toLocaleString()}`}
              style={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}
            >
              {title || chat_id}
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}

export default ChatSidebar;
