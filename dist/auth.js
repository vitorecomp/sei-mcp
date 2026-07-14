/**
 * Express middleware to validate authentication credentials for MCP endpoint requests.
 * Supports:
 *  1. Header: `Authorization: Bearer <token>`
 *  2. Header: `x-api-key: <token>`
 *  3. Query param: `?token=<token>` (useful for browsers / native EventSource clients)
 */
export function authenticateRequest(req, res, next) {
    const requireAuth = process.env.REQUIRE_AUTH !== "false";
    if (!requireAuth) {
        return next();
    }
    const configuredToken = process.env.AUTH_TOKEN;
    if (!configuredToken) {
        console.warn("⚠️ AUTH_TOKEN is not configured in environment. Rejecting request.");
        res.status(500).json({ error: "Server authentication misconfigured." });
        return;
    }
    // Extract token from multiple supported locations
    const authHeader = req.headers["authorization"];
    let token;
    if (authHeader && authHeader.startsWith("Bearer ")) {
        token = authHeader.substring(7).trim();
    }
    else if (req.headers["x-api-key"]) {
        token = req.headers["x-api-key"];
    }
    else if (typeof req.query.token === "string") {
        token = req.query.token;
    }
    if (!token) {
        res.status(401).json({
            error: "Unauthorized",
            message: "Missing authentication token. Provide Authorization header (Bearer <token>) or x-api-key.",
        });
        return;
    }
    // Token comparison (simple secret token validation)
    if (token !== configuredToken) {
        res.status(403).json({
            error: "Forbidden",
            message: "Invalid authentication token.",
        });
        return;
    }
    // Verification succeeded
    next();
}
