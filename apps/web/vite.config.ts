import path from "path";
import { fileURLToPath } from "url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
      },
    },
  },
  // Same-origin /api routing for `vite preview`, mirroring how the
  // production stack fronts the built bundle with a reverse proxy.
  //
  // The Host header is deliberately left alone. `changeOrigin: true` rewrites it
  // to the upstream's netloc, which makes the API's same-origin CSRF guard see
  // Origin (the browser's 4173) disagree with Host (8000) and reject every
  // state-changing request — sign-in included — with CSRF_ORIGIN_MISMATCH.
  preview: {
    port: 4173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
      },
    },
  },
});
