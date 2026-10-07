# 🌾 Crop Disease AI Web Application

An end-to-end, AI-powered Crop Disease Detection and Care Advisory web application. The platform provides automated plant leaf analysis, pathogen identification across 38 PlantVillage classes, computer vision lesion severity assessment, field weather telemetry, multilingual translation (English, Telugu, Hindi), and offline text-to-speech advisory.

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Requirements](#-requirements)
- [Installation & Setup](#-installation--setup)
- [Dataset Setup & Organization](#-dataset-setup--organization)
- [Model Training & ONNX Export](#-model-training--onnx-export)
- [Backend Startup](#-backend-startup)
- [Frontend Startup](#-frontend-startup)
- [Environment Variables](#-environment-variables)
- [API Documentation](#-api-documentation)
- [Severity & Health Score Methodology](#-severity--health-score-methodology)
- [Troubleshooting](#-troubleshooting)
- [Deployment Instructions](#-deployment-instructions)

---

## 🌿 Project Overview

Crop Disease AI empowers farmers and agronomists to diagnose leaf diseases quickly and accurately directly from their device.

**Key Features:**
- **Automatic Crop & Disease Detection:** No manual crop selection required. MobileNetV3 Small (ONNX runtime) classifies the leaf into 38 PlantVillage classes.
- **Out-of-Distribution (OOD) Safety Gating:** Temperature-calibrated confidence filtering safely abstains to `Unknown` instead of forcing incorrect diagnoses on out-of-domain images.
- **Independent Severity Assessment:** Severity and affected leaf surface areas are measured through Computer Vision color segmentation and the LLRL HLFA-Net model, completely decoupled from classification confidence (`severity != confidence`).
- **Multilingual Support:** Full UI and advisory translation in **English**, **తెలుగు (Telugu)**, and **हिन्दी (Hindi)**.
- **Offline Piper Speech Synthesis:** Native ONNX speech synthesis for English, Telugu, and Hindi audio output without relying on external cloud APIs or device TTS.
- **Local Weather Context:** Real-time temperature, humidity, rainfall, and pathogen infection risk analysis powered by Open-Meteo.
- **Local History & Analytics Dashboard:** Browser `localStorage`-backed history with real statistical breakdowns (health ratios, disease frequency distributions, host crop distributions).

---

## 🏛️ Architecture

```text
┌────────────────────────────────────────────────────────┐
│                   React 19 Frontend                    │
│   (Home • Camera/Upload • Results • History • Dash)    │
└───────────────────────────▲────────────────────────────┘
                            │ HTTP REST / JSON
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Backend                     │
│                 (Uvicorn ASGI Server)                  │
├────────────────────────────────────────────────────────┤
│ • /api/predict     : ONNX inference + CV severity gate │
│ • /api/model/classes: List supported classes           │
│ • /api/weather     : Open-Meteo telemetry & risk       │
│ • /api/translate   : Multilingual agricultural mapping │
│ • /api/speech      : Piper ONNX neural text-to-speech  │
│ • /api/health      : Availability & status check       │
├────────────────────────────────────────────────────────┤
│                       AI Models                        │
│ • Classifier : MobileNetV3-Small (ONNX opset 14/18)    │
│ • Severity   : LLRL HLFA-Net + OpenCV Color Lesion CV  │
│ • Voices     : Piper Medium ONNX (en_US, te_IN, hi_IN) │
└────────────────────────────────────────────────────────┘
```

---

## 💻 Requirements

### System Requirements
- **OS:** Windows 10/11 (or Linux/macOS)
- **Python:** 3.10 or 3.11+
- **Node.js:** v18.0.0 or higher
- **RAM:** Minimum 4 GB (8 GB recommended)

---

## 📦 Installation & Setup

### 1. Clone or Open Workspace
Open Windows PowerShell in the project root:
```powershell
cd c:\Users\PC\OneDrive\Desktop\crop
```

### 2. Python Environment Setup
The project contains a pre-configured virtual environment in `backend\venv`. To activate:
```powershell
.\backend\venv\Scripts\activate
```
To install or verify backend dependencies:
```powershell
pip install -r backend\requirements.txt
pip install onnx onnxruntime onnxscript
```

### 3. Frontend Setup
In a PowerShell terminal:
```powershell
cd frontend
npm install
cd ..
```

---

## 📂 Dataset Setup & Organization

The system uses the standard 38-class **PlantVillage** dataset, structured in ImageFolder format:

```text
PlantVillage-Dataset/
└── raw/
    └── color/
        ├── Apple___Apple_scab/
        ├── Apple___Black_rot/
        ├── Apple___Cedar_apple_rust/
        ├── Apple___healthy/
        ├── Blueberry___healthy/
        ├── Corn_(maize)___Common_rust_/
        ├── Tomato___Early_blight/
        └── ... (38 classes total)
```

The dataset split script validates image integrity and generates stratified CSV splits:
```powershell
.\backend\venv\Scripts\python.exe scripts\setup_dataset.py
```
- **Total Valid Images:** 54,305 across 38 classes
- **Splits:** Train (37,997 images, 70%), Validation (8,129 images, 15%), Test (8,179 images, 15%)

---

## 🤖 Model Training & ONNX Export

### Training MobileNetV3 Small
Run transfer learning training with temperature calibration:
```powershell
.\backend\venv\Scripts\activate
python backend\training\train.py
```
- **Architecture:** MobileNetV3-Small transfer learning
- **Best Validation Accuracy:** ~97.79%
- **Outputs:** `backend/model/crop_disease_mobilenetv3.pth`

### Evaluation
Evaluate the checkpoint against the 8,179 unseen test samples:
```powershell
python backend\training\evaluate.py
```
- **Accuracy:** 97.85%
- **Macro Precision:** 97.70%
- **Macro Recall:** 97.08%
- **Macro F1:** 97.29%

### Export to ONNX
Export the trained PyTorch model and labels to production ONNX runtime artifacts:
```powershell
python backend\training\export_onnx.py
```
Generates verified artifacts:
- `model/artifacts/model.onnx`
- `model/artifacts/labels.json`

---

## 🚀 Backend Startup

From the project root:
```powershell
.\backend\venv\Scripts\activate
uvicorn backend.app.main:app --reload --port 8000
```
Or from inside the `backend` directory:
```powershell
cd backend
..\backend\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Verify backend health:
```powershell
curl http://127.0.0.1:8000/api/health
```

---

## 🌐 Frontend Startup

In a separate terminal:
```powershell
cd frontend
npm run dev
```
The application will launch at:
`http://localhost:5173`

To build for production:
```powershell
npm run build
```

---

## ⚙️ Environment Variables

### Frontend (`frontend/.env` or `.env.local`)
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 📡 API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check, model availability, and class counts |
| `GET` | `/api/model/classes` | Returns the 38 supported plant pathology classes |
| `POST` | `/api/predict` | Multipart upload for leaf image diagnosis (JPG, PNG, WebP ≤ 10MB) |
| `GET` | `/api/weather` | Open-Meteo real-time telemetry (query `latitude`, `longitude`) |
| `POST` | `/api/translate` | Multilingual text translation (`en`, `te`, `hi`) |
| `POST` | `/api/speech` | Piper TTS neural audio generation (`en`, `te`, `hi`) |
| `POST` | `/api/tts` | Alias for `/api/speech` |

### Sample Response (`POST /api/predict`)
```json
{
  "success": true,
  "filename": "grape.png",
  "result": {
    "crop": "Grape",
    "condition": "Disease Detected",
    "disease": "Black rot",
    "confidence": 100.0,
    "probability_gap": 100.0,
    "reliability": "High",
    "reliability_message": "The model strongly favors this class based on leaf pattern matching.",
    "health_status": "Disease Detected",
    "unsupported": false
  },
  "severity": {
    "severity": "Medium",
    "affected_area": "14.9%",
    "health_score": 85,
    "method": "Estimated (Computer Vision Leaf Area Analysis)",
    "is_estimated": true
  },
  "disease_info": {
    "available": true,
    "disease_name": "Black rot",
    "crop_name": "Grape",
    "symptoms": [
      "Small circular spots appear on leaves with dark borders.",
      "Infected leaves may become distorted or dry up."
    ],
    "causes": "Fungal disease caused by Guignardia bidwellii.",
    "recommendations": [
      "Prune out mummified fruits and dead twigs during dormant season.",
      "Apply recommended bio-fungicides or captan/mancozeb during early shoot development.",
      "Improve drainage and avoid overhead irrigation."
    ],
    "prevention": [
      "Prune vines to maximize air circulation and sunlight penetration.",
      "Remove mummified berries from the vineyard floor."
    ]
  }
}
```

---

## 🔍 Severity & Health Score Methodology

The application strictly separates **Classification Confidence** from **Disease Severity**:
- Confidence reflects the statistical probability of the image matching a disease category.
- Severity measures how much of the plant leaf surface is compromised:
  - **Healthy Leaves:** Severity: `None`, Affected Area: `0%`, Health Score: `100`.
  - **Apple / Potato / Tomato:** Utilizes the pre-trained LLRL HLFA-Net deep-learning severity checkpoint when available.
  - **General Leaf Segmentation:** Uses OpenCV HSV color-space thresholding to isolate healthy leaf tissue from necrotic spots, chlorotic patches, and fungal mold, calculating the exact surface ratio:
    $$\text{Affected Area} = \frac{\text{Lesion Pixels}}{\text{Total Leaf Pixels}} \times 100\%$$
    - `< 12%`: Low Severity
    - `12% - 28%`: Medium Severity
    - `> 28%`: High Severity
    - $\text{Health Score} = 100 - \text{Affected Area}$

---

## 🛠️ Troubleshooting

1. **AI Model Unavailable (503 Error):**
   - Verify that `model/artifacts/model.onnx` and `model/artifacts/labels.json` exist.
   - If missing, re-run `python backend/training/export_onnx.py`.

2. **CORS / Network Error in Browser:**
   - Ensure the FastAPI server is running on port 8000: `http://127.0.0.1:8000`.
   - Check `frontend/.env` has `VITE_API_BASE_URL=http://127.0.0.1:8000`.

3. **Piper Voice Generation Notice:**
   - Voice models for `en`, `hi`, and `te` are stored in `backend/voices/`. Ensure files are not moved or renamed.

---

## 🚢 Deployment Instructions

### Production Frontend Build
```powershell
cd frontend
npm run build
```
Serve the generated `dist/` directory using Nginx, Cloudflare Pages, Vercel, or FastAPI static mounting.

### Production Backend Deployment
Run using Uvicorn with multiple workers behind an SSL reverse proxy (e.g., Caddy or Nginx):
```powershell
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---
*Developed with Google DeepMind Advanced Agentic Coding.*
