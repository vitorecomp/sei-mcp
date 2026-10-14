"""Unit tests for WSDL schema parsing and SOAP 1.1 RPC/Encoded envelope serialization."""

from __future__ import annotations

import unittest
from lxml import etree

from src.client.sei_client import SeiSoapClient, SeiSoapFaultError
from src.config import SeiConfig


class TestWsdlAndSoapClient(unittest.TestCase):
    """Verifies WSDL schema registry and SOAP 1.1 RPC/Encoded serialization/deserialization."""

    def setUp(self) -> None:
        self.config = SeiConfig(
            sei_ws_url="https://sei.exemplo.gov.br/sei/controlador_ws.php?servico=sei",
            sei_wsdl_path="sei-documentation/sei.wsdl",
            sip_ws_url="https://sei.exemplo.gov.br/sip/controlador_ws.php?servico=wsdl",
            rh_ws_url="https://rh.exemplo.gov.br/ws/CargoFuncaoWS.php",
            sigla_sistema="SISTEMA_TESTE",
            identificacao_servico="TOKEN_SERVICO_123",
            id_unidade="110000999",
            soap_encoding="UTF-8",
            verify_ssl=True,
            timeout=30,
            port=3000,
            host="0.0.0.0",
            environment="test",
            oauth_enabled=False,
            oauth_client_id=None,
            oauth_protected_resource="https://mcp-demo-sei.aidemo.space",
            oauth_authorization_server="https://accounts.google.com",
        )
        self.client = SeiSoapClient(config=self.config)

    def test_wsdl_operations_loaded(self) -> None:
        """All 67 operations from sei.wsdl plus 3 SIP + 1 RH operation (71 total) must be registered."""
        self.assertEqual(len(self.client.registry.operations), 71)
        self.assertIn("gerarProcedimento", self.client.registry.operations)
        self.assertIn("incluirDocumento", self.client.registry.operations)
        self.assertIn("consultarProcedimento", self.client.registry.operations)
        self.assertIn("listarPermissao", self.client.registry.operations)
        self.assertIn("replicarPermissao", self.client.registry.operations)
        self.assertIn("replicarUsuario", self.client.registry.operations)
        self.assertIn("listarCargoFuncao", self.client.registry.operations)

    def test_build_soap_envelope_injects_sei_auth_credentials(self) -> None:
        """SiglaSistema, IdentificacaoServico, and default IdUnidade must be injected automatically."""
        xml_bytes, op_def = self.client.build_soap_envelope(
            "consultarProcedimento",
            {
                "ProtocoloProcedimento": "12.1.000000077-4",
                "SinRetornarAssuntos": "S",
            },
        )
        self.assertEqual(op_def.soap_action, "SeiAction")
        root = etree.fromstring(xml_bytes)
        self.assertEqual(root.xpath("string(//SiglaSistema)"), "SISTEMA_TESTE")
        self.assertEqual(root.xpath("string(//IdentificacaoServico)"), "TOKEN_SERVICO_123")
        self.assertEqual(root.xpath("string(//IdUnidade)"), "110000999")
        self.assertEqual(root.xpath("string(//ProtocoloProcedimento)"), "12.1.000000077-4")
        self.assertEqual(root.xpath("string(//SinRetornarAssuntos)"), "S")

    def test_build_soap_envelope_gerar_procedimento_complex_types(self) -> None:
        """Complex structures (Procedimento, ArrayOfAssunto, ArrayOfInteressado) serialize properly."""
        xml_bytes, _ = self.client.build_soap_envelope(
            "gerarProcedimento",
            {
                "Procedimento": {
                    "IdTipoProcedimento": "100000368",
                    "Especificacao": "Processo de Teste",
                    "Assuntos": [{"CodigoEstruturado": "00.01.01.01"}],
                    "Interessados": [{"Sigla": "dgx", "Nome": "Alberto"}],
                    "NivelAcesso": "0",
                },
                "UnidadesEnvio": ["110000015", "100000983"],
                "SinManterAbertoUnidade": "S",
            },
        )
        root = etree.fromstring(xml_bytes)
        self.assertEqual(
            root.xpath("string(//Procedimento/IdTipoProcedimento)"),
            "100000368",
        )
        self.assertEqual(
            root.xpath("string(//Procedimento/Assuntos/item/CodigoEstruturado)"),
            "00.01.01.01",
        )
        self.assertEqual(
            root.xpath("string(//Procedimento/Interessados/item/Nome)"),
            "Alberto",
        )
        unidades = [el.text for el in root.xpath("//UnidadesEnvio/item")]
        self.assertEqual(unidades, ["110000015", "100000983"])

    def test_parse_soap_response_and_multiref(self) -> None:
        """SOAP 1.1 responses with nested structs and arrays deserialize into dicts and lists."""
        sample_response = b"""<?xml version="1.0" encoding="UTF-8"?>
        <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
                           xmlns:ns1="Sei"
                           xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
                           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <SOAP-ENV:Body>
            <ns1:consultarProcedimentoResponse>
              <parametros xsi:type="ns1:RetornoConsultaProcedimento">
                <IdProcedimento>1210000000774</IdProcedimento>
                <ProcedimentoFormatado>12.1.000000077-4</ProcedimentoFormatado>
                <Especificacao>Compra de equipamentos</Especificacao>
                <AndamentoConclusao xsi:nil="true"/>
                <Assuntos SOAP-ENC:arrayType="ns1:Assunto[1]" xsi:type="SOAP-ENC:Array">
                  <item xsi:type="ns1:Assunto">
                    <CodigoEstruturado>00.01.01.01</CodigoEstruturado>
                    <Descricao>Material Permanente</Descricao>
                  </item>
                </Assuntos>
              </parametros>
            </ns1:consultarProcedimentoResponse>
          </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>"""

        parsed = self.client.parse_soap_response(sample_response, "consultarProcedimento")
        self.assertEqual(parsed["IdProcedimento"], "1210000000774")
        self.assertEqual(parsed["ProcedimentoFormatado"], "12.1.000000077-4")
        self.assertIsNone(parsed["AndamentoConclusao"])
        self.assertEqual(len(parsed["Assuntos"]), 1)
        self.assertEqual(parsed["Assuntos"][0]["CodigoEstruturado"], "00.01.01.01")

    def test_parse_soap_fault_raises_sei_soap_fault_error(self) -> None:
        """SOAP Fault envelopes raise SeiSoapFaultError with faultcode and faultstring."""
        fault_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
          <SOAP-ENV:Body>
            <SOAP-ENV:Fault>
              <faultcode>SOAP-ENV:Server</faultcode>
              <faultstring>Acesso Negado para este servidor.</faultstring>
            </SOAP-ENV:Fault>
          </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>"""

        with self.assertRaises(SeiSoapFaultError) as ctx:
            self.client.parse_soap_response(fault_xml, "listarUnidades")
        self.assertIn("Acesso Negado", str(ctx.exception))
        self.assertEqual(ctx.exception.operation, "listarUnidades")

    def test_base64_and_md5_helpers(self) -> None:
        """Base64 and MD5 helpers compute accurate values for adicionarArquivo & incluirDocumento."""
        html = "<p>Parecer Jurídico n. 123/2026</p>"
        b64 = SeiSoapClient.ensure_base64(html)
        # Calling ensure_base64 again on an already-encoded Base64 string must be idempotent
        self.assertEqual(SeiSoapClient.ensure_base64(b64), b64)
        size_str, md5_str = SeiSoapClient.compute_file_size_and_md5_from_base64(b64)
        self.assertEqual(int(size_str), len(html.encode("utf-8")))
        self.assertEqual(len(md5_str), 32)


if __name__ == "__main__":
    unittest.main()
