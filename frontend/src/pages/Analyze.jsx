import { useRef, useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import CameraCapture from "../components/CameraCapture";
import { predictCropDisease } from "../services/api";
import "./Analyze.css";

function Analyze() {
  const navigate = useNavigate();
  const location = useLocation();
  const fileInputRef = useRef(null);

  const [selectedImage, setSelectedImage] = useState(null);
  const [error, setError] = useState("");
  const [showCamera, setShowCamera] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Auto-launch camera if requested from Home page
  useEffect(() => {
    if (location.state?.autoCamera) {
      setShowCamera(true);
    }
  }, [location.state]);

  const validateFile = (file) => {
    if (!file) {
      setError("Please select an image file.");
      return false;
    }

    const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type.toLowerCase())) {
      setError("Unsupported format. Please upload JPG, JPEG, PNG, or WebP.");
      return false;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError(`Image size (${(file.size / (1024 * 1024)).toFixed(1)} MB) exceeds 10 MB limit.`);
      return false;
    }

    setError("");
    return true;
  };

  const setFile = (file) => {
    if (!validateFile(file)) return;

    if (selectedImage?.url) {
      URL.revokeObjectURL(selectedImage.url);
    }

    const imageUrl = URL.createObjectURL(file);
    setSelectedImage({
      file,
      url: imageUrl,
    });
    setError("");
  };

  const handleUpload = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      setFile(file);
    }
    event.target.value = "";
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setFile(file);
    }
  };

  const handleCameraCapture = (file) => {
    if (file) {
      setFile(file);
    }
    setShowCamera(false);
  };

  const handleRemove = () => {
    if (selectedImage?.url) {
      URL.revokeObjectURL(selectedImage.url);
    }
    setSelectedImage(null);
    setError("");
  };

  const handleRetake = () => {
    handleRemove();
    setShowCamera(true);
  };

  const handleAnalyze = async () => {
    if (!selectedImage) {
      setError("Please upload or capture a crop leaf image first.");
      return;
    }

    setError("");
    setIsAnalyzing(true);

    try {
      const data = await predictCropDisease(selectedImage.file);

      navigate("/result", {
        state: {
          image: selectedImage.url,
          fileName: selectedImage.file.name,
          prediction: data.result,
          severity: data.severity,
          disease_info: data.disease_info,
          symptoms: data.symptoms,
        },
      });
    } catch (err) {
      console.error("Prediction error:", err);
      setError(err.message || "Unable to analyze the image. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="analyze-page">
      <div className="analyze-container">
        <div className="analyze-header">
          <h1>Analyze Crop Leaf</h1>
          <p>
            Upload or capture a sharp photo of the crop leaf for automatic disease diagnosis and severity assessment.
          </p>
        </div>

        {/* Drag & Drop / Upload area when no image is selected */}
        {!selectedImage && (
          <div
            className={`upload-dropzone ${isDragging ? "dragging" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            style={{
              border: isDragging ? "2px dashed #287443" : "2px dashed #b2d8c3",
              background: isDragging ? "#eaf6ee" : "#fbfdfc",
              borderRadius: "16px",
              padding: "36px 20px",
              textAlign: "center",
              marginBottom: "24px",
              transition: "all 0.2s ease",
            }}
          >
            <div style={{ fontSize: "42px", marginBottom: "12px" }}>🍃</div>
            <h3 style={{ margin: "0 0 8px 0", color: "#1b382b" }}>
              Drag &amp; Drop Leaf Image Here
            </h3>
            <p style={{ margin: "0 0 20px 0", color: "#666", fontSize: "0.95rem" }}>
              Supports JPG, JPEG, PNG, or WebP up to 10 MB
            </p>

            <div className="upload-options" style={{ display: "flex", justifyContent: "center", gap: "16px" }}>
              <button
                type="button"
                className="primary-button"
                onClick={() => fileInputRef.current?.click()}
              >
                📁 Browse File
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={() => {
                  setError("");
                  setShowCamera(true);
                }}
              >
                📷 Open Camera
              </button>
            </div>
          </div>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleUpload}
          style={{ display: "none" }}
        />

        {/* Selected Image Preview with Actions */}
        {selectedImage && (
          <div className="selected-image-section">
            <div className="image-preview-container">
              <img
                src={selectedImage.url}
                alt="Selected crop leaf"
                className="image-preview"
              />
            </div>

            <p className="selected-file-name">
              📄 {selectedImage.file.name} ({(selectedImage.file.size / 1024).toFixed(1)} KB)
            </p>

            <div className="analyze-actions" style={{ display: "flex", gap: "12px", justifyContent: "center", flexWrap: "wrap" }}>
              <button
                type="button"
                className="secondary-button"
                onClick={handleRemove}
                disabled={isAnalyzing}
              >
                🗑️ Remove
              </button>

              <button
                type="button"
                className="secondary-button"
                onClick={handleRetake}
                disabled={isAnalyzing}
              >
                🔄 Retake Photo
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                style={{ minWidth: "160px" }}
              >
                {isAnalyzing ? "🔬 Analyzing..." : "✨ Analyze Leaf"}
              </button>
            </div>
          </div>
        )}

        {/* Loading Indicator */}
        {isAnalyzing && (
          <div style={{
            margin: "20px auto",
            textAlign: "center",
            padding: "16px",
            background: "#f0fdf4",
            borderRadius: "8px",
            color: "#166534"
          }}>
            <div className="loading-spinner" style={{
              width: "28px",
              height: "28px",
              border: "3px solid #bbf7d0",
              borderTopColor: "#166534",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: "0 auto 8px auto"
            }} />
            <p style={{ margin: 0, fontWeight: 600 }}>
              Analyzing leaf patterns &amp; running AI inference...
            </p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-message" style={{ marginTop: "16px" }}>
            ⚠️ {error}
          </div>
        )}

        <div className="analyze-note" style={{ marginTop: "24px" }}>
          <strong>For Highest Diagnostic Accuracy:</strong>
          <span>
            Position a single leaf against a uniform background in daylight. Ensure symptoms are in sharp focus.
          </span>
        </div>
      </div>

      {showCamera && (
        <CameraCapture
          onCapture={handleCameraCapture}
          onClose={() => setShowCamera(false)}
        />
      )}
    </div>
  );
}

export default Analyze;