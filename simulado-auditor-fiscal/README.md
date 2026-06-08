# Simulados — Auditor Fiscal da Receita Municipal (Campina Grande/PB)

App de estudo no formato de **prova real**: você responde, as respostas são apenas
**gravadas** (nada de "certo/errado" durante a prova) e a **nota só aparece no final**,
calculada pelos **pesos do edital**. O gabarito fica trancado no servidor e **não é
revelado** — nem ao terminar.

> Construído a partir do projeto `question-project` (mesma arquitetura), adaptado para
> simulados no padrão do edital **IDECAN / Campina Grande**.

## Os simulados (10 modelos × 40 questões)

Cada simulado segue a distribuição do edital (nível superior):

| Área | Questões | Peso | Pontos |
|------|----------|------|--------|
| Língua Portuguesa | 10 | 1 | 10 |
| Noções de Informática | 4 | 1 | 4 |
| História de Campina Grande/PB | 3 | 1 | 3 |
| Legislação e Ética no Serviço Público | 3 | 1 | 3 |
| **Conhecimentos Específicos** | **20** | **2** | **40** |
| **Total** | **40** | — | **60** |

Disponíveis: `Simulado 01` a `Simulado 10` (todos múltipla escolha A–D). Cada
simulado tem o gabarito balanceado (10 alternativas corretas em cada letra A/B/C/D).

## Como funciona a correção

- Durante a prova: cada alternativa escolhida é gravada via `POST /api/responder`,
  **sem retorno de acerto/erro**.
- Ao **finalizar** (`POST /api/finalizar`): o servidor corrige pelos pesos e devolve a
  **nota /60**, o **percentual**, o **desempenho por disciplina** (acertos e pontos) e se
  você foi **aprovado no simulado** (regra do edital: ≥ 50% e ao menos 1 acerto em cada
  disciplina). **Não** há correção questão a questão — o gabarito permanece oculto.

## Gabarito protegido (base64 em arquivo separado)

As respostas ficam **só** em base64, num arquivo à parte:

- `respostas.b64` — base64 das chaves dos 4 simulados (apenas os índices corretos).
- `gerar_gabaritos.py` — ao rodar, **decodifica** o `respostas.b64`, **monta e valida** o
  gabarito de cada simulado contra `simulados/*.json` e **recodifica** em
  `gabaritos/simulado-0X.enc` (base64). Nenhuma resposta em texto puro no repositório.
- O servidor carrega os `.enc` em memória; o navegador nunca recebe o gabarito.

## Requisitos

- Python 3.8+ (apenas biblioteca padrão).

## Como rodar

```bash
# 1) Gerar/atualizar os gabaritos codificados (sempre que mudar respostas.b64 ou as questões)
python gerar_gabaritos.py

# 2) Subir o servidor
python servidor.py
```

Abra **http://localhost:8000**.

## Como usar

1. Crie ou escolha um **usuário** (progresso e notas próprios).
2. Escolha um **simulado** (os cards mostram se está em andamento ou concluído, com a nota).
3. Responda às 40 questões (A–D), navegando com **Anterior/Próxima**. Nada é revelado.
4. Clique em **Finalizar e ver resultado** → veja a nota /60 e o desempenho por disciplina.
5. **Refazer** zera aquele simulado; **Escolher outro** volta à lista.

## Arquivos

| Arquivo / pasta              | Papel                                                         |
|------------------------------|---------------------------------------------------------------|
| `simulados/simulado-0X.json` | Base de questões (somente leitura).                           |
| `respostas.b64`              | Chaves de resposta em **base64** (fonte do gabarito).         |
| `gerar_gabaritos.py`         | Decodifica `respostas.b64` → valida → grava os `.enc`.        |
| `gabaritos/simulado-0X.enc`  | Gabarito codificado (**só o servidor lê**).                   |
| `servidor.py`                | Servidor HTTP (stdlib) + correção ponderada.                  |
| `index.html`, `style.css`, `app.js` | Front-end (telas: usuário → simulado → prova → resultado). |
| `usuarios.json`              | `[{id, nome, criadoEm}]`.                                     |
| `respostas.json`             | Respostas e resultado por usuário/simulado (sem gabarito).    |

Estrutura de `respostas.json`:

```json
{
  "<usuarioId>": {
    "<simuladoId>": {
      "respostas": { "<questaoId>": <indiceEscolhido> },
      "resultado": { "nota": 0, "max": 60, "percentual": 0, "aprovado": false, "porArea": [], "finalizadoEm": "..." }
    }
  }
}
```

## Adicionar um 5º simulado

1. Crie `simulados/simulado-05.json` com 40 questões (mesmo schema; distribuição 10/4/3/3/20).
2. Acrescente a chave `"simulado-05": [i1..i40]` (índices 0-based A–D) ao conteúdo de
   `respostas.b64`. Para regerar o base64 a partir das chaves, edite-o com uma ferramenta de
   sua preferência (o conteúdo decodificado é um JSON `{ "simulado-0X": [...] }`).
3. Rode `python gerar_gabaritos.py` e reinicie o servidor. O novo card aparece sozinho.

## Esquema de uma questão

```json
{
  "id": 1,
  "area": "Conhecimentos Específicos",
  "difficulty": "Médio",
  "type": "múltipla escolha",
  "questionText": "Enunciado...",
  "options": ["Alternativa A", "Alternativa B", "Alternativa C", "Alternativa D"]
}
```

> ⚠️ As questões são **autorais**, para treino no padrão da banca; não reproduzem provas
> oficiais. Confira sempre o conteúdo na lei seca (CTN, CF/88, LRF, Lei 4.320/64, LC 116/2003
> e legislação municipal de Campina Grande).
