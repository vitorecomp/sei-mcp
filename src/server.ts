import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { createMcpServer } from "./mcp.js";
import { authenticateRequest } from "./auth.js";

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Map to store active SSE transport sessions by session ID
const activeTransports = new Map<string, SSEServerTransport>();

// Unauthenticated health check endpoint for Cloud / Load Balancers
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    service: "sei-mcp-server",
    authRequired: process.env.REQUIRE_AUTH !== "false",
    activeSessions: activeTransports.size,
  });
});

// SSE endpoint to open event stream (Authenticated)
app.get("/sse", authenticateRequest, async (req, res) => {
  console.log("🔌 Received SSE connection request");

  // SSEServerTransport takes the relative path where messages should be posted
  const transport = new SSEServerTransport("/messages", res);
  const server = createMcpServer();

  activeTransports.set(transport.sessionId, transport);
  console.log(`✅ Session created: ${transport.sessionId}`);

  transport.onclose = () => {
    console.log(`❌ Session closed: ${transport.sessionId}`);
    activeTransports.delete(transport.sessionId);
  };

  try {
    await server.connect(transport);
  } catch (error) {
    console.error(`Failed to connect session ${transport.sessionId}:`, error);
    activeTransports.delete(transport.sessionId);
  }
});

// POST endpoint to handle client JSON-RPC messages (Authenticated)
app.post("/messages", authenticateRequest, async (req, res) => {
  const sessionId = req.query.sessionId as string;

  if (!sessionId) {
    res.status(400).json({ error: "Bad Request: Missing 'sessionId' query parameter" });
    return;
  }

  const transport = activeTransports.get(sessionId);
  if (!transport) {
    res.status(404).json({ error: `Session not found or expired: ${sessionId}` });
    return;
  }

  try {
    await transport.handlePostMessage(req, res);
  } catch (error) {
    console.error(`Error handling message for session ${sessionId}:`, error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

const PORT = parseInt(process.env.PORT || "3000", 10);
const HOST = process.env.HOST || "0.0.0.0";

app.listen(PORT, HOST, () => {
  console.log(`\n==================================================`);
  console.log(`🚀 Enterprise MCP Server is running`);
  console.log(`🌐 Address: http://${HOST}:${PORT}`);
  console.log(`📡 SSE Endpoint: http://${HOST}:${PORT}/sse`);
  console.log(`🏥 Health Check: http://${HOST}:${PORT}/health`);
  console.log(`🔐 Authentication: ${process.env.REQUIRE_AUTH !== "false" ? "REQUIRED" : "DISABLED"}`);
  console.log(`==================================================\n`);
});
