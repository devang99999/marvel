function ChatMessage({ messages }) {
  return (
    <div className="p-3 overflow-auto">
      {messages.map((msg, idx) => (
        <div
          key={idx}
          className={`p-3 rounded mb-3 text-wrap text-sm ${
            msg.role === "user"
              ? "bg-primary text-white ms-auto"
              : "bg-light text-dark me-auto"
          }`}
          style={{ maxWidth: '75%', whiteSpace: 'pre-wrap' }}
        >
          {msg.content}
        </div>
      ))}
    </div>
  );
}

export default ChatMessage;
