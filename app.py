"""Application web pour organiser des notes de reunion et generer un PDF via l'IA."""

import io
import json
import os
import re
from werkzeug.utils import secure_filename

try:
    import docx as _docx_mod
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except Exception:  # pragma: no cover
    _docx_mod = None

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from fpdf import FPDF

try:
    import docx as _docx
except Exception:  # pragma: no cover
    _docx = None

try:
    from pypdf import PdfReader as _PdfReader
except Exception:  # pragma: no cover
    _PdfReader = None

load_dotenv()

BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

app = Flask(__name__)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 Mo
ALLOWED_EXTENSIONS = {".txt", ".md", ".csv", ".log", ".json", ".docx", ".pdf"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".log", ".json"}

SYSTEM_PROMPT = """Tu es un assistant expert en prise de notes de reunion.
A partir des notes brutes fournies par l'utilisateur, tu dois produire un compte-rendu structure et clair en francais.

Reponds UNIQUEMENT avec un objet JSON valide (pas de markdown, pas de texte autour), avec cette structure exacte :
{
  "titre": "Titre de la reunion",
  "date": "Date si mentionnee, sinon chaîne vide",
  "participants": ["Nom 1", "Nom 2"],
  "resume": "Resume executif en 2-4 phrases.",
  "points_cles": ["Point cle 1", "Point cle 2"],
  "decisions": ["Decision 1", "Decision 2"],
  "actions": [
    {"tache": "Description de la tache", "responsable": "Nom", "echeance": "Date ou delai"}
  ],
  "prochaines_etapes": ["Etape 1", "Etape 2"],
  "notes_diverses": "Informations complementaires ou chaîne vide"
}

Si une information manque, mets une liste vide ou une chaîne vide. Ne fabrique pas de fausses informations.
Les listes doivent contenir des chaînes concises et actionnables."""


def chat(prompt: str) -> str:
    url = f"{BASE_URL}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def parse_json(text: str) -> dict:
    text = text.strip()
    # Remove markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    # Fallback: extract first {...} block
    if not text.startswith("{"):
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            text = m.group(0)
    return json.loads(text)


def build_pdf(data: dict) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, _safe(data.get("titre") or "Compte-rendu de reunion"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    date = data.get("date") or ""
    if date:
        pdf.cell(0, 6, f"Date : {date}", new_x="LMARGIN", new_y="NEXT")
    participants = data.get("participants") or []
    if participants:
        pdf.cell(0, 6, "Participants : " + ", ".join(participants), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    def section(title, body_fn):
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 11)
        body_fn()
        pdf.ln(2)

    resume = data.get("resume") or ""
    if resume:
        section("Resume executif", lambda: pdf.multi_cell(0, 6, _safe(resume)))

    points = data.get("points_cles") or []
    if points:
        section("Points cles", lambda: _list_items(pdf, points))

    decisions = data.get("decisions") or []
    if decisions:
        section("Decisions", lambda: _list_items(pdf, decisions))

    actions = data.get("actions") or []
    if actions:
        section("Actions a realiser", lambda: _actions(pdf, actions))

    etapes = data.get("prochaines_etapes") or []
    if etapes:
        section("Prochaines etapes", lambda: _list_items(pdf, etapes))

    notes = data.get("notes_diverses") or ""
    if notes:
        section("Notes diverses", lambda: pdf.multi_cell(0, 6, _safe(notes)))

    return bytes(pdf.output())


def _safe(text) -> str:
    if text is None:
        return ""
    text = str(text)
    # fpdf core fonts are latin-1; replace unsupported chars
    return text.encode("latin-1", "replace").decode("latin-1")


def _list_items(pdf, items):
    for item in items:
        pdf.cell(6, 6, "-", new_x="RIGHT", new_y="TOP")
        pdf.multi_cell(0, 6, _safe(item))
        pdf.ln(1)


def _actions(pdf, actions):
    for a in actions:
        tache = a.get("tache", "")
        resp = a.get("responsable", "")
        ech = a.get("echeance", "")
        line = f"- {tache}"
        if resp:
            line += f"  (Responsable : {resp})"
        if ech:
            line += f"  [Echeance : {ech}]"
        pdf.multi_cell(0, 6, _safe(line))
        pdf.ln(1)


def _extract_text(filename: str, raw: bytes) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in TEXT_EXTENSIONS:
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")
    if ext == ".docx":
        if _docx is None:
            raise RuntimeError("python-docx non installe.")
        doc = _docx.Document(io.BytesIO(raw))
        parts = [p.text for p in doc.paragraphs]
        # tables
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text for c in row.cells))
        return "\n".join(parts)
    if ext == ".pdf":
        if _PdfReader is None:
            raise RuntimeError("pypdf non installe.")
        reader = _PdfReader(io.BytesIO(raw))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n\n".join(pages)
    raise ValueError(f"Format non supporte : {ext}")


@app.route("/api/import", methods=["POST"])
def import_file():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni."}), 400
    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "Fichier invalide."}), 400
    filename = secure_filename(f.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Format non supporte ({ext}). Formats acceptes : {', '.join(sorted(ALLOWED_EXTENSIONS))}"}), 400
    raw = f.read()
    if len(raw) == 0:
        return jsonify({"error": "Fichier vide."}), 400
    if len(raw) > MAX_UPLOAD_BYTES:
        return jsonify({"error": f"Fichier trop volumineux (max {MAX_UPLOAD_BYTES // (1024*1024)} Mo)."}), 413
    try:
        text = _extract_text(filename, raw)
    except Exception as e:
        return jsonify({"error": f"Echec de l'extraction : {e}"}), 500
    if not text.strip():
        return jsonify({"error": "Aucun texte extractible dans ce fichier."}), 400
    return jsonify({"text": text, "filename": filename})


def build_docx(data: dict) -> bytes:
    if _docx_mod is None:
        raise RuntimeError("python-docx non installe.")
    doc = _docx_mod.Document()

    # Title
    title = doc.add_heading(_safe(data.get("titre") or "Compte-rendu de reunion"), level=0)
    for run in title.runs:
        run.font.color.rgb = RGBColor(0x63, 0x66, 0xF1)

    date = data.get("date") or ""
    if date:
        p = doc.add_paragraph()
        r = p.add_run(f"Date : {date}")
        r.bold = True
    participants = data.get("participants") or []
    if participants:
        p = doc.add_paragraph()
        r = p.add_run("Participants : " + ", ".join(participants))
        r.bold = True
    doc.add_paragraph()

    def heading(text):
        h = doc.add_heading(text, level=1)
        for run in h.runs:
            run.font.color.rgb = RGBColor(0x22, 0xD3, 0xEE)

    def bullets(items):
        for item in items:
            doc.add_paragraph(_safe(item), style="List Bullet")

    resume = data.get("resume") or ""
    if resume:
        heading("Resume executif")
        doc.add_paragraph(_safe(resume))

    points = data.get("points_cles") or []
    if points:
        heading("Points cles")
        bullets(points)

    decisions = data.get("decisions") or []
    if decisions:
        heading("Decisions")
        bullets(decisions)

    actions = data.get("actions") or []
    if actions:
        heading("Actions a realiser")
        table = doc.add_table(rows=1, cols=3)
        table.style = "Light Grid Accent 1"
        hdr = table.rows[0].cells
        hdr[0].text = "Tache"
        hdr[1].text = "Responsable"
        hdr[2].text = "Echeance"
        for a in actions:
            cells = table.add_row().cells
            cells[0].text = _safe(a.get("tache", ""))
            cells[1].text = _safe(a.get("responsable", ""))
            cells[2].text = _safe(a.get("echeance", ""))

    etapes = data.get("prochaines_etapes") or []
    if etapes:
        heading("Prochaines etapes")
        bullets(etapes)

    notes = data.get("notes_diverses") or ""
    if notes:
        heading("Notes diverses")
        doc.add_paragraph(_safe(notes))

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


@app.route("/api/docx", methods=["POST"])
def docx_route():
    payload = request.get_json(silent=True) or {}
    data = payload.get("data")
    if not isinstance(data, dict):
        return jsonify({"error": "Donnees manquantes."}), 400
    try:
        docx_bytes = build_docx(data)
    except Exception as e:
        return jsonify({"error": f"Echec de la generation DOCX : {e}"}), 500
    buf = io.BytesIO(docx_bytes)
    buf.seek(0)
    filename = _safe_filename(data.get("titre") or "compte_rendu")
    return send_file(buf, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     as_attachment=True, download_name=filename + ".docx")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/organize", methods=["POST"])
def organize():
    payload = request.get_json(silent=True) or {}
    notes = (payload.get("notes") or "").strip()
    if not notes:
        return jsonify({"error": "Les notes sont vides."}), 400
    if not API_KEY or API_KEY == "your_deepseek_api_key_here":
        return jsonify({"error": "DEEPSEEK_API_KEY manquante. Configurez le fichier .env."}), 500
    try:
        reply = chat(notes)
        data = parse_json(reply)
    except Exception as e:
        return jsonify({"error": f"Echec de l'analyse IA : {e}", "raw": reply if "reply" in locals() else None}), 500
    return jsonify({"data": data, "raw": reply})


@app.route("/api/pdf", methods=["POST"])
def pdf_route():
    payload = request.get_json(silent=True) or {}
    data = payload.get("data")
    if not isinstance(data, dict):
        return jsonify({"error": "Donnees manquantes."}), 400
    try:
        pdf_bytes = build_pdf(data)
    except Exception as e:
        return jsonify({"error": f"Echec de la generation PDF : {e}"}), 500
    buf = io.BytesIO(pdf_bytes)
    buf.seek(0)
    filename = _safe_filename(data.get("titre") or "compte_rendu")
    return send_file(buf, mimetype="application/pdf", as_attachment=True, download_name=filename + ".pdf")


def _safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\- ]+", "", name, flags=re.UNICODE)
    name = name.strip().replace(" ", "_")
    return name or "compte_rendu"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
