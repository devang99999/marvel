function DarkModeToggle({ darkMode, setDarkMode }) {
  return (
    <button
      onClick={() => setDarkMode(!darkMode)}
      className={`btn btn-sm ${darkMode ? "btn-secondary" : "btn-outline-dark"}`}
    >
      {darkMode ? "☀️ Light" : "🌙 Dark"}
    </button>
  );
}

export default DarkModeToggle;
