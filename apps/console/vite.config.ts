import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const approvalTarget = env.VITE_APPROVAL_PROXY_TARGET ?? "http://127.0.0.1:8080";
  const incidentTarget = env.VITE_INCIDENT_STORE_PROXY_TARGET ?? "http://127.0.0.1:8080";
  const routerTarget = env.VITE_ROUTER_PROXY_TARGET ?? "http://127.0.0.1:8080";
  const auditTarget = env.VITE_AUDIT_PROXY_TARGET ?? "http://127.0.0.1:8080";
  const scenarioTarget = env.VITE_SCENARIO_PROXY_TARGET ?? "http://127.0.0.1:8080";

  return {
    server: {
      host: true,
      port: 5173,
      proxy: {
        "/api/approval": {
          target: approvalTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/approval/, "")
        },
        "/api/incidents-store": {
          target: incidentTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/incidents-store/, "")
        },
        "/api/router": {
          target: routerTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/router/, "")
        },
        "/api/audit": {
          target: auditTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/audit/, "")
        },
        "/api/scenario": {
          target: scenarioTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/scenario/, "")
        }
      }
    }
  };
});
