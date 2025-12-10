"""
Configuration du système de recommandation musicale
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Chemins
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RESPONSES_DIR = BASE_DIR / "user_responses"
REFERENTIEL_DIR = BASE_DIR / "referentiel"

# Créer les dossiers nécessaires
RESPONSES_DIR.mkdir(exist_ok=True)
REFERENTIEL_DIR.mkdir(exist_ok=True)

# API Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Modèle SBERT
SBERT_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # Modèle multilingue pour français/anglais

# Paramètres de recommandation
TOP_N_RECOMMENDATIONS = 3
MIN_WORDS_FOR_ENRICHMENT = 5  # Seuil pour enrichissement GenAI

# Paramètres de scoring
WEIGHTS = {
    "semantic_similarity": 0.5,    # Similarité sémantique (SBERT)
    "mood_match": 0.2,             # Correspondance de mood
    "preference_likert": 0.2,      # Préférences utilisateur (Likert)
    "audio_features": 0.1          # Caractéristiques audio (BPM, énergie, etc.)
}

# Mapping des moods vers les caractéristiques audio
# Toutes les valeurs sont sur échelle 0.0-1.0 sauf tempo (BPM) et loudness (dB)
MOOD_MAPPINGS = {
    "joyeux": {"valence": (0.6, 1.0), "energy": (0.6, 1.0), "danceability": (0.6, 1.0)},
    "triste": {"valence": (0.0, 0.4), "energy": (0.0, 0.5), "acousticness": (0.4, 1.0)},
    "énergique": {"energy": (0.7, 1.0), "tempo": (120, 200), "danceability": (0.6, 1.0)},
    "calme": {"energy": (0.0, 0.4), "tempo": (60, 100), "acousticness": (0.5, 1.0)},
    "mélancolique": {"valence": (0.0, 0.45), "energy": (0.2, 0.6), "acousticness": (0.4, 1.0)},
    "motivant": {"energy": (0.7, 1.0), "valence": (0.6, 1.0), "tempo": (110, 180)},
    "romantique": {"valence": (0.4, 0.8), "energy": (0.2, 0.6), "acousticness": (0.3, 0.9)},
    "festif": {"valence": (0.7, 1.0), "energy": (0.7, 1.0), "danceability": (0.7, 1.0)},
    "relaxant": {"energy": (0.0, 0.35), "valence": (0.4, 0.8), "acousticness": (0.6, 1.0)},
    "intense": {"energy": (0.8, 1.0), "loudness": (-10, 0), "tempo": (130, 200)},
}

# Ambiances prédéfinies
AMBIANCES = {
    "soirée_entre_amis": "Musique festive et dansante pour passer une bonne soirée entre amis",
    "concentration": "Musique calme et instrumentale pour se concentrer sur son travail",
    "sport": "Musique énergique et motivante pour s'entraîner",
    "détente": "Musique relaxante pour se détendre et décompresser",
    "romantique": "Musique douce et romantique pour un moment intime",
    "voyage": "Musique inspirante et variée pour voyager",
    "mélancolie": "Musique mélancolique et émotionnelle pour moments introspectifs",
    "réveil": "Musique énergisante pour bien commencer la journée",
    "nostalgie": "Musique rétro et nostalgique rappelant de bons souvenirs",
    "danse": "Musique rythmée pour danser et bouger"
}
