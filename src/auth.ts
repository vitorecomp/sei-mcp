import { Request, Response, NextFunction } from "express";
import { OAuth2Client } from "google-auth-library";

const TOOLS_CALL_METHOD = "tools/call";

/**
 * Middleware to enforce OAuth on MCP requests following the Google Chrome Enterprise Premium MCP pattern:
 * 1. Tool discovery requests (`initialize`, `tools/list`, etc.) are permitted without blocking discovery,
 *    allowing Gemini Enterprise "Reload custom actions" to always succeed.
 * 2. Tool execution requests (`tools/call`) require authentication if OAuth is enabled.
 */
export async function oauthMiddleware(req: Request, res: Response, next: NextFunction): Promise<void> {
  const isDev =
    process.env.NODE_ENV === "dev" ||
    process.env.NODE_ENV === "development" ||
    process.env.ENV === "dev";

  const oauthEnabled = process.env.OAUTH_ENABLED === "true" || (!isDev && process.env.OAUTH_ENABLED !== "false");

  // Only enforce OAuth for actual tool execution calls if enabled
  if (!oauthEnabled || !req.body || req.body.method !== TOOLS_CALL_METHOD) {
    return next();
  }

  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    res.status(401).json({
      jsonrpc: "2.0",
      error: {
        code: -32001,
        message: "Authentication required. Please provide a Bearer token in the Authorization header.",
      },
      id: req.body?.id || null,
    });
    return;
  }

  const token = authHeader.substring(7).trim();
  const audience = process.env.OAUTH_CLIENT_ID || process.env.GOOGLE_OAUTH_AUDIENCE;

  try {
    const auth = new OAuth2Client();
    const tokenInfo = await auth.getTokenInfo(token);

    if (audience && tokenInfo.aud !== audience) {
      console.warn(`⚠️ Token audience mismatch: ${tokenInfo.aud} vs ${audience}`);
      res.status(403).json({
        jsonrpc: "2.0",
        error: {
          code: -32001,
          message: `Invalid audience: expected ${audience}`,
        },
        id: req.body?.id || null,
      });
      return;
    }

    // Attach verified user info to request
    (req as any).user = tokenInfo;
    return next();
  } catch (error: any) {
    console.error("Error verifying OAuth token:", error?.message || error);
    res.status(401).json({
      jsonrpc: "2.0",
      error: {
        code: -32001,
        message: "Invalid or expired OAuth token.",
        data: error?.message,
      },
      id: req.body?.id || null,
    });
  }
}
