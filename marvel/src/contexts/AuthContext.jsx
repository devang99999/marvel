// src/contexts/AuthContext.jsx
import React, { createContext, useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();
const BASE_URL = import.meta.env.VITE_API_URL;

export const AuthProvider = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);

  const login = async (email, password, navigate) => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Login failed');

      if (!data.user || !data.user.id) {
        throw new Error('User data missing in response');
      }

      localStorage.setItem('userId', data.user.id);
      localStorage.setItem('email', data.user.email);
      setUser(data.user);

      window.location.replace("/")
    } catch (err) {
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email, password, navigate) => {
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Registration failed');

      if (!data.user || !data.user.id) {
        throw new Error('User data missing in response');
      }

      localStorage.setItem('userId', data.user.id);
      localStorage.setItem('email', data.user.email);
      setUser(data.user);

      if (navigate) navigate('/');
    } catch (err) {
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = (navigate) => {
    localStorage.removeItem('userId');
    localStorage.removeItem('email');
    setUser(null);
    if (navigate) navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ login, register, logout, user, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
