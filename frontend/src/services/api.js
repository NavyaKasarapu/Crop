const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function handleResponse(response, defaultError = "Request failed") {
  if (response.ok) {
    return await response.json();
  }

  let errorDetail = "";
  try {
    const errorData = await response.json();
    errorDetail = errorData.detail || errorData.message || "";
  } catch {
    // Non-JSON response
  }

  if (response.status === 503) {
    throw new Error(
      errorDetail || "AI model is currently unavailable. Please train/export the model first."
    );
  }

  if (response.status === 413) {
    throw new Error("Uploaded file is too large. Maximum file size is 10 MB.");
  }

  if (response.status === 400) {
    throw new Error(errorDetail || "Invalid request. Please verify the uploaded file.");
  }

  if (response.status >= 500) {
    throw new Error(
      errorDetail || "Server error occurred. Please try again or check the backend service."
    );
  }

  throw new Error(errorDetail || defaultError);
}

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`, {
      method: "GET",
    });
    return await handleResponse(response, "Health check failed");
  } catch (err) {
    return { status: "unreachable", error: err.message };
  }
}

export async function getModelClasses() {
  const response = await fetch(`${API_BASE_URL}/api/model/classes`, {
    method: "GET",
  });
  return await handleResponse(response, "Failed to load model classes");
}

export async function predictCropDisease(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/predict`, {
      method: "POST",
      body: formData,
    });
    return await handleResponse(response, "Prediction request failed");
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error(
        "Cannot connect to the backend server. Please verify FastAPI is running at " + API_BASE_URL
      );
    }
    throw error;
  }
}

export async function generateSpeech(text, language = "en") {
  try {
    const response = await fetch(`${API_BASE_URL}/api/speech`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        language,
      }),
    });

    if (!response.ok) {
      let message = "Speech synthesis failed.";
      try {
        const data = await response.json();
        message = data.detail || message;
      } catch {
        // Fallback
      }
      throw new Error(message);
    }

    return await response.blob();
  } catch (error) {
    if (error.name === "TypeError" && error.message.includes("fetch")) {
      throw new Error("Cannot connect to backend TTS service.");
    }
    throw error;
  }
}

export async function getWeather(latitude = 17.3850, longitude = 78.4867) {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/weather?latitude=${latitude}&longitude=${longitude}`,
      { method: "GET" }
    );
    if (!response.ok) {
      return { available: false, error: "Weather service unavailable" };
    }
    return await response.json();
  } catch (err) {
    return { available: false, error: err.message };
  }
}

export async function translateText(text, targetLanguage) {
  if (!text || targetLanguage === "en") return text;
  try {
    const response = await fetch(`${API_BASE_URL}/api/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target_language: targetLanguage }),
    });
    if (!response.ok) return text;
    const data = await response.json();
    return data.translated_text || text;
  } catch {
    return text; // Graceful fallback
  }
}

export async function translateTexts(texts, targetLanguage) {
  if (!texts || !texts.length || targetLanguage === "en") return texts;
  try {
    const response = await fetch(`${API_BASE_URL}/api/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texts, target_language: targetLanguage }),
    });
    if (!response.ok) return texts;
    const data = await response.json();
    return data.translated_texts || texts;
  } catch {
    return texts; // Graceful fallback
  }
}
