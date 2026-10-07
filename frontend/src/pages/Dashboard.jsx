import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import "./Dashboard.css";

const STORAGE_KEY = "cropDiseaseAnalyses";

const CONDITION_COLORS = {
  Healthy: "#16a34a",
  Diseased: "#dc2626",
  Unsupported: "#f59e0b",
};

const CROP_PALETTE = [
  "#059669", "#2563eb", "#7c3aed", "#db2777", "#d97706",
  "#0891b2", "#65a30d", "#ca8a04", "#4f46e5", "#0d9488",
  "#e11d48", "#9333ea", "#0284c7", "#16a34a"
];

function Dashboard() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [cropChartType, setCropChartType] = useState("bar"); // "bar" or "pie"

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      setHistory(Array.isArray(saved) ? saved : []);
    } catch (error) {
      console.error("Unable to load history:", error);
      setHistory([]);
    }
  }, []);

  // 1. Metric Counts
  const total = history.length;
  const healthy = history.filter((item) => item.condition === "Healthy").length;
  const diseased = history.filter((item) => item.condition === "Disease Detected").length;
  const unsupported = history.filter(
    (item) =>
      item.condition === "Unsupported" ||
      item.condition === "Unknown" ||
      item.condition === "Unable to determine" ||
      item.unsupported === true ||
      item.crop === "Unsupported Image / Crop" ||
      item.crop === "Unknown"
  ).length;

  // 2. Condition Donut Chart Data
  const conditionDonutData = [
    { name: "Healthy", value: healthy, color: CONDITION_COLORS.Healthy },
    { name: "Diseased", value: diseased, color: CONDITION_COLORS.Diseased },
    { name: "Unsupported", value: unsupported, color: CONDITION_COLORS.Unsupported },
  ].filter((d) => d.value > 0);

  // 3. Predictions by Crop
  const cropCounts = {};
  history.forEach((item) => {
    const cropName = item.crop;
    if (
      cropName &&
      cropName !== "Unknown" &&
      cropName !== "Unsupported Image / Crop" &&
      cropName !== "Unknown / Unsupported"
    ) {
      cropCounts[cropName] = (cropCounts[cropName] || 0) + 1;
    }
  });

  const cropChartData = Object.entries(cropCounts)
    .map(([crop, count], index) => ({
      crop,
      count,
      percentage: total > 0 ? ((count / total) * 100).toFixed(1) : 0,
      fill: CROP_PALETTE[index % CROP_PALETTE.length],
    }))
    .sort((a, b) => b.count - a.count);

  // 4. Most Detected Diseases
  const diseaseCounts = {};
  history.forEach((item) => {
    const d = item.disease;
    if (
      d &&
      d !== "None" &&
      d !== "Healthy" &&
      d !== "Healthy (None detected)" &&
      d !== "Unknown" &&
      d !== "Unsupported Image / Crop" &&
      !d.includes("fallback") &&
      !d.includes("Unable to confidently identify")
    ) {
      diseaseCounts[d] = (diseaseCounts[d] || 0) + 1;
    }
  });

  const mostDetectedDiseases = Object.entries(diseaseCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const clearHistory = () => {
    if (window.confirm("Are you sure you want to clear all analysis history?")) {
      localStorage.removeItem(STORAGE_KEY);
      setHistory([]);
    }
  };

  const formatDate = (dateStr) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "-";
    }
  };

  const handleOpenResult = (item) => {
    navigate("/result", {
      state: {
        prediction: {
          crop: item.crop,
          disease: item.disease,
          condition: item.condition,
          confidence: item.confidence,
          unsupported: item.unsupported,
        },
        severity: {
          severity: item.severity,
          affected_area: item.affected_area,
          health_score: item.health_score,
        },
        disease_info: item.disease_info || {},
        image: item.image,
        fileName: item.fileName,
      },
    });
  };

  if (total === 0) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-container">
          <div className="dashboard-header">
            <div>
              <h1>📊 Crop Pathology &amp; Analytics Dashboard</h1>
              <p>Empirical statistics and distribution insights computed from real field inspections.</p>
            </div>
            <button
              type="button"
              className="dashboard-primary-button"
              onClick={() => navigate("/analyze")}
            >
              + Analyze First Leaf
            </button>
          </div>

          <div className="dashboard-empty-card">
            <div className="dashboard-empty-icon">🌱</div>
            <h2>No Field Analyses Recorded Yet</h2>
            <p>
              This dashboard reflects genuine diagnostic records from your usage. Upload or scan crop leaves to track health ratios, disease prevalence, and crop distributions.
            </p>
            <button
              type="button"
              className="dashboard-primary-button"
              onClick={() => navigate("/analyze")}
            >
              Start Analysis
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        {/* HEADER */}
        <div className="dashboard-header">
          <div>
            <h1>📊 Crop Pathology &amp; Analytics Dashboard</h1>
            <p>
              Empirical insights across <strong>{total}</strong> verified scan{total > 1 ? "s" : ""}.
            </p>
          </div>

          <div className="dashboard-header-actions">
            <button
              type="button"
              className="dashboard-clear-button"
              onClick={() => navigate("/")}
            >
              🏠 Home
            </button>
            <button
              type="button"
              className="dashboard-primary-button"
              onClick={() => navigate("/analyze")}
            >
              + New Analysis
            </button>
            <button
              type="button"
              className="dashboard-clear-button"
              onClick={clearHistory}
            >
              Clear History
            </button>
          </div>
        </div>

        {/* 1. REAL STAT SUMMARY CARDS */}
        <div className="dashboard-stat-grid">
          <div className="dashboard-stat-card total-card">
            <div className="stat-card-icon">📷</div>
            <div className="stat-card-body">
              <span className="stat-card-label">TOTAL SCANS</span>
              <strong className="stat-card-val">{total}</strong>
              <small className="stat-card-sub">Recorded locally</small>
            </div>
          </div>

          <div className="dashboard-stat-card healthy-card">
            <div className="stat-card-icon">🌿</div>
            <div className="stat-card-body">
              <span className="stat-card-label">HEALTHY COUNT</span>
              <strong className="stat-card-val" style={{ color: "#16a34a" }}>{healthy}</strong>
              <small className="stat-card-sub">
                {total > 0 ? `${((healthy / total) * 100).toFixed(1)}% of scans` : "0%"}
              </small>
            </div>
          </div>

          <div className="dashboard-stat-card diseased-card">
            <div className="stat-card-icon">🦠</div>
            <div className="stat-card-body">
              <span className="stat-card-label">DISEASED COUNT</span>
              <strong className="stat-card-val" style={{ color: "#dc2626" }}>{diseased}</strong>
              <small className="stat-card-sub">
                {total > 0 ? `${((diseased / total) * 100).toFixed(1)}% of scans` : "0%"}
              </small>
            </div>
          </div>

          <div className="dashboard-stat-card unsupported-card">
            <div className="stat-card-icon">⚠️</div>
            <div className="stat-card-body">
              <span className="stat-card-label">UNSUPPORTED COUNT</span>
              <strong className="stat-card-val" style={{ color: "#d97706" }}>{unsupported}</strong>
              <small className="stat-card-sub">
                {total > 0 ? `${((unsupported / total) * 100).toFixed(1)}% out-of-distribution` : "0%"}
              </small>
            </div>
          </div>
        </div>

        {/* 2. CHARTS SECTION (DONUT + PIE/BAR CROP CHART) */}
        <div className="dashboard-chart-grid">
          {/* DONUT CHART: Healthy vs Diseased vs Unsupported */}
          <div className="dashboard-card">
            <div className="card-header-row">
              <div>
                <h2>Health Ratio Distribution</h2>
                <p className="card-subtitle">Healthy vs Diseased vs Unsupported breakdown</p>
              </div>
            </div>

            <div className="chart-wrapper" style={{ height: "300px" }}>
              {conditionDonutData.length === 0 ? (
                <div className="chart-empty-state">No condition records available</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={conditionDonutData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={65}
                      outerRadius={95}
                      paddingAngle={4}
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    >
                      {conditionDonutData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val, name) => [`${val} (${((val / total) * 100).toFixed(1)}%)`, name]}
                      contentStyle={{ borderRadius: "8px", border: "1px solid #d1d5db" }}
                    />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="donut-legend-summary">
              <div className="donut-summary-pill" style={{ borderColor: "#16a34a" }}>
                <span className="pill-dot" style={{ background: "#16a34a" }} />
                <span>Healthy: <strong>{healthy}</strong></span>
              </div>
              <div className="donut-summary-pill" style={{ borderColor: "#dc2626" }}>
                <span className="pill-dot" style={{ background: "#dc2626" }} />
                <span>Diseased: <strong>{diseased}</strong></span>
              </div>
              <div className="donut-summary-pill" style={{ borderColor: "#f59e0b" }}>
                <span className="pill-dot" style={{ background: "#f59e0b" }} />
                <span>Unsupported: <strong>{unsupported}</strong></span>
              </div>
            </div>
          </div>

          {/* PIE / BAR CHART: Predictions by Crop */}
          <div className="dashboard-card">
            <div className="card-header-row">
              <div>
                <h2>Predictions by Crop</h2>
                <p className="card-subtitle">Frequency of scans across host crop species</p>
              </div>
              <div className="chart-view-toggle">
                <button
                  type="button"
                  className={`toggle-btn ${cropChartType === "bar" ? "active" : ""}`}
                  onClick={() => setCropChartType("bar")}
                >
                  Bar
                </button>
                <button
                  type="button"
                  className={`toggle-btn ${cropChartType === "pie" ? "active" : ""}`}
                  onClick={() => setCropChartType("pie")}
                >
                  Pie
                </button>
              </div>
            </div>

            <div className="chart-wrapper" style={{ height: "300px" }}>
              {cropChartData.length === 0 ? (
                <div className="chart-empty-state">No crop predictions recorded yet</div>
              ) : cropChartType === "bar" ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={cropChartData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis
                      dataKey="crop"
                      stroke="#4b5563"
                      fontSize={11}
                      interval={0}
                      angle={-25}
                      textAnchor="end"
                    />
                    <YAxis allowDecimals={false} stroke="#4b5563" fontSize={11} />
                    <Tooltip
                      formatter={(val) => [`${val} scans`, "Count"]}
                      contentStyle={{ borderRadius: "8px", border: "1px solid #d1d5db" }}
                    />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {cropChartData.map((entry, index) => (
                        <Cell key={`crop-cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={cropChartData}
                      dataKey="count"
                      nameKey="crop"
                      cx="50%"
                      cy="50%"
                      outerRadius={95}
                      label={({ crop, percent }) => `${crop} (${(percent * 100).toFixed(0)}%)`}
                    >
                      {cropChartData.map((entry, index) => (
                        <Cell key={`pie-cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val, name) => [`${val} scans`, name]}
                      contentStyle={{ borderRadius: "8px", border: "1px solid #d1d5db" }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>

        {/* 3. MOST DETECTED CROPS & DISEASES ROW */}
        <div className="dashboard-split-grid">
          {/* Most Detected Crops */}
          <div className="dashboard-card">
            <h2>🌱 Most Detected Crops</h2>
            <p className="card-subtitle">Highest frequency crop types from scans</p>

            {cropChartData.length === 0 ? (
              <p className="empty-subtext">No supported crops logged yet.</p>
            ) : (
              <div className="rank-list">
                {cropChartData.slice(0, 5).map((item, idx) => (
                  <div className="rank-item" key={item.crop}>
                    <div className="rank-index">#{idx + 1}</div>
                    <div className="rank-name">
                      <strong>{item.crop}</strong>
                    </div>
                    <div className="rank-badge">
                      {item.count} scan{item.count > 1 ? "s" : ""} ({item.percentage}%)
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Most Detected Diseases */}
          <div className="dashboard-card">
            <h2>🦠 Most Detected Diseases</h2>
            <p className="card-subtitle">Pathogens with the highest detection count</p>

            {mostDetectedDiseases.length === 0 ? (
              <p className="empty-subtext">No crop diseases diagnosed in history yet.</p>
            ) : (
              <div className="rank-list">
                {mostDetectedDiseases.map(([dis, count], idx) => (
                  <div className="rank-item" key={dis}>
                    <div className="rank-index disease-idx">#{idx + 1}</div>
                    <div className="rank-name">
                      <strong>{dis}</strong>
                    </div>
                    <div className="rank-badge disease-badge">
                      {count} case{count > 1 ? "s" : ""}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 4. RECENT PREDICTIONS LIST */}
        <div className="dashboard-card recent-scans-card">
          <div className="card-header-row">
            <div>
              <h2>🕒 Recent Predictions</h2>
              <p className="card-subtitle">Detailed log of recent leaf diagnostics</p>
            </div>
            <button
              type="button"
              className="text-link-button"
              onClick={() => navigate("/history")}
            >
              View Full History →
            </button>
          </div>

          <div className="recent-table-container">
            <table className="dashboard-recent-table">
              <thead>
                <tr>
                  <th>Preview</th>
                  <th>Date</th>
                  <th>Crop</th>
                  <th>Condition / Disease</th>
                  <th>Confidence</th>
                  <th>Severity</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {history.slice(0, 8).map((item) => {
                  const isH = item.condition === "Healthy";
                  const isU =
                    item.condition === "Unsupported" ||
                    item.condition === "Unknown" ||
                    item.unsupported;

                  return (
                    <tr key={item.id} onClick={() => handleOpenResult(item)} className="table-clickable-row">
                      <td className="thumb-cell">
                        {item.image ? (
                          <img src={item.image} alt={item.crop} className="table-thumb" />
                        ) : (
                          <div className="table-thumb-placeholder">🌿</div>
                        )}
                      </td>
                      <td>{formatDate(item.date)}</td>
                      <td>
                        <strong>{item.crop || "Unknown"}</strong>
                      </td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span
                            className="condition-chip"
                            style={{
                              background: isH ? "#dcfce7" : isU ? "#fef3c7" : "#fee2e2",
                              color: isH ? "#15803d" : isU ? "#b45309" : "#b91c1c",
                            }}
                          >
                            {item.condition}
                          </span>
                          <span className="disease-cell-name">{item.disease}</span>
                        </div>
                      </td>
                      <td>
                        <strong>
                          {item.confidence ? `${Number(item.confidence).toFixed(1)}%` : "N/A"}
                        </strong>
                      </td>
                      <td>{item.severity || "—"}</td>
                      <td>
                        <button
                          type="button"
                          className="view-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenResult(item);
                          }}
                        >
                          View Result
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;