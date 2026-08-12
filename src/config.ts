import dotenv from "dotenv";

dotenv.config();

export interface SeiConfig {
  // Base URLs
  seiProcessosUrl: string;
  seiDocumentosUrl: string;
  seiParametrosUrl: string;

  // IDP.SP OAuth 2.0 / Bearer Authentication
  idpspTokenUrl: string;
  idpspClientId: string;
  idpspClientSecret: string;
  idpspAccessToken: string;

  // SEI Headers
  siglaSistema: string;
  identificacaoServico: string;
  idUnidade: string;
  regional?: string;

  // Server settings
  port: number;
  host: string;
}

export function getSeiConfig(): SeiConfig {
  return {
    seiProcessosUrl:
      process.env.SEI_PROCESSOS_URL ||
      "https://sei-processos.api-hml.rota.sp.gov.br",
    seiDocumentosUrl:
      process.env.SEI_DOCUMENTOS_URL ||
      "https://sei-documentos.api-hml.rota.sp.gov.br",
    seiParametrosUrl:
      process.env.SEI_PARAMETROS_URL ||
      "https://sei-parametros.api-hml.rota.sp.gov.br",

    idpspTokenUrl:
      process.env.IDPSP_TOKEN_URL ||
      "https://rhsso.idp-hml.sp.gov.br/auth/realms/idpsp/protocol/openid-connect/token",
    idpspClientId: process.env.IDPSP_CLIENT_ID || "",
    idpspClientSecret: process.env.IDPSP_CLIENT_SECRET || "",
    idpspAccessToken:
      process.env.SEI_BEARER_TOKEN || process.env.IDPSP_ACCESS_TOKEN || "",

    siglaSistema: process.env.SEI_SIGLA_SISTEMA || "",
    identificacaoServico: process.env.SEI_IDENTIFICACAO_SERVICO || "",
    idUnidade: process.env.SEI_ID_UNIDADE || "",
    regional: process.env.SEI_REGIONAL || undefined,

    port: parseInt(process.env.PORT || "3000", 10),
    host: process.env.HOST || "0.0.0.0",
  };
}
