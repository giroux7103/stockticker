import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

import faviconUrl from './favicon.ico'

// 2. Dynamically find or create the favicon link tag
let faviconLink = document.querySelector("link[rel~='icon']")
if (!faviconLink) {
  faviconLink = document.createElement('link')
  faviconLink.rel = 'icon'
  document.head.appendChild(faviconLink)
}

// 3. Update the href attribute with the Vite-resolved asset path
faviconLink.href = faviconUrl

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
