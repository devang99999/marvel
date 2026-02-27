const SOURCE_LABELS = {
  database: "From your database (RAG)",
  groq_only: "From AI (no DB context)",
  cached: "From cache (refreshes periodically)",
  web: "From web search",
};

function ChatMessage({ messages, darkMode }) {
  return (
    <div className="p-3 overflow-auto">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`p-3 rounded mb-3 text-wrap text-sm ${
            msg.role === "user"
              ? "bg-primary text-white ms-auto"
              : darkMode
                ? "bg-secondary text-white me-auto"
                : "bg-light text-dark me-auto"
          }`}
          style={{ maxWidth: "75%", whiteSpace: "pre-wrap" }}
        >
          {msg.content}
          {msg.role === "assistant" && msg.source && (
            <div
              className="mt-2 pt-2 border-top border-opacity-25 small opacity-75"
              style={{ fontSize: "0.7rem" }}
              title={msg.chunksUsed ? `${msg.chunksUsed} chunk(s) used` : ""}
            >
              {SOURCE_LABELS[msg.source] ?? msg.source}
              {msg.chunksUsed > 0 && ` (${msg.chunksUsed} chunks)`}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

export default ChatMessage;
