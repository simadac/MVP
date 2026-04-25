"""
routes/ocorrencias_routes.py — SIMAD
Define as rotas da API e conecta cada uma ao seu controller.
"""

from flask import Blueprint
from controllers.ocorrencias_controller import (
    cadastrar_ocorrencia,
    listar_ocorrencias,
    buscar_ocorrencia,
    listar_por_morador,
    atualizar_status,
)

# Blueprint agrupa todas as rotas de ocorrências
ocorrencias_bp = Blueprint("ocorrencias", __name__)

# POST  /api/ocorrencias          → cadastrar
ocorrencias_bp.route("/", methods=["POST"])(cadastrar_ocorrencia)

# GET   /api/ocorrencias          → listar todas (com filtros via query params)
ocorrencias_bp.route("/", methods=["GET"])(listar_ocorrencias)

# GET   /api/ocorrencias/<id>     → buscar uma específica
ocorrencias_bp.route("/<int:id_ocorrencia>", methods=["GET"])(buscar_ocorrencia)

# GET   /api/ocorrencias/morador/<id_morador>
ocorrencias_bp.route("/morador/<int:id_morador>", methods=["GET"])(listar_por_morador)

# PUT   /api/ocorrencias/<id>/status → agente atualiza status
ocorrencias_bp.route("/<int:id_ocorrencia>/status", methods=["PUT"])(atualizar_status)
