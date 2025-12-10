# Guide de démarrage - Vibeyf-AI Application Web

## 📋 Structure du projet

```
Vibeyf-ai/
├── api.py                      # Backend FastAPI
├── requirements-api.txt        # Dépendances backend
├── frontend/                   # Frontend HTML/CSS/JS
│   ├── index.html
│   ├── style.css
│   └── app.js
├── services/                   # Services backend
├── config/
└── data/
```

## 🚀 Installation et lancement

### 1. Installation des dépendances backend

```bash
pip install -r requirements-api.txt
```

### 2. Configuration

Créez un fichier `.env` à la racine avec votre clé Gemini (optionnel) :

```
GEMINI_API_KEY=votre_clé_api_ici
```

### 3. Lancement du backend API

```bash
python api.py
```

Le serveur démarre sur `http://localhost:3000`

### 4. Lancement du frontend

**Option 1 - Serveur HTTP simple (Python):**
```bash
cd frontend
python -m http.server 3000
```

**Option 2 - Serveur HTTP simple (Node.js):**
```bash
cd frontend
npx serve -p 3000
```

**Option 3 - Ouvrir directement:**
Double-cliquez sur `frontend/index.html` (peut avoir des problèmes CORS)

Le frontend sera accessible sur `http://localhost:3000`

## 📡 Endpoints API

### `GET /questionnaire`
Récupère la structure complète du questionnaire

### `POST /recommend`
Génère les recommandations musicales

**Body:**
```json
{
  "likert": {
    "q1_energie": 4,
    "q2_calme": 3,
    ...
  },
  "ouvertes": {
    "qo1_mood": "calme et relaxant",
    "qo4_genres": ["rock", "pop"],
    ...
  }
}
```

### `GET /health`
Vérification de l'état du service

## 🎨 Interface utilisateur

L'interface est inspirée de ChatGPT avec :
- ✅ Chat conversationnel progressif
- ✅ Questions affichées une par une
- ✅ Échelle de Likert interactive (1-5)
- ✅ Champs texte pour questions ouvertes
- ✅ Indicateur de progression
- ✅ Affichage des recommandations avec cartes
- ✅ Liens Spotify pour écouter directement
- ✅ Design moderne type Spotify
- ✅ Responsive (mobile-friendly)

## 🔧 Personnalisation

### Modifier l'URL de l'API

Dans `frontend/app.js`, ligne 2 :
```javascript
const API_URL = 'http://localhost:8000';
```

### Modifier le nombre de recommandations

Dans `api.py`, ligne 84 :
```python
top_n=10  # Changez ce nombre
```

### Changer les couleurs

Dans `frontend/style.css`, lignes 9-18 (variables CSS) :
```css
:root {
    --primary-color: #1DB954;  /* Vert Spotify */
    --accent-purple: #8E44AD;
    /* ... */
}
```

## 🐛 Dépannage

**Problème CORS :**
- Assurez-vous que le backend tourne sur `localhost:8000`
- Vérifiez que le frontend accède via un serveur HTTP (pas file://)

**Backend ne démarre pas :**
- Vérifiez que toutes les dépendances sont installées
- Vérifiez que le cache des embeddings existe dans `referentiel/`
- Si premier lancement, attendez que le système construise le référentiel

**Recommandations vides :**
- Vérifiez que `spotify_songs.csv` est dans le dossier `data/`
- Vérifiez les logs du backend pour les erreurs
