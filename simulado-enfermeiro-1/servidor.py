# -*- coding: utf-8 -*-
"""
Servidor local dos simulados de concurso (Auditor Fiscal da Receita Municipal).

Comportamento de PROVA:
  - As respostas são GRAVADAS sem informar acerto/erro durante a prova.
  - O resultado é calculado apenas ao FINALIZAR, seguindo os pesos do edital:
      Conhecimentos Gerais  -> peso 1 por questão (20 questões = 20 pts)
      Conhecimentos Específicos -> peso 2 por questão (20 questões = 40 pts)
      Total = 60 pontos.
  - O gabarito (gabaritos/*.enc) é carregado em memória e NUNCA é enviado ao
    navegador; o resultado mostra apenas a NOTA e o desempenho por disciplina.

Persistência (JSON):
  - simulados/simulado-0X.json : base de questões (somente leitura).
  - gabaritos/simulado-0X.enc  : gabarito codificado (só o servidor lê).
  - usuarios.json              : controle de usuário.
  - respostas.json             : respostas e resultado por usuário/simulado.

Rodar:  python servidor.py   ->   http://localhost:8000
"""
import base64
import glob
import json
import os
import re
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTA = 8000

DIR_SIMULADOS = os.path.join(BASE_DIR, "simulados")
DIR_GABARITOS = os.path.join(BASE_DIR, "gabaritos")
ARQ_USUARIOS = os.path.join(BASE_DIR, "usuarios.json")
ARQ_RESPOSTAS = os.path.join(BASE_DIR, "respostas.json")

ESTATICOS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
}

# Ordem das disciplinas para exibição do desempenho.
AREAS_ORDEM = [
    "Língua Portuguesa",
    "Noções de Informática",
    "História de Campina Grande/PB",
    "Legislação e Ética no Serviço Público",
    "Conhecimentos Específicos",
]
AREA_ESPECIFICOS = "Conhecimentos Específicos"

_lock = threading.Lock()  # serializa leitura/escrita dos JSON de estado


def peso(area):
    """Peso da questão conforme o edital: Específicos = 2, Gerais = 1."""
    return 2 if area == AREA_ESPECIFICOS else 1


# --------------------------------------------------------------------------- #
# Carregamento das bases (questões + gabaritos)
# --------------------------------------------------------------------------- #
def carregar_simulados():
    simulados = {}
    for caminho in sorted(glob.glob(os.path.join(DIR_SIMULADOS, "*.json"))):
        sid = os.path.splitext(os.path.basename(caminho))[0]
        with open(caminho, encoding="utf-8") as f:
            simulados[sid] = json.load(f)
    if not simulados:
        raise SystemExit("Nenhum simulado encontrado em simulados/.")
    return simulados


def carregar_gabaritos():
    gabaritos = {}
    for caminho in sorted(glob.glob(os.path.join(DIR_GABARITOS, "*.enc"))):
        sid = os.path.splitext(os.path.basename(caminho))[0]
        with open(caminho, "rb") as f:
            dados = json.loads(base64.b64decode(f.read()).decode("utf-8"))
        gabaritos[sid] = {g["id"]: g["indice_correto"] for g in dados}
    return gabaritos


SIMULADOS = carregar_simulados()
GABARITOS = carregar_gabaritos()

faltando = [sid for sid in SIMULADOS if sid not in GABARITOS]
if faltando:
    raise SystemExit(
        "Gabarito ausente para: " + ", ".join(faltando) +
        ". Rode primeiro: python gerar_gabaritos.py"
    )


def titulo_simulado(sid):
    m = re.search(r"(\d+)$", sid)
    return f"Simulado {m.group(1)}" if m else sid


# --------------------------------------------------------------------------- #
# JSON de estado (escrita atômica)
# --------------------------------------------------------------------------- #
def _ler_json(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return padrao


def _gravar_json(caminho, dados):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho)


def _slug(nome):
    base = re.sub(r"[^a-z0-9]+", "-", nome.strip().lower()).strip("-")
    return base or "usuario"


# --------------------------------------------------------------------------- #
# Usuários
# --------------------------------------------------------------------------- #
def criar_ou_obter_usuario(nome):
    nome = (nome or "").strip()
    if not nome:
        return None
    with _lock:
        usuarios = _ler_json(ARQ_USUARIOS, [])
        for u in usuarios:
            if u["nome"].strip().lower() == nome.lower():
                return u
        novo_id = _slug(nome)
        existentes = {u["id"] for u in usuarios}
        uid, n = novo_id, 2
        while uid in existentes:
            uid = f"{novo_id}-{n}"
            n += 1
        usuario = {"id": uid, "nome": nome, "criadoEm": datetime.now().isoformat(timespec="seconds")}
        usuarios.append(usuario)
        _gravar_json(ARQ_USUARIOS, usuarios)
        return usuario


# --------------------------------------------------------------------------- #
# Respostas / estado por usuário+simulado
# --------------------------------------------------------------------------- #
def _estado(respostas, usuario_id, simulado_id):
    return respostas.setdefault(usuario_id, {}).setdefault(
        simulado_id, {"respostas": {}, "resultado": None}
    )


def obter_estado(usuario_id, simulado_id):
    respostas = _ler_json(ARQ_RESPOSTAS, {})
    est = respostas.get(usuario_id, {}).get(simulado_id, {"respostas": {}, "resultado": None})
    return {"respostas": est.get("respostas", {}), "resultado": est.get("resultado")}


def salvar_resposta(usuario_id, simulado_id, questao_id, indice):
    """Grava a alternativa escolhida SEM informar se está correta."""
    with _lock:
        respostas = _ler_json(ARQ_RESPOSTAS, {})
        est = _estado(respostas, usuario_id, simulado_id)
        if est.get("resultado") is not None:
            return False  # já finalizado; não aceita novas respostas
        est["respostas"][str(questao_id)] = indice
        _gravar_json(ARQ_RESPOSTAS, respostas)
        return True


def refazer(usuario_id, simulado_id):
    with _lock:
        respostas = _ler_json(ARQ_RESPOSTAS, {})
        if usuario_id in respostas and simulado_id in respostas[usuario_id]:
            respostas[usuario_id][simulado_id] = {"respostas": {}, "resultado": None}
            _gravar_json(ARQ_RESPOSTAS, respostas)
        return True


def _corrigir(simulado_id, respostas_dadas):
    """Calcula o resultado ponderado. Não revela o gabarito por questão."""
    questoes = SIMULADOS[simulado_id]
    gabarito = GABARITOS[simulado_id]

    por_area = {}
    nota = 0.0
    maximo = 0.0
    for q in questoes:
        area = q.get("area", "Conhecimentos Específicos")
        p = peso(area)
        maximo += p
        bloco = por_area.setdefault(
            area, {"area": area, "acertos": 0, "total": 0, "pontos": 0, "maxPontos": 0}
        )
        bloco["total"] += 1
        bloco["maxPontos"] += p
        escolhido = respostas_dadas.get(str(q["id"]))
        if escolhido is not None and escolhido == gabarito.get(q["id"]):
            nota += p
            bloco["acertos"] += 1
            bloco["pontos"] += p

    ordenado = [por_area[a] for a in AREAS_ORDEM if a in por_area]
    ordenado += [v for k, v in por_area.items() if k not in AREAS_ORDEM]

    # Aprovação no simulado (regra 10.3 do edital): >= 50% do total,
    # >= 1 acerto em cada disciplina de Conhecimentos Gerais e >= 1 em Específicos.
    aprovado = nota >= (maximo / 2)
    for bloco in ordenado:
        if bloco["acertos"] < 1:
            aprovado = False

    return {
        "nota": round(nota, 2),
        "max": round(maximo, 2),
        "percentual": round((nota / maximo) * 100, 1) if maximo else 0.0,
        "aprovado": aprovado,
        "porArea": ordenado,
        "finalizadoEm": datetime.now().isoformat(timespec="seconds"),
    }


def finalizar(usuario_id, simulado_id):
    with _lock:
        respostas = _ler_json(ARQ_RESPOSTAS, {})
        est = _estado(respostas, usuario_id, simulado_id)
        if est.get("resultado") is not None:
            return est["resultado"]  # idempotente
        resultado = _corrigir(simulado_id, est.get("respostas", {}))
        est["resultado"] = resultado
        _gravar_json(ARQ_RESPOSTAS, respostas)
        return resultado


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, obj, status=200):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo_json(self):
        tam = int(self.headers.get("Content-Length", 0))
        if not tam:
            return {}
        try:
            return json.loads(self.rfile.read(tam).decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _estatico(self, arquivo, content_type):
        caminho = os.path.join(BASE_DIR, arquivo)
        if not os.path.exists(caminho):
            self._json({"erro": "não encontrado"}, 404)
            return
        with open(caminho, "rb") as f:
            corpo = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    # -- GET --------------------------------------------------------------- #
    def do_GET(self):
        rota = urlparse(self.path)
        caminho = rota.path
        params = parse_qs(rota.query)

        if caminho in ESTATICOS:
            arquivo, content_type = ESTATICOS[caminho]
            self._estatico(arquivo, content_type)
            return

        if caminho == "/api/simulados":
            lista = [
                {"id": sid, "titulo": titulo_simulado(sid), "total": len(SIMULADOS[sid])}
                for sid in sorted(SIMULADOS)
            ]
            self._json(lista)
            return

        if caminho == "/api/questoes":
            sid = (params.get("simulado") or [""])[0]
            if sid not in SIMULADOS:
                self._json({"erro": "simulado inexistente"}, 404)
                return
            self._json(SIMULADOS[sid])  # sem qualquer dado de resposta
            return

        if caminho == "/api/usuarios":
            self._json(_ler_json(ARQ_USUARIOS, []))
            return

        if caminho == "/api/estado":
            uid = (params.get("usuarioId") or [""])[0]
            sid = (params.get("simulado") or [""])[0]
            if sid not in SIMULADOS:
                self._json({"erro": "simulado inexistente"}, 404)
                return
            self._json(obter_estado(uid, sid))
            return

        self._json({"erro": "rota não encontrada"}, 404)

    # -- POST -------------------------------------------------------------- #
    def do_POST(self):
        caminho = urlparse(self.path).path
        dados = self._corpo_json()

        if caminho == "/api/usuarios":
            usuario = criar_ou_obter_usuario(dados.get("nome"))
            if usuario is None:
                self._json({"erro": "nome obrigatório"}, 400)
            else:
                self._json(usuario)
            return

        if caminho == "/api/responder":
            uid = dados.get("usuarioId")
            sid = dados.get("simulado")
            if sid not in SIMULADOS or not uid:
                self._json({"erro": "dados inválidos"}, 400)
                return
            try:
                qid = int(dados.get("id"))
                indice = int(dados.get("indice"))
            except (TypeError, ValueError):
                self._json({"erro": "id/indice inválidos"}, 400)
                return
            ok = salvar_resposta(uid, sid, qid, indice)
            self._json({"ok": ok})  # NÃO informa acerto/erro
            return

        if caminho == "/api/finalizar":
            uid = dados.get("usuarioId")
            sid = dados.get("simulado")
            if sid not in SIMULADOS or not uid:
                self._json({"erro": "dados inválidos"}, 400)
                return
            self._json(finalizar(uid, sid))
            return

        if caminho == "/api/refazer":
            uid = dados.get("usuarioId")
            sid = dados.get("simulado")
            if sid not in SIMULADOS or not uid:
                self._json({"erro": "dados inválidos"}, 400)
                return
            refazer(uid, sid)
            self._json({"ok": True})
            return

        self._json({"erro": "rota não encontrada"}, 404)


def main():
    servidor = ThreadingHTTPServer(("localhost", PORTA), Handler)
    print(f"Simulados em http://localhost:{PORTA}  ({len(SIMULADOS)} disponíveis · Ctrl+C para sair)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando.")
        servidor.shutdown()


if __name__ == "__main__":
    main()
