# Organisateur de notes de reunion

Application web qui structure vos notes de reunion avec l'aide de l'IA (API DeepSeek, compatible OpenAI)
et genere un compte-rendu au format PDF.

## Fonctionnalites

- Collage de notes brutes (texte libre, puces, transcription...)
- Structuration automatique par l'IA : titre, date, participants, resume executif, points cles,
  decisions, actions (responsable + echeance), prochaines etapes, notes diverses
- Edition manuelle du resultat avant export
- Generation et telechargement d'un PDF formate

## Setup

```bash
cp .env.example .env
# editez .env avec votre cle API DeepSeek
pip install -r requirements.txt
```

## Lancement

```bash
python app.py
```

Puis ouvrez http://127.0.0.1:5000 dans votre navigateur.

## Configuration (.env)

- `DEEPSEEK_BASE_URL` : URL de base de l'API (defaut https://api.deepseek.com)
- `DEEPSEEK_API_KEY` : votre cle API DeepSeek
- `DEEPSEEK_MODEL` : modele a utiliser (defaut deepseek-chat)

## Serveur MCP (OpenCode)

Un serveur MCP `document-generator` est configure dans `opencode.json` pour generer des
documents Word/PDF depuis OpenCode (via `npx document-generator-mcp@latest`).
Necessite Node.js 18+.

## Fichiers

- `app.py` : serveur Flask + logique IA + generation PDF
- `templates/index.html` : interface web
- `static/style.css`, `static/app.js` : styles et interactions
- `main.py` : exemple minimal d'appel a l'API
- `opencode.json` : configuration MCP (document-generator)