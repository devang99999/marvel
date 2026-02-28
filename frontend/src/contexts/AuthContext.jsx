// src/contexts/AuthContext.jsx
import React, { createContext, useContext, useState } from "react";
import { useNavigate } from "react-router-dom";

const AuthContext = createContext();
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

// Rehydrate user from localStorage so auth persists across reloads
function getStoredUser() {
  const token = localStorage.getItem("token");
  const userId = localStorage.getItem("userId");
  const email = localStorage.getItem("email");
  if (token && userId) return { id: userId, email: email || "" };
  return null;
}

export const AuthProvider = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(() => getStoredUser());

  const login = async (email, password, navigate) => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || data.message || "Login failed");

      const token = data.token ?? data.access_token;
      if (!data.user?.id || !token) {
        throw new Error("Server did not return a token. Ensure the backend returns { token, user: { id, email } }.");
      }

      localStorage.setItem("token", token);
      localStorage.setItem("userId", data.user.id);
      localStorage.setItem("email", data.user.email ?? "");
      setUser(data.user);

      window.location.replace("/chat");
    } catch (err) {
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, password, navigate) => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/register`, { // signup → register API, not /login
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || data.message || "Registration failed");

      const token = data.token ?? data.access_token;
      if (!data.user?.id || !token) {
        throw new Error("Server did not return a token. Ensure the backend returns { token, user: { id, email } }.");
      }

      localStorage.setItem("token", token);
      localStorage.setItem("userId", data.user.id);
      localStorage.setItem("email", data.user.email ?? "");
      setUser(data.user);

      window.location.replace("/chat");
    } catch (err) {
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = (navigate) => {
    localStorage.removeItem("token");
    localStorage.removeItem("userId");
    localStorage.removeItem("email");
    setUser(null);
    if (navigate) navigate("/login");
  };

  return (
    <AuthContext.Provider value={{ login, register, logout, user, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
