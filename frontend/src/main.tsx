import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

// Tipografías servidas por la propia app (no por Google Fonts): así el panel se
// ve igual sin internet, cuando funcione como PWA instalada.
import "@fontsource/gloock/400.css";
import "@fontsource-variable/instrument-sans";
import "@fontsource/jetbrains-mono/500.css";
import "@fontsource/jetbrains-mono/700.css";

import { App } from "./App";
import "./estilos.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
