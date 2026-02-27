// src/chatapi.js

const BASE_URL = import.meta.env.VITE_API_URL; // Your Flask backend

// Auth headers using userId as token
const getAuthHeaders = () => {
  const token = localStorage.getItem("userId");
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
};

// ✅ Fetch chat sessions by user ID
export async function fetchChatSessions(userId) {
  const res = await fetch(`${BASE_URL}/chat_sessions/${userId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch chat sessions: ${res.status}`);
  }
  return await res.json();
}

// ✅ Get chat history by chat ID
export async function getChatHistory(chatId) {
  const res = await fetch(`${BASE_URL}/history/${chatId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch chat history: ${res.statusText}`);
  }
  const data = await res.json();

  // Flatten to [{ role: "user", ... }, { role: "assistant", ... }]
  const messages = data.flatMap((doc) => [
    { role: "user", content: doc.question },
    { role: "assistant", content: doc.answer },
  ]);

  return messages;
}

// ✅ Send a chat request to backend, receive answer + chat ID
export async function getChatResponse(messages, chatId) {
  const token = localStorage.getItem("userId");
  const res = await fetch(`${BASE_URL}/chat-response`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ messages, userId: token, chatId }),
  });
  if (!res.ok) {
    throw new Error("Failed to get chat response");
  }
  const data = await res.json();
  return {
    answer: data.answer,
    chatId: data.chat_id,
  };
}

// ✅ Get recommended topics based on chat context
export async function getRecommendations(messages) {
  const res = await fetch(`${BASE_URL}/recommendations`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) {
    throw new Error("Failed to get recommendations");
  }
  return await res.json();
}
