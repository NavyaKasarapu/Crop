import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Analyze from "./pages/Analyze";
import Result from "./pages/Result";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyze" element={<Analyze />} />
        <Route path="/result" element={<Result />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/history" element={<History />} />

        <Route
          path="*"
          element={
            <div
              style={{
                minHeight: "100vh",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexDirection: "column",
                gap: "12px",
                fontFamily: "Arial, sans-serif",
              }}
            >
              <h1>Page Not Found</h1>

              <button
                type="button"
                onClick={() => {
                  window.location.href = "/";
                }}
                style={{
                  padding: "12px 20px",
                  border: "none",
                  borderRadius: "8px",
                  background: "#287443",
                  color: "#ffffff",
                  cursor: "pointer",
                  fontWeight: "700",
                }}
              >
                BACK TO HOME
              </button>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;