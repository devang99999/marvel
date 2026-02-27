import { useState } from "react";

function ChatInput({ onSend, darkMode }) {
  const [msg, setMsg] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (msg.trim()) {
      onSend(msg);
      setMsg("");
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className={`d-flex gap-2 p-3 border-top ${
        darkMode ? "bg-dark border-secondary" : "bg-white border-light"
      }`}
    >
      <input
        type="text"
        value={msg}
        onChange={(e) => setMsg(e.target.value)}
        placeholder="Type your Marvel question..."
        className={`form-control ${
          darkMode ? "bg-secondary text-white border-secondary" : ""
        }`}
      />
      <button type="submit" className="btn btn-primary">
        Send
      </button>
    </form>
  );
}

export default ChatInput;
