import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./History.css";

const STORAGE_KEY = "cropDiseaseAnalyses";

function History() {
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = () => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      if (Array.isArray(saved)) {
        const sorted = saved.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
        setRecords(sorted);
      } else {
        setRecords([]);
      }
    } catch (error) {
      console.error("History loading error:", error);
      setRecords([]);
    }
  };

  const deleteRecord = (id, e) => {
    e.stopPropagation();
    const updated = records.filter((record) => record.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    setRecords(updated);
  };

  const clearHistory = () => {
    if (records.length === 0) return;
    if (window.confirm("Are you sure you want to clear your analysis history?")) {
      localStorage.removeItem(STORAGE_KEY);
      setRecords([]);
    }
  };

  const openRecord = (record) => {
    navigate("/result", {
      state: {
        prediction: {
          crop: record.crop,
          disease: record.disease,
          condition: record.condition,
          confidence: record.confidence,
          reliability: record.reliability || "High",
          health_status: record.condition,
          unsupported: record.condition === "Unknown",
        },
        severity: record.severityDetails || {
          severity: record.severity || "None",
          affected_area: record.affected_area || "0%",
          health_score: record.health_score || (record.condition === "Healthy" ? 100 : 75),
          is_estimated: true,
          method: "Historical Assessment",
        },
        disease_info: record.disease_info || null,
        symptoms: record.symptoms || null,
        fileName: record.fileName || "Historical Record",
        image: record.image || null,
      },
    });
  };

  const formatDate = (date) => {
    try {
      const parsed = new Date(date);
      if (Number.isNaN(parsed.getTime())) return "Unknown date";
      return parsed.toLocaleString();
    } catch {
      return "Unknown date";
    }
  };

  const getConditionStyle = (cond) => {
    if (cond === "Healthy") {
      return { bg: "#e8f5e9", color: "#2e7d32", border: "#a5d6a7" };
    }
    if (cond === "Unknown") {
      return { bg: "#fff3e0", color: "#e65100", border: "#ffcc80" };
    }
    return { bg: "#ffebee", color: "#c62828", border: "#ef9a9a" };
  };

  return (
    <div className="history-page">
      <div className="history-container">
        <div className="history-header">
          <div className="history-title-area">
            <div className="history-icon">📜</div>
            <div>
              <h1>Diagnostic History</h1>
              <p>Previously saved crop evaluations and records</p>
            </div>
          </div>

          <div className="history-count">
            {records.length} {records.length === 1 ? "Record" : "Records"}
          </div>
        </div>

        <div className="history-actions" style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "20px" }}>
          <button type="button" className="history-btn secondary" onClick={() => navigate("/")}>
            🏠 Home
          </button>
          <button type="button" className="history-btn secondary" onClick={() => navigate("/dashboard")}>
            📊 Dashboard
          </button>
          <button type="button" className="history-btn primary" onClick={() => navigate("/analyze")}>
            + Analyze New Leaf
          </button>
          {records.length > 0 && (
            <button type="button" className="history-btn" style={{ background: "#fee2e2", color: "#991b1b", border: "none" }} onClick={clearHistory}>
              🗑️ Clear All History
            </button>
          )}
        </div>

        {records.length === 0 ? (
          <div className="history-empty" style={{ textAlign: "center", padding: "60px 20px", background: "#ffffff", borderRadius: "12px" }}>
            <div style={{ fontSize: "56px", marginBottom: "16px" }}>📋</div>
            <h2>No History Found</h2>
            <p style={{ color: "#666", maxWidth: "450px", margin: "0 auto 20px auto" }}>
              Every time you diagnose a leaf photo, the complete analysis report will be securely saved right here in your browser.
            </p>
            <button type="button" className="history-btn primary" onClick={() => navigate("/analyze")}>
              Analyze First Leaf
            </button>
          </div>
        ) : (
          <div className="history-list" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {records.map((record) => {
              const style = getConditionStyle(record.condition);
              return (
                <div
                  key={record.id}
                  onClick={() => openRecord(record)}
                  className="history-card"
                  style={{
                    background: "#ffffff",
                    borderRadius: "12px",
                    padding: "20px",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                    cursor: "pointer",
                    borderLeft: `6px solid ${style.color}`,
                    transition: "transform 0.15s ease",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
                    <div>
                      <span style={{ fontSize: "0.8rem", color: "#777" }}>
                        🕒 {formatDate(record.date)}
                      </span>
                      <h2 style={{ margin: "4px 0", fontSize: "1.25rem", color: "#1b382b" }}>
                        {record.crop || "Unknown Crop"}
                      </h2>
                    </div>

                    <span
                      style={{
                        padding: "4px 12px",
                        borderRadius: "20px",
                        background: style.bg,
                        color: style.color,
                        fontWeight: 700,
                        fontSize: "0.85rem",
                      }}
                    >
                      {record.condition || "Unknown"}
                    </span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "12px", marginTop: "14px" }}>
                    <div>
                      <small style={{ color: "#777", display: "block" }}>DISEASE IDENTIFIED</small>
                      <strong style={{ color: "#222" }}>{record.disease || "None"}</strong>
                    </div>

                    {record.confidence && (
                      <div>
                        <small style={{ color: "#777", display: "block" }}>CONFIDENCE</small>
                        <strong style={{ color: "#222" }}>{Number(record.confidence).toFixed(1)}%</strong>
                      </div>
                    )}

                    {record.severity && (
                      <div>
                        <small style={{ color: "#777", display: "block" }}>SEVERITY</small>
                        <strong style={{ color: "#222" }}>{record.severity}</strong>
                      </div>
                    )}

                    {record.affected_area && (
                      <div>
                        <small style={{ color: "#777", display: "block" }}>AFFECTED AREA</small>
                        <strong style={{ color: "#222" }}>{record.affected_area}</strong>
                      </div>
                    )}
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px", paddingTop: "12px", borderTop: "1px solid #f0f0f0" }}>
                    <span style={{ fontSize: "0.85rem", color: "#287443", fontWeight: 600 }}>
                      🔍 Click to Open Full Diagnosis Report →
                    </span>
                    <button
                      type="button"
                      onClick={(e) => deleteRecord(record.id, e)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "#c62828",
                        cursor: "pointer",
                        fontSize: "0.85rem",
                        fontWeight: 600,
                      }}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default History;