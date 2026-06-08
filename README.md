# Concurso — Campina Grande/PB (IDECAN, Edital 01/2026)

Materiais de estudo e **apps de simulado** para o concurso da Prefeitura de Campina
Grande/PB (banca IDECAN). Cada app é uma aplicação local em Python (biblioteca padrão) +
front-end, no formato de **prova real**: você responde, as respostas são apenas gravadas
(sem dizer se acertou) e a **nota só aparece no final**, calculada pelos **pesos do edital**
(Conhecimentos Gerais ×1, Específicos ×2 — total 60 pontos). O **gabarito fica trancado no
servidor** e não é revelado.

## Conteúdo do repositório

| Pasta | Descrição |
|-------|-----------|
| [`simulado-auditor-fiscal/`](simulado-auditor-fiscal/) | 10 simulados para **Auditor Fiscal da Receita Municipal** (Direito Tributário, Tributos Municipais, AFO, Contabilidade, Auditoria). |
| [`simulado-enfermeiro-1/`](simulado-enfermeiro-1/) | 10 simulados para **Enfermeiro I** (Fundamentos/Lei 7.498, SUS, APS/ESF, urgência/SBV, biossegurança, imunização). |
| `Editais/` | Edital de abertura, retificações e respostas às impugnações (PDF). |

Cada simulado tem 40 questões (10 Português · 4 Informática · 3 História de Campina
Grande · 3 Legislação/Ética · 20 Conhecimentos Específicos), com gabarito **balanceado**
(10 alternativas corretas em cada letra A/B/C/D).

## Como rodar um app

```bash
cd simulado-auditor-fiscal      # ou: cd simulado-enfermeiro-1
python gerar_gabaritos.py       # gera os gabaritos codificados (uma vez)
python servidor.py              # sobe o servidor
```

Abra **http://localhost:8000** no navegador, crie um usuário, escolha um simulado e
responda. Veja o `README.md` de cada pasta para detalhes (arquitetura, gabarito em base64,
como adicionar novos simulados).

> ⚠️ As questões dos simulados são **autorais**, elaboradas para treino no padrão da banca;
> não reproduzem provas oficiais. Confira sempre o conteúdo nas fontes oficiais e na lei seca.
