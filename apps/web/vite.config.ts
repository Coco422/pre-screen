import { defineConfig } from "vitest/config";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("vue-pdf-embed") || id.includes("pdfjs-dist")) {
            return "pdf-viewer";
          }
        }
      }
    }
  },
  server: {
    proxy: {
      "/api": {
        target: "http://192.168.1.128:8000",
        // 192.168.1.128
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "")
      }
    }
  },
  test: {
    environment: "jsdom",
    globals: true
  }
});
