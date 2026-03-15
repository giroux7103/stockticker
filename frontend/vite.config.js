import fs from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

function getHttpsConfig() {
  const useHttps = process.env.VITE_DEV_HTTPS === "true";
  if (!useHttps) {
    return undefined;
  }

  const certFile = process.env.VITE_DEV_SSL_CERT_FILE;
  const keyFile = process.env.VITE_DEV_SSL_KEY_FILE;
  if (!certFile || !keyFile) {
    throw new Error(
      "VITE_DEV_HTTPS=true requires VITE_DEV_SSL_CERT_FILE and VITE_DEV_SSL_KEY_FILE."
    );
  }

  return {
    cert: fs.readFileSync(certFile),
    key: fs.readFileSync(keyFile),
  };
}

export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.VITE_DEV_PORT || 5173),
    https: getHttpsConfig(),
  },
});
