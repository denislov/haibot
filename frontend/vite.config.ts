import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import { resolve } from "path";

export default defineConfig(({ command, mode }) => {
  
  const env = loadEnv(mode, process.cwd(),'')

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        "@": resolve(__dirname, "src"),
      },
    },
    define: {
      __APP_ENV__: JSON.stringify(env.APP_ENV)
    },
    server: {
      port: 5173,
      proxy: {
        "/agent": "http://127.0.0.1:8088",
        "/chats": "http://127.0.0.1:8088",
        "/config": "http://127.0.0.1:8088",
        "/cron": "http://127.0.0.1:8088",
        "/models": "http://127.0.0.1:8088",
        "/skills": "http://127.0.0.1:8088",
        "/envs": "http://127.0.0.1:8088",
        "/workspace": "http://127.0.0.1:8088",
        "/console": "http://127.0.0.1:8088",
        "/version": "http://127.0.0.1:8088",
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
