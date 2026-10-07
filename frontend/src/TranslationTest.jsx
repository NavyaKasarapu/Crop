import { useState } from "react";
import { translateText } from "./services/translation/indicTransTranslator";

function TranslationTest() {
  const [language, setLanguage] = useState("te");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleTranslate = async () => {
    setLoading(true);
    setResult("");
    setError("");

    try {
      const translated = await translateText(
        "The detected disease is Early Blight. The plant needs proper care and regular monitoring.",
        language
      );

      setResult(translated);
    } catch (err) {
      console.error("Translation error:", err);
      setError(err.message || "Translation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        maxWidth: "800px",
        margin: "40px auto",
        padding: "30px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1>Translation Test</h1>

      <p>
        This test checks English → Telugu/Hindi translation in the browser.
      </p>

      <select
        value={language}
        onChange={(event) => setLanguage(event.target.value)}
        style={{
          padding: "10px",
          marginRight: "10px",
        }}
      >
        <option value="te">Telugu</option>
        <option value="hi">Hindi</option>
      </select>

      <button
        type="button"
        onClick={handleTranslate}
        disabled={loading}
        style={{
          padding: "10px 18px",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "TRANSLATING..." : "TRANSLATE"}
      </button>

      {loading && (
        <p>
          First translation may take some time because the AI model is
          loading in the browser.
        </p>
      )}

      {result && (
        <div
          style={{
            marginTop: "25px",
            padding: "20px",
            border: "1px solid #ccc",
            borderRadius: "10px",
          }}
        >
          <h2>Translated Result</h2>
          <p>{result}</p>
        </div>
      )}

      {error && (
        <div
          style={{
            marginTop: "25px",
            padding: "20px",
            color: "red",
            border: "1px solid red",
            borderRadius: "10px",
          }}
        >
          <strong>Error:</strong>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}

export default TranslationTest;