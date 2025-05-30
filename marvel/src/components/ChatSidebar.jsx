import { useEffect, useState } from "react";
import 'bootstrap-icons/font/bootstrap-icons.css';

function ChatSidebar({ onSelect, darkMode }) {
  const [chatSessions, setChatSessions] = useState([]);
  const userId = localStorage.getItem("userId"); // Or however you identify user
  
  useEffect(() => {
    async function fetchChatSessions() {
      if (!userId) return;
      try {
        const res = await fetch(`https://9tw16vkj-5000.inc1.devtunnels.ms/chats/${userId}`);
        if (!res.ok) throw new Error("Failed to fetch chat sessions");
        const data = await res.json();
        setChatSessions(data);
      } catch (err) {
        console.error(err);
      }
    }
    fetchChatSessions();
  }, [userId]);

  return (
    <aside
      className={`border-end p-3 ${darkMode ? 'bg-dark text-white' : 'bg-light text-dark'}`}
      style={{ width: "250px" }}
    >
      <h2 className="h6 fw-semibold mb-3">
        <i className="bi bi-chat-dots-fill me-2"></i>
        Chats
      </h2>
      <ul className="list-unstyled d-flex flex-column gap-2" style={{ maxHeight: "80vh", overflowY: "auto" }}>
        {chatSessions.length === 0 && <li>No chats yet</li>}

        {chatSessions.map(({ chat_id, title, last_updated }) => (
          <li key={chat_id}>
            <button
              className={`w-100 text-start btn ${
                darkMode ? 'btn-secondary text-white' : 'btn-light text-dark'
              }`}
              onClick={() => onSelect(chat_id)}
              title={`Last updated: ${new Date(last_updated).toLocaleString()}`}
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
