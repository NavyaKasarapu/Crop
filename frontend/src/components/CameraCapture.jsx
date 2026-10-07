import { useEffect, useRef, useState } from "react";

function CameraCapture({ onCapture, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const [cameraReady, setCameraReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;

    const startCamera = async () => {
      try {
        setError("");

        if (!navigator.mediaDevices?.getUserMedia) {
          setError("Camera is not supported by this browser.");
          return;
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: { ideal: "environment" },
          },
          audio: false,
        });

        if (!mounted) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setCameraReady(true);
        }
      } catch (err) {
        console.error(err);

        if (err.name === "NotAllowedError") {
          setError(
            "Camera permission was denied. Please allow camera access."
          );
        } else if (err.name === "NotFoundError") {
          setError("No camera was found on this device.");
        } else {
          setError("Unable to access the camera.");
        }
      }
    };

    startCamera();

    return () => {
      mounted = false;

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => {
          track.stop();
        });

        streamRef.current = null;
      }
    };
  }, []);

  const handleCapture = () => {
    if (!videoRef.current || !cameraReady) {
      return;
    }

    const video = videoRef.current;

    const canvas = document.createElement("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError("Unable to capture image. Please try again.");
          return;
        }

        const file = new File(
          [blob],
          `crop-${Date.now()}.jpg`,
          {
            type: "image/jpeg",
          }
        );

        const url = URL.createObjectURL(blob);

        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => {
            track.stop();
          });

          streamRef.current = null;
        }

        onCapture({
          file,
          url,
        });
      },
      "image/jpeg",
      0.92
    );
  };

  const handleClose = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });

      streamRef.current = null;
    }

    onClose();
  };

  return (
    <div className="camera-overlay">
      <div className="camera-modal">

        <div className="camera-header">
          <div>
            <span className="camera-badge">
              CAMERA
            </span>

            <h2>Take a Crop Photo</h2>

            <p>
              Position the affected leaf clearly inside the frame.
            </p>
          </div>

          <button
            className="camera-close-btn"
            onClick={handleClose}
            aria-label="Close camera"
          >
            ×
          </button>
        </div>

        <div className="camera-preview">

          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
          />

          <div className="camera-frame">
            <span className="corner top-left"></span>
            <span className="corner top-right"></span>
            <span className="corner bottom-left"></span>
            <span className="corner bottom-right"></span>
          </div>

          {!cameraReady && !error && (
            <div className="camera-loading">
              Starting camera...
            </div>
          )}

        </div>

        {error && (
          <div className="camera-error">
            ⚠️ {error}
          </div>
        )}

        <div className="camera-controls">

          <button
            className="camera-cancel-btn"
            onClick={handleClose}
          >
            Cancel
          </button>

          <button
            className="capture-btn"
            onClick={handleCapture}
            disabled={!cameraReady}
            aria-label="Capture photo"
          >
            <span className="capture-inner"></span>
          </button>

          <div className="camera-control-space"></div>

        </div>

      </div>
    </div>
  );
}

export default CameraCapture;