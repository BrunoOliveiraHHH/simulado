# -*- coding: utf-8 -*-
"""
Gera os gabaritos codificados (gabaritos/simulado-0X.enc) a partir das respostas
guardadas em base64 no arquivo separado `respostas.b64`.

Fluxo (conforme solicitado):
  1. LÊ `respostas.b64`  ->  base64-decode  ("descriptografa")
  2. MONTA o gabarito de cada simulado e VALIDA contra simulados/simulado-0X.json
  3. base64-encode  ("criptografa novamente")  ->  grava gabaritos/simulado-0X.enc

`respostas.b64` contém apenas as respostas, no formato (após decode):
  { "simulado-01": [i1..i40], ... }   onde iN = índice 0-based da alternativa
  correta da questão de id N (0=A, 1=B, 2=C, 3=D).

Nenhuma resposta é impressa; apenas um resumo por simulado.
"""
import base64
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQ_RESPOSTAS_B64 = os.path.join(BASE_DIR, "respostas.b64")
DIR_SIMULADOS = os.path.join(BASE_DIR, "simulados")
DIR_GABARITOS = os.path.join(BASE_DIR, "gabaritos")


def carregar_chaves():
    """Lê respostas.b64 e devolve {simuladoId: [indices]} (descriptografa)."""
    if not os.path.exists(ARQ_RESPOSTAS_B64):
        raise SystemExit("respostas.b64 não encontrado.")
    with open(ARQ_RESPOSTAS_B64, "rb") as f:
        bruto = base64.b64decode(f.read())
    return json.loads(bruto.decode("utf-8"))


def carregar_questoes(simulado_id):
    caminho = os.path.join(DIR_SIMULADOS, simulado_id + ".json")
    if not os.path.exists(caminho):
        raise SystemExit(f"Simulado não encontrado: {caminho}")
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def montar_gabarito(simulado_id, indices, questoes):
    """Expande a lista de índices no gabarito [{id, tipo, indice_correto}] e valida."""
    if len(indices) != len(questoes):
        raise SystemExit(
            f"{simulado_id}: {len(indices)} respostas para {len(questoes)} questões."
        )
    por_id = {q["id"]: q for q in questoes}
    gabarito = []
    # as questões são numeradas de 1..N; a i-ésima resposta corresponde ao id i+1
    for pos, q in enumerate(sorted(questoes, key=lambda x: x["id"])):
        indice = indices[pos]
        n_opcoes = len(q.get("options", []))
        if not (0 <= indice < n_opcoes):
            raise SystemExit(
                f"{simulado_id}: índice {indice} inválido na questão {q['id']}."
            )
        gabarito.append({"id": q["id"], "tipo": "mc", "indice_correto": indice})
    # sanidade: todos os ids cobertos
    if {g["id"] for g in gabarito} != set(por_id):
        raise SystemExit(f"{simulado_id}: ids do gabarito não batem com as questões.")
    return gabarito


def gravar_enc(simulado_id, gabarito):
    """base64-encode (criptografa novamente) e grava gabaritos/simulado-0X.enc."""
    os.makedirs(DIR_GABARITOS, exist_ok=True)
    bruto = json.dumps(gabarito, ensure_ascii=False).encode("utf-8")
    codificado = base64.b64encode(bruto)
    saida = os.path.join(DIR_GABARITOS, simulado_id + ".enc")
    with open(saida, "wb") as f:
        f.write(codificado)


def main():
    chaves = carregar_chaves()
    if not chaves:
        raise SystemExit("Nenhuma resposta encontrada em respostas.b64.")
    for simulado_id in sorted(chaves):
        questoes = carregar_questoes(simulado_id)
        gabarito = montar_gabarito(simulado_id, chaves[simulado_id], questoes)
        gravar_enc(simulado_id, gabarito)
        print(f"{simulado_id}: {len(gabarito)} questões OK -> gabaritos/{simulado_id}.enc")
    print("Concluído. As respostas continuam apenas em respostas.b64 e nos .enc (base64).")


if __name__ == "__main__":
    main()
