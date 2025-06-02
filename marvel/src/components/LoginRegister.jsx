import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext.jsx";
import { useNavigate } from "react-router-dom";

export default function LoginRegister() {
  const { login, register, loading } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(true);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "login") {
        await login(email, password, navigate);
      } else {
        await register(email, password, navigate);
      }
    } catch {
      setError("Failed to " + (mode === "login" ? "login" : "register"));
    }
  };

  const closeModal = () => setShowModal(false);

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
      <link
        href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css"
        rel="stylesheet"
      />
      <link
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
        rel="stylesheet"
      />

      {/* Modal */}
      {showModal && (
        <div
          className="modal fade show"
          style={{ display: "block", backgroundColor: "rgba(0,0,0,0.6)" }}
          tabIndex="-1"
          aria-modal="true"
          role="dialog"
        >
          <div className="modal-dialog modal-dialog-centered modal-lg">
            <div className="modal-content" style={{ borderRadius: "15px" }}>
              <div
                className="modal-header"
                style={{
                  background:
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  color: "white",
                  borderTopLeftRadius: "15px",
                  borderTopRightRadius: "15px",
                }}
              >
                <h5 className="modal-title">
                  <i className="fas fa-info-circle me-2"></i> Welcome!
                </h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={closeModal}
                ></button>
              </div>
              <div className="modal-body text-center">
                <p style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>
                  Thanks for visiting! This app's backend is hosted on Render's
                  free tier.
                </p>
                <p>
                  If it's inactive, it may take up to 30 seconds to wake up.
                  Please be patient
                </p>
                <p className="mb-0">
                  Or click below to manually ping the backend:
                </p>
                <a
                  href="https://marvel-b1wd.onrender.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-outline-primary mt-3"
                >
                  Wake up backend
                </a>
              </div>
              <div className="modal-footer justify-content-center">
                <button className="btn btn-primary" onClick={closeModal}>
                  Got it, continue
                </button>
              </div>
              <div className="modal-footer justify-content-center">
                <a target="_balnk" href="https://www.linkedin.com/in/webdevanggandhi/">
                  <button className="btn btn-primary" onClick={closeModal}>
                    Or just text me
                  </button>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Auth Card */}
      <div
        className="auth-card p-4 bg-white rounded-4 shadow"
        style={{ maxWidth: 450, width: "100%" }}
      >
        <div
          className="auth-header text-center text-white p-4 rounded-top"
          style={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          }}
        >
          <div className="icon mb-2">
            <i
              className={`fas ${
                mode === "login" ? "fa-sign-in-alt" : "fa-user-plus"
              } fa-2x`}
            ></i>
          </div>
          <h2>{mode === "login" ? "Welcome Back" : "Create Account"}</h2>
          <p className="mb-0 opacity-75">
            {mode === "login" ? "Sign in to your account" : "Join us today"}
          </p>
        </div>

        <div className="auth-body mt-4">
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="alert alert-danger" role="alert">
                <i className="fas fa-exclamation-triangle me-2"></i>
                {error}
              </div>
            )}

            <div className="input-group mb-3">
              <span className="input-group-text">
                <i className="fas fa-envelope"></i>
              </span>
              <input
                type="email"
                className="form-control"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="input-group mb-4">
              <span className="input-group-text">
                <i className="fas fa-lock"></i>
              </span>
              <input
                type="password"
                className="form-control"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-100"
            >
              {loading ? (
                <>
                  <span
                    className="spinner-border spinner-border-sm me-2"
                    role="status"
                    aria-hidden="true"
                  ></span>
                  Please wait...
                </>
              ) : (
                <>
                  <i
                    className={`fas me-2 ${
                      mode === "login" ? "fa-sign-in-alt" : "fa-user-plus"
                    }`}
                  ></i>
                  {mode === "login" ? "Sign In" : "Create Account"}
                </>
              )}
            </button>
          </form>

          <div className="text-center mt-4">
            <p className="text-muted">
              {mode === "login"
                ? "Don't have an account?"
                : "Already have an account?"}
            </p>
            <button
              className="btn btn-link p-0"
              style={{ color: "#667eea", fontWeight: "600" }}
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
