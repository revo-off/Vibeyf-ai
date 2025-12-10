# 🚀 Démarrage de l'Application Web Vibeyf-AI

## Prérequis
- Python 3.8+
- Node.js (optionnel, pour servir le frontend)

## Installation

1. **Installer les dépendances Python**
```bash
pip install -r requirements.txt
```

2. **Configurer l'environnement**
Créer un fichier `.env` à la racine avec :
```
GEMINI_API_KEY=your_api_key_here
```
(Optionnel : l'app fonctionne sans Gemini mais avec des fonctionnalités réduites)

## Lancement de l'Application

### 1. Démarrer le Backend API

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur : http://localhost:8000
Documentation Swagger : http://localhost:8000/docs

### 2. Démarrer le Frontend

**Option A : Serveur simple Python**
```bash
cd frontend
python -m http.server 3000
```

**Option B : Live Server (VS Code)**
- Installer l'extension "Live Server"
- Clic droit sur `frontend/index.html` → "Open with Live Server"

**Option C : Serveur Node.js**
```bash
cd frontend
npx serve -s . -p 3000
```

Le frontend sera accessible sur : http://localhost:3000

## Utilisation

1. Ouvrir http://localhost:3000 dans votre navigateur
2. Cliquer sur "Commencer le questionnaire"
3. Répondre aux questions une par une
4. Obtenir vos recommandations personnalisées avec liens Spotify

## Dépannage

**Port déjà utilisé ?**
```bash
# Backend sur un autre port
uvicorn api:app --reload --port 8001

# Frontend sur un autre port
cd frontend && python -m http.server 5000
```

**Erreur de connexion API ?**
Vérifier que le backend est bien démarré sur le port 8000

**Cache des embeddings ?**
Le premier lancement peut prendre 1-2 minutes pour créer le cache
Les lancements suivants seront instantanés
