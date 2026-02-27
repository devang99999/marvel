import { useState } from "react";

function ChatInput({ onSend, darkMode, disabled = false }) {
  const [msg, setMsg] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (msg.trim() && !disabled) {
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
        disabled={disabled}
      />
      <button type="submit" className="btn btn-primary" disabled={disabled}>
        {disabled ? "Sending..." : "Send"}
      </button>
    </form>
  );
}

export default ChatInput;
