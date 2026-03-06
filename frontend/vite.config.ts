import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig(({ mode }) => {
  
  const env = loadEnv(mode, process.cwd(),'')
  const apiBaseUrl = env.BASE_URL ?? ""

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
      },
    },
    define: {
      BASE_URL: JSON.stringify(apiBaseUrl),
      TOKEN: JSON.stringify(env.TOKEN || ""),
      MOBILE: false,
    },
    server: {
      port: 5173,
      proxy: {
        "/api/agent": "http://127.0.0.1:8088",
        "/api/chats": "http://127.0.0.1:8088",
        "/api/config": "http://127.0.0.1:8088",
        "/api/cron": "http://127.0.0.1:8088",
        "/api/models": "http://127.0.0.1:8088",
        "/api/skills": "http://127.0.0.1:8088",
        "/api/envs": "http://127.0.0.1:8088",
        "/api/workspace": "http://127.0.0.1:8088",
        "/api/console": "http://127.0.0.1:8088",
        "/api/version": "http://127.0.0.1:8088",
        "/api/mcp": "http://127.0.0.1:8088",
      },
    },
    build: {
      outDir: "../backend/haibot/console",
      emptyOutDir: true,
      rollupOptions: {
        output: {
          manualChunks: {
            "vue-vendor": ["vue", "vue-router", "pinia"],
            "el-plus": ["element-plus", "@element-plus/icons-vue"],
            markdown: ["marked", "highlight.js"],
          },
        },
      },
    },
  };
});
