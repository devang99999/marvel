import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import LoginRegister from "./components/LoginRegister.jsx";
// import Register from "./pages/Register";
import Chat from "./components/Chat.jsx";
// import LoginRegister from "./components/test.jsx"  // the file where you move your current chatbot logic

function App() {
  const isAuthenticated = !!localStorage.getItem("userId");

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={isAuthenticated ? <Chat /> : <Navigate to="/auth" />}
        />
        {/* <Route path="/c" element={isAuthenticated ? <Chat /> : <Navigate to="/auth" />} /> */}
        {/* <Route path="/" element={<Chat />} /> fallback to generate new */}
        <Route path="/auth" element={<LoginRegister />} />
      </Routes>
    </Router>
  );
}

export default App;
