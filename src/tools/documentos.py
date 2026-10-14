"""Document, File Repository, Publication, and Email MCP Tools for SEI SOAP Web Services."""

from __future__ import annotations

from typing import Any, Dict

from src.client.sei_client import SeiSoapClient, get_sei_client
from src.mcp_server import McpServer
from src.tools.processos import _yn


def register_documentos_tools(server: McpServer) -> None:
    """Registers all 13 Document, File, Publication, and Email SOAP operations from sei.wsdl."""
    client = get_sei_client()

    participant_schema = {
        "type": "object",
        "properties": {
            "IdContato": {"type": "string", "description": "ID interno do contato (opcional)."},
            "Cpf": {"type": "string", "description": "CPF do participante (opcional)."},
            "Cnpj": {"type": "string", "description": "CNPJ do participante (opcional)."},
            "Sigla": {"type": "string", "description": "Sigla do participante."},
            "Nome": {"type": "string", "description": "Nome do participante."},
        },
    }

    # 1. incluirDocumento -> sei_incluir_documento
    def _handle_incluir_documento(args: Dict[str, Any]) -> Any:
        raw_content = args.get("conteudo")
        b64_content = SeiSoapClient.ensure_base64(raw_content) if raw_content else None

        doc_struct = {
            "Tipo": args["tipo"],
            "IdProcedimento": args.get("idProcedimento"),
            "ProtocoloProcedimento": args.get("protocoloProcedimento"),
            "IdSerie": args["idSerie"],
            "Numero": args.get("numero"),
            "NomeArvore": args.get("nomeArvore"),
            "DinValor": args.get("dinValor"),
            "Data": args.get("data"),
            "Descricao": args.get("descricao"),
            "IdTipoConferencia": args.get("idTipoConferencia"),
            "SinArquivamento": _yn(args.get("sinArquivamento"), "N")
            if args.get("sinArquivamento") is not None
            else None,
            "Remetente": args.get("remetente"),
            "Interessados": args.get("interessados") or [],
            "Destinatarios": args.get("destinatarios") or [],
            "Observacao": args.get("observacao"),
            "NomeArquivo": args.get("nomeArquivo"),
            "NivelAcesso": args.get("nivelAcesso"),
            "IdHipoteseLegal": args.get("idHipoteseLegal"),
            "Conteudo": b64_content,
            "ConteudoSecoes": args.get("conteudoSecoes"),
            "ConteudoMTOM": args.get("conteudoMTOM"),
            "IdArquivo": args.get("idArquivo"),
            "Campos": args.get("campos") or [],
            "SinBloqueado": _yn(args.get("sinBloqueado"), "N")
            if args.get("sinBloqueado") is not None
            else None,
            "IdItemEtapa": args.get("idItemEtapa"),
        }
        return client.call(
            "incluirDocumento",
            {
                "IdUnidade": args.get("idUnidade"),
                "Documento": doc_struct,
            },
        )

    server.register_tool(
        name="sei_incluir_documento",
        title="Incluir Documento no Processo (SEI)",
        description=(
            "Inclui um documento gerado (Tipo='G', conteúdo HTML/texto convertido automaticamente "
            "para Base64) ou documento externo/recebido (Tipo='R', informando Conteudo em Base64 ou "
            "IdArquivo obtido via sei_adicionar_arquivo) em um processo do SEI (serviço SOAP incluirDocumento)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "tipo": {
                    "type": "string",
                    "enum": ["G", "R"],
                    "description": "'G' = Documento Gerado (interno HTML) | 'R' = Documento Recebido (externo/anexo).",
                },
                "idProcedimento": {
                    "type": "string",
                    "description": "ID interno do processo (opcional se protocoloProcedimento for informado).",
                },
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo visível para o usuário (ex: 12.1.000000077-4).",
                },
                "idSerie": {
                    "type": "string",
                    "description": "Identificador do tipo de documento/série no SEI (obtido via sei_listar_series).",
                },
                "numero": {
                    "type": "string",
                    "description": "Número ou nome na árvore para documentos externos (ou gerados com numeração informada).",
                },
                "nomeArvore": {
                    "type": "string",
                    "description": "Complemento do nome exibido na árvore do processo.",
                },
                "dinValor": {
                    "type": "string",
                    "description": "Valor monetário associado ao documento (opcional).",
                },
                "data": {
                    "type": "string",
                    "description": "Data do documento (DD/MM/AAAA) — obrigatório para documentos externos (Tipo='R').",
                },
                "descricao": {
                    "type": "string",
                    "description": "Descrição do documento (para documentos gerados).",
                },
                "idTipoConferencia": {
                    "type": "string",
                    "description": "Identificador do tipo de conferência para documentos externos.",
                },
                "sinArquivamento": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica arquivamento.",
                },
                "remetente": {
                    **participant_schema,
                    "description": "Dados do remetente (obrigatório para documentos externos Tipo='R').",
                },
                "interessados": {
                    "type": "array",
                    "description": "Conjunto de interessados do documento.",
                    "items": participant_schema,
                },
                "destinatarios": {
                    "type": "array",
                    "description": "Conjunto de destinatários do documento.",
                    "items": participant_schema,
                },
                "observacao": {
                    "type": "string",
                    "description": "Texto da observação da unidade.",
                },
                "nomeArquivo": {
                    "type": "string",
                    "description": "Nome do arquivo anexo (obrigatório para documentos externos Tipo='R', ex: 'oficio.pdf').",
                },
                "nivelAcesso": {
                    "type": "string",
                    "enum": ["0", "1", "2"],
                    "description": "0 = Público, 1 = Restrito, 2 = Sigiloso (se omitido, assume o padrão do processo).",
                },
                "idHipoteseLegal": {
                    "type": "string",
                    "description": "ID da hipótese legal associada (obrigatório para nível restrito/sigiloso).",
                },
                "conteudo": {
                    "type": "string",
                    "description": "Conteúdo do documento em texto/HTML (convertido automaticamente para Base64) ou já em Base64.",
                },
                "conteudoSecoes": {
                    "type": "array",
                    "description": "Opcional. Conteúdo estruturado por seções do documento (Nome, Conteudo).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Nome": {"type": "string"},
                            "Conteudo": {"type": "string"},
                        },
                        "required": ["Nome", "Conteudo"],
                    },
                },
                "idArquivo": {
                    "type": "string",
                    "description": "Identificador do arquivo previamente enviado via sei_adicionar_arquivo.",
                },
                "campos": {
                    "type": "array",
                    "description": "Campos de formulário do documento (Nome, Valor).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "Nome": {"type": "string"},
                            "Valor": {"type": "string"},
                        },
                        "required": ["Nome", "Valor"],
                    },
                },
                "sinBloqueado": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Se 'S', bloqueia o documento contra alterações após inclusão.",
                },
            },
            "required": ["tipo", "idSerie"],
        },
        handler=_handle_incluir_documento,
    )

    # 2. consultarDocumento -> sei_consultar_documento
    server.register_tool(
        name="sei_consultar_documento",
        title="Consultar Documento por Protocolo (SEI)",
        description=(
            "Consulta metadados, link de acesso, andamento de geração, assinaturas, "
            "publicação, campos de formulário e blocos de um documento no SEI (serviço SOAP consultarDocumento)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloDocumento": {
                    "type": "string",
                    "description": "Número do documento visível para o usuário (ex: 0003934).",
                },
                "sinRetornarAndamentoGeracao": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Retorna andamento de geração do documento (padrão 'N').",
                },
                "sinRetornarAssinaturas": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Retorna assinaturas do documento (padrão 'N').",
                },
                "sinRetornarPublicacao": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Retorna dados de publicação do documento (padrão 'N').",
                },
                "sinRetornarCampos": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Retorna campos do formulário do documento (padrão 'N').",
                },
                "sinRetornarBlocos": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Retorna blocos nos quais o documento está incluído (padrão 'N').",
                },
            },
            "required": ["protocoloDocumento"],
        },
        handler=lambda args: client.call(
            "consultarDocumento",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloDocumento": args["protocoloDocumento"],
                "SinRetornarAndamentoGeracao": _yn(
                    args.get("sinRetornarAndamentoGeracao"), "N"
                ),
                "SinRetornarAssinaturas": _yn(args.get("sinRetornarAssinaturas"), "N"),
                "SinRetornarPublicacao": _yn(args.get("sinRetornarPublicacao"), "N"),
                "SinRetornarCampos": _yn(args.get("sinRetornarCampos"), "N"),
                "SinRetornarBlocos": _yn(args.get("sinRetornarBlocos"), "N"),
            },
        ),
    )

    # 3. cancelarDocumento -> sei_cancelar_documento
    server.register_tool(
        name="sei_cancelar_documento",
        title="Cancelar Documento (SEI)",
        description="Cancela formalmente um documento no SEI informando o motivo (serviço SOAP cancelarDocumento).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o processo está aberto."},
                "protocoloDocumento": {
                    "type": "string",
                    "description": "Número do documento visível ao usuário (ex: 0003934).",
                },
                "motivo": {
                    "type": "string",
                    "description": "Texto informando o motivo do cancelamento.",
                },
            },
            "required": ["protocoloDocumento", "motivo"],
        },
        handler=lambda args: client.call(
            "cancelarDocumento",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloDocumento": args["protocoloDocumento"],
                "Motivo": args["motivo"],
            },
        ),
    )

    # 4. bloquearDocumento -> sei_bloquear_documento
    server.register_tool(
        name="sei_bloquear_documento",
        title="Bloquear Documento (SEI)",
        description="Bloqueia um documento contra alterações e exclusão no SEI (serviço SOAP bloquearDocumento).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloDocumento": {
                    "type": "string",
                    "description": "Número do documento visível ao usuário (ex: 0003934).",
                },
            },
            "required": ["protocoloDocumento"],
        },
        handler=lambda args: client.call(
            "bloquearDocumento",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloDocumento": args["protocoloDocumento"],
            },
        ),
    )

    # 5. excluirDocumento -> sei_excluir_documento
    server.register_tool(
        name="sei_excluir_documento",
        title="Excluir Documento (SEI)",
        description="Exclui um documento no SEI que ainda possa ser removido (serviço SOAP excluirDocumento).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloDocumento": {
                    "type": "string",
                    "description": "Número do documento visível ao usuário (ex: 0003934).",
                },
            },
            "required": ["protocoloDocumento"],
        },
        handler=lambda args: client.call(
            "excluirDocumento",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloDocumento": args["protocoloDocumento"],
            },
        ),
    )

    # 6. adicionarArquivo -> sei_adicionar_arquivo
    def _handle_adicionar_arquivo(args: Dict[str, Any]) -> Any:
        b64_content = SeiSoapClient.ensure_base64(args["conteudo"])
        tamanho = args.get("tamanho")
        md5_hash = args.get("hash")
        if not tamanho or not md5_hash:
            calc_size, calc_md5 = SeiSoapClient.compute_file_size_and_md5_from_base64(
                b64_content
            )
            tamanho = tamanho or calc_size
            md5_hash = md5_hash or calc_md5

        return client.call(
            "adicionarArquivo",
            {
                "IdUnidade": args.get("idUnidade"),
                "Nome": args["nome"],
                "Tamanho": str(tamanho),
                "Hash": str(md5_hash),
                "Conteudo": b64_content,
            },
        )

    server.register_tool(
        name="sei_adicionar_arquivo",
        title="Adicionar Arquivo ao Repositório (SEI)",
        description=(
            "Cria um arquivo no repositório de documentos do SEI e retorna seu IdArquivo "
            "(serviço SOAP adicionarArquivo). Calcula automaticamente Tamanho (bytes) e Hash (MD5) "
            "caso não sejam informados, permitindo upload completo ou particionado com sei_adicionar_conteudo_arquivo."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "nome": {"type": "string", "description": "Nome do arquivo (ex: 'relatorio.pdf')."},
                "conteudo": {
                    "type": "string",
                    "description": "Conteúdo total ou primeira parte do arquivo codificado em Base64.",
                },
                "tamanho": {
                    "type": "string",
                    "description": "Opcional. Tamanho total do arquivo em bytes (calculado automaticamente se envio único).",
                },
                "hash": {
                    "type": "string",
                    "description": "Opcional. Hash MD5 do conteúdo total do arquivo (calculado automaticamente se envio único).",
                },
            },
            "required": ["nome", "conteudo"],
        },
        handler=_handle_adicionar_arquivo,
    )

    # 7. adicionarConteudoArquivo -> sei_adicionar_conteudo_arquivo
    server.register_tool(
        name="sei_adicionar_conteudo_arquivo",
        title="Adicionar Conteúdo Particionado a Arquivo (SEI)",
        description=(
            "Adiciona partes adicionais de conteúdo em Base64 a um arquivo previamente criado com "
            "sei_adicionar_arquivo (serviço SOAP adicionarConteudoArquivo)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idArquivo": {
                    "type": "string",
                    "description": "Identificador do arquivo retornado por sei_adicionar_arquivo.",
                },
                "conteudo": {
                    "type": "string",
                    "description": "Parte do conteúdo codificado em Base64 a ser concatenada ao arquivo.",
                },
            },
            "required": ["idArquivo", "conteudo"],
        },
        handler=lambda args: client.call(
            "adicionarConteudoArquivo",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdArquivo": args["idArquivo"],
                "Conteudo": SeiSoapClient.ensure_base64(args["conteudo"]),
            },
        ),
    )

    # 8. consultarPublicacao -> sei_consultar_publicacao
    server.register_tool(
        name="sei_consultar_publicacao",
        title="Consultar Publicação de Documento (SEI)",
        description=(
            "Consulta dados de publicação de um documento no SEI informando IdPublicacao, "
            "IdDocumento ou ProtocoloDocumento (serviço SOAP consultarPublicacao)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idPublicacao": {"type": "string", "description": "ID interno da publicação (opcional)."},
                "idDocumento": {"type": "string", "description": "ID interno do documento (opcional)."},
                "protocoloDocumento": {
                    "type": "string",
                    "description": "Número do documento visível para o usuário (ex: 0003934).",
                },
                "sinRetornarAndamento": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Retorna andamento de publicação (padrão 'N').",
                },
                "sinRetornarAssinaturas": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Retorna assinaturas do documento publicado (padrão 'N').",
                },
            },
        },
        handler=lambda args: client.call(
            "consultarPublicacao",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdPublicacao": args.get("idPublicacao"),
                "IdDocumento": args.get("idDocumento"),
                "ProtocoloDocumento": args.get("protocoloDocumento"),
                "SinRetornarAndamento": _yn(args.get("sinRetornarAndamento"), "N"),
                "SinRetornarAssinaturas": _yn(args.get("sinRetornarAssinaturas"), "N"),
            },
        ),
    )

    # 9. agendarPublicacao -> sei_agendar_publicacao
    server.register_tool(
        name="sei_agendar_publicacao",
        title="Agendar Publicação de Documento (SEI)",
        description=(
            "Agenda a publicação de um documento em veículo de publicação (serviço SOAP agendarPublicacao). "
            "Retorna o identificador interno da publicação (IdPublicacao)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idDocumento": {"type": "string", "description": "ID interno do documento (opcional se protocoloDocumento informado)."},
                "protocoloDocumento": {
                    "type": "string",
                    "description": "Número do documento visível para o usuário (ex: 0003934).",
                },
                "staMotivo": {
                    "type": "string",
                    "enum": ["1", "2", "3", "4"],
                    "description": "Motivo: '1' = Publicação, '2' = Retificação, '3' = Republicação, '4' = Apostilamento.",
                },
                "idVeiculoPublicacao": {
                    "type": "string",
                    "description": "Identificador do veículo de publicação.",
                },
                "dataDisponibilizacao": {
                    "type": "string",
                    "description": "Data de disponibilização (DD/MM/AAAA).",
                },
                "resumo": {
                    "type": "string",
                    "description": "Texto do resumo da publicação.",
                },
                "imprensaNacional": {
                    "type": "object",
                    "description": "Opcional. Dados informativos da Imprensa Nacional (IdVeiculo, SiglaVeiculo, DescricaoVeiculo, Pagina, IdSecao, Secao, Data).",
                },
            },
            "required": ["staMotivo", "idVeiculoPublicacao", "dataDisponibilizacao"],
        },
        handler=lambda args: client.call(
            "agendarPublicacao",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdDocumento": args.get("idDocumento"),
                "ProtocoloDocumento": args.get("protocoloDocumento"),
                "StaMotivo": args["staMotivo"],
                "IdVeiculoPublicacao": args["idVeiculoPublicacao"],
                "DataDisponibilizacao": args["dataDisponibilizacao"],
                "Resumo": args.get("resumo"),
                "ImprensaNacional": args.get("imprensaNacional"),
            },
        ),
    )

    # 10. alterarPublicacao -> sei_alterar_publicacao
    server.register_tool(
        name="sei_alterar_publicacao",
        title="Alterar Agendamento de Publicação (SEI)",
        description=(
            "Altera os dados de um agendamento de publicação no SEI "
            "(serviço SOAP alterarPublicacao)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idPublicacao": {"type": "string", "description": "ID da publicação."},
                "idDocumento": {"type": "string", "description": "ID do documento."},
                "protocoloDocumento": {"type": "string", "description": "Protocolo formatado do documento."},
                "staMotivo": {
                    "type": "string",
                    "enum": ["1", "2", "3", "4"],
                    "description": "1 = Publicação, 2 = Retificação, 3 = Republicação, 4 = Apostilamento.",
                },
                "idVeiculoPublicacao": {"type": "string", "description": "ID do veículo de publicação."},
                "dataDisponibilizacao": {"type": "string", "description": "Data de disponibilização (DD/MM/AAAA)."},
                "resumo": {"type": "string", "description": "Resumo da publicação."},
                "imprensaNacional": {
                    "type": "object",
                    "description": "Opcional. Dados da Imprensa Nacional.",
                },
            },
            "required": ["staMotivo", "idVeiculoPublicacao", "dataDisponibilizacao"],
        },
        handler=lambda args: client.call(
            "alterarPublicacao",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdPublicacao": args.get("idPublicacao"),
                "IdDocumento": args.get("idDocumento"),
                "ProtocoloDocumento": args.get("protocoloDocumento"),
                "StaMotivo": args["staMotivo"],
                "IdVeiculoPublicacao": args["idVeiculoPublicacao"],
                "DataDisponibilizacao": args["dataDisponibilizacao"],
                "Resumo": args.get("resumo"),
                "ImprensaNacional": args.get("imprensaNacional"),
            },
        ),
    )

    # 11. cancelarAgendamentoPublicacao -> sei_cancelar_agendamento_publicacao
    server.register_tool(
        name="sei_cancelar_agendamento_publicacao",
        title="Cancelar Agendamento de Publicação (SEI)",
        description=(
            "Cancela um agendamento de publicação informando IdPublicacao, IdDocumento ou ProtocoloDocumento "
            "(serviço SOAP cancelarAgendamentoPublicacao)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idPublicacao": {"type": "string", "description": "ID da publicação."},
                "idDocumento": {"type": "string", "description": "ID do documento."},
                "protocoloDocumento": {"type": "string", "description": "Protocolo formatado do documento."},
            },
        },
        handler=lambda args: client.call(
            "cancelarAgendamentoPublicacao",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdPublicacao": args.get("idPublicacao"),
                "IdDocumento": args.get("idDocumento"),
                "ProtocoloDocumento": args.get("protocoloDocumento"),
            },
        ),
    )

    # 12. confirmarDisponibilizacaoPublicacao -> sei_confirmar_disponibilizacao_publicacao
    server.register_tool(
        name="sei_confirmar_disponibilizacao_publicacao",
        title="Confirmar Disponibilização de Publicação (SEI)",
        description=(
            "Confirma a disponibilização de publicações em veículo externo, atualizando o andamento "
            "no processo com o número e data efetiva da publicação (serviço SOAP confirmarDisponibilizacaoPublicacao)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idVeiculoPublicacao": {"type": "string", "description": "Identificador do veículo de publicação."},
                "dataDisponibilizacao": {"type": "string", "description": "Data de disponibilização (DD/MM/AAAA)."},
                "dataPublicacao": {"type": "string", "description": "Data efetiva de publicação (DD/MM/AAAA)."},
                "numero": {"type": "string", "description": "Número da edição/publicação."},
                "idDocumentos": {
                    "type": "array",
                    "description": "Conjunto de identificadores internos (IdDocumento) dos documentos publicados.",
                    "items": {"type": "string"},
                },
            },
            "required": [
                "idVeiculoPublicacao",
                "dataDisponibilizacao",
                "dataPublicacao",
                "numero",
                "idDocumentos",
            ],
        },
        handler=lambda args: client.call(
            "confirmarDisponibilizacaoPublicacao",
            {
                "IdVeiculoPublicacao": args["idVeiculoPublicacao"],
                "DataDisponibilizacao": args["dataDisponibilizacao"],
                "DataPublicacao": args["dataPublicacao"],
                "Numero": args["numero"],
                "IdDocumentos": args["idDocumentos"],
            },
        ),
    )

    # 13. enviarEmail -> sei_enviar_email
    server.register_tool(
        name="sei_enviar_email",
        title="Enviar E-mail no Processo (SEI)",
        description=(
            "Envia e-mail oficial vinculado a um processo no SEI com opção de anexar documentos do processo "
            "(serviço SOAP enviarEmail)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo (ex: 12.1.000000077-4).",
                },
                "de": {"type": "string", "description": "Endereço de e-mail do remetente (da unidade)."},
                "para": {"type": "string", "description": "Endereço(s) de e-mail destinatário(s)."},
                "cco": {"type": "string", "description": "Endereço(s) de e-mail em cópia oculta (opcional)."},
                "assunto": {"type": "string", "description": "Assunto da mensagem de e-mail."},
                "mensagem": {"type": "string", "description": "Corpo do e-mail."},
                "idDocumentos": {
                    "type": "array",
                    "description": "Lista de IDs de documentos do processo a serem enviados como anexo.",
                    "items": {"type": "string"},
                },
            },
            "required": ["protocoloProcedimento", "de", "para", "assunto", "mensagem"],
        },
        handler=lambda args: client.call(
            "enviarEmail",
            {
                "IdUnidade": args.get("idUnidade"),
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "De": args["de"],
                "Para": args["para"],
                "CCO": args.get("cco") or "",
                "Assunto": args["assunto"],
                "Mensagem": args["mensagem"],
                "IdDocumentos": args.get("idDocumentos") or [],
            },
        ),
    )
