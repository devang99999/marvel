import React, { useState, useEffect } from "react";
import "./App.css"

function MarvelChatbot() {
  const [chatInput, setChatInput] = useState("");
  const [messages, setMessages] = useState([]); // { from: "user"|"bot", text: string }
  const [recommendations, setRecommendations] = useState({
    query_based: [],
    history_based: [],
    popular: [],
  });
  const [loadingRecs, setLoadingRecs] = useState(false);

  // Send chat message to backend and get reply
  const sendMessage = async (message) => {
    if (!message.trim()) return;

    setMessages((msgs) => [...msgs, { from: "user", text: message }]);
    setChatInput("");

    // Call backend chat API (replace with your actual API)
    const chatResponse = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await chatResponse.json();

    setMessages((msgs) => [...msgs, { from: "bot", text: data.reply }]);

    // Fetch recommendations based on this query
    fetchRecommendations(message);
  };

  // Fetch recommendations from backend
  const fetchRecommendations = async (query) => {
    setLoadingRecs(true);
    try {
      const res = await fetch("/api/recommendations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const recData = await res.json();
      setRecommendations(recData);
    } catch (e) {
      console.error("Failed to fetch recommendations", e);
      setRecommendations({
        query_based: [],
        history_based: [],
        popular: [],
      });
    } finally {
      setLoadingRecs(false);
    }
  };

  // When user clicks a recommendation, send that message
  const onRecommendationClick = (recText) => {
    sendMessage(recText);
  };

  // On first render, you might want to fetch popular recommendations or keep empty
  useEffect(() => {
    fetchRecommendations("");
  }, []);

  return (
    <div style={{ display: "flex", height: "90vh", maxWidth: 900, margin: "auto", border: "1px solid #ddd", borderRadius: 8 }}>
      {/* Chat Section */}
      <div style={{ flex: 3, display: "flex", flexDirection: "column", padding: 16 }}>
        <div
          style={{
            flex: 1,
            overflowY: "auto",
            border: "1px solid #ccc",
            borderRadius: 4,
            padding: 12,
            marginBottom: 12,
            backgroundColor: "#f9f9f9",
          }}
        >
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                marginBottom: 10,
                textAlign: msg.from === "user" ? "right" : "left",
              }}
            >
              <span
                style={{
                  display: "inline-block",
                  padding: "8px 12px",
                  borderRadius: 16,
                  backgroundColor: msg.from === "user" ? "#0078d4" : "#e1e1e1",
                  color: msg.from === "user" ? "white" : "black",
                }}
              >
                {msg.text}
              </span>
            </div>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(chatInput);
          }}
          style={{ display: "flex" }}
        >
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Ask about Marvel..."
            style={{
              flex: 1,
              padding: 10,
              fontSize: 16,
              borderRadius: 4,
              border: "1px solid #ccc",
            }}
          />
          <button
            type="submit"
            style={{
              marginLeft: 8,
              padding: "10px 16px",
              fontSize: 16,
              borderRadius: 4,
              border: "none",
              backgroundColor: "#0078d4",
              color: "white",
              cursor: "pointer",
            }}
          >
            Send
          </button>
        </form>
      </div>

      {/* Recommendations Sidebar */}
      <div
        style={{
          flex: 1,
          borderLeft: "1px solid #ddd",
          padding: 16,
          backgroundColor: "#f0f0f0",
          overflowY: "auto",
        }}
      >
        <h3 style={{ marginTop: 0 }}>Recommendations</h3>
        {loadingRecs && <p>Loading...</p>}

        {!loadingRecs && (
          <>
            <RecSection title="Related to Your Query" items={recommendations.query_based} onClick={onRecommendationClick} />
            <RecSection title="Based on Your History" items={recommendations.history_based} onClick={onRecommendationClick} />
            <RecSection title="Popular Topics" items={recommendations.popular} onClick={onRecommendationClick} />
          </>
        )}
      </div>
    </div>
  );
}

// Helper component to render a section of recommendations
function RecSection({ title, items, onClick }) {
  if (!items || items.length === 0) return null;
  return (
    <div style={{ marginBottom: 20 }}>
      <h4 style={{ marginBottom: 8 }}>{title}</h4>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {items.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onClick(item)}
            style={{
              backgroundColor: "#0078d4",
              border: "none",
              borderRadius: 20,
              padding: "6px 12px",
              color: "white",
              cursor: "pointer",
              fontSize: 14,
            }}
            title={`Ask about "${item}"`}
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  );
}

export default MarvelChatbot;
