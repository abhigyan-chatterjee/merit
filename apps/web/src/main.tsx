import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App";
import { ErrorBoundary } from "./components/ErrorBoundary";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {/* A render crash anywhere below would otherwise leave a blank document
        with no way back. The boundary keeps the recovery UI alive. */}
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>
);
