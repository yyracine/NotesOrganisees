const $ = (id) => document.getElementById(id);

let currentData = null;

// ---------- Theme toggle ----------
const THEME_KEY = "theme";
const themeToggle = $("themeToggle");
const themeColorMeta = $("themeColor");

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  themeColorMeta.setAttribute("content", theme === "light" ? "#f5f7fb" : "#0b1020");
  const icon = themeToggle.querySelector(".theme-icon");
  if (icon) icon.textContent = theme === "light" ? "☀️" : "🌙";
  themeToggle.setAttribute("aria-label", theme === "light" ? "Basculer en theme sombre" : "Basculer en theme clair");
}

function initTheme() {
  let theme = localStorage.getItem(THEME_KEY);
  if (!theme) {
    theme = window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  }
  applyTheme(theme);
}
initTheme();

themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "light" ? "dark" : "light";
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
});

// ---------- Status helpers ----------
function setStatus(msg, kind = "") {
  const el = $("status");
  el.textContent = msg;
  el.className = "status " + kind;
}
function setImportStatus(msg, kind = "") {
  const el = $("importStatus");
  el.textContent = msg;
  el.className = "status " + kind;
}

// ---------- Button loading state ----------
function setLoading(btn, loading) {
  btn.disabled = loading;
  btn.classList.toggle("loading", loading);
}

// ---------- Field builders ----------
let fieldCounter = 0;
function makeField(label, key, value, multiline = false) {
  const wrap = document.createElement("div");
  wrap.className = "field";
  const id = "field_" + (++fieldCounter);
  const lab = document.createElement("label");
  lab.textContent = label;
  lab.setAttribute("for", id);
  wrap.appendChild(lab);
  const el = document.createElement(multiline ? "textarea" : "input");
  if (!multiline) el.type = "text";
  el.id = id;
  el.name = key;
  el.dataset.key = key;
  el.autocomplete = "off";
  el.value = value || "";
  wrap.appendChild(el);
  return wrap;
}

function makeListEditor(label, key, items) {
  const wrap = document.createElement("div");
  wrap.className = "field";
  const container = document.createElement("div");
  container.className = "list-editor";
  container.dataset.key = key;
  (items || []).forEach((it) => addListRow(container, it, label));
  const addBtn = document.createElement("button");
  addBtn.className = "add-btn";
  addBtn.type = "button";
  addBtn.textContent = "+ Ajouter";
  addBtn.addEventListener("click", () => addListRow(container, "", label));
  container.appendChild(addBtn);
  const lab = document.createElement("label");
  lab.textContent = label;
  wrap.appendChild(lab);
  wrap.appendChild(container);
  return wrap;
}

function addListRow(container, value, ariaLabel) {
  const row = document.createElement("div");
  row.className = "list-row";
  const input = document.createElement("input");
  input.type = "text";
  input.value = value || "";
  input.autocomplete = "off";
  input.setAttribute("aria-label", ariaLabel || "Element");
  row.appendChild(input);
  const del = document.createElement("button");
  del.type = "button";
  del.textContent = "×";
  del.setAttribute("aria-label", "Supprimer");
  del.addEventListener("click", () => row.remove());
  row.appendChild(del);
  const addBtn = container.querySelector(".add-btn");
  container.insertBefore(row, addBtn);
}

function makeActionsEditor(actions) {
  const wrap = document.createElement("div");
  wrap.className = "field";
  const lab = document.createElement("label");
  lab.textContent = "Actions a realiser";
  wrap.appendChild(lab);
  const container = document.createElement("div");
  container.id = "actionsContainer";
  (actions || []).forEach((a) => addActionCard(container, a));
  const addBtn = document.createElement("button");
  addBtn.className = "add-btn";
  addBtn.type = "button";
  addBtn.textContent = "+ Ajouter une action";
  addBtn.addEventListener("click", () => addActionCard(container, { tache: "", responsable: "", echeance: "" }));
  container.appendChild(addBtn);
  wrap.appendChild(container);
  return wrap;
}

function addActionCard(container, a) {
  const card = document.createElement("div");
  card.className = "action-card";
  const r1 = document.createElement("div");
  r1.className = "row";
  const tache = document.createElement("input");
  tache.placeholder = "Tache";
  tache.value = a.tache || "";
  tache.dataset.field = "tache";
  tache.autocomplete = "off";
  tache.setAttribute("aria-label", "Tache");
  r1.appendChild(tache);
  const del = document.createElement("button");
  del.type = "button";
  del.textContent = "×";
  del.setAttribute("aria-label", "Supprimer l'action");
  del.addEventListener("click", () => card.remove());
  r1.appendChild(del);
  card.appendChild(r1);
  const r2 = document.createElement("div");
  r2.className = "row";
  const resp = document.createElement("input");
  resp.placeholder = "Responsable";
  resp.value = a.responsable || "";
  resp.dataset.field = "responsable";
  resp.autocomplete = "off";
  resp.setAttribute("aria-label", "Responsable");
  r2.appendChild(resp);
  const ech = document.createElement("input");
  ech.placeholder = "Echeance";
  ech.value = a.echeance || "";
  ech.dataset.field = "echeance";
  ech.autocomplete = "off";
  ech.setAttribute("aria-label", "Echeance");
  r2.appendChild(ech);
  card.appendChild(r2);
  const addBtn = container.querySelector(".add-btn");
  container.insertBefore(card, addBtn);
}

function renderResult(data) {
  const root = $("result");
  root.innerHTML = "";
  currentData = JSON.parse(JSON.stringify(data));

  root.appendChild(makeField("Titre", "titre", data.titre));
  root.appendChild(makeField("Date", "date", data.date));
  root.appendChild(makeField("Participants (separes par des virgules)", "participants", (data.participants || []).join(", ")));
  root.appendChild(makeField("Resume executif", "resume", data.resume, true));
  root.appendChild(makeListEditor("Points cles", "points_cles", data.points_cles));
  root.appendChild(makeListEditor("Decisions", "decisions", data.decisions));
  root.appendChild(makeActionsEditor(data.actions));
  root.appendChild(makeListEditor("Prochaines etapes", "prochaines_etapes", data.prochaines_etapes));
  root.appendChild(makeField("Notes diverses", "notes_diverses", data.notes_diverses, true));

  $("resultCard").hidden = false;
  $("resultCard").scrollIntoView({ behavior: "smooth", block: "start" });
}

function collectData() {
  const root = $("result");
  const data = {};
  root.querySelectorAll(".field > input, .field > textarea").forEach((el) => {
    if (el.dataset.key) {
      const key = el.dataset.key;
      if (key === "participants") {
        data[key] = el.value.split(",").map((s) => s.trim()).filter(Boolean);
      } else {
        data[key] = el.value;
      }
    }
  });
  root.querySelectorAll(".list-editor").forEach((container) => {
    const key = container.dataset.key;
    const vals = [];
    container.querySelectorAll(".list-row input").forEach((inp) => {
      if (inp.value.trim()) vals.push(inp.value.trim());
    });
    data[key] = vals;
  });
  const actions = [];
  root.querySelectorAll("#actionsContainer .action-card").forEach((card) => {
    const a = {};
    card.querySelectorAll("input").forEach((inp) => {
      a[inp.dataset.field] = inp.value;
    });
    if (a.tache && a.tache.trim()) actions.push(a);
  });
  data.actions = actions;
  return data;
}

// ---------- Organize ----------
$("btnOrganize").addEventListener("click", async () => {
  const notes = $("notes").value.trim();
  if (!notes) { setStatus("Veuillez saisir des notes.", "error"); return; }
  const btn = $("btnOrganize");
  setStatus("Analyse en cours…", "");
  setLoading(btn, true);
  try {
    const resp = await fetch("/api/organize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes }),
    });
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.error || "Erreur");
    renderResult(json.data);
    setStatus("Organisation terminee.", "ok");
  } catch (e) {
    setStatus("Erreur : " + e.message, "error");
  } finally {
    setLoading(btn, false);
  }
});

// ---------- PDF ----------
$("btnPdf").addEventListener("click", async () => {
  const data = collectData();
  const btn = $("btnPdf");
  setStatus("Generation du PDF…", "");
  setLoading(btn, true);
  try {
    const resp = await fetch("/api/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data }),
    });
    if (!resp.ok) {
      const j = await resp.json();
      throw new Error(j.error || "Erreur");
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = (data.titre || "compte_rendu").replace(/\s+/g, "_") + ".pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    setStatus("PDF telecharge.", "ok");
  } catch (e) {
    setStatus("Erreur : " + e.message, "error");
  } finally {
    setLoading(btn, false);
  }
});

// ---------- DOCX ----------
$("btnDocx").addEventListener("click", async () => {
  const data = collectData();
  const btn = $("btnDocx");
  setStatus("Generation du DOCX…", "");
  setLoading(btn, true);
  try {
    const resp = await fetch("/api/docx", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data }),
    });
    if (!resp.ok) {
      const j = await resp.json();
      throw new Error(j.error || "Erreur");
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = (data.titre || "compte_rendu").replace(/\s+/g, "_") + ".docx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    setStatus("DOCX telecharge.", "ok");
  } catch (e) {
    setStatus("Erreur : " + e.message, "error");
  } finally {
    setLoading(btn, false);
  }
});

// ---------- Reset ----------
$("btnReset").addEventListener("click", () => {
  if (!confirm("Reinitialiser le compte-rendu ? Les modifications non exportees seront perdues.")) return;
  $("result").innerHTML = "";
  $("resultCard").hidden = true;
  currentData = null;
  setStatus("");
});

// ---------- Import de fichiers ----------
const dropzone = $("dropzone");
const fileInput = $("fileInput");

async function uploadFile(file) {
  setImportStatus("Import en cours…", "");
  const fd = new FormData();
  fd.append("file", file);
  try {
    const resp = await fetch("/api/import", { method: "POST", body: fd });
    const json = await resp.json();
    if (!resp.ok) throw new Error(json.error || "Erreur");
    $("notes").value = json.text;
    setImportStatus("Fichier importe : " + json.filename, "ok");
  } catch (e) {
    setImportStatus("Erreur : " + e.message, "error");
  }
}

fileInput.addEventListener("change", () => {
  if (fileInput.files && fileInput.files[0]) {
    uploadFile(fileInput.files[0]);
    fileInput.value = "";
  }
});

// keyboard support for dropzone
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});
dropzone.addEventListener("click", (e) => {
  if (e.target === dropzone || e.target.classList.contains("dropzone-icon") || e.target.classList.contains("dropzone-title") || e.target.classList.contains("dropzone-sub") || e.target.classList.contains("muted")) {
    fileInput.click();
  }
});

["dragenter", "dragover"].forEach((ev) => {
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.add("dragover");
  });
});
["dragleave", "drop"].forEach((ev) => {
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    e.stopPropagation();
    dropzone.classList.remove("dragover");
  });
});
dropzone.addEventListener("drop", (e) => {
  const files = e.dataTransfer && e.dataTransfer.files;
  if (files && files[0]) uploadFile(files[0]);
});