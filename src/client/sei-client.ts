import crypto from "crypto";
import { getSeiConfig, SeiConfig } from "../config.js";

export type SeiService = "processos" | "documentos" | "parametros";

export interface RequestOptions {
  service: SeiService;
  path: string;
  method?: "GET" | "POST" | "PUT" | "DELETE";
  params?: Record<string, any>;
  body?: any;
  headers?: Record<string, string>;
  responseType?: "json" | "text" | "binary";
}

export interface SeiClientOptions {
  config?: SeiConfig;
}

export class SeiClient {
  private config: SeiConfig;
  private cachedToken: string | null = null;
  private tokenExpiresAt: number = 0;

  constructor(options?: SeiClientOptions) {
    this.config = options?.config || getSeiConfig();
  }

  /**
   * Generates a unique trace ID for each request.
   */
  public generateTraceId(): string {
    return `sei-mcp-${Date.now()}-${crypto.randomBytes(4).toString("hex")}`;
  }

  /**
   * Helper to convert UTF-8 string or Buffer to Base64
   */
  public static toBase64(data: string | Buffer): string {
    if (Buffer.isBuffer(data)) {
      return data.toString("base64");
    }
    return Buffer.from(data, "utf-8").toString("base64");
  }

  /**
   * Helper to decode Base64 to UTF-8 string
   */
  public static fromBase64(base64: string): string {
    return Buffer.from(base64, "base64").toString("utf-8");
  }

  /**
   * Helper to calculate MD5 hash of string or Buffer
   */
  public static calculateMd5(data: string | Buffer): string {
    return crypto.createHash("md5").update(data).digest("hex");
  }

  /**
   * Retrieves or refreshes OAuth2 token from IDP.SP or static configuration.
   */
  public async getAccessToken(): Promise<string> {
    // 1. Static token takes priority if configured
    if (this.config.idpspAccessToken) {
      return this.config.idpspAccessToken;
    }

    // 2. Return cached token if valid (with 60-second safety margin)
    const now = Date.now();
    if (this.cachedToken && this.tokenExpiresAt > now + 60000) {
      return this.cachedToken;
    }

    // 3. Authenticate via IDP.SP OAuth 2.0 Client Credentials flow
    if (this.config.idpspClientId && this.config.idpspClientSecret) {
      try {
        const bodyParams = new URLSearchParams({
          grant_type: "client_credentials",
          client_id: this.config.idpspClientId,
          client_secret: this.config.idpspClientSecret,
        });

        const res = await fetch(this.config.idpspTokenUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
          body: bodyParams.toString(),
        });

        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(
            `IDP.SP authentication failed (HTTP ${res.status}): ${errorText}`
          );
        }

        const data = (await res.json()) as {
          access_token: string;
          expires_in?: number;
        };

        this.cachedToken = data.access_token;
        const expiresInSec = data.expires_in || 3600;
        this.tokenExpiresAt = now + expiresInSec * 1000;
        return this.cachedToken;
      } catch (error: any) {
        throw new Error(
          `Failed to authenticate with IDP.SP: ${error?.message || error}`
        );
      }
    }

    return "";
  }

  /**
   * Resolves service base URL.
   */
  private getServiceBaseUrl(service: SeiService): string {
    switch (service) {
      case "processos":
        return this.config.seiProcessosUrl;
      case "documentos":
        return this.config.seiDocumentosUrl;
      case "parametros":
        return this.config.seiParametrosUrl;
      default:
        throw new Error(`Unknown SEI service: ${service}`);
    }
  }

  /**
   * Executes an HTTP request against the SEI API.
   */
  public async request<T = any>(options: RequestOptions): Promise<T> {
    const baseUrl = this.getServiceBaseUrl(options.service).replace(/\/+$/, "");
    const cleanPath = options.path.startsWith("/") ? options.path : `/${options.path}`;
    let url = `${baseUrl}${cleanPath}`;

    // Append query parameters
    if (options.params) {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(options.params)) {
        if (value !== undefined && value !== null && value !== "") {
          if (Array.isArray(value)) {
            value.forEach((v) => searchParams.append(key, String(v)));
          } else {
            searchParams.append(key, String(value));
          }
        }
      }
      const queryString = searchParams.toString();
      if (queryString) {
        url += (url.includes("?") ? "&" : "?") + queryString;
      }
    }

    const headers: Record<string, string> = {
      Accept: "application/json",
      "X-TraceId-SP": options.headers?.["X-TraceId-SP"] || this.generateTraceId(),
      "X-SiglaSistema":
        options.headers?.["X-SiglaSistema"] || this.config.siglaSistema,
      "X-IdentificacaoServico":
        options.headers?.["X-IdentificacaoServico"] ||
        this.config.identificacaoServico,
      "X-IdUnidade":
        options.headers?.["X-IdUnidade"] || this.config.idUnidade,
      ...options.headers,
    };

    if (this.config.regional || options.headers?.["X-Regional"]) {
      headers["X-Regional"] =
        options.headers?.["X-Regional"] || this.config.regional || "";
    }

    const token = await this.getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    let bodyData: any = undefined;
    if (options.body !== undefined && options.body !== null) {
      if (typeof options.body === "object") {
        headers["Content-Type"] = "application/json";
        bodyData = JSON.stringify(options.body);
      } else {
        bodyData = options.body;
      }
    }

    const method = options.method || "GET";

    let response: Response;
    try {
      response = await fetch(url, {
        method,
        headers,
        body: bodyData,
      });
    } catch (networkError: any) {
      throw new Error(
        `SEI API Network Request Failed (${method} ${url}): ${networkError.message || networkError}`
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return { success: true, status: 204 } as unknown as T;
    }

    // Handle binary responses (e.g. PDF attachments)
    if (options.responseType === "binary") {
      if (!response.ok) {
        const errText = await response.text();
        throw new Error(
          `SEI Error (${response.status} ${response.statusText}): ${errText}`
        );
      }
      const arrayBuffer = await response.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      return {
        base64: buffer.toString("base64"),
        sizeBytes: buffer.length,
        contentType: response.headers.get("content-type") || "application/pdf",
        contentDisposition: response.headers.get("content-disposition") || "",
      } as unknown as T;
    }

    const contentType = response.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");

    if (!response.ok) {
      let errorMessage = `SEI API Error (${response.status} ${response.statusText}) on ${method} ${url}`;
      if (isJson) {
        try {
          const errJson = await response.json();
          if (errJson.messages && Array.isArray(errJson.messages)) {
            errorMessage += `\nMessages: ${errJson.messages.join("; ")}`;
          } else if (errJson.message) {
            errorMessage += `\nMessage: ${errJson.message}`;
          }
          if (errJson.trace) {
            errorMessage += `\nTrace ID: ${errJson.trace}`;
          }
          errorMessage += `\nDetails: ${JSON.stringify(errJson, null, 2)}`;
        } catch {
          const rawText = await response.text();
          errorMessage += `\nBody: ${rawText}`;
        }
      } else {
        const rawText = await response.text();
        errorMessage += `\nBody: ${rawText}`;
      }
      throw new Error(errorMessage);
    }

    if (isJson) {
      return (await response.json()) as T;
    }

    return (await response.text()) as unknown as T;
  }
}

// Global default client instance
let defaultClient: SeiClient | null = null;

export function getSeiClient(): SeiClient {
  if (!defaultClient) {
    defaultClient = new SeiClient();
  }
  return defaultClient;
}
