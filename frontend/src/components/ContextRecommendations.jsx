// src/components/ContextRecommendations.jsx

function ContextRecommendations({ recommendations, onClick, darkMode }) {
  if (!Array.isArray(recommendations)) return null; // Safely exit if not an array

  return (
    <div className={`p-3 border-top ${darkMode ? "bg-dark text-white" : "bg-light"}`}>
      <h3 className="small fw-semibold mb-2">🧠 Recommendations:</h3>
      <div className="d-flex flex-wrap gap-2">
        {recommendations.map((rec, idx) => (
          <button
            key={idx}
            onClick={() => onClick(rec)}
            className={`btn btn-sm ${darkMode ? "btn-outline-light" : "btn-outline-primary"}`}
          >
            {rec}
          </button>
        ))}
      </div>
    </div>
  );
}

export default ContextRecommendations;
