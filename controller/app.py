"""
app.py — SIMAD
Ponto de entrada do servidor Flask.
Execute com: python app.py
"""

from flask import Flask, jsonify
from flask_cors import CORS

from routes.ocorrencias_routes import ocorrencias_bp

# ============================================================
# Criação do app Flask
# ============================================================
app = Flask(__name__)

# CORS permite que o front-end (HTML aberto no navegador) chame
# a API mesmo em domínios/portas diferentes. Ajuste 'origins'
# quando fizer deploy em produção.
CORS(app, origins="*")


# ============================================================
# Registro dos Blueprints (grupos de rotas)
# ============================================================
# Todas as rotas de ocorrências ficam sob /api/ocorrencias
app.register_blueprint(ocorrencias_bp, url_prefix="/api/ocorrencias")

# TODO: quando o módulo de login estiver pronto, registre aqui:
# from routes.auth_routes import auth_bp
# app.register_blueprint(auth_bp, url_prefix="/api/auth")


# ============================================================
# Rota de health-check — útil para testar se o servidor está vivo
# ============================================================
@app.route("/api/ping")
def ping():
    return jsonify({"status": "ok", "sistema": "SIMAD"})


# ============================================================
# Tratamento global de erros
# ============================================================
@app.errorhandler(404)
def nao_encontrado(e):
    return jsonify({"erro": "Rota não encontrada"}), 404


@app.errorhandler(500)
def erro_interno(e):
    return jsonify({"erro": "Erro interno no servidor"}), 500


# ============================================================
# Execução
# ============================================================
if __name__ == "__main__":
    # debug=True: reinicia automaticamente ao salvar o arquivo.
    # Desative em produção (debug=False).
    app.run(debug=True, host="0.0.0.0", port=5000)
