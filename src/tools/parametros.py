"""Blocks, Parameters, Catalogs, SIP, and External RH MCP Tools for SEI SOAP Web Services."""

from __future__ import annotations

from typing import Any, Dict

from src.client.sei_client import get_sei_client
from src.mcp_server import McpServer
from src.tools.processos import _yn


def register_parametros_tools(server: McpServer) -> None:
    """Registers all 33 Block, Parameter, Catalog, SIP, and External RH SOAP operations."""
    client = get_sei_client()

    # ==========================================================================
    # BLOCOS (Assinatura, Reunião, Interno) — 12 tools
    # ==========================================================================

    # 1. gerarBloco -> sei_gerar_bloco
    server.register_tool(
        name="sei_gerar_bloco",
        title="Gerar Bloco de Assinatura / Reunião / Interno (SEI)",
        description=(
            "Gera um novo bloco no SEI (Tipo: 'A'=Assinatura, 'R'=Reunião, 'I'=Interno), "
            "permitindo incluir documentos e disponibilizar para outras unidades (serviço SOAP gerarBloco)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde será gerado o bloco."},
                "tipo": {
                    "type": "string",
                    "enum": ["A", "R", "I"],
                    "description": "Tipo do bloco: 'A' = Assinatura, 'R' = Reunião, 'I' = Interno.",
                },
                "descricao": {"type": "string", "description": "Descrição do bloco."},
                "unidadesDisponibilizacao": {
                    "type": "array",
                    "description": "Lista de IDs de unidades para disponibilização do bloco.",
                    "items": {"type": "string"},
                },
                "documentos": {
                    "type": "array",
                    "description": "Lista de protocolos formatados de documentos para incluir no bloco.",
                    "items": {"type": "string"},
                },
                "sinDisponibilizar": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Indica se o bloco deve ser disponibilizado automaticamente após geração (padrão 'N').",
                },
            },
            "required": ["tipo", "descricao"],
        },
        handler=lambda args: client.call(
            "gerarBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "Tipo": args["tipo"],
                "Descricao": args["descricao"],
                "UnidadesDisponibilizacao": args.get("unidadesDisponibilizacao") or [],
                "Documentos": args.get("documentos") or [],
                "SinDisponibilizar": _yn(args.get("sinDisponibilizar"), "N"),
            },
        ),
    )

    # 2. consultarBloco -> sei_consultar_bloco
    server.register_tool(
        name="sei_consultar_bloco",
        title="Consultar Bloco (SEI)",
        description=(
            "Consulta informações de um bloco no SEI e opcionalmente os protocolos incluídos nele "
            "(serviço SOAP consultarBloco)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idBloco": {"type": "string", "description": "Número / identificador do bloco."},
                "sinRetornarProtocolos": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "S/N - Sinalizador para retorno dos protocolos do bloco (padrão 'N').",
                },
            },
            "required": ["idBloco"],
        },
        handler=lambda args: client.call(
            "consultarBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
                "SinRetornarProtocolos": _yn(args.get("sinRetornarProtocolos"), "N"),
            },
        ),
    )

    # 3. excluirBloco -> sei_excluir_bloco
    server.register_tool(
        name="sei_excluir_bloco",
        title="Excluir Bloco (SEI)",
        description="Exclui um bloco na unidade (serviço SOAP excluirBloco).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o bloco foi gerado."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
            },
            "required": ["idBloco"],
        },
        handler=lambda args: client.call(
            "excluirBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
            },
        ),
    )

    # 4. disponibilizarBloco -> sei_disponibilizar_bloco
    server.register_tool(
        name="sei_disponibilizar_bloco",
        title="Disponibilizar Bloco (SEI)",
        description="Disponibiliza um bloco para as unidades configuradas (serviço SOAP disponibilizarBloco).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o bloco foi gerado."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
            },
            "required": ["idBloco"],
        },
        handler=lambda args: client.call(
            "disponibilizarBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
            },
        ),
    )

    # 5. cancelarDisponibilizacaoBloco -> sei_cancelar_disponibilizacao_bloco
    server.register_tool(
        name="sei_cancelar_disponibilizacao_bloco",
        title="Cancelar Disponibilização de Bloco (SEI)",
        description=(
            "Cancela a disponibilização de um bloco no SEI "
            "(serviço SOAP cancelarDisponibilizacaoBloco)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o bloco foi gerado."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
            },
            "required": ["idBloco"],
        },
        handler=lambda args: client.call(
            "cancelarDisponibilizacaoBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
            },
        ),
    )

    # 6. concluirBloco -> sei_concluir_bloco
    server.register_tool(
        name="sei_concluir_bloco",
        title="Concluir Bloco (SEI)",
        description="Conclui um bloco na unidade (serviço SOAP concluirBloco).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
            },
            "required": ["idBloco"],
        },
        handler=lambda args: client.call(
            "concluirBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
            },
        ),
    )

    # 7. reabrirBloco -> sei_reabrir_bloco
    server.register_tool(
        name="sei_reabrir_bloco",
        title="Reabrir Bloco (SEI)",
        description="Reabre um bloco concluído na unidade (serviço SOAP reabrirBloco).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
            },
            "required": ["idBloco"],
        },
        handler=lambda args: client.call(
            "reabrirBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
            },
        ),
    )

    # 8. devolverBloco -> sei_devolver_bloco
    server.register_tool(
        name="sei_devolver_bloco",
        title="Devolver Bloco (SEI)",
        description="Devolve um bloco disponibilizado para a unidade geradora (serviço SOAP devolverBloco).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
            },
            "required": ["idBloco"],
        },
        handler=lambda args: client.call(
            "devolverBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
            },
        ),
    )

    # 9. incluirDocumentoBloco -> sei_incluir_documento_bloco
    server.register_tool(
        name="sei_incluir_documento_bloco",
        title="Incluir Documento em Bloco (SEI)",
        description=(
            "Inclui um documento em um bloco de assinatura, reunião ou interno "
            "(serviço SOAP incluirDocumentoBloco)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o bloco foi gerado."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
                "protocoloDocumento": {
                    "type": "string",
                    "description": "Número do documento visível para o usuário (ex: 0003934).",
                },
                "anotacao": {
                    "type": "string",
                    "description": "Opcional. Texto de anotação associado ao documento no bloco.",
                },
            },
            "required": ["idBloco", "protocoloDocumento"],
        },
        handler=lambda args: client.call(
            "incluirDocumentoBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
                "ProtocoloDocumento": args["protocoloDocumento"],
                "Anotacao": args.get("anotacao"),
            },
        ),
    )

    # 10. retirarDocumentoBloco -> sei_retirar_documento_bloco
    server.register_tool(
        name="sei_retirar_documento_bloco",
        title="Retirar Documento de Bloco (SEI)",
        description="Retira um documento de um bloco no SEI (serviço SOAP retirarDocumentoBloco).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o bloco foi gerado."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
                "protocoloDocumento": {
                    "type": "string",
                    "description": "Número do documento visível para o usuário (ex: 0003934).",
                },
            },
            "required": ["idBloco", "protocoloDocumento"],
        },
        handler=lambda args: client.call(
            "retirarDocumentoBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
                "ProtocoloDocumento": args["protocoloDocumento"],
            },
        ),
    )

    # 11. incluirProcessoBloco -> sei_incluir_processo_bloco
    server.register_tool(
        name="sei_incluir_processo_bloco",
        title="Incluir Processo em Bloco (SEI)",
        description=(
            "Inclui um processo em um bloco de reunião ou interno "
            "(serviço SOAP incluirProcessoBloco)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o bloco foi gerado."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo visível para o usuário (ex: 12.1.000000077-4).",
                },
                "anotacao": {
                    "type": "string",
                    "description": "Opcional. Texto de anotação associado ao processo no bloco.",
                },
            },
            "required": ["idBloco", "protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "incluirProcessoBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
                "ProtocoloProcedimento": args["protocoloProcedimento"],
                "Anotacao": args.get("anotacao"),
            },
        ),
    )

    # 12. retirarProcessoBloco -> sei_retirar_processo_bloco
    server.register_tool(
        name="sei_retirar_processo_bloco",
        title="Retirar Processo de Bloco (SEI)",
        description="Retira um processo de um bloco no SEI (serviço SOAP retirarProcessoBloco).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade onde o bloco foi gerado."},
                "idBloco": {"type": "string", "description": "Número do bloco."},
                "protocoloProcedimento": {
                    "type": "string",
                    "description": "Número do processo visível para o usuário (ex: 12.1.000000077-4).",
                },
            },
            "required": ["idBloco", "protocoloProcedimento"],
        },
        handler=lambda args: client.call(
            "retirarProcessoBloco",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdBloco": args["idBloco"],
                "ProtocoloProcedimento": args["protocoloProcedimento"],
            },
        ),
    )

    # ==========================================================================
    # PARÂMETROS E CATÁLOGOS DO SEI — 17 tools
    # ==========================================================================

    # 13. listarUnidades -> sei_listar_unidades
    server.register_tool(
        name="sei_listar_unidades",
        title="Listar Unidades Disponíveis (SEI)",
        description=(
            "Lista as unidades configuradas no acesso do serviço no SEI, podendo filtrar por "
            "IdTipoProcedimento e IdSerie (serviço SOAP listarUnidades)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idTipoProcedimento": {
                    "type": "string",
                    "description": "Opcional. Filtra unidades pelo ID do tipo de processo.",
                },
                "idSerie": {
                    "type": "string",
                    "description": "Opcional. Filtra unidades pelo ID do tipo de documento (série).",
                },
            },
        },
        handler=lambda args: client.call(
            "listarUnidades",
            {
                "IdTipoProcedimento": args.get("idTipoProcedimento"),
                "IdSerie": args.get("idSerie"),
            },
        ),
    )

    # 14. listarTiposProcedimento -> sei_listar_tipos_procedimento
    server.register_tool(
        name="sei_listar_tipos_procedimento",
        title="Listar Tipos de Processo (SEI)",
        description=(
            "Lista os tipos de processo liberados para o serviço no SEI "
            "(serviço SOAP listarTiposProcedimento)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "Opcional. ID da unidade cadastrada no serviço."},
                "idSerie": {"type": "string", "description": "Opcional. ID da série documental cadastrada no serviço."},
                "sinIndividual": {
                    "type": "string",
                    "enum": ["S", "N"],
                    "description": "Opcional. Filtra por tipos de processo individuais ('S' ou 'N').",
                },
            },
        },
        handler=lambda args: client.call(
            "listarTiposProcedimento",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdSerie": args.get("idSerie"),
                "SinIndividual": args.get("sinIndividual"),
            },
        ),
    )

    # 15. listarTiposPrioridade -> sei_listar_tipos_prioridade
    server.register_tool(
        name="sei_listar_tipos_prioridade",
        title="Listar Tipos de Prioridade (SEI)",
        description="Lista os tipos de prioridade de processo disponíveis no SEI (serviço SOAP listarTiposPrioridade).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
            },
        },
        handler=lambda args: client.call(
            "listarTiposPrioridade",
            {
                "IdUnidade": args.get("idUnidade"),
            },
        ),
    )

    # 16. listarTiposProcedimentoOuvidoria -> sei_listar_tipos_procedimento_ouvidoria
    server.register_tool(
        name="sei_listar_tipos_procedimento_ouvidoria",
        title="Listar Tipos de Processo da Ouvidoria (SEI)",
        description=(
            "Lista os tipos de processo habilitados para registro de ouvidoria "
            "(serviço SOAP listarTiposProcedimentoOuvidoria)."
        ),
        input_schema={"type": "object", "properties": {}},
        handler=lambda _args: client.call("listarTiposProcedimentoOuvidoria", {}),
    )

    # 17. listarSeries -> sei_listar_series
    server.register_tool(
        name="sei_listar_series",
        title="Listar Séries Documentais / Tipos de Documento (SEI)",
        description=(
            "Lista as séries (tipos de documento) liberadas para o serviço no SEI "
            "(serviço SOAP listarSeries)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "Opcional. ID da unidade cadastrada no serviço."},
                "idTipoProcedimento": {
                    "type": "string",
                    "description": "Opcional. Filtra pelo ID do tipo de processo.",
                },
            },
        },
        handler=lambda args: client.call(
            "listarSeries",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdTipoProcedimento": args.get("idTipoProcedimento"),
            },
        ),
    )

    # 18. listarContatos -> sei_listar_contatos
    server.register_tool(
        name="sei_listar_contatos",
        title="Listar e Pesquisar Contatos (SEI)",
        description=(
            "Pesquisa contatos cadastrados no SEI por tipo de contato, sigla, nome, CPF, CNPJ, "
            "matrícula ou lista de IDs (serviço SOAP listarContatos)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idTipoContato": {"type": "string", "description": "Opcional. Filtra pelo ID do tipo de contato."},
                "paginaRegistros": {
                    "type": "string",
                    "description": "Opcional. Número máximo de registros por página (1 a 1000, padrão '100').",
                },
                "paginaAtual": {
                    "type": "string",
                    "description": "Opcional. Número da página atual (padrão '1').",
                },
                "sigla": {"type": "string", "description": "Opcional. Filtra contato pela sigla."},
                "nome": {"type": "string", "description": "Opcional. Filtra contato pelo nome."},
                "cpf": {"type": "string", "description": "Opcional. Filtra contato pelo CPF."},
                "cnpj": {"type": "string", "description": "Opcional. Filtra contato pelo CNPJ."},
                "matricula": {"type": "string", "description": "Opcional. Filtra contato pela matrícula."},
                "idContatos": {
                    "type": "array",
                    "description": "Opcional. Lista de identificadores internos de contatos (IdContato).",
                    "items": {"type": "string"},
                },
            },
        },
        handler=lambda args: client.call(
            "listarContatos",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdTipoContato": args.get("idTipoContato"),
                "PaginaRegistros": str(args.get("paginaRegistros") or "100"),
                "PaginaAtual": str(args.get("paginaAtual") or "1"),
                "Sigla": args.get("sigla"),
                "Nome": args.get("nome"),
                "Cpf": args.get("cpf"),
                "Cnpj": args.get("cnpj"),
                "Matricula": args.get("matricula"),
                "IdContatos": args.get("idContatos") or [],
            },
        ),
    )

    # 19. atualizarContatos -> sei_atualizar_contatos
    server.register_tool(
        name="sei_atualizar_contatos",
        title="Atualizar / Cadastrar / Excluir / Desativar Contatos (SEI)",
        description=(
            "Atualiza um conjunto de contatos no SEI (serviço SOAP atualizarContatos). "
            "No campo StaOperacao de cada Contato informe: 'A'=Atualizar (cadastramento ou alteração), "
            "'E'=Excluir, 'D'=Desativar, 'R'=Reativar."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "contatos": {
                    "type": "array",
                    "description": "Conjunto de estruturas Contato para atualização.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "StaOperacao": {
                                "type": "string",
                                "enum": ["A", "E", "D", "R"],
                                "description": "A=Atualizar/Cadastrar, E=Excluir, D=Desativar, R=Reativar.",
                            },
                            "IdContato": {"type": "string", "description": "ID interno do contato."},
                            "IdTipoContato": {"type": "string", "description": "ID do tipo de contato."},
                            "Sigla": {"type": "string", "description": "Sigla do contato."},
                            "Nome": {"type": "string", "description": "Nome do contato."},
                            "NomeSocial": {"type": "string"},
                            "StaNatureza": {
                                "type": "string",
                                "enum": ["F", "J"],
                                "description": "F=Pessoa Física, J=Pessoa Jurídica.",
                            },
                            "IdContatoAssociado": {"type": "string"},
                            "SinEnderecoAssociado": {"type": "string", "enum": ["S", "N"]},
                            "Endereco": {"type": "string"},
                            "Complemento": {"type": "string"},
                            "Bairro": {"type": "string"},
                            "IdCidade": {"type": "string"},
                            "IdEstado": {"type": "string"},
                            "IdPais": {"type": "string"},
                            "Cep": {"type": "string"},
                            "StaGenero": {"type": "string", "enum": ["F", "M"]},
                            "IdCargo": {"type": "string"},
                            "Cpf": {"type": "string"},
                            "Cnpj": {"type": "string"},
                            "Rg": {"type": "string"},
                            "OrgaoExpedidor": {"type": "string"},
                            "Matricula": {"type": "string"},
                            "MatriculaOab": {"type": "string"},
                            "TelefoneComercial": {"type": "string"},
                            "TelefoneResidencial": {"type": "string"},
                            "TelefoneCelular": {"type": "string"},
                            "DataNascimento": {"type": "string"},
                            "Email": {"type": "string"},
                            "SitioInternet": {"type": "string"},
                            "Observacao": {"type": "string"},
                            "SinAtivo": {"type": "string", "enum": ["S", "N"]},
                        },
                        "required": ["StaOperacao", "Nome"],
                    },
                },
            },
            "required": ["contatos"],
        },
        handler=lambda args: client.call(
            "atualizarContatos",
            {
                "IdUnidade": args.get("idUnidade"),
                "Contatos": args["contatos"],
            },
        ),
    )

    # 20. listarUsuarios -> sei_listar_usuarios
    server.register_tool(
        name="sei_listar_usuarios",
        title="Listar Usuários da Unidade (SEI)",
        description=(
            "Retorna o conjunto de usuários que possuem o perfil 'Básico' do SEI na unidade "
            "(serviço SOAP listarUsuarios)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idUsuario": {
                    "type": "string",
                    "description": "Opcional. Filtra por um usuário determinado (IdUsuario).",
                },
            },
        },
        handler=lambda args: client.call(
            "listarUsuarios",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdUsuario": args.get("idUsuario"),
            },
        ),
    )

    # 21. listarExtensoesPermitidas -> sei_listar_extensoes_permitidas
    server.register_tool(
        name="sei_listar_extensoes_permitidas",
        title="Listar Extensões de Arquivo Permitidas (SEI)",
        description=(
            "Lista as extensões de arquivos permitidas para documentos externos no SEI "
            "(serviço SOAP listarExtensoesPermitidas)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idArquivoExtensao": {
                    "type": "string",
                    "description": "Opcional. Filtra por uma extensão específica.",
                },
            },
        },
        handler=lambda args: client.call(
            "listarExtensoesPermitidas",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdArquivoExtensao": args.get("idArquivoExtensao"),
            },
        ),
    )

    # 22. listarHipotesesLegais -> sei_listar_hipoteses_legais
    server.register_tool(
        name="sei_listar_hipoteses_legais",
        title="Listar Hipóteses Legais (SEI)",
        description=(
            "Lista as hipóteses legais disponíveis no SEI, opcionalmente filtradas pelo nível de acesso "
            "(1 = Restrito, 2 = Sigiloso) (serviço SOAP listarHipotesesLegais)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "nivelAcesso": {
                    "type": "string",
                    "enum": ["1", "2"],
                    "description": "Opcional. Filtra hipóteses pelo nível de acesso ('1' = Restrito, '2' = Sigiloso).",
                },
            },
        },
        handler=lambda args: client.call(
            "listarHipotesesLegais",
            {
                "IdUnidade": args.get("idUnidade"),
                "NivelAcesso": args.get("nivelAcesso"),
            },
        ),
    )

    # 23. listarTiposConferencia -> sei_listar_tipos_conferencia
    server.register_tool(
        name="sei_listar_tipos_conferencia",
        title="Listar Tipos de Conferência (SEI)",
        description=(
            "Lista os tipos de conferência disponíveis para documentos externos no SEI "
            "(serviço SOAP listarTiposConferencia)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "Opcional. ID da unidade cadastrada no serviço."},
            },
        },
        handler=lambda args: client.call(
            "listarTiposConferencia",
            {
                "IdUnidade": args.get("idUnidade"),
            },
        ),
    )

    # 24. listarMarcadoresUnidade -> sei_listar_marcadores_unidade
    server.register_tool(
        name="sei_listar_marcadores_unidade",
        title="Listar Marcadores da Unidade (SEI)",
        description="Lista os marcadores disponíveis na unidade no SEI (serviço SOAP listarMarcadoresUnidade).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
            },
        },
        handler=lambda args: client.call(
            "listarMarcadoresUnidade",
            {
                "IdUnidade": args.get("idUnidade"),
            },
        ),
    )

    # 25. listarCargos -> sei_listar_cargos
    server.register_tool(
        name="sei_listar_cargos",
        title="Listar Cargos (SEI)",
        description=(
            "Lista os cargos cadastrados no SEI com ExpressaoCargo, ExpressaoTratamento e ExpressaoVocativo "
            "(serviço SOAP listarCargos)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idCargo": {"type": "string", "description": "Opcional. Filtra por um cargo específico."},
            },
        },
        handler=lambda args: client.call(
            "listarCargos",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdCargo": args.get("idCargo"),
            },
        ),
    )

    # 26. listarPaises -> sei_listar_paises
    server.register_tool(
        name="sei_listar_paises",
        title="Listar Países (SEI)",
        description="Lista os países cadastrados no SEI (serviço SOAP listarPaises).",
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
            },
        },
        handler=lambda args: client.call(
            "listarPaises",
            {
                "IdUnidade": args.get("idUnidade"),
            },
        ),
    )

    # 27. listarEstados -> sei_listar_estados
    server.register_tool(
        name="sei_listar_estados",
        title="Listar Estados / UFs (SEI)",
        description=(
            "Lista os estados cadastrados no SEI com código IBGE, opcionalmente filtrados por IdPais "
            "(serviço SOAP listarEstados)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idPais": {"type": "string", "description": "Opcional. Filtra estados pelo ID do país."},
            },
        },
        handler=lambda args: client.call(
            "listarEstados",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdPais": args.get("idPais"),
            },
        ),
    )

    # 28. listarCidades -> sei_listar_cidades
    server.register_tool(
        name="sei_listar_cidades",
        title="Listar Cidades / Municípios (SEI)",
        description=(
            "Lista as cidades cadastradas no SEI com código IBGE, capital e coordenadas, "
            "filtradas por IdPais e IdEstado (serviço SOAP listarCidades)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idPais": {"type": "string", "description": "Opcional. Filtra cidades pelo país informado."},
                "idEstado": {"type": "string", "description": "Opcional. Filtra cidades pelo estado informado."},
            },
        },
        handler=lambda args: client.call(
            "listarCidades",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdPais": args.get("idPais"),
                "IdEstado": args.get("idEstado"),
            },
        ),
    )

    # 29. listarFeriados -> sei_listar_feriados
    server.register_tool(
        name="sei_listar_feriados",
        title="Listar Feriados (SEI)",
        description=(
            "Lista os feriados cadastrados para um órgão em um período de datas "
            "(serviço SOAP listarFeriados)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idUnidade": {"type": "string", "description": "ID da unidade no SEI."},
                "idOrgao": {"type": "string", "description": "Identificador do órgão."},
                "dataInicial": {"type": "string", "description": "Data inicial da consulta (DD/MM/AAAA)."},
                "dataFinal": {"type": "string", "description": "Data final da consulta (DD/MM/AAAA)."},
            },
            "required": ["idOrgao", "dataInicial", "dataFinal"],
        },
        handler=lambda args: client.call(
            "listarFeriados",
            {
                "IdUnidade": args.get("idUnidade"),
                "IdOrgao": args["idOrgao"],
                "DataInicial": args["dataInicial"],
                "DataFinal": args["dataFinal"],
            },
        ),
    )

    # ==========================================================================
    # SERVIÇOS SIP (Seção 4 do Manual SEI Web Services v3.1) — 3 tools
    # ==========================================================================

    # 30. listarPermissao -> sip_listar_permissao
    server.register_tool(
        name="sip_listar_permissao",
        title="Listar Permissões de Usuários (SIP)",
        description=(
            "Lista permissões de usuários cadastradas no SIP (Seção 4.2 — serviço SOAP listarPermissao em "
            "/sip/controlador_ws.php?servico=wsdl)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idSistema": {"type": "string", "description": "ID do sistema no SIP."},
                "idOrgaoUsuario": {"type": "string", "description": "Opcional. ID do órgão do usuário no SIP."},
                "idUsuario": {"type": "string", "description": "Opcional. ID do usuário no SIP."},
                "idOrigemUsuario": {"type": "string", "description": "Opcional. ID do usuário no sistema de origem."},
                "idOrgaoUnidade": {"type": "string", "description": "Opcional. ID do órgão da unidade no SIP."},
                "idUnidade": {"type": "string", "description": "Opcional. ID da unidade no SIP."},
                "idOrigemUnidade": {"type": "string", "description": "Opcional. ID da unidade no sistema de origem."},
                "idPerfil": {"type": "string", "description": "Opcional. ID do perfil no SIP."},
            },
            "required": ["idSistema"],
        },
        handler=lambda args: client.call(
            "listarPermissao",
            {
                "IdSistema": args["idSistema"],
                "IdOrgaoUsuario": args.get("idOrgaoUsuario"),
                "IdUsuario": args.get("idUsuario"),
                "IdOrigemUsuario": args.get("idOrigemUsuario"),
                "IdOrgaoUnidade": args.get("idOrgaoUnidade"),
                "IdUnidade": args.get("idUnidade"),
                "IdOrigemUnidade": args.get("idOrigemUnidade"),
                "IdPerfil": args.get("idPerfil"),
            },
        ),
    )

    # 31. replicarPermissao -> sip_replicar_permissao
    server.register_tool(
        name="sip_replicar_permissao",
        title="Replicar Permissões de Usuários (SIP)",
        description=(
            "Cadastra/altera (StaOperacao='A') ou exclui (StaOperacao='E') permissões no SIP "
            "(Seção 4.2 — serviço SOAP replicarPermissao)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "permissoes": {
                    "type": "array",
                    "description": "Conjunto de estruturas Permissao para replicação no SIP.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "StaOperacao": {"type": "string", "enum": ["A", "E"]},
                            "IdSistema": {"type": "string"},
                            "IdOrgaoUsuario": {"type": "string"},
                            "IdUsuario": {"type": "string"},
                            "IdOrigemUsuario": {"type": "string"},
                            "IdOrgaoUnidade": {"type": "string"},
                            "IdUnidade": {"type": "string"},
                            "IdOrigemUnidade": {"type": "string"},
                            "IdPerfil": {"type": "string"},
                            "DataInicial": {"type": "string"},
                            "DataFinal": {"type": "string"},
                            "SinSubunidades": {"type": "string", "enum": ["S", "N"]},
                        },
                        "required": [
                            "StaOperacao",
                            "IdSistema",
                            "IdOrgaoUsuario",
                            "IdOrgaoUnidade",
                            "IdPerfil",
                        ],
                    },
                },
            },
            "required": ["permissoes"],
        },
        handler=lambda args: client.call(
            "replicarPermissao",
            {
                "Permissoes": args["permissoes"],
            },
        ),
    )

    # 32. replicarUsuario -> sip_replicar_usuario
    server.register_tool(
        name="sip_replicar_usuario",
        title="Replicar Usuários (SIP)",
        description=(
            "Replica usuários no SIP (StaOperacao: 'A'=Atualizar, 'E'=Excluir, 'D'=Desativar, 'R'=Reativar) "
            "(Seção 4.2 — serviço SOAP replicarUsuario)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "usuarios": {
                    "type": "array",
                    "description": "Conjunto de estruturas Usuario para replicação no SIP.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "StaOperacao": {"type": "string", "enum": ["A", "E", "D", "R"]},
                            "IdOrigem": {"type": "string"},
                            "IdOrgao": {"type": "string"},
                            "Sigla": {"type": "string"},
                            "Nome": {"type": "string"},
                        },
                        "required": ["StaOperacao", "IdOrgao", "Sigla", "Nome"],
                    },
                },
            },
            "required": ["usuarios"],
        },
        handler=lambda args: client.call(
            "replicarUsuario",
            {
                "Usuarios": args["usuarios"],
            },
        ),
    )

    # ==========================================================================
    # SERVIÇOS ACESSADOS EM OUTROS SISTEMAS (Seção 5) — 1 tool
    # ==========================================================================

    # 33. listarCargoFuncao -> sei_listar_cargo_funcao
    server.register_tool(
        name="sei_listar_cargo_funcao",
        title="Listar Cargos e Funções de Assinatura no Sistema de RH (SEI)",
        description=(
            "Consulta a lista de cargos e funções de assinatura de um usuário no Web Service externo de RH "
            "(Seção 5 do Manual SEI Web Services v3.1 — serviço SOAP listarCargoFuncao)."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "idOrgao": {"type": "string", "description": "ID do órgão associado com o usuário."},
                "idOrigem": {"type": "string", "description": "ID de origem associado com o usuário."},
                "sigla": {"type": "string", "description": "Sigla do usuário."},
            },
            "required": ["idOrgao", "idOrigem", "sigla"],
        },
        handler=lambda args: client.call(
            "listarCargoFuncao",
            {
                "IdOrgao": args["idOrgao"],
                "IdOrigem": args["idOrigem"],
                "Sigla": args["sigla"],
            },
        ),
    )
