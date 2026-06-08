"use strict";

// -------------------------------------------------------------------------
// Estado
// -------------------------------------------------------------------------
const estado = {
  usuario: null,        // {id, nome}
  simulado: null,       // id do simulado atual
  questoes: [],         // questões do simulado (sem respostas)
  pos: 0,               // posição atual
  selecao: {},          // qid -> índice escolhido
};

const $ = (sel) => document.querySelector(sel);

async function api(url, opcoes) {
  const r = await fetch(url, opcoes);
  if (!r.ok) throw new Error("Falha na requisição: " + url);
  return r.json();
}

function mostrarTela(id) {
  ["tela-usuario", "tela-simulados", "tela-prova", "tela-resultado"].forEach((t) => {
    $("#" + t).hidden = (t !== id);
  });
}

// -------------------------------------------------------------------------
// Usuário
// -------------------------------------------------------------------------
async function iniciar() {
  await renderListaUsuarios();
  $("#form-usuario").addEventListener("submit", async (e) => {
    e.preventDefault();
    const nome = $("#nome-usuario").value.trim();
    if (!nome) return;
    const u = await api("/api/usuarios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nome }),
    });
    entrar(u);
  });
  $("#btn-trocar").addEventListener("click", trocarUsuario);

  const salvo = localStorage.getItem("usuarioId");
  if (salvo) {
    const usuarios = await api("/api/usuarios");
    const u = usuarios.find((x) => x.id === salvo);
    if (u) entrar(u);
  }
}

async function renderListaUsuarios() {
  const usuarios = await api("/api/usuarios");
  const cont = $("#lista-usuarios");
  cont.innerHTML = "";
  if (!usuarios.length) {
    cont.innerHTML = '<span class="ajuda">Nenhum usuário ainda — crie o primeiro abaixo.</span>';
    return;
  }
  usuarios.forEach((u) => {
    const b = document.createElement("button");
    b.className = "chip-usuario";
    b.textContent = "👤 " + u.nome;
    b.addEventListener("click", () => entrar(u));
    cont.appendChild(b);
  });
}

function trocarUsuario() {
  localStorage.removeItem("usuarioId");
  estado.usuario = null;
  $("#usuario-atual").hidden = true;
  $("#nome-usuario").value = "";
  renderListaUsuarios();
  mostrarTela("tela-usuario");
}

async function entrar(usuario) {
  estado.usuario = usuario;
  localStorage.setItem("usuarioId", usuario.id);
  $("#usuario-nome").textContent = usuario.nome;
  $("#usuario-atual").hidden = false;
  await abrirListaSimulados();
}

// -------------------------------------------------------------------------
// Lista de simulados
// -------------------------------------------------------------------------
async function abrirListaSimulados() {
  const simulados = await api("/api/simulados");
  const estados = await Promise.all(
    simulados.map((s) =>
      api(`/api/estado?usuarioId=${encodeURIComponent(estado.usuario.id)}&simulado=${s.id}`)
    )
  );

  const cont = $("#lista-simulados");
  cont.innerHTML = "";
  simulados.forEach((s, i) => {
    const est = estados[i];
    const respondidas = Object.keys(est.respostas || {}).length;
    const resultado = est.resultado;

    let statusTxt, statusCls;
    if (resultado) {
      statusTxt = `✓ Concluído — ${resultado.nota}/${resultado.max} (${resultado.percentual}%)`;
      statusCls = "feito";
    } else if (respondidas > 0) {
      statusTxt = `Em andamento — ${respondidas}/${s.total} respondidas`;
      statusCls = "andamento";
    } else {
      statusTxt = "Não iniciado";
      statusCls = "novo";
    }

    const card = document.createElement("button");
    card.className = "card-simulado";
    card.innerHTML =
      `<h3>📝 ${s.titulo}</h3>` +
      `<span class="meta-card">${s.total} questões · 60 pontos</span>` +
      `<span class="status ${statusCls}">${statusTxt}</span>`;
    card.addEventListener("click", () => abrirSimulado(s.id, !!resultado));
    cont.appendChild(card);
  });

  mostrarTela("tela-simulados");
}

// -------------------------------------------------------------------------
// Abrir um simulado (prova ou resultado)
// -------------------------------------------------------------------------
async function abrirSimulado(simuladoId, jaConcluido) {
  estado.simulado = simuladoId;
  const [questoes, est] = await Promise.all([
    api(`/api/questoes?simulado=${simuladoId}`),
    api(`/api/estado?usuarioId=${encodeURIComponent(estado.usuario.id)}&simulado=${simuladoId}`),
  ]);
  estado.questoes = questoes;
  estado.selecao = {};
  Object.entries(est.respostas || {}).forEach(([qid, idx]) => {
    estado.selecao[Number(qid)] = idx;
  });

  if (jaConcluido && est.resultado) {
    renderResultado(est.resultado);
    return;
  }
  estado.pos = 0;
  renderQuestao();
  mostrarTela("tela-prova");
}

// -------------------------------------------------------------------------
// Prova (sem veredito)
// -------------------------------------------------------------------------
function questaoAtual() {
  return estado.questoes[estado.pos];
}

function renderQuestao() {
  const q = questaoAtual();
  $("#prova-titulo").textContent = tituloAtual();
  $("#q-num").textContent = `Questão ${estado.pos + 1} de ${estado.questoes.length}`;

  const area = $("#q-area");
  area.textContent = q.area || "";
  area.hidden = !q.area;
  const dif = $("#q-dif");
  dif.textContent = q.difficulty;
  dif.dataset.dif = q.difficulty;
  $("#q-texto").textContent = q.questionText;

  const areaResp = $("#area-resposta");
  areaResp.innerHTML = "";
  const grid = document.createElement("div");
  grid.className = "opcoes";
  q.options.forEach((opt, i) => {
    const b = document.createElement("button");
    b.className = "opcao";
    b.innerHTML = `<span class="letra">${String.fromCharCode(65 + i)}</span><span>${opt}</span>`;
    if (estado.selecao[q.id] === i) b.classList.add("selecionada");
    b.addEventListener("click", () => escolher(q, i, grid, b));
    grid.appendChild(b);
  });
  areaResp.appendChild(grid);

  $("#btn-anterior").disabled = estado.pos === 0;
  const ultimo = estado.pos === estado.questoes.length - 1;
  $("#btn-proxima").disabled = ultimo;

  atualizarProgresso();
}

async function escolher(q, indice, grid, botao) {
  estado.selecao[q.id] = indice;
  grid.querySelectorAll(".opcao").forEach((o) => o.classList.remove("selecionada"));
  botao.classList.add("selecionada");
  atualizarProgresso();
  // grava a resposta SEM saber se está certa
  try {
    await api("/api/responder", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        usuarioId: estado.usuario.id, simulado: estado.simulado, id: q.id, indice,
      }),
    });
  } catch (e) { /* mantém seleção local mesmo se falhar a gravação */ }
}

function tituloAtual() {
  const m = String(estado.simulado).match(/(\d+)$/);
  return m ? `Simulado ${m[1]}` : estado.simulado;
}

function atualizarProgresso() {
  const total = estado.questoes.length;
  const n = Object.keys(estado.selecao).length;
  $("#prova-respondidas").textContent = `${n} / ${total} respondidas`;
  $("#preenchimento").style.width = (total ? (n / total) * 100 : 0) + "%";
  const faltam = total - n;
  $("#aviso-pendentes").textContent = faltam > 0
    ? `Você ainda não respondeu ${faltam} questão(ões). Pode finalizar mesmo assim — elas contam como erro.`
    : "Todas respondidas. Pode finalizar.";
}

function anterior() { if (estado.pos > 0) { estado.pos--; renderQuestao(); } }
function proxima() { if (estado.pos < estado.questoes.length - 1) { estado.pos++; renderQuestao(); } }

async function finalizar() {
  const total = estado.questoes.length;
  const n = Object.keys(estado.selecao).length;
  if (n < total) {
    const ok = confirm(`Faltam ${total - n} questão(ões) sem resposta. Finalizar mesmo assim?`);
    if (!ok) return;
  }
  const resultado = await api("/api/finalizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuarioId: estado.usuario.id, simulado: estado.simulado }),
  });
  renderResultado(resultado);
}

// -------------------------------------------------------------------------
// Resultado (só a nota / desempenho por disciplina)
// -------------------------------------------------------------------------
function renderResultado(r) {
  const selo = $("#selo-aprovacao");
  selo.textContent = r.aprovado ? "Aprovado no simulado" : "Abaixo do corte";
  selo.className = "selo " + (r.aprovado ? "aprovado" : "reprovado");

  $("#resultado-titulo").textContent = tituloAtual() + " — resultado";
  $("#nota-valor").textContent = formatarNota(r.nota);
  $("#resultado-percentual").textContent = `${r.percentual}% de aproveitamento`;

  const cont = $("#desempenho");
  cont.innerHTML = "";
  (r.porArea || []).forEach((a) => {
    const pct = a.maxPontos ? (a.pontos / a.maxPontos) * 100 : 0;
    const linha = document.createElement("div");
    linha.className = "linha-area";
    linha.innerHTML =
      `<div class="cab"><span class="nome">${a.area}</span>` +
      `<span class="num">${a.acertos}/${a.total} acertos · ${formatarNota(a.pontos)}/${a.maxPontos} pts</span></div>` +
      `<div class="barra"><div style="width:${pct}%"></div></div>`;
    cont.appendChild(linha);
  });

  mostrarTela("tela-resultado");
}

function formatarNota(n) {
  return Number.isInteger(n) ? String(n) : String(n).replace(".", ",");
}

async function refazer() {
  await api("/api/refazer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ usuarioId: estado.usuario.id, simulado: estado.simulado }),
  });
  estado.selecao = {};
  estado.pos = 0;
  renderQuestao();
  mostrarTela("tela-prova");
}

// -------------------------------------------------------------------------
// Ligações
// -------------------------------------------------------------------------
$("#btn-anterior").addEventListener("click", anterior);
$("#btn-proxima").addEventListener("click", proxima);
$("#btn-finalizar").addEventListener("click", finalizar);
$("#btn-voltar-simulados").addEventListener("click", abrirListaSimulados);
$("#btn-outro-simulado").addEventListener("click", abrirListaSimulados);
$("#btn-refazer").addEventListener("click", refazer);

iniciar();
