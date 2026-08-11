import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";
import { createMcpServer } from "./mcp.js";
import { oauthMiddleware } from "./auth.js";
dotenv.config();
const app = express();
app.use(cors());
app.use(express.json());
// Map to store active SSE transport sessions by session ID
const sseTransports = new Map();
// 1. Health check endpoint for Cloud Run and Load Balancers
app.get("/health", (_req, res) => {
    res.json({
        status: "healthy",
        service: "sei-mcp-server",
        protocol: "Model Context Protocol",
        transports: ["StreamableHTTP (/mcp)", "SSE (/sse)"],
        environment: process.env.NODE_ENV || "production",
    });
});
// 2. StreamableHTTP Endpoint (Modern MCP Standard used by Gemini Enterprise)
app.post("/mcp", oauthMiddleware, async (req, res) => {
    const server = createMcpServer();
    try {
        const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
        await server.connect(transport);
        await transport.handleRequest(req, res, req.body);
        res.on("close", () => {
            transport.close();
            server.close();
        });
    }
    catch (error) {
        console.error("Error handling MCP StreamableHTTP request:", error);
        if (!res.headersSent) {
            const status = error.status || 500;
            res.status(status).json({
                jsonrpc: "2.0",
                error: {
                    code: status === 401 ? -32001 : -32603,
                    message: error.message || "Internal server error",
                },
                id: null,
            });
        }
    }
});
app.get("/mcp", (_req, res) => {
    res.status(405).json({
        jsonrpc: "2.0",
        error: { code: -32000, message: "Method not allowed. Use POST for StreamableHTTP MCP requests." },
        id: null,
    });
});
// 3. Well-Known OAuth Discovery Endpoints (Used by Gemini Enterprise for automated OAuth discovery)
app.get("/.well-known/oauth-protected-resource", (_req, res) => {
    res.json({
        resource: process.env.OAUTH_PROTECTED_RESOURCE || "https://mcp-demo-sei.aidemo.space",
        authorization_servers: [
            process.env.OAUTH_AUTHORIZATION_SERVER || "https://accounts.google.com",
        ],
        scopes_supported: ["openid", "email", "profile"],
        bearer_methods_supported: ["header"],
    });
});
app.get("/.well-known/oauth-authorization-server", (_req, res) => {
    res.json({
        issuer: "https://accounts.google.com",
        authorization_endpoint: "https://accounts.google.com/o/oauth2/v2/auth",
        token_endpoint: "https://oauth2.googleapis.com/token",
        scopes_supported: ["openid", "email", "profile"],
        response_types_supported: ["code"],
    });
});
// 4. SSE Endpoints (Server-Sent Events transport)
app.get("/sse", oauthMiddleware, async (_req, res) => {
    console.log("🔌 Received SSE connection request");
    const server = createMcpServer();
    const transport = new SSEServerTransport("/messages", res);
    sseTransports.set(transport.sessionId, transport);
    res.on("close", () => {
        console.log(`❌ SSE Session closed: ${transport.sessionId}`);
        sseTransports.delete(transport.sessionId);
    });
    try {
        await server.connect(transport);
    }
    catch (error) {
        console.error(`Failed to connect SSE session ${transport.sessionId}:`, error);
        sseTransports.delete(transport.sessionId);
    }
});
app.post("/messages", oauthMiddleware, async (req, res) => {
    const sessionId = req.query.sessionId;
    if (!sessionId) {
        res.status(400).json({ error: "Bad Request: Missing 'sessionId' query parameter" });
        return;
    }
    const transport = sseTransports.get(sessionId);
    if (!transport) {
        res.status(404).json({ error: `Session not found or expired: ${sessionId}` });
        return;
    }
    try {
        await transport.handlePostMessage(req, res, req.body);
    }
    catch (error) {
        console.error(`Error handling message for session ${sessionId}:`, error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});
const PORT = parseInt(process.env.PORT || "3000", 10);
const HOST = process.env.HOST || "0.0.0.0";
app.listen(PORT, HOST, () => {
    console.log(`\n==================================================`);
    console.log(`🚀 Enterprise MCP Server running on port ${PORT}`);
    console.log(`🌐 StreamableHTTP Endpoint: http://${HOST}:${PORT}/mcp`);
    console.log(`📡 SSE Endpoint: http://${HOST}:${PORT}/sse`);
    console.log(`🏥 Health Check: http://${HOST}:${PORT}/health`);
    console.log(`==================================================\n`);
});
