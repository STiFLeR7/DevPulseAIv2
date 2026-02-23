import express from "express";
import { createServer as createViteServer } from "vite";
import http from "http";

/**
 * Production static file server + Vite dev middleware.
 * All API/WS routes are proxied to the real FastAPI backend via vite.config.ts.
 * No mock routes needed.
 */
async function startServer() {
  const app = express();
  const server = http.createServer(app);
  const PORT = parseInt(process.env.PORT || "3000");

  if (process.env.NODE_ENV !== "production") {
    // Dev: Vite handles SPA + HMR + the proxy to FastAPI
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    // Prod: serve pre-built static files
    app.use(express.static("dist"));
    app.get("*", (_req, res) => {
      res.sendFile("dist/index.html", { root: "." });
    });
  }

  server.listen(PORT, "0.0.0.0", () => {
    console.log(`UI server running on http://localhost:${PORT}`);
  });
}

startServer();
