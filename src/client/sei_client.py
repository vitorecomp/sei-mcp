"""SOAP 1.1 RPC/Encoded Client for SEI and SIP Web Services (v3.1+)."""

from __future__ import annotations

import base64
import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from lxml import etree

from src.config import SeiConfig, get_sei_config

logger = logging.getLogger(__name__)

SOAP_ENV_NS = "http://schemas.xmlsoap.org/soap/envelope/"
SOAP_ENC_NS = "http://schemas.xmlsoap.org/soap/encoding/"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
WSDL_NS = "http://schemas.xmlsoap.org/wsdl/"
SEI_NS = "Sei"
SIP_NS = "Sip"


class SeiSoapFaultError(RuntimeError):
    """Exception raised when SEI/SIP returns a SOAP Fault or InfraException."""

    def __init__(
        self,
        operation: str,
        faultcode: str,
        faultstring: str,
        detail: Optional[Any] = None,
        status_code: int = 500,
    ) -> None:
        self.operation = operation
        self.faultcode = faultcode
        self.faultstring = faultstring
        self.detail = detail
        self.status_code = status_code
        msg = f"SEI SOAP Fault in '{operation}' [{faultcode}]: {faultstring}"
        if detail:
            msg += f" | Detail: {detail}"
        super().__init__(msg)


@dataclass
class WsdlElementDef:
    """Represents a field inside an XSD complexType."""

    name: str
    xsd_type: str
    min_occurs: int = 1
    nillable: bool = False


@dataclass
class WsdlOperationDef:
    """Represents a SOAP operation parsed from sei.wsdl or SIP specification."""

    name: str
    documentation: str
    namespace: str
    soap_action: str
    input_parts: List[Tuple[str, str]] = field(default_factory=list)
    output_parts: List[Tuple[str, str]] = field(default_factory=list)
    service: str = "sei"


class WsdlSchemaRegistry:
    """Parses sei.wsdl and registers SEI, SIP, and External RH SOAP definitions."""

    def __init__(self, wsdl_path: str) -> None:
        self.wsdl_path = wsdl_path
        self.array_item_types: Dict[str, str] = {}
        self.complex_types: Dict[str, List[WsdlElementDef]] = {}
        self.operations: Dict[str, WsdlOperationDef] = {}
        self._load_wsdl(wsdl_path)
        self._register_sip_and_rh_extensions()

    def _load_wsdl(self, wsdl_path: str) -> None:
        path = Path(wsdl_path)
        if not path.exists():
            logger.warning("WSDL file not found at %s; falling back to default path", wsdl_path)
            fallback = Path(__file__).resolve().parent.parent.parent / "sei-documentation" / "sei.wsdl"
            if fallback.exists():
                path = fallback
            else:
                return

        tree = etree.parse(str(path))
        ns = {
            "wsdl": WSDL_NS,
            "xsd": XSD_NS,
            "soap": "http://schemas.xmlsoap.org/wsdl/soap/",
        }

        # 1. Parse complexTypes (both ArrayOf* and struct types)
        for ctype in tree.xpath("//xsd:schema/xsd:complexType", namespaces=ns):
            type_name = ctype.get("name")
            if not type_name:
                continue

            # Check if SOAP-ENC:Array restriction
            restriction = ctype.find(".//xsd:restriction[@base='SOAP-ENC:Array']", namespaces=ns)
            if restriction is not None:
                attr = restriction.find("xsd:attribute", namespaces=ns)
                array_type = ""
                if attr is not None:
                    for k, v in attr.attrib.items():
                        if k.endswith("arrayType"):
                            array_type = v
                            break
                # e.g. "tns:Feriado[]" or "xsd:string[]"
                item_type = array_type[:-2] if array_type.endswith("[]") else "xsd:string"
                self.array_item_types[type_name] = item_type
                continue

            # Struct complexType (<xsd:all> or <xsd:sequence>)
            elements: List[WsdlElementDef] = []
            for elem in ctype.xpath(".//xsd:element", namespaces=ns):
                el_name = elem.get("name")
                el_type = elem.get("type", "xsd:string")
                min_occ = int(elem.get("minOccurs", "1"))
                nillable = elem.get("nillable", "false").lower() == "true"
                if el_name:
                    elements.append(
                        WsdlElementDef(
                            name=el_name,
                            xsd_type=el_type,
                            min_occurs=min_occ,
                            nillable=nillable,
                        )
                    )
            self.complex_types[type_name] = elements

        # 2. Parse messages
        messages: Dict[str, List[Tuple[str, str]]] = {}
        for msg in tree.xpath("//wsdl:message", namespaces=ns):
            msg_name = msg.get("name")
            if not msg_name:
                continue
            parts: List[Tuple[str, str]] = []
            for part in msg.xpath("wsdl:part", namespaces=ns):
                p_name = part.get("name")
                p_type = part.get("type", "xsd:string")
                if p_name:
                    parts.append((p_name, p_type))
            messages[msg_name] = parts

        # 3. Parse portType operations
        for op in tree.xpath("//wsdl:portType/wsdl:operation", namespaces=ns):
            op_name = op.get("name")
            if not op_name:
                continue
            doc = (op.findtext("wsdl:documentation", default="", namespaces=ns) or "").strip()
            in_el = op.find("wsdl:input", namespaces=ns)
            out_el = op.find("wsdl:output", namespaces=ns)
            in_msg_name = in_el.get("message", "").split(":")[-1] if in_el is not None else ""
            out_msg_name = out_el.get("message", "").split(":")[-1] if out_el is not None else ""

            self.operations[op_name] = WsdlOperationDef(
                name=op_name,
                documentation=doc,
                namespace=SEI_NS,
                soap_action="SeiAction",
                input_parts=messages.get(in_msg_name, []),
                output_parts=messages.get(out_msg_name, []),
                service="sei",
            )

    def _register_sip_and_rh_extensions(self) -> None:
        """Registers Section 4 (Serviços SIP) and Section 5 (Serviços Acessados em outros Sistemas)
        from SEI-WebServices-v3.1.pdf (pages 45-48)."""
        # SIP Usuario structure (page 45)
        self.complex_types["UsuarioSip"] = [
            WsdlElementDef("StaOperacao", "xsd:string"),
            WsdlElementDef("IdOrigem", "xsd:string", min_occurs=0, nillable=True),
            WsdlElementDef("IdOrgao", "xsd:string"),
            WsdlElementDef("Sigla", "xsd:string"),
            WsdlElementDef("Nome", "xsd:string"),
        ]
        self.array_item_types["ArrayOfUsuarioSip"] = "tns:Usuario"

        # SIP Permissao structure (page 46)
        self.complex_types["Permissao"] = [
            WsdlElementDef("StaOperacao", "xsd:string"),
            WsdlElementDef("IdSistema", "xsd:string"),
            WsdlElementDef("IdOrgaoUsuario", "xsd:string"),
            WsdlElementDef("IdUsuario", "xsd:string", min_occurs=0, nillable=True),
            WsdlElementDef("IdOrigemUsuario", "xsd:string", min_occurs=0, nillable=True),
            WsdlElementDef("IdOrgaoUnidade", "xsd:string"),
            WsdlElementDef("IdUnidade", "xsd:string", min_occurs=0, nillable=True),
            WsdlElementDef("IdOrigemUnidade", "xsd:string", min_occurs=0, nillable=True),
            WsdlElementDef("IdPerfil", "xsd:string"),
            WsdlElementDef("DataInicial", "xsd:string", min_occurs=0, nillable=True),
            WsdlElementDef("DataFinal", "xsd:string", min_occurs=0, nillable=True),
            WsdlElementDef("SinSubunidades", "xsd:string", min_occurs=0, nillable=True),
        ]
        self.array_item_types["ArrayOfPermissao"] = "tns:Permissao"
        self.array_item_types["ArrayOfCargoFuncao"] = "xsd:string"

        # SIP Operations (Section 4.2, pages 46-47)
        self.operations["listarPermissao"] = WsdlOperationDef(
            name="listarPermissao",
            documentation="Lista permissoes no SIP (Seção 4.2)",
            namespace=SIP_NS,
            soap_action="SipAction",
            input_parts=[
                ("IdSistema", "xsd:string"),
                ("IdOrgaoUsuario", "xsd:string"),
                ("IdUsuario", "xsd:string"),
                ("IdOrigemUsuario", "xsd:string"),
                ("IdOrgaoUnidade", "xsd:string"),
                ("IdUnidade", "xsd:string"),
                ("IdOrigemUnidade", "xsd:string"),
                ("IdPerfil", "xsd:string"),
            ],
            output_parts=[("Retorno", "tns:ArrayOfPermissao")],
            service="sip",
        )
        self.operations["replicarPermissao"] = WsdlOperationDef(
            name="replicarPermissao",
            documentation="Replica permissoes no SIP (Seção 4.2)",
            namespace=SIP_NS,
            soap_action="SipAction",
            input_parts=[
                ("Permissoes", "tns:ArrayOfPermissao"),
            ],
            output_parts=[("Retorno", "xsd:string")],
            service="sip",
        )
        self.operations["replicarUsuario"] = WsdlOperationDef(
            name="replicarUsuario",
            documentation="Replica usuarios no SIP (Seção 4.2)",
            namespace=SIP_NS,
            soap_action="SipAction",
            input_parts=[
                ("Usuarios", "tns:ArrayOfUsuarioSip"),
            ],
            output_parts=[("Retorno", "xsd:string")],
            service="sip",
        )

        # Section 5: listarCargoFuncao (page 48)
        self.operations["listarCargoFuncao"] = WsdlOperationDef(
            name="listarCargoFuncao",
            documentation="Lista cargos e funcoes do usuario em sistema externo de RH (Seção 5)",
            namespace=SEI_NS,
            soap_action="SeiAction",
            input_parts=[
                ("IdOrgao", "xsd:string"),
                ("IdOrigem", "xsd:string"),
                ("Sigla", "xsd:string"),
            ],
            output_parts=[("CargosFuncoes", "tns:ArrayOfCargoFuncao")],
            service="rh",
        )


def _lookup_case_insensitive(mapping: Dict[str, Any], target_key: str) -> Tuple[bool, Any]:
    """Finds a key in `mapping` matching `target_key` case-insensitively."""
    if target_key in mapping:
        return True, mapping[target_key]
    lower_target = target_key.lower()
    for k, v in mapping.items():
        if k.lower() == lower_target:
            return True, v
    return False, None


class SeiSoapClient:
    """SOAP 1.1 RPC/Encoded Client for SEI and SIP Web Services."""

    def __init__(self, config: Optional[SeiConfig] = None) -> None:
        self.config = config or get_sei_config()
        self.registry = WsdlSchemaRegistry(self.config.sei_wsdl_path)
        self.session = requests.Session()

    @staticmethod
    def to_base64(data: str | bytes) -> str:
        """Encodes UTF-8 text or raw bytes into a Base64 string."""
        if isinstance(data, str):
            raw = data.encode("utf-8")
        else:
            raw = data
        return base64.b64encode(raw).decode("ascii")

    @staticmethod
    def from_base64(b64_data: str) -> bytes:
        """Decodes a Base64 string into raw bytes."""
        clean = re.sub(r"\s+", "", b64_data)
        return base64.b64decode(clean)

    @classmethod
    def ensure_base64(cls, content: str) -> str:
        """Returns `content` as Base64. If it is plain text/HTML, encodes it to Base64."""
        stripped = re.sub(r"\s+", "", content)
        if (
            stripped
            and len(stripped) % 4 == 0
            and re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", stripped)
        ):
            try:
                base64.b64decode(stripped, validate=True)
                return stripped
            except Exception:
                pass
        return cls.to_base64(content)

    @staticmethod
    def calculate_md5(data: str | bytes) -> str:
        """Calculates the hexadecimal MD5 digest of `data` (used by adicionarArquivo)."""
        if isinstance(data, str):
            raw = data.encode("utf-8")
        else:
            raw = data
        return hashlib.md5(raw).hexdigest()

    @classmethod
    def compute_file_size_and_md5_from_base64(cls, b64_content: str) -> Tuple[str, str]:
        """Decodes Base64 file content and returns `(size_in_bytes_str, md5_hex_str)`."""
        raw_bytes = cls.from_base64(b64_content)
        return str(len(raw_bytes)), hashlib.md5(raw_bytes).hexdigest()

    def _format_scalar(self, field_name: str, value: Any) -> str:
        if isinstance(value, bool):
            if field_name.lower().startswith("sin"):
                return "S" if value else "N"
            return "true" if value else "false"
        return str(value)

    def _serialize_value(
        self,
        parent: etree._Element,
        tag_name: str,
        xsd_type: str,
        value: Any,
    ) -> etree._Element:
        """Serializes a Python value into a SOAP 1.1 RPC/Encoded XML element."""
        el = etree.SubElement(parent, tag_name)
        short_type = xsd_type.split(":")[-1]

        # 1. Check if this is an ArrayOf* type
        if short_type in self.registry.array_item_types:
            item_xsd_type = self.registry.array_item_types[short_type]
            if value is None:
                items_list: List[Any] = []
            elif isinstance(value, (list, tuple)):
                items_list = list(value)
            else:
                items_list = [value]

            el.set(f"{{{XSI_NS}}}type", "SOAP-ENC:Array")
            el.set(f"{{{SOAP_ENC_NS}}}arrayType", f"{item_xsd_type}[{len(items_list)}]")
            for item_val in items_list:
                self._serialize_value(el, "item", item_xsd_type, item_val)
            return el

        # 2. Check if value is None -> xsi:nil="true"
        if value is None:
            el.set(f"{{{XSI_NS}}}nil", "true")
            return el

        # 3. Check if this is a complex struct type (e.g. Procedimento, Documento, Contato)
        if short_type in self.registry.complex_types and isinstance(value, dict):
            xml_type_name = "tns:Usuario" if short_type == "UsuarioSip" else f"tns:{short_type}"
            el.set(f"{{{XSI_NS}}}type", xml_type_name)
            struct_fields = self.registry.complex_types[short_type]
            for fdef in struct_fields:
                found, fval = _lookup_case_insensitive(value, fdef.name)
                if not found:
                    # For nested arrays in Procedimento/Documento, SEI requires an empty array if not provided
                    f_short_type = fdef.xsd_type.split(":")[-1]
                    if f_short_type in self.registry.array_item_types:
                        self._serialize_value(el, fdef.name, fdef.xsd_type, [])
                    elif fdef.nillable or fdef.min_occurs == 0:
                        nil_child = etree.SubElement(el, fdef.name)
                        nil_child.set(f"{{{XSI_NS}}}nil", "true")
                    else:
                        nil_child = etree.SubElement(el, fdef.name)
                        nil_child.set(f"{{{XSI_NS}}}nil", "true")
                else:
                    self._serialize_value(el, fdef.name, fdef.xsd_type, fval)
            return el

        # 4. Scalar / primitive type (xsd:string, xsd:base64Binary, etc.)
        el.set(f"{{{XSI_NS}}}type", xsd_type if ":" in xsd_type else f"xsd:{xsd_type}")
        el.text = self._format_scalar(tag_name, value)
        return el

    def build_soap_envelope(
        self,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bytes, WsdlOperationDef]:
        """Builds a complete SOAP 1.1 RPC/Encoded XML request envelope for `operation`."""
        if operation not in self.registry.operations:
            raise ValueError(f"Unknown SEI/SIP SOAP operation: '{operation}'")

        op_def = self.registry.operations[operation]
        raw_params = dict(params or {})

        # Inject default SEI authentication credentials (SiglaSistema, IdentificacaoServico, IdUnidade)
        found_sigla, val_sigla = _lookup_case_insensitive(raw_params, "SiglaSistema")
        if not found_sigla or not val_sigla:
            raw_params["SiglaSistema"] = self.config.sigla_sistema

        found_ident, val_ident = _lookup_case_insensitive(raw_params, "IdentificacaoServico")
        if not found_ident or not val_ident:
            raw_params["IdentificacaoServico"] = self.config.identificacao_servico

        # Inject default IdUnidade only for SEI operations where IdUnidade is required or defaulted
        found_unid, val_unid = _lookup_case_insensitive(raw_params, "IdUnidade")
        if (not found_unid or val_unid is None or val_unid == "") and op_def.service == "sei":
            if self.config.id_unidade:
                raw_params["IdUnidade"] = self.config.id_unidade

        nsmap = {
            "SOAP-ENV": SOAP_ENV_NS,
            "tns": op_def.namespace,
            "xsd": XSD_NS,
            "xsi": XSI_NS,
            "SOAP-ENC": SOAP_ENC_NS,
        }

        envelope = etree.Element(f"{{{SOAP_ENV_NS}}}Envelope", nsmap=nsmap)
        envelope.set(f"{{{SOAP_ENV_NS}}}encodingStyle", SOAP_ENC_NS)
        body = etree.SubElement(envelope, f"{{{SOAP_ENV_NS}}}Body")
        op_el = etree.SubElement(body, f"{{{op_def.namespace}}}{op_def.name}")

        for part_name, part_type in op_def.input_parts:
            found, part_val = _lookup_case_insensitive(raw_params, part_name)
            if not found:
                part_val = None
            self._serialize_value(op_el, part_name, part_type, part_val)

        encoding = self.config.soap_encoding or "UTF-8"
        xml_bytes = etree.tostring(
            envelope,
            xml_declaration=True,
            encoding=encoding,
            pretty_print=False,
        )
        return xml_bytes, op_def

    def _deserialize_element(
        self,
        elem: etree._Element,
        id_map: Dict[str, etree._Element],
    ) -> Any:
        """Recursively converts a SOAP XML response element into Python dicts/lists/scalars."""
        # Resolve SOAP 1.1 multi-ref href="#id"
        href = elem.get("href")
        if href and href.startswith("#"):
            target = id_map.get(href[1:])
            if target is not None:
                elem = target

        # Check xsi:nil="true"
        nil_attr = elem.get(f"{{{XSI_NS}}}nil") or elem.get("nil")
        if nil_attr and nil_attr.lower() == "true":
            return None

        # Check if SOAP-ENC:Array
        xsi_type = elem.get(f"{{{XSI_NS}}}type") or ""
        array_type = None
        for k, v in elem.attrib.items():
            if k.endswith("arrayType"):
                array_type = v
                break

        children = [c for c in elem if isinstance(c.tag, str)]

        if array_type is not None or xsi_type.endswith(":Array") or xsi_type == "Array":
            return [self._deserialize_element(child, id_map) for child in children]

        if not children:
            return elem.text if elem.text is not None else ""

        # If all children are named <item> (common in PHP SoapServer array responses)
        child_tags = [etree.QName(c).localname for c in children]
        if all(t == "item" for t in child_tags):
            return [self._deserialize_element(child, id_map) for child in children]

        # Complex object / struct -> dict
        result: Dict[str, Any] = {}
        for child in children:
            local_name = etree.QName(child).localname
            val = self._deserialize_element(child, id_map)
            if local_name in result:
                if not isinstance(result[local_name], list):
                    result[local_name] = [result[local_name]]
                result[local_name].append(val)
            else:
                result[local_name] = val
        return result

    def parse_soap_response(self, xml_bytes: bytes, operation: str) -> Any:
        """Parses a SOAP 1.1 XML response envelope or raises `SeiSoapFaultError` on Fault."""
        parser = etree.XMLParser(recover=True, resolve_entities=False)
        root = etree.fromstring(xml_bytes, parser=parser)
        if root is None:
            raise ValueError(f"Empty or malformed XML response from SEI on '{operation}'")

        # Build multi-ref ID lookup map for href="#..." resolution
        id_map: Dict[str, etree._Element] = {}
        for el in root.iter():
            if isinstance(el.tag, str):
                el_id = el.get("id")
                if el_id:
                    id_map[el_id] = el

        # Locate SOAP Body
        body = None
        for child in root:
            if isinstance(child.tag, str) and etree.QName(child).localname == "Body":
                body = child
                break
        if body is None:
            body = root

        # Check for SOAP Fault
        for child in body:
            if not isinstance(child.tag, str):
                continue
            if etree.QName(child).localname == "Fault":
                faultcode = ""
                faultstring = ""
                detail_val: Any = None
                for fchild in child:
                    if not isinstance(fchild.tag, str):
                        continue
                    fname = etree.QName(fchild).localname
                    if fname == "faultcode":
                        faultcode = (fchild.text or "").strip()
                    elif fname == "faultstring":
                        faultstring = (fchild.text or "").strip()
                    elif fname == "detail":
                        detail_val = self._deserialize_element(fchild, id_map)
                raise SeiSoapFaultError(
                    operation=operation,
                    faultcode=faultcode or "SOAP-ENV:Server",
                    faultstring=faultstring or "Unknown SOAP Fault",
                    detail=detail_val,
                )

        # Extract response element (<{operation}Response>)
        for child in body:
            if not isinstance(child.tag, str):
                continue
            resp_children = [c for c in child if isinstance(c.tag, str)]
            if len(resp_children) == 1:
                # Typically <parametros>, <processo>, <Retorno>, or <CargosFuncoes>
                return self._deserialize_element(resp_children[0], id_map)
            return self._deserialize_element(child, id_map)

        return None

    def _resolve_endpoint_url(self, service: str) -> str:
        if service == "sip":
            if not self.config.sip_ws_url:
                raise ValueError("SIP_WS_URL is not configured for SIP Web Services.")
            return self.config.sip_ws_url
        if service == "rh":
            if not self.config.rh_ws_url:
                raise ValueError(
                    "RH_WS_URL is not configured for external RH CargoFuncao Web Service."
                )
            return self.config.rh_ws_url
        return self.config.sei_ws_url

    def call(
        self,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Executes a SOAP 1.1 RPC/Encoded call against SEI/SIP Web Services."""
        xml_bytes, op_def = self.build_soap_envelope(operation, params)
        endpoint_url = self._resolve_endpoint_url(op_def.service)
        encoding = self.config.soap_encoding or "UTF-8"

        headers = {
            "Content-Type": f"text/xml; charset={encoding}",
            "SOAPAction": f'"{op_def.soap_action}"',
            "Accept": "text/xml, application/soap+xml, application/xml",
            "User-Agent": "SEI-MCP-Server-Python/1.0",
        }

        try:
            response = self.session.post(
                endpoint_url,
                data=xml_bytes,
                headers=headers,
                verify=self.config.verify_ssl,
                timeout=self.config.timeout,
            )
        except requests.RequestException as exc:
            raise RuntimeError(
                f"SEI SOAP Network Request Failed ({operation} -> {endpoint_url}): {exc}"
            ) from exc

        # Even on HTTP 500, SOAP servers return <SOAP-ENV:Fault> in XML body
        if response.content and b"Envelope" in response.content:
            return self.parse_soap_response(response.content, operation)

        if not response.ok:
            raise RuntimeError(
                f"SEI HTTP Error ({response.status_code} {response.reason}) "
                f"on '{operation}' at {endpoint_url}: {response.text[:1000]}"
            )

        return self.parse_soap_response(response.content, operation)


_default_client: Optional[SeiSoapClient] = None


def get_sei_client(config: Optional[SeiConfig] = None) -> SeiSoapClient:
    """Returns a singleton `SeiSoapClient` instance (or creates a new one if `config` is passed)."""
    global _default_client
    if config is not None:
        return SeiSoapClient(config=config)
    if _default_client is None:
        _default_client = SeiSoapClient()
    return _default_client
