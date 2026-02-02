# 🎵 Guide de Démarrage Rapide - Vibeyf-AI

## Installation

### 1. Cloner le projet
```bash
git clone https://github.com/votre-username/Vibeyf-ai.git
cd Vibeyf-ai
```

### 2. Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### 3. Configurer les APIs (optionnel)

#### API Gemini (pour enrichir les recommandations)
- Obtenez une clé sur [Google AI Studio](https://makersuite.google.com/app/apikey)

#### API Spotify (pour les images d'albums)
- Suivez le guide: [SPOTIFY_API_SETUP.md](SPOTIFY_API_SETUP.md)

#### Créer le fichier .env
```bash
copy .env.example .env
```

Puis éditez `.env` avec vos credentials:
```env
GEMINI_API_KEY=votre_cle_ici
SPOTIFY_CLIENT_ID=votre_client_id_ici
SPOTIFY_CLIENT_SECRET=votre_client_secret_ici
```

> **Note**: Sans ces APIs, l'application fonctionnera quand même avec des fonctionnalités réduites (pas d'enrichissement GenAI, images placeholder).

## Lancer l'application

### Backend (API FastAPI)
```bash
python api.py
```
L'API sera disponible sur: `http://localhost:8000`

### Frontend (Interface Web)
Ouvrez simplement le fichier dans votre navigateur:
```
frontend/index.html
```

Ou utilisez un serveur local:
```bash
# Python
cd frontend
python -m http.server 3000

# Node.js
npx http-server frontend -p 3000
```

## Fonctionnalités

### ✅ Avec toutes les APIs configurées
- 🎯 Recommandations musicales personnalisées basées sur SBERT
- 🖼️ Images d'albums Spotify
- 🤖 **Amélioration automatique des requêtes courtes** (< 10 mots) via Gemini AI
- 🤖 Enrichissement des recommandations par Gemini AI (max 100 mots)
- 📊 Scores détaillés (sémantique, mood, préférences, audio)
- 💾 Sauvegarde des sessions utilisateur

### ⚠️ Sans les APIs
- 🎯 Recommandations musicales (fonctionne toujours)
- 📊 Scores détaillés
- 💾 Sauvegarde des sessions
- 🖼️ Images placeholder génériques au lieu des pochettes d'album
- ❌ Pas d'amélioration des requêtes courtes
- ❌ Pas d'enrichissement GenAI

## Architecture

```
Vibeyf-ai/
├── api.py                 # Backend FastAPI
├── config/
│   └── config.py          # Configuration et paramètres
├── services/
│   ├── referentiel_service.py    # Catalogue musical (30 chansons/genre)
│   ├── nlp_service.py            # SBERT embeddings
│   ├── scoring_service.py        # Algorithme de scoring
│   ├── questionnaire_service.py  # 3 Likert + 3 questions ouvertes
│   ├── gemini_service.py         # Intégration Gemini (optionnel)
│   └── spotify_service.py        # Intégration Spotify (optionnel)
├── frontend/
│   ├── index.html         # Interface utilisateur
│   ├── app.js             # Logique frontend
│   └── style.css          # Styles
├── data/
│   └── spotify_songs.csv  # Dataset Spotify (32K chansons)
└── user_responses/        # Sessions utilisateur sauvegardées
```

## Questionnaire

### Questions Likert (échelle 1-7):
1. **Énergie**: Préférez-vous une musique énergique ou calme?
2. **Humeur**: Recherchez-vous une musique joyeuse ou mélancolique?
3. **Ouverture**: Êtes-vous ouvert à découvrir de nouveaux genres?

### Questions Ouvertes:
1. **Préférences**: Décrivez le type de musique que vous aimez (inclut détection automatique des genres)
2. **Contexte**: Dans quel contexte allez-vous écouter cette musique?
3. **Artistes**: Quels sont vos artistes/groupes préférés?

## Algorithme de Scoring

Chaque recommandation est évaluée sur 4 dimensions:

- **50%** - Similarité sémantique (SBERT sur les réponses)
- **20%** - Correspondance de mood (caractéristiques audio)
- **20%** - Préférences Likert (énergie, humeur, ouverture)
- **10%** - Audio features (tempo, danceability, etc.)

**Bonus**: +80% pour le genre favori, dégressif jusqu'à +15% pour le 5ème

## Ressources

- [RESUME_PROJET.txt](RESUME_PROJET.txt) - Documentation complète du projet
- [SPOTIFY_API_SETUP.md](SPOTIFY_API_SETUP.md) - Configuration Spotify
- [START-WEB-APP.md](START-WEB-APP.md) - Déploiement en production

## Support

Pour toute question, consultez la documentation ou créez une issue sur GitHub.
