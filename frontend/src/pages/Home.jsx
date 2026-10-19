import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSupportedCrops } from "../services/api";
import "./Home.css";

const STORAGE_KEY = "cropDiseaseAnalyses";

function Home() {
  const navigate = useNavigate();
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  const [supportedCrops, setSupportedCrops] = useState([]);
  const [cropsLoading, setCropsLoading] = useState(true);
  const [cropsError, setCropsError] = useState(null);

  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      if (Array.isArray(saved)) {
        setRecentAnalyses(saved.slice(0, 5));
      }
    } catch {
      setRecentAnalyses([]);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function loadCrops() {
      try {
        setCropsLoading(true);
        const res = await getSupportedCrops();
        if (isMounted) {
          if (res && res.crops && Array.isArray(res.crops)) {
            setSupportedCrops(res.crops);
            setCropsError(null);
          } else {
            setSupportedCrops([]);
            setCropsError("Supported crop list is currently unavailable.");
          }
        }
      } catch (err) {
        if (isMounted) {
          setSupportedCrops([]);
          setCropsError(err.message || "Supported crop list is currently unavailable.");
        }
      } finally {
        if (isMounted) {
          setCropsLoading(false);
        }
      }
    }
    loadCrops();
    return () => {
      isMounted = false;
    };
  }, []);

  const openRecent = (item) => {
    navigate("/result", {
      state: {
        prediction: {
          crop: item.crop,
          disease: item.disease,
          condition: item.condition,
          confidence: item.confidence,
          reliability: item.reliability || "High",
          health_status: item.condition,
          unsupported: item.condition === "Unknown",
        },
        severity: item.severityDetails || {
          severity: item.severity || "None",
          affected_area: item.affected_area || "0%",
          health_score: item.health_score || (item.condition === "Healthy" ? 100 : 75),
          is_estimated: true,
          method: "Historical Record",
        },
        disease_info: item.disease_info || null,
        symptoms: item.symptoms || null,
        fileName: item.fileName || "Historical Record",
        image: item.image || null,
      },
    });
  };

  return (
    <div className="home-page">
      <main>
        <section className="hero-section">
          <div className="hero-content">
            <span className="hero-badge">🌿 AI-Powered Plant Pathology</span>

            <h1>
              Crop Disease AI
              <span> Early Diagnosis &amp; Care</span>
            </h1>

            <p>
              Automated leaf disease diagnosis powered by MobileNetV3 transfer learning.
              Simply upload or capture an image of any crop leaf—the AI automatically identifies the
              crop, detects disease symptoms, measures severity, and provides actionable recommendations.
            </p>

            <div className="hero-buttons">
              <button
                className="primary-button"
                onClick={() => navigate("/analyze", { state: { autoCamera: true } })}
              >
                📷 Take Photo
              </button>

              <button
                className="secondary-button"
                onClick={() => navigate("/analyze")}
              >
                📁 Upload Image
              </button>

              <button
                className="secondary-button"
                onClick={() => navigate("/dashboard")}
              >
                📊 Dashboard
              </button>

              <button
                className="secondary-button"
                onClick={() => navigate("/history")}
              >
                📜 History
              </button>
            </div>

            <p className="privacy-note">
              🌱 No manual crop selection required. The AI detects the crop and condition automatically from the leaf photo.
            </p>
          </div>

          <div className="hero-visual">
            <div className="plant-illustration">
              <div className="leaf leaf-one">🌿</div>
              <div className="leaf leaf-two">🍃</div>
              <div className="leaf leaf-three">🌾</div>
              <div className="stem">│</div>
            </div>

            <div className="analysis-card">
              <div className="analysis-header">
                <span>Quick Diagnostic</span>
                <span className="status-dot">●</span>
              </div>

              <div className="analysis-result">
                <span>🍃</span>
                <div>
                  <strong>Diagnose a Crop Leaf</strong>
                  <small>Instant classification, severity estimate, and voice assistant in English, Telugu, or Hindi.</small>
                </div>
              </div>

              <button
                className="primary-button"
                onClick={() => navigate("/analyze")}
              >
                Start Analysis →
              </button>
            </div>
          </div>
        </section>

        {/* RECENT ANALYSES */}
        <section className="recent-analyses-section" style={{ marginTop: "32px" }}>
          <div className="section-heading">
            <span>Activity</span>
            <h2>Recent Analyses</h2>
            <p>Review your recent leaf diagnoses or start a fresh inspection.</p>
          </div>

          {recentAnalyses.length === 0 ? (
            <div style={{
              background: "#ffffff",
              padding: "28px",
              borderRadius: "12px",
              textAlign: "center",
              boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
              maxWidth: "600px",
              margin: "0 auto"
            }}>
              <p style={{ color: "#666", marginBottom: "16px" }}>
                No recent analyses yet. Upload or capture a crop leaf image to see your real diagnostic history here.
              </p>
              <button
                className="primary-button"
                onClick={() => navigate("/analyze")}
              >
                Analyze Your First Leaf
              </button>
            </div>
          ) : (
            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
              gap: "16px",
              maxWidth: "1000px",
              margin: "0 auto"
            }}>
              {recentAnalyses.map((item) => (
                <div
                  key={item.id}
                  onClick={() => openRecent(item)}
                  style={{
                    background: "#ffffff",
                    borderRadius: "10px",
                    padding: "16px",
                    boxShadow: "0 2px 6px rgba(0,0,0,0.06)",
                    cursor: "pointer",
                    borderLeft: `5px solid ${
                      item.condition === "Healthy"
                        ? "#2e7d32"
                        : item.condition === "Unknown"
                        ? "#f57c00"
                        : "#d32f2f"
                    }`,
                    transition: "transform 0.15s ease",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <strong style={{ fontSize: "1.05rem", color: "#1b382b" }}>{item.crop || "Unknown"}</strong>
                    <span style={{
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: "12px",
                      background: item.condition === "Healthy" ? "#e8f5e9" : item.condition === "Unknown" ? "#fff3e0" : "#ffebee",
                      color: item.condition === "Healthy" ? "#2e7d32" : item.condition === "Unknown" ? "#e65100" : "#c62828",
                    }}>
                      {item.condition}
                    </span>
                  </div>
                  <p style={{ margin: "4px 0", color: "#444", fontSize: "0.9rem" }}>
                    {item.disease}
                  </p>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", color: "#888", marginTop: "8px" }}>
                    <span>{item.date ? new Date(item.date).toLocaleDateString() : ""}</span>
                    {item.confidence && <span>{Number(item.confidence).toFixed(1)}% match</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* WORKFLOW GUIDE */}
        <section className="how-section">
          <div className="section-heading">
            <span>Simple Workflow</span>
            <h2>How It Works</h2>
            <p>Three straightforward steps to examine any crop leaf in your field.</p>
          </div>

          <div className="steps-grid">
            <div className="step-card">
              <div className="step-number">01</div>
              <div className="step-icon">📷</div>
              <h3>Capture or Upload</h3>
              <p>Take a sharp photo using your camera or upload a JPG, PNG, or WebP leaf image.</p>
            </div>

            <div className="step-card">
              <div className="step-number">02</div>
              <div className="step-icon">🧠</div>
              <h3>AI Inference &amp; Validation</h3>
              <p>Calibrated MobileNetV3 small classifier evaluates the leaf patterns with confidence safety gates.</p>
            </div>

            <div className="step-card">
              <div className="step-number">03</div>
              <div className="step-icon">📊</div>
              <h3>Actionable Care &amp; Voice</h3>
              <p>Receive disease identification, severity estimate, care tips, weather context, and speech guidance.</p>
            </div>
          </div>
        </section>

        {/* SUPPORTED CROPS SECTION */}
        <section className="supported-crops-section" id="supported-crops">
          <div className="section-heading">
            <span>Model Scope</span>
            <h2>Supported Crops</h2>
            <p>
              The AI model is trained and calibrated exclusively for the following {supportedCrops.length > 0 ? supportedCrops.length : 14} crop species.
            </p>
          </div>

          {cropsLoading ? (
            <div style={{ textAlign: "center", padding: "36px", color: "#666" }}>
              <span style={{ fontSize: "1.1rem" }}>🌱 Loading supported crops from trained model metadata...</span>
            </div>
          ) : cropsError || supportedCrops.length === 0 ? (
            <div style={{
              background: "#fff7ed",
              border: "1px solid #fed7aa",
              borderRadius: "12px",
              padding: "24px",
              textAlign: "center",
              maxWidth: "600px",
              margin: "20px auto 0",
              color: "#9a3412"
            }}>
              <span style={{ fontSize: "32px", display: "block", marginBottom: "8px" }}>⚠️</span>
              <strong style={{ fontSize: "1.05rem", display: "block" }}>Supported crop list is currently unavailable</strong>
              <p style={{ margin: "8px 0 0 0", fontSize: "0.9rem", color: "#7c2d12" }}>
                Unable to load verified crop labels from the AI model service. Please verify the backend is running.
              </p>
            </div>
          ) : (
            <div className="supported-crops-grid">
              {supportedCrops.map((crop) => (
                <div key={crop.name} className="supported-crop-card">
                  <span className="supported-crop-icon">{crop.icon || "🌱"}</span>
                  <span className="supported-crop-name">{crop.name}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="disclaimer">
          <strong>Notice:</strong> Crop Disease AI provides machine learning assisted assessments based on leaf image patterns. Always corroborate with local agronomic specialists before taking critical crop-protection interventions.
        </section>
      </main>

      <footer>
        <p>© 2026 Crop Disease AI • Automated Plant Pathology System</p>
      </footer>
    </div>
  );
}

export default Home;