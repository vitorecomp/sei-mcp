"""Process Management MCP Tools for SEI SOAP Web Services (SeiWS v3.1+)."""

from __future__ import annotations

from typing import Any, Dict, List

from src.client.sei_client import get_sei_client
from src.mcp_server import McpServer


def _yn(val: Any, default: str = "N") -> str:
    if val is None or val == "":
        return default
    if isinstance(val, bool):
        return "S" if val else "N"
    s = str(val).strip().upper()
    if s in ("S", "SIM", "TRUE", "1", "Y", "YES"):
        return "S"
    if s in ("N", "NAO", "NÃO", "FALSE", "0", "NO"):
        return "N"
    return s


def register_processos_tools(server: McpServer) -> None:
    """Registers all 25 Process-related SOAP operations from sei.wsdl."""
    client = get_sei_client()

    # 1. gerarProcedimento -> sei_gerar_processo
    server.register_tool(
        name="sei_gerar_processo",
        title="Gerar / Criar Novo Processo (SEI)",
        description=(
            "Cria um novo processo administrativo no SEI (serviço SOAP gerarProcedimento) "
            "com dados do Procedimento (IdTipoProcedimento, Especificacao, Assuntos, Interessados, "
            "Observacao, NivelAcesso, IdHipoteseLegal, IdTipoPrioridade), permitindo também incluir "
            "documentos iniciais, relacionar processos, enviar para unidades, aplicar marcador e definir prazo."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {
                    "type": "string",
                    "description": "ID da unidade no SEI (opcional; usa SEI_ID_UNIDADE por padrão).",
                },
                "idTipoProcedimento": {
                    "type": "string",
                    "description": "Identificador do tipo de processo no SEI (obtido via sei_listar_tipos_procedimento).",
                },
                "numeroProtocolo": {
                    "type": "string",
                    "description": "Número do processo caso informado manualmente (se omitido, o SEI gera automaticamente).",
                },
                "dataAutuacao": {
                    "type": "string",
                    "description": "Data de autuação do processo (DD/MM/AAAA). Se omitida, utiliza a data atual.",
                },
                "especificacao": {
                    "type": "string",
                    "description": "Especificação / síntese do objeto do processo.",
                },
                "assuntos": {
                    "type": "array",
                    "description": "Lista de assuntos do processo (ex: [{'CodigoEstruturado': '00.01.01.01'}]).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "CodigoEstruturado": {
                                "type": "string",
                                "description": "Código estruturado do assunto (ex: 00.01.01.01).",
                            },
                            "Descricao": {
                                "type": "string",
                                "description": "Descrição do assunto (opcional).",
                            },
                        },
                        "required": ["CodigoEstruturado"],
                    },
                },
                "interessados": {
                    "type": "array",
                    "description": "Lista de interessados do processo (ex: [{'Sigla': 'usr', 'Nome': 'Maria'}]).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "IdContato": {"type": "string"},
                            "Cpf": {"type": "string"},
                            "Cnpj": {"type": "string"},
                            "Sigla": {"type": "string", "description": "Sigla do participante."},
                            "Nome": {"type": "string", "description": "Nome do participante."},
                        },
                    },
                },
                "observacao": {
                    "type": "string",
                    "description": "Observação associada à unidade geradora.",
                },
                "nivelAcesso": {
                    "type": "string",
                    "enum": ["0", "1", "2"],
                    "description": "Nível de acesso: '0' = Público, '1' = Restrito, '2' = Sigiloso (se omitido, usa o padrão do tipo de processo).",
                },
                "idHipoteseLegal": {
                    "type": "string",
                    "description": "Identificador da hipótese legal (obrigatório quando nivelAcesso='1' ou '2').",
                },
                "idTipoPrioridade": {
                    "type": "string",
                    "description": "Identificador do tipo de prioridade do processo (opcional).",
                },
                "documentos": {
                    "type": "array",
                    "description": "Conjunto opcional de documentos (estrutura Documento) a serem gerados junto com o processo.",
                    "items": {"type": "object"},
                },
                "procedimentosRelacionados": {
                    "type": "array",
                    "description": "Lista de IDs ou protocolos de processos a serem relacionados automaticamente.",
                    "items": {"type": "string"},
                },
                "unidadesEnvio": {
                    "type": "array",
                    "description": "Lista de IDs de unidades para envio imediato do processo após a geração.",
                    "items": {"type": "string"},
                },
                "sinManterAbertoUnidade": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se o processo deve ser mantido aberto na unidade de origem (padrão 'S').",
                },
                "sinEnviarEmailNotificacao": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se deve enviar e-mail de aviso às unidades destinatárias (padrão 'N').",
                },
                "dataRetornoProgramado": {
                    "type": "string",
                    "description": "Data para Retorno Programado (DD/MM/AAAA).",
                },
                "diasRetornoProgramado": {
                    "type": "string",
                    "description": "Número de dias para Retorno Programado.",
                },
                "sinDiasUteisRetornoProgramado": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se a contagem de dias de retorno programado é em dias úteis (padrão 'N').",
                },
                "idMarcador": {
                    "type": "string",
                    "description": "Opcional. ID de marcador da unidade para associação imediata.",
                },
                "textoMarcador": {
                    "type": "string",
                    "description": "Opcional. Texto do marcador.",
                },
                "dataControlePrazo": {
                    "type": "string",
                    "description": "Opcional. Data para definição de controle de prazo (DD/MM/AAAA).",
                },
                "diasControlePrazo": {
                    "type": "string",
                    "description": "Opcional. Número de dias para controle de prazo.",
                },
                "sinDiasUteisControlePrazo": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se os dias do controle de prazo são dias úteis.",
                },
            },
            "required": ["idTipoProcedimento"],
        },
        handler=lambda args: client.call(
            "gerarProcedimento",
            {
                "IdUnidade": args.get("idUnidade"),
                "Procedimento": {
                    "IdTipoProcedimento": args["idTipoProcedimento"],
                    "NumeroProtocolo": args.get("numeroProtocolo"),
                    "DataAutuacao": args.get("dataAutuacao"),
                    "Especificacao": args.get("especificacao"),
                    "Assuntos": args.get("assuntos") or [],
                    "Interessados": args.get("interessados") or [],
                    "Observacao": args.get("observacao"),
                    "NivelAcesso": args.get("nivelAcesso"),
                    "IdHipoteseLegal": args.get("idHipoteseLegal"),
                    "IdTipoPrioridade": args.get("idTipoPrioridade"),
                },
                "Documentos": args.get("documentos") or [],
                "ProcedimentosRelacionados": args.get("procedimentosRelacionados") or [],
                "UnidadesEnvio": args.get("unidadesEnvio") or [],
                "SinManterAbertoUnidade": _yn(args.get("sinManterAbertoUnidade"), "S"),
                "SinEnviarEmailNotificacao": _yn(args.get("sinEnviarEmailNotificacao"), "N"),
                "DataRetornoProgramado": args.get("dataRetornoProgramado"),
                "DiasRetornoProgramado": args.get("diasRetornoProgramado"),
                "SinDiasUteisRetornoProgramado": _yn(
                    args.get("sinDiasUteisRetornoProgramado"), "N"
                ),
                "IdMarcador": args.get("idMarcador"),
                "TextoMarcador": args.get("textoMarcador"),
                "DataControlePrazo": args.get("dataControlePrazo"),
                "DiasControlePrazo": args.get("diasControlePrazo"),
                "SinDiasUteisControlePrazo": _yn(args.get("sinDiasUteisControlePrazo"), "N"),
            },
        ),
    )

    # 2. consultarProcedimento -> sei_consultar_processo
    server.register_tool(
        name="sei_consultar_processo",
        title="Consultar Processo por Protocolo (SEI)",
        description=(
            "Consulta metadados e detalhes de um processo no SEI pelo seu número de protocolo "
            "(serviço SOAP consultarProcedimento), permitindo retornar assuntos, interessados, "
            "observações, andamentos de geração/conclusão/último, unidades onde está aberto e processos relacionados/anexados."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {
                    "type": "string",
                    "description": "ID da unidade no SEI (opcional; usa SEI_ID_UNIDADE por padrão).",
                },
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo visível para o usuário (ex: 12.1.000000077-4).",
                },
                "sinRetornarAssuntos": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno dos assuntos do processo (padrão 'N').",
                },
                "sinRetornarInteressados": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno dos interessados do processo (padrão 'N').",
                },
                "sinRetornarObservacoes": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno das observações das unidades (padrão 'N').",
                },
                "sinRetornarAndamentoGeracao": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno do andamento de geração (padrão 'N').",
                },
                "sinRetornarAndamentoConclusao": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno do andamento de conclusão (padrão 'N').",
                },
                "sinRetornarUltimoAndamento": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno do último andamento (padrão 'N').",
                },
                "sinRetornarUnidadesProcedimentoAberto": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno das unidades onde o processo está aberto (padrão 'N').",
                },
                "sinRetornarProcedimentosRelacionados": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno dos processos relacionados (padrão 'N').",
                },
                "sinRetornarProcedimentosAnexados": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno dos processos anexados (padrão 'N').",
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "consultarProcedimento",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "SinRetornarAssuntos": _yn(args.get("sinRetornarAssuntos"), "N"),
                "SinRetornarInteressados": _yn(args.get("sinRetornarInteressados"), "N"),
                "SinRetornarObservacoes": _yn(args.get("sinRetornarObservacoes"), "N"),
                "SinRetornarAndamentoGeracao": _yn(args.get("sinRetornarAndamentoGeracao"), "N"),
                "SinRetornarAndamentoConclusao": _yn(
                    args.get("sinRetornarAndamentoConclusao"), "N"
                ),
                "SinRetornarUltimoAndamento": _yn(args.get("sinRetornarUltimoAndamento"), "N"),
                "SinRetornarUnidadesProcedimentoAberto": _yn(
                    args.get("sinRetornarUnidadesProcedimentoAberto"), "N"
                ),
                "SinRetornarProcedimentosRelacionados": _yn(
                    args.get("sinRetornarProcedimentosRelacionados"), "N"
                ),
                "SinRetornarProcedimentosAnexados": _yn(
                    args.get("sinRetornarProcedimentosAnexados"), "N"
                ),
            },
        ),
    )

    # 3. consultarProcedimentoIndividual -> sei_consultar_processo_individual
    server.register_tool(
        name="sei_consultar_processo_individual",
        title="Consultar Processo Individual por Usuário Interessado (SEI)",
        description=(
            "Consulta processos individuais (onde o tipo de processo está configurado como "
            "'Processo único no órgão por usuário interessado') a partir do órgão, tipo de processo e sigla do usuário "
            "(serviço SOAP consultarProcedimentoIndividual)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idOrgaoProcedimento": {
                    "type": "string",
                    "description": "Identificador do órgão do processo.",
                },
                "idTipoProcedimento": {
                    "type": "string",
                    "description": "Identificador do tipo do processo.",
                },
                "idOrgaoUsuario": {
                    "type": "string",
                    "description": "Identificador do órgão do usuário interessado.",
                },
                "siglaUsuario": {
                    "type": "string",
                    "description": "Sigla do usuário interessado.",
                },
            },
            "required": [
                "idOrgaoProcedimento",
                "idTipoProcedimento",
                "idOrgaoUsuario",
                "siglaUsuario",
            ],
        },
        handler=lambda args: client.call(
            "consultarProcedimentoIndividual",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdOrgaoProcedimento": args["idOrgaoProcedimento"],
                "IdTipoProcedimento": args["idTipoProcedimento"],
                "IdOrgaoUsuario": args["idOrgaoUsuario"],
                "SiglaUsuario": args["siglaUsuario"],
            },
        ),
    )

    # 4. excluirProcesso -> sei_excluir_processo
    server.register_tool(
        name="sei_excluir_processo",
        title="Excluir Processo (SEI)",
        description="Exclui um processo no SEI (serviço SOAP excluirProcesso).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo visível para o usuário (ex: 12.1.000000077-4).",
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "excluirProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
            },
        ),
    )

    # 5. enviarProcesso -> sei_enviar_processo
    server.register_tool(
        name="sei_enviar_processo",
        title="Enviar / Tramitar Processo para Outras Unidades (SEI)",
        description=(
            "Movimenta/envia um processo para uma ou mais unidades destinatárias "
            "(serviço SOAP enviarProcesso)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade de origem no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo visível para o usuário (ex: 12.1.000000077-4).",
                },
                "unidadesDestino": {
                    "type": "array",
                    "description": "Lista de IDs das unidades destinatárias.",
                    "items": {"type": "string"},
                },
                "sinManterAbertoUnidade": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se o processo deve ser mantido aberto na unidade de origem (padrão 'N').",
                },
                "sinRemoverAnotacao": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se deve remover anotação do processo (padrão 'N').",
                },
                "sinEnviarEmailNotificacao": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se deve enviar e-mail de aviso para as unidades destinatárias (padrão 'N').",
                },
                "dataRetornoProgramado": {
                    "type": "string",
                    "description": "Data para definição de Retorno Programado (DD/MM/AAAA).",
                },
                "diasRetornoProgramado": {
                    "type": "string",
                    "description": "Número de dias para o Retorno Programado.",
                },
                "sinDiasUteisRetornoProgramado": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se DiasRetornoProgramado corresponde a dias úteis (padrão 'N').",
                },
                "sinReabrir": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se o processo deve ser reaberto automaticamente caso concluído na unidade (padrão 'N').",
                },
            },
            "required": ["protocoloProcedimento", "unidadesDestino"],
        },
        handler=lambda args: client.call(
            "enviarProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "UnidadesDestino": args["unidadesDestino"],
                "SinManterAbertoUnidade": _yn(args.get("sinManterAbertoUnidade"), "N"),
                "SinRemoverAnotacao": _yn(args.get("sinRemoverAnotacao"), "N"),
                "SinEnviarEmailNotificacao": _yn(args.get("sinEnviarEmailNotificacao"), "N"),
                "DataRetornoProgramado": args.get("dataRetornoProgramado"),
                "DiasRetornoProgramado": args.get("diasRetornoProgramado"),
                "SinDiasUteisRetornoProgramado": _yn(
                    args.get("sinDiasUteisRetornoProgramado"), "N"
                ),
                "SinReabrir": _yn(args.get("sinReabrir"), "N"),
            },
        ),
    )

    # 6. concluirProcesso -> sei_concluir_processo
    server.register_tool(
        name="sei_concluir_processo",
        title="Concluir Processo na Unidade (SEI)",
        description="Conclui um processo aberto na unidade informada (serviço SOAP concluirProcesso).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o processo está aberto."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "concluirProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
            },
        ),
    )

    # 7. reabrirProcesso -> sei_reabrir_processo
    server.register_tool(
        name="sei_reabrir_processo",
        title="Reabrir Processo na Unidade (SEI)",
        description="Reabre um processo já tramitado/concluído na unidade (serviço SOAP reabrirProcesso).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade por onde o processo tramitou."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "reabrirProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
            },
        ),
    )

    # 8. atribuirProcesso -> sei_atribuir_processo
    server.register_tool(
        name="sei_atribuir_processo",
        title="Atribuir Processo a Usuário (SEI)",
        description=(
            "Atribui um processo para um usuário específico na unidade "
            "(serviço SOAP atribuirProcesso)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
                "idUsuario": {
                    "type": "string",
                    "description": "Identificador do usuário no SIP/SEI (ou vazio para remover atribuição).",
                },
                "sinReabrir": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se o processo deve ser reaberto automaticamente (padrão 'N').",
                },
            },
            "required": ["protocoloProcedimento", "idUsuario"],
        },
        handler=lambda args: client.call(
            "atribuirProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "IdUsuario": args["idUsuario"],
                "SinReabrir": _yn(args.get("sinReabrir"), "N"),
            },
        ),
    )

    # 9. bloquearProcesso -> sei_bloquear_processo
    server.register_tool(
        name="sei_bloquear_processo",
        title="Bloquear Processo (SEI)",
        description="Bloqueia um processo aberto contra alterações (serviço SOAP bloquearProcesso).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o processo está aberto."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "bloquearProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
            },
        ),
    )

    # 10. desbloquearProcesso -> sei_desbloquear_processo
    server.register_tool(
        name="sei_desbloquear_processo",
        title="Desbloquear Processo (SEI)",
        description="Desbloqueia um processo no SEI (serviço SOAP desbloquearProcesso).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o processo está aberto."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "desbloquearProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
            },
        ),
    )

    # 11. relacionarProcesso -> sei_relacionar_processo
    server.register_tool(
        name="sei_relacionar_processo",
        title="Relacionar Processos (SEI)",
        description=(
            "Cria um relacionamento bilateral entre dois processos no SEI "
            "(serviço SOAP relacionarProcesso)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento1": {
                    "type": "string",
                    "description": "Número do primeiro processo (ex: 12.1.000000077-4).",
                },
                "protocoloProcedimento2": {
                    "type": "string",
                    "description": "Número do segundo processo (ex: 11.1.000000293-2).",
                },
            },
            "required": ["protocoloProcedimento1", "protocoloProcedimento2"],
        },
        handler=lambda args: client.call(
            "relacionarProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento1": args["protocoloProcedimento1"],
                "ProtocoloProcedimento2": args["protocoloProcedimento2"],
            },
        ),
    )

    # 12. removerRelacionamentoProcesso -> sei_remover_relacionamento_processo
    server.register_tool(
        name="sei_remover_relacionamento_processo",
        title="Remover Relacionamento entre Processos (SEI)",
        description=(
            "Remove o relacionamento bilateral entre dois processos no SEI "
            "(serviço SOAP removerRelacionamentoProcesso)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento1": {
                    "type": "string",
                    "description": "Número do primeiro processo (ex: 12.1.000000077-4).",
                },
                "protocoloProcedimento2": {
                    "type": "string",
                    "description": "Número do segundo processo (ex: 11.1.000000293-2).",
                },
            },
            "required": ["protocoloProcedimento1", "protocoloProcedimento2"],
        },
        handler=lambda args: client.call(
            "removerRelacionamentoProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento1": args["protocoloProcedimento1"],
                "ProtocoloProcedimento2": args["protocoloProcedimento2"],
            },
        ),
    )

    # 13. sobrestarProcesso -> sei_sobrestar_processo
    server.register_tool(
        name="sei_sobrestar_processo",
        title="Sobrestar Processo (SEI)",
        description=(
            "Sobresta (suspende temporariamente) um processo no SEI, opcionalmente vinculado a outro processo "
            "(serviço SOAP sobrestarProcesso)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo a ser sobrestado (ex: 12.1.000000077-4).",
                },
                "protocoloProcedimentoVinculado": {
                    "type": "string",
                    "description": "Opcional. Número do processo vinculado que motiva o sobrestamento.",
                },
                "motivo": {
                    "type": "string",
                    "description": "Texto descritivo do motivo do sobrestamento.",
                },
            },
            "required": ["protocoloProcedimento", "motivo"],
        },
        handler=lambda args: client.call(
            "sobrestarProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "ProtocoloProcedimentoVinculado": args.get("protocoloProcedimentoVinculado"),
                "Motivo": args["motivo"],
            },
        ),
    )

    # 14. removerSobrestamentoProcesso -> sei_remover_sobrestamento_processo
    server.register_tool(
        name="sei_remover_sobrestamento_processo",
        title="Remover Sobrestamento de Processo (SEI)",
        description="Remove o sobrestamento de um processo no SEI (serviço SOAP removerSobrestamentoProcesso).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo sobrestado (ex: 12.1.000000077-4).",
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "removerSobrestamentoProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
            },
        ),
    )

    # 15. anexarProcesso -> sei_anexar_processo
    server.register_tool(
        name="sei_anexar_processo",
        title="Anexar Processo (SEI)",
        description="Anexa um processo secundário a um processo principal no SEI (serviço SOAP anexarProcesso).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimentoPrincipal": {
                    "type": "string",
                    "description": "Número do processo principal (ex: 12.1.000000077-4).",
                },
                "protocoloProcedimentoAnexado": {
                    "type": "string",
                    "description": "Número do processo a ser anexado (ex: 12.1.000000099-1).",
                },
            },
            "required": ["protocoloProcedimentoPrincipal", "protocoloProcedimentoAnexado"],
        },
        handler=lambda args: client.call(
            "anexarProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimentoPrincipal": args["protocoloProcedimentoPrincipal"],
                "ProtocoloProcedimentoAnexado": args["protocoloProcedimentoAnexado"],
            },
        ),
    )

    # 16. desanexarProcesso -> sei_desanexar_processo
    server.register_tool(
        name="sei_desanexar_processo",
        title="Desanexar Processo (SEI)",
        description=(
            "Desanexa um processo secundário de um processo principal mediante justificativa "
            "(serviço SOAP desanexarProcesso)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimentoPrincipal": {
                    "type": "string",
                    "description": "Número do processo principal.",
                },
                "protocoloProcedimentoAnexado": {
                    "type": "string",
                    "description": "Número do processo anexado.",
                },
                "motivo": {
                    "type": "string",
                    "description": "Texto do motivo da desanexação.",
                },
            },
            "required": [
                "protocoloProcedimentoPrincipal",
                "protocoloProcedimentoAnexado",
                "motivo",
            ],
        },
        handler=lambda args: client.call(
            "desanexarProcesso",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimentoPrincipal": args["protocoloProcedimentoPrincipal"],
                "ProtocoloProcedimentoAnexado": args["protocoloProcedimentoAnexado"],
                "Motivo": args["motivo"],
            },
        ),
    )

    # 17. lancarAndamento -> sei_lancar_andamento
    server.register_tool(
        name="sei_lancar_andamento",
        title="Lançar Andamento no Processo (SEI)",
        description=(
            "Registra um andamento manual no histórico do processo (serviço SOAP lancarAndamento). "
            "IdTarefa deve ser >= 1000 ou 65 (atualização de andamento, informando atributo Nome='DESCRICAO' e Valor='texto')."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
                "idTarefa": {
                    "type": "string",
                    "description": "Identificador da tarefa associada (ex: '65' para atualização de andamento).",
                },
                "idTarefaModulo": {
                    "type": "string",
                    "description": "Identificador da tarefa de módulo (alternativo a idTarefa).",
                },
                "atributos": {
                    "type": "array",
                    "description": "Conjunto de atributos do andamento (ex: [{'Nome': 'DESCRICAO', 'Valor': 'Texto', 'IdOrigem': ''}]).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Nome": {"type": "string"},
                            "Valor": {"type": "string"},
                            "IdOrigem": {"type": "string"},
                        },
                        "required": ["Nome", "Valor"],
                    },
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "lancarAndamento",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "IdTarefa": args.get("idTarefa") or "65",
                "IdTarefaModulo": args.get("idTarefaModulo"),
                "Atributos": args.get("atributos") or [],
            },
        ),
    )

    # 18. listarAndamentos -> sei_listar_andamentos
    server.register_tool(
        name="sei_listar_andamentos",
        title="Listar Andamentos do Processo (SEI)",
        description=(
            "Lista o histórico de andamentos de um processo no SEI (serviço SOAP listarAndamentos). "
            "Conforme documentação do SEI, é necessário filtrar por pelo menos um dos conjuntos: "
            "andamentos, tarefas ou tarefasModulos."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
                "sinRetornarAtributos": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno dos atributos associados (padrão 'S').",
                },
                "andamentos": {
                    "type": "array",
                    "description": "Opcional. Filtra andamentos pelos IDs internos de andamento informados.",
                    "items": {"type": "string"},
                },
                "tarefas": {
                    "type": "array",
                    "description": "Opcional. Filtra andamentos pelos IDs de tarefas (ex: ['1', '65']).",
                    "items": {"type": "string"},
                },
                "tarefasModulos": {
                    "type": "array",
                    "description": "Opcional. Filtra andamentos pelos IDs de tarefas de módulo.",
                    "items": {"type": "string"},
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "listarAndamentos",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "SinRetornarAtributos": _yn(args.get("sinRetornarAtributos"), "S"),
                "Andamentos": args.get("andamentos") or [],
                "Tarefas": args.get("tarefas") or [],
                "TarefasModulos": args.get("tarefasModulos") or [],
            },
        ),
    )

    # 19. definirMarcador -> sei_definir_marcador
    def _handle_definir_marcador(args: Dict[str, Any]) -> Any:
        definicoes: List[Dict[str, Any]] = list(args.get("definicoes") or [])
        if not definicoes and args.get("protocoloProcedimento"):
            definicoes.append(
                {
                    "ProtocoloProcedimento": args["protocoloProcedimento"],
                    "IdMarcador": args.get("idMarcador", ""),
                    "Texto": args.get("texto", ""),
                }
            )
        return client.call(
            "definirMarcador",
            {
                "IdUnidade": args.get("idUnidade"),
                "Definicoes": definicoes,
            },
        )

    server.register_tool(
        name="sei_definir_marcador",
        title="Definir Marcador em Processo (SEI)",
        description=(
            "Associa, altera ou remove marcadores em um ou mais processos abertos na unidade "
            "(serviço SOAP definirMarcador)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o processo está aberto."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (atalho para definir em um único processo).",
                },
                "idMarcador": {
                    "type": "string",
                    "description": "Identificador do marcador disponível na unidade (atalho individual).",
                },
                "texto": {
                    "type": "string",
                    "description": "Texto para associação ao marcador (atalho individual).",
                },
                "definicoes": {
                    "type": "array",
                    "description": "Lista de definições de marcador em lote (estrutura DefinicaoMarcador).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ProtocoloProcedimento": {"type": "string"},
                            "IdMarcador": {"type": "string"},
                            "Texto": {"type": "string"},
                        },
                        "required": ["ProtocoloProcedimento", "IdMarcador"],
                    },
                },
            },
        },
        handler=_handle_definir_marcador,
    )

    # 20. listarAndamentosMarcadores -> sei_listar_andamentos_marcadores
    server.register_tool(
        name="sei_listar_andamentos_marcadores",
        title="Listar Andamentos de Marcadores do Processo (SEI)",
        description=(
            "Lista o histórico de andamentos de marcadores de um processo na unidade "
            "(serviço SOAP listarAndamentosMarcadores)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
                "marcadores": {
                    "type": "array",
                    "description": "Opcional. Lista de IDs de marcadores para filtrar.",
                    "items": {"type": "string"},
                },
            },
            "required": ["protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "listarAndamentosMarcadores",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "Marcadores": args.get("marcadores") or [],
            },
        ),
    )

    # 21. definirControlePrazo -> sei_definir_controle_prazo
    def _handle_definir_controle_prazo(args: Dict[str, Any]) -> Any:
        definicoes: List[Dict[str, Any]] = list(args.get("definicoes") or [])
        if not definicoes and args.get("protocoloProcedimento"):
            definicoes.append(
                {
                    "ProtocoloProcedimento": args["protocoloProcedimento"],
                    "DataPrazo": args.get("dataPrazo"),
                    "Dias": args.get("dias"),
                    "SinDiasUteis": _yn(args.get("sinDiasUteis"), "N"),
                }
            )
        return client.call(
            "definirControlePrazo",
            {
                "IdUnidade": args.get("idUnidade"),
                "Definicoes": definicoes,
            },
        )

    server.register_tool(
        name="sei_definir_controle_prazo",
        title="Definir Controle de Prazo em Processo (SEI)",
        description=(
            "Define controle de prazo em um ou mais processos abertos na unidade "
            "(serviço SOAP definirControlePrazo)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (atalho individual).",
                },
                "dataPrazo": {
                    "type": "string",
                    "description": "Data final do prazo no formato DD/MM/AAAA (atalho individual).",
                },
                "dias": {
                    "type": "string",
                    "description": "Quantidade de dias de prazo (atalho individual).",
                },
                "sinDiasUteis": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Se a contagem de dias é em dias úteis (padrão 'N').",
                },
                "definicoes": {
                    "type": "array",
                    "description": "Lista de definições de controle de prazo em lote (DefinicaoControlePrazo).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ProtocoloProcedimento": {"type": "string"},
                            "DataPrazo": {"type": "string"},
                            "Dias": {"type": "string"},
                            "SinDiasUteis": {"type": "string"},
                        },
                        "required": ["ProtocoloProcedimento"],
                    },
                },
            },
        },
        handler=_handle_definir_controle_prazo,
    )

    # 22. concluirControlePrazo -> sei_concluir_controle_prazo
    server.register_tool(
        name="sei_concluir_controle_prazo",
        title="Concluir Controle de Prazo (SEI)",
        description=(
            "Conclui o controle de prazo de um ou mais processos na unidade "
            "(serviço SOAP concluirControlePrazo)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número de um único processo (atalho).",
                },
                "protocolosProcedimentos": {
                    "type": "array",
                    "description": "Lista de números de processos para concluir o controle de prazo.",
                    "items": {"type": "string"},
                },
            },
        },
        handler=lambda args: client.call(
            "concluirControlePrazo",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocolosProcedimentos": args.get("protocolosProcedimentos")
                or (
                    [args["protocoloProcedimento"]]
                    if args.get("protocoloProcedimento")
                    else []
                ),
            },
        ),
    )

    # 23. removerControlePrazo -> sei_remover_controle_prazo
    server.register_tool(
        name="sei_remover_controle_prazo",
        title="Remover Controle de Prazo (SEI)",
        description=(
            "Remove o controle de prazo de um ou mais processos na unidade "
            "(serviço SOAP removerControlePrazo)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número de um único processo (atalho).",
                },
                "protocolosProcedimentos": {
                    "type": "array",
                    "description": "Lista de números de processos para remover o controle de prazo.",
                    "items": {"type": "string"},
                },
            },
        },
        handler=lambda args: client.call(
            "removerControlePrazo",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocolosProcedimentos": args.get("protocolosProcedimentos")
                or (
                    [args["protocoloProcedimento"]]
                    if args.get("protocoloProcedimento")
                    else []
                ),
            },
        ),
    )

    # 24. registrarAnotacao -> sei_registrar_anotacao
    def _handle_registrar_anotacao(args: Dict[str, Any]) -> Any:
        anotacoes: List[Dict[str, Any]] = list(args.get("anotacoes") or [])
        if not anotacoes and args.get("protocoloProcedimento"):
            anotacoes.append(
                {
                    "ProtocoloProcedimento": args["protocoloProcedimento"],
                    "Descricao": args.get("descricao", ""),
                    "SinPrioridade": _yn(args.get("sinPrioridade"), "N"),
                }
            )
        return client.call(
            "registrarAnotacao",
            {
                "IdUnidade": args.get("idUnidade"),
                "Anotacoes": anotacoes,
            },
        )

    server.register_tool(
        name="sei_registrar_anotacao",
        title="Registrar Anotação em Processo (SEI)",
        description=(
            "Registra ou atualiza anotações em um ou mais processos na unidade "
            "(serviço SOAP registrarAnotacao)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (atalho individual).",
                },
                "descricao": {
                    "type": "string",
                    "description": "Texto da anotação (atalho individual).",
                },
                "sinPrioridade": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica prioridade na anotação (padrão 'N').",
                },
                "anotacoes": {
                    "type": "array",
                    "description": "Lista de anotações em lote (estrutura Anotacao).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ProtocoloProcedimento": {"type": "string"},
                            "Descricao": {"type": "string"},
                            "SinPrioridade": {"type": "string"},
                        },
                        "required": ["ProtocoloProcedimento", "Descricao"],
                    },
                },
            },
        },
        handler=_handle_registrar_anotacao,
    )

    # 25. registrarOuvidoria -> sei_registrar_ouvidoria
    server.register_tool(
        name="sei_registrar_ouvidoria",
        title="Registrar Manifestação de Ouvidoria (SEI)",
        description=(
            "Registra um contato/manifestação de ouvidoria gerando automaticamente um processo no SEI "
            "(serviço SOAP registrarOuvidoria)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idOrgao": {"type": "string", "description": "ID do órgão destinatário da ouvidoria."},
                "nome": {"type": "string", "description": "Nome completo do manifestante."},
                "nomeSocial": {"type": "string", "description": "Nome social do manifestante (opcional)."},
                "email": {"type": "string", "description": "E-mail do manifestante."},
                "cpf": {"type": "string", "description": "CPF do manifestante."},
                "rg": {"type": "string", "description": "RG do manifestante."},
                "orgaoExpedidor": {"type": "string", "description": "Órgão expedidor do RG."},
                "telefone": {"type": "string", "description": "Telefone de contato."},
                "idEstado": {"type": "string", "description": "ID do estado (UF)."},
                "idCidade": {"type": "string", "description": "ID da cidade."},
                "idTipoProcedimento": {
                    "type": "string",
                    "description": "ID do tipo de procedimento de ouvidoria (obtido via sei_listar_tipos_procedimento_ouvidoria).",
                },
                "processos": {
                    "type": "string",
                    "description": "Números de processos relacionados informados pelo cidadão (opcional).",
                },
                "sinRetorno": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se o manifestante aguarda retorno.",
                },
                "mensagem": {"type": "string", "description": "Conteúdo da manifestação de ouvidoria."},
                "atributosAdicionais": {
                    "type": "array",
                    "description": "Lista opcional de atributos adicionais (AtributoOuvidoria: Id, Nome, Titulo, Valor).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Id": {"type": "string"},
                            "Nome": {"type": "string"},
                            "Titulo": {"type": "string"},
                            "Valor": {"type": "string"},
                        },
                        "required": ["Nome", "Titulo", "Valor"],
                    },
                },
            },
            "required": ["idOrgao", "nome", "email", "idTipoProcedimento", "mensagem"],
        },
        handler=lambda args: client.call(
            "registrarOuvidoria",
            {
                "IdOrgao": args["idOrgao"],
                "Nome": args["nome"],
                "NomeSocial": args.get("nomeSocial"),
                "Email": args["email"],
                "Cpf": args.get("cpf"),
                "Rg": args.get("rg"),
                "OrgaoExpedidor": args.get("orgaoExpedidor"),
                "Telefone": args.get("telefone"),
                "IdEstado": args.get("idEstado"),
                "IdCidade": args.get("idCidade"),
                "IdTipoProcedimento": args["idTipoProcedimento"],
                "Processos": args.get("processos"),
                "SinRetorno": _yn(args.get("sinRetorno"), "S"),
                "Mensagem": args["mensagem"],
                "AtributosAdicionais": args.get("atributosAdicionais") or [],
            },
        ),
    )
