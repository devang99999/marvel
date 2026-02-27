import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import LoginRegister from "./components/LoginRegister.jsx";
import Chat from "./components/Chat.jsx";

function App() {
  const isAuthenticated = !!localStorage.getItem("userId");

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            isAuthenticated ? (
              <Navigate to="/chat" replace />
            ) : (
              <LoginRegister />
            )
          }
        />
        <Route
          path="/chat"
          element={
            isAuthenticated ? (
              <Chat />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="/chat/:chatId"
          element={
            isAuthenticated ? (
              <Chat />
            ) : (
              <Navigate to="/" replace />
            )
          }
        />
        <Route
          path="*"
          element={
            <center>
              <h1>404 NOT FOUND</h1>
              <br />
              <a href="/">go to home page</a>
            </center>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
