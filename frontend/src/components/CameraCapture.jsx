import { useEffect, useRef, useState, useCallback } from "react";

function CameraCapture({ onCapture, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const [cameraReady, setCameraReady] = useState(false);
  const [error, setError] = useState("");
  const [capturedImage, setCapturedImage] = useState(null); // { file, url }
  const [isStarting, setIsStarting] = useState(false);

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      try {
        streamRef.current.getTracks().forEach((track) => {
          track.stop();
        });
      } catch (e) {
        console.warn("Error stopping camera tracks:", e);
      }
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraReady(false);
  }, []);

  const startCamera = useCallback(async () => {
    setError("");
    setIsStarting(true);
    setCameraReady(false);

    // 1. Check for secure context
    if (
      typeof window !== "undefined" &&
      !window.isSecureContext &&
      window.location.hostname !== "localhost" &&
      window.location.hostname !== "127.0.0.1"
    ) {
      setError(
        "Camera access requires a secure connection (HTTPS or localhost). Please open this app over HTTPS or localhost, or upload a photo from your files."
      );
      setIsStarting(false);
      return;
    }

    // 2. Check for getUserMedia support
    if (!navigator.mediaDevices?.getUserMedia) {
      setError(
        "Camera access is not supported by this browser. Please use a modern browser (Chrome, Edge, Firefox, Safari) or use the 'Browse File' option."
      );
      setIsStarting(false);
      return;
    }

    // Make sure previous stream is stopped
    stopStream();

    try {
      let stream = null;
      try {
        // Prefer rear camera with reasonable resolution for leaf inspection
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" },
            width: { ideal: 1920 },
            height: { ideal: 1080 },
          },
          audio: false,
        });
      } catch (constraintErr) {
        // Fallback to basic video constraints if ideal constraints fail
        console.warn("Ideal video constraints failed, trying basic fallback:", constraintErr);
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      }

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        try {
          await videoRef.current.play();
        } catch (playErr) {
          // Some browsers require explicit user interaction or handle autoplay differently
          console.warn("video.play() notice:", playErr);
        }
        setCameraReady(true);
      }
    } catch (err) {
      console.error("Camera access error:", err);
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setError(
          "Camera permission was denied. Please allow camera access in your browser settings (look for the camera icon in your browser address bar) and try again."
        );
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        setError(
          "No camera hardware was detected on this device. You can upload an image using the 'Browse File' button instead."
        );
      } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
        setError(
          "The camera is currently in use by another application or browser tab. Please close any other apps using the camera and try again."
        );
      } else if (err.name === "SecurityError") {
        setError(
          "Camera access is restricted due to security policies. Please ensure you are accessing via HTTPS or localhost."
        );
      } else {
        setError(
          `Unable to access camera: ${err.message || "Unknown error occurred"}. Please use the 'Browse File' button to upload a leaf image.`
        );
      }
    } finally {
      setIsStarting(false);
    }
  }, [stopStream]);

  // Start camera on mount
  useEffect(() => {
    let active = true;
    startCamera();

    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopStream();
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      active = false;
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      stopStream();
    };
  }, [startCamera, stopStream]);

  // Clean up any captured object URL on unmount
  useEffect(() => {
    return () => {
      if (capturedImage?.url) {
        URL.revokeObjectURL(capturedImage.url);
      }
    };
  }, [capturedImage]);

  // Capture frame to canvas and convert to File/Blob
  const handleCapture = () => {
    if (!videoRef.current || !cameraReady) {
      return;
    }

    try {
      const video = videoRef.current;
      const width = video.videoWidth || 1280;
      const height = video.videoHeight || 720;

      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;

      const context = canvas.getContext("2d");
      context.drawImage(video, 0, 0, width, height);

      canvas.toBlob(
        (blob) => {
          if (!blob) {
            setError("Failed to create image snapshot from camera. Please try again.");
            return;
          }

          const file = new File([blob], `crop-camera-${Date.now()}.jpg`, {
            type: "image/jpeg",
          });
          const url = URL.createObjectURL(blob);

          // Stop live stream so camera hardware is released
          stopStream();

          setCapturedImage({ file, url });
          setError("");
        },
        "image/jpeg",
        0.92
      );
    } catch (err) {
      console.error("Frame capture error:", err);
      setError("Unable to capture frame: " + (err.message || "Unknown error"));
    }
  };

  // Retake photo: discard captured snapshot and restart camera
  const handleRetake = () => {
    if (capturedImage?.url) {
      URL.revokeObjectURL(capturedImage.url);
    }
    setCapturedImage(null);
    setError("");
    startCamera();
  };

  // Confirm photo and analyze immediately
  const handleConfirmAndAnalyze = () => {
    if (!capturedImage?.file) return;
    const file = capturedImage.file;
    const url = capturedImage.url;
    stopStream();
    onCapture({ file, url, autoAnalyze: true });
  };

  // Confirm photo and return to review on analyze page
  const handleUsePhoto = () => {
    if (!capturedImage?.file) return;
    const file = capturedImage.file;
    const url = capturedImage.url;
    stopStream();
    onCapture({ file, url, autoAnalyze: false });
  };

  // Close modal completely
  const handleClose = () => {
    stopStream();
    if (capturedImage?.url) {
      URL.revokeObjectURL(capturedImage.url);
    }
    onClose();
  };

  return (
    <div className="camera-overlay" role="dialog" aria-modal="true" aria-label="Camera Capture Dialog">
      <div className="camera-modal">
        <div className="camera-header">
          <div>
            <span className="camera-badge">CAMERA DIAGNOSTICS</span>
            <h2>{capturedImage ? "Review Captured Photo" : "Take a Crop Photo"}</h2>
            <p>
              {capturedImage
                ? "Verify the leaf is in focus and symptoms are clearly visible."
                : "Position the affected crop leaf clearly inside the viewfinder frame."}
            </p>
          </div>

          <button
            type="button"
            className="camera-close-btn"
            onClick={handleClose}
            aria-label="Close camera"
          >
            ×
          </button>
        </div>

        <div className="camera-preview">
          {capturedImage ? (
            <img
              src={capturedImage.url}
              alt="Captured leaf snapshot"
              style={{
                width: "100%",
                height: "100%",
                objectFit: "contain",
                display: "block",
                background: "#000",
              }}
            />
          ) : (
            <>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                onLoadedMetadata={() => setCameraReady(true)}
              />

              <div className="camera-frame">
                <span className="corner top-left"></span>
                <span className="corner top-right"></span>
                <span className="corner bottom-left"></span>
                <span className="corner bottom-right"></span>
              </div>

              {!cameraReady && !error && (
                <div className="camera-loading">
                  <span>🍃 Starting camera preview...</span>
                </div>
              )}
            </>
          )}
        </div>

        {error && (
          <div className="camera-error" role="alert">
            <span style={{ fontWeight: 700, display: "block", marginBottom: "4px" }}>
              ⚠️ Camera Notice
            </span>
            <span>{error}</span>
          </div>
        )}

        <div className="camera-controls">
          {capturedImage ? (
            <div
              style={{
                display: "flex",
                width: "100%",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              <button
                type="button"
                className="secondary-button"
                onClick={handleRetake}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "10px 18px",
                  borderRadius: "10px",
                  fontWeight: 700,
                  fontSize: "14px",
                  cursor: "pointer",
                }}
              >
                🔄 Retake Photo
              </button>

              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={handleUsePhoto}
                  style={{
                    padding: "10px 18px",
                    borderRadius: "10px",
                    fontWeight: 700,
                    fontSize: "14px",
                    cursor: "pointer",
                  }}
                >
                  ✓ Use Photo
                </button>

                <button
                  type="button"
                  className="primary-button"
                  onClick={handleConfirmAndAnalyze}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "10px 22px",
                    borderRadius: "10px",
                    background: "#2f8f46",
                    color: "#fff",
                    fontWeight: 700,
                    fontSize: "14px",
                    border: "none",
                    cursor: "pointer",
                  }}
                >
                  ✨ Analyze Leaf
                </button>
              </div>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                width: "100%",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <button
                type="button"
                className="camera-cancel-btn"
                onClick={handleClose}
              >
                Cancel
              </button>

              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" }}>
                <button
                  type="button"
                  className="capture-btn"
                  onClick={handleCapture}
                  disabled={!cameraReady || isStarting}
                  aria-label="Capture photo"
                  title={cameraReady ? "Capture photo" : "Waiting for camera..."}
                >
                  <span className="capture-inner"></span>
                </button>
                <span style={{ fontSize: "12px", color: "#4f6f57", fontWeight: 600 }}>
                  Capture Photo
                </span>
              </div>

              <div className="camera-control-space"></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default CameraCapture;