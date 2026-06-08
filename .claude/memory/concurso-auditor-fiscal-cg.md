---
name: concurso-auditor-fiscal-cg
description: Objetivo do usuário — concurso Auditor Fiscal da Receita Municipal de Campina Grande/PB (IDECAN), e o app de simulados construído
metadata:
  type: project
---

O usuário (Bruno) estuda para o cargo de **Auditor Fiscal da Receita Municipal de Campina Grande/PB**, banca **IDECAN**, Edital 01/2026. **Meta: ficar entre os 4 primeiros** (4 vagas).

Fatos-chave do edital (lidos em /Editais — edital + Retificações 01 e 02 + respostas a impugnações):
- **Prova objetiva: 30/08/2026 (domingo, manhã)**. Resultado final: 11/12/2026.
- 40 questões / 60 pts: 10 Port + 4 Informática + 3 História de CG + 3 Legisl/Ética (todas peso 1) + **20 Específicos (peso 2 = 40 pts, decidem a vaga)**.
- Requisito: superior em **qualquer área** (retificado pela LC Municipal 204/2024).
- **2ª etapa = Análise de Vida Pregressa** (eliminatória, só Auditor Fiscal). NÃO há prova discursiva (era erro do cronograma, removido na Retificação 01).
- Específicos: Direito Tributário (CTN), Tributos Municipais (IPTU/ISS/ITBI), **Código Tributário Municipal de CG (LC 116/2016)** = diferencial, AFO/LRF, Contabilidade, Auditoria, Lei 14.133.

**App de simulados** em `concurso-project/simulado-auditor-fiscal/` (Python stdlib + front-end), base no projeto `../question-project`. Comportamento de PROVA REAL: grava as respostas **sem revelar acerto/erro**; a nota só sai ao **finalizar**, ponderada pelos pesos do edital (Gerais ×1, Específicos ×2, total 60). O resultado mostra **só a nota** e o desempenho por disciplina — **gabarito nunca é revelado**. Aprovação no simulado = ≥50% e ≥1 acerto em cada disciplina (regra 10.3).
- **10 simulados** (Simulado 01–10), 40 questões autorais cada, no formato do edital; gabarito balanceado (10 A/B/C/D por simulado, padrão diferente entre eles).
- Gabarito protegido em **base64 em arquivo separado**: `respostas.b64` (só as chaves) → `python gerar_gabaritos.py` decodifica, valida e recriptografa em `gabaritos/*.enc`. Servidor: `python servidor.py` → localhost:8000.
- Rotas: `/api/simulados`, `/api/questoes?simulado=ID`, `/api/responder` (grava sem veredito), `/api/finalizar` (corrige ponderado), `/api/estado`, `/api/refazer`.
- Adicionar 5º simulado: novo `simulados/simulado-05.json` + chave em `respostas.b64` + rodar `gerar_gabaritos.py` (documentado no README).

Plano de estudos detalhado (12 semanas) em [[plano-estudos]].
