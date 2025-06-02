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
          element={isAuthenticated ? <Chat /> : <LoginRegister />}
        />
         <Route
        path="*"
        element={<> <center><h1>404 NOT FOUND <br/> <a href="/">go to home page</a></h1></center></>}
      />
      </Routes>
    </Router>
  );
}

export default App;
