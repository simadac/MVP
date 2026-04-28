"""
controllers/ocorrencias_controller.py — SIMAD
Contém toda a lógica de negócio das ocorrências.
As rotas apenas chamam as funções daqui.
"""

from datetime import datetime
from flask import jsonify, request
from database import get_connection


# ============================================================
# POST /api/ocorrencias
# Cadastra uma nova ocorrência enviada pelo morador
# ============================================================
def cadastrar_ocorrencia():
    dados = request.get_json()

    # Validações mínimas
    campos_obrigatorios = ["titulo", "descricao", "id_morador"]
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            return jsonify({"erro": f"Campo obrigatório ausente: {campo}"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            INSERT INTO ocorrencias
                (titulo, tipo_ocorrencia, descricao, cep, endereco, bairro,
                 cidade, estado, latitude, longitude, urgencia,
                 status, id_morador, data_criacao)
            VALUES
                (%s, %s, %s, %s, %s, %s,
                 %s, %s, %s, %s, %s,
                 'pendente', %s, %s)
        """
        valores = (
            dados.get("titulo"),
            dados.get("tipo_ocorrencia", "Geral"),
            dados.get("descricao"),
            dados.get("cep"),
            dados.get("endereco"),
            dados.get("bairro"),
            dados.get("cidade"),
            dados.get("estado"),
            dados.get("latitude"),
            dados.get("longitude"),
            dados.get("urgencia", "medio"),
            dados.get("id_morador"),
            datetime.now(),
        )
        cursor.execute(sql, valores)
        id_novo = cursor.lastrowid

        # Salva fotos enviadas pelo front-end, quando existirem.
        # Neste MVP as fotos podem chegar como Base64 no campo "fotos".
        # Em produção, o ideal é salvar os arquivos em uma pasta/storage
        # e gravar apenas o caminho da imagem no banco.
        fotos = dados.get("fotos", [])
        for foto in fotos:
            caminho_foto = foto.get("caminho_foto") if isinstance(foto, dict) else foto

            if not caminho_foto:
                continue

            cursor.execute(
                """
                    INSERT INTO fotos_ocorrencia
                        (id_ocorrencia, caminho_foto, data_upload)
                    VALUES
                        (%s, %s, %s)
                """,
                (id_novo, caminho_foto, datetime.now()),
            )

        conn.commit()
        return jsonify({"mensagem": "Ocorrência cadastrada com sucesso", "id": id_novo}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"erro": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/ocorrencias
# Lista todas as ocorrências (para o agente), com filtros opcionais
# Parâmetros de query: status, tipo_ocorrencia, bairro, data_inicio, data_fim
# ============================================================
def listar_ocorrencias():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Monta filtros dinamicamente conforme parâmetros recebidos
        condicoes = []
        valores = []

        status = request.args.get("status")
        tipo = request.args.get("tipo_ocorrencia")
        bairro = request.args.get("bairro")
        data_inicio = request.args.get("data_inicio")
        data_fim = request.args.get("data_fim")

        if status:
            condicoes.append("o.status = %s")
            valores.append(status)
        if tipo:
            condicoes.append("o.tipo_ocorrencia = %s")
            valores.append(tipo)
        if bairro:
            condicoes.append("o.bairro LIKE %s")
            valores.append(f"%{bairro}%")
        if data_inicio:
            condicoes.append("DATE(o.data_criacao) >= %s")
            valores.append(data_inicio)
        if data_fim:
            condicoes.append("DATE(o.data_criacao) <= %s")
            valores.append(data_fim)

        where_clause = "WHERE " + " AND ".join(condicoes) if condicoes else ""

        sql = f"""
            SELECT
                o.*,
                u.nome AS morador_nome,
                u.telefone AS morador_telefone,
                ag.nome AS agente_nome
            FROM ocorrencias o
            LEFT JOIN usuarios u  ON o.id_morador = u.id
            LEFT JOIN usuarios ag ON o.id_agente_responsavel = ag.id
            {where_clause}
            ORDER BY o.data_criacao DESC
        """
        cursor.execute(sql, valores)
        ocorrencias = cursor.fetchall()
        # Converter datas para string (JSON-serializável)
        ocorrencias = _serializar_lista(ocorrencias)
        return jsonify(ocorrencias), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/ocorrencias/<id>
# Retorna uma ocorrência específica pelo ID
# ============================================================
def buscar_ocorrencia(id_ocorrencia):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            SELECT
                o.*,
                u.nome  AS morador_nome,
                u.email AS morador_email,
                ag.nome AS agente_nome
            FROM ocorrencias o
            LEFT JOIN usuarios u  ON o.id_morador = u.id
            LEFT JOIN usuarios ag ON o.id_agente_responsavel = ag.id
            WHERE o.id = %s
        """
        cursor.execute(sql, (id_ocorrencia,))
        ocorrencia = cursor.fetchone()

        if not ocorrencia:
            return jsonify({"erro": "Ocorrência não encontrada"}), 404

        # Busca fotos vinculadas
        cursor.execute(
            "SELECT * FROM fotos_ocorrencia WHERE id_ocorrencia = %s", (id_ocorrencia,)
        )
        ocorrencia["fotos"] = cursor.fetchall()

        return jsonify(_serializar(ocorrencia)), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ============================================================
# GET /api/ocorrencias/morador/<id_morador>
# Lista ocorrências de um morador específico
# ============================================================
def listar_por_morador(id_morador):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            SELECT
                o.*,
                ag.nome AS agente_nome
            FROM ocorrencias o
            LEFT JOIN usuarios ag ON o.id_agente_responsavel = ag.id
            WHERE o.id_morador = %s
            ORDER BY o.data_criacao DESC
        """
        cursor.execute(sql, (id_morador,))
        ocorrencias = cursor.fetchall()
        return jsonify(_serializar_lista(ocorrencias)), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ============================================================
# PUT /api/ocorrencias/<id>/status
# Agente atualiza o status de uma ocorrência
# ============================================================
def atualizar_status(id_ocorrencia):
    dados = request.get_json()

    status_validos = ["pendente", "em_andamento", "aprovado", "resolvido", "rejeitado"]
    novo_status = dados.get("status")

    if not novo_status or novo_status not in status_validos:
        return jsonify({"erro": "Status inválido ou ausente"}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        sql = """
            UPDATE ocorrencias SET
                status                  = %s,
                observacao_agente       = %s,
                comentario_interno      = %s,
                equipe                  = %s,
                id_agente_responsavel   = %s,
                data_atualizacao        = %s
            WHERE id = %s
        """
        valores = (
            novo_status,
            dados.get("observacao_agente"),
            dados.get("comentario_interno"),
            dados.get("equipe"),
            dados.get("id_agente"),
            datetime.now(),
            id_ocorrencia,
        )
        cursor.execute(sql, valores)

        if cursor.rowcount == 0:
            return jsonify({"erro": "Ocorrência não encontrada"}), 404

        conn.commit()
        return jsonify({"mensagem": "Status atualizado com sucesso"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"erro": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ============================================================
# Funções auxiliares internas
# ============================================================
def _serializar(obj):
    """Converte campos datetime para string ISO antes de retornar JSON."""
    for chave, valor in obj.items():
        if isinstance(valor, datetime):
            obj[chave] = valor.isoformat()
    return obj


def _serializar_lista(lista):
    return [_serializar(item) for item in lista]
