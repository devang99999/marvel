import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext.jsx";

export default function LoginRegister() {
  const { login, register, loading } = useAuth();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);


  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch {
      setError("Failed to " + (mode === "login" ? "login" : "register"));
    }
  };
  return (
    <div
      style={{
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        minHeight: "100vh",
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      {/* Bootstrap CSS */}
      <link
        href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css"
        rel="stylesheet"
      />
      <link
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
        rel="stylesheet"
      />

      <style>{`
        .auth-card {
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(10px);
          border-radius: 20px;
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
          border: 1px solid rgba(255, 255, 255, 0.2);
          overflow: hidden;
          max-width: 450px;
          width: 100%;
          transition: transform 0.3s ease;
          animation: fadeIn 0.5s ease-in;
        }
        
        .auth-card:hover {
          transform: translateY(-5px);
        }
        
        .auth-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 2rem;
          text-align: center;
          position: relative;
          overflow: hidden;
        }
        
        .auth-header::before {
          content: '';
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
          animation: shimmer 3s infinite;
        }
        
        @keyframes shimmer {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(180deg); }
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        .auth-header h2 {
          margin: 0;
          font-weight: 600;
          font-size: 1.8rem;
          position: relative;
          z-index: 1;
        }
        
        .auth-header .icon {
          font-size: 3rem;
          margin-bottom: 1rem;
          opacity: 0.9;
          position: relative;
          z-index: 1;
        }
        
        .auth-body {
          padding: 2.5rem;
        }
        
        .form-control {
          border-radius: 12px;
          border: 2px solid #e9ecef;
          padding: 1rem 1.25rem;
          font-size: 1rem;
          transition: all 0.3s ease;
          background: rgba(248, 249, 250, 0.8);
          margin-bottom: 1.5rem;
        }
        
        .form-control:focus {
          border-color: #667eea;
          box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
          background: white;
          transform: translateY(-2px);
          outline: none;
        }
        
        .btn-primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          border-radius: 12px;
          padding: 1rem 2rem;
          font-weight: 600;
          font-size: 1.1rem;
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
          color: white;
          cursor: pointer;
        }
        
        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
          background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
        }
        
        .btn-primary:active {
          transform: translateY(0);
        }
        
        .btn-primary:disabled {
          opacity: 0.7;
          cursor: not-allowed;
          transform: none;
        }
        
        .btn-primary::before {
          content: '';
          position: absolute;
          top: 0;
          left: -100%;
          width: 100%;
          height: 100%;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
          transition: left 0.5s;
        }
        
        .btn-primary:hover::before {
          left: 100%;
        }
        
        .switch-mode {
          text-align: center;
          margin-top: 2rem;
          padding-top: 1.5rem;
          border-top: 1px solid #e9ecef;
        }
        
        .switch-btn {
          color: #667eea;
          text-decoration: none;
          font-weight: 600;
          transition: all 0.3s ease;
          position: relative;
          cursor: pointer;
          background: none;
          border: none;
          padding: 0;
        }
        
        .switch-btn:hover {
          color: #764ba2;
          text-decoration: none;
        }
        
        .switch-btn::after {
          content: '';
          position: absolute;
          width: 0;
          height: 2px;
          bottom: -2px;
          left: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          transition: all 0.3s ease;
        }
        
        .switch-btn:hover::after {
          width: 100%;
          left: 0;
        }
        
        .alert {
          border-radius: 10px;
          border: none;
          margin-bottom: 1.5rem;
          background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
          color: white;
          padding: 1rem;
          animation: fadeIn 0.5s ease-in;
        }
        
        .input-group {
          margin-bottom: 1.5rem;
          position: relative;
        }
        
        .input-group-text {
          background: transparent;
          border: 2px solid #e9ecef;
          border-right: none;
          border-radius: 12px 0 0 12px;
          color: #6c757d;
          padding: 1rem 1.25rem;
        }
        
        .input-group .form-control {
          border-left: none;
          border-radius: 0 12px 12px 0;
          margin-bottom: 0;
        }
        
        .input-group:focus-within .input-group-text {
          border-color: #667eea;
          color: #667eea;
        }
        
        .spinner-border-sm {
          width: 1rem;
          height: 1rem;
          border-width: 0.125em;
        }
        
        .spinner-border {
          display: inline-block;
          vertical-align: text-bottom;
          border: 0.25em solid currentColor;
          border-right-color: transparent;
          border-radius: 50%;
          animation: spinner-border .75s linear infinite;
        }
        
        @keyframes spinner-border {
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="auth-card">
        <div className="auth-header">
          <div className="icon">
            <i
              className={`fas ${
                mode === "login" ? "fa-sign-in-alt" : "fa-user-plus"
              }`}
            ></i>
          </div>
          <h2>{mode === "login" ? "Welcome Back" : "Create Account"}</h2>
          <p className="mb-0" style={{ opacity: 0.75 }}>
            {mode === "login" ? "Sign in to your account" : "Join us today"}
          </p>
        </div>

        <div className="auth-body">
          <div onSubmit={handleSubmit}>
            {error && (
              <div className="alert" role="alert">
                <i
                  className="fas fa-exclamation-triangle"
                  style={{ marginRight: "0.5rem" }}
                ></i>
                {error}
              </div>
            )}

            <div className="input-group">
              <span className="input-group-text">
                <i className="fas fa-envelope"></i>
              </span>
              <input
                type="email"
                className="form-control"
                placeholder="Enter your email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="input-group">
              <span className="input-group-text">
                <i className="fas fa-lock"></i>
              </span>
              <input
                type="password"
                className="form-control"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-100 mb-3"
              onClick={handleSubmit}
            >
              {loading ? (
                <>
                  <span
                    className="spinner-border spinner-border-sm"
                    style={{ marginRight: "0.5rem" }}
                    role="status"
                    aria-hidden="true"
                  ></span>
                  Please wait...
                </>
              ) : (
                <>
                  <i
                    className={`fas ${
                      mode === "login" ? "fa-sign-in-alt" : "fa-user-plus"
                    }`}
                    style={{ marginRight: "0.5rem" }}
                  ></i>
                  {mode === "login" ? "Sign In" : "Create Account"}
                </>
              )}
            </button>
          </div>

          <div className="switch-mode">
            <p className="text-muted mb-2">
              {mode === "login"
                ? "Don't have an account?"
                : "Already have an account?"}
            </p>
            <button
              className="switch-btn"
              onClick={() => {
                setError(null);
                setMode(mode === "login" ? "register" : "login");
              }}
            >
              {mode === "login" ? "Create Account" : "Sign In"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
