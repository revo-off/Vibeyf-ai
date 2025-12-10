"""
API Backend pour Vibeyf-AI
FastAPI REST API pour le système de recommandation musicale
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime

from services.referentiel_service import ReferentielMusical
from services.questionnaire_service import QuestionnaireService
from services.nlp_service import MoteurNLP
from services.scoring_service import SystemeScoring
from services.gemini_service import GeminiService

app = FastAPI(title="Vibeyf-AI API", version="1.0.0")

# Configuration CORS pour React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite et CRA
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation des services (au démarrage)
vibey_system = None

@app.on_event("startup")
async def startup_event():
    """Initialise le système au démarrage"""
    global vibey_system
    vibey_system = VibeyfAIBackend()


class VibeyfAIBackend:
    """Backend du système de recommandation"""
    
    def __init__(self, use_gemini: bool = True):
        self.referentiel = ReferentielMusical()
        self.moteur_nlp = MoteurNLP()
        
        if not self.moteur_nlp.charger_cache():
            textes_ref = self.referentiel.get_all_semantic_texts()
            self.moteur_nlp.preparer_referentiel(textes_ref)
        
        self.scoring = SystemeScoring()
        self.questionnaire = QuestionnaireService()
        self.use_gemini = use_gemini
        self.gemini = GeminiService() if use_gemini else None
    
    def process_recommendation(self, reponses_utilisateur: dict) -> dict:
        """Traite une demande de recommandation"""
        user_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        reponses_structurees = self.questionnaire.collecter_reponses_dict(
            reponses_utilisateur
        )
        
        texte_utilisateur = self.questionnaire.extraire_texte_semantique(
            reponses_structurees
        )
        
        texte_enrichi = texte_utilisateur
        if self.use_gemini and self.gemini and self.gemini.model:
            try:
                texte_enrichi = self.gemini.enrichir_texte_court(texte_utilisateur)
            except:
                pass
        
        elements_avec_similarite = self.moteur_nlp.obtenir_scores_detailles(
            texte_enrichi
        )
        
        preferences_audio = self.questionnaire.extraire_preferences_audio(
            reponses_structurees
        )
        
        genres_preferes = self.questionnaire.extraire_genres_preferes(
            reponses_structurees
        )
        
        niveau_ouverture = self.questionnaire.extraire_niveau_ouverture(
            reponses_structurees
        )
        
        elements_scores = self.scoring.calculer_scores_elements(
            elements_avec_similarite,
            preferences_audio,
            texte_enrichi,
            moods_detectes=None,
            genres_preferes=genres_preferes,
            niveau_ouverture=niveau_ouverture
        )
        
        recommandations = self.scoring.generer_recommandations(
            elements_scores,
            top_n=10  # Plus de recommandations pour l'interface web
        )
        
        rapport_genai = None
        if self.use_gemini and self.gemini and self.gemini.model:
            try:
                rapport_genai = self.gemini.generer_rapport_complet(
                    recommandations,
                    texte_utilisateur,
                    texte_enrichi
                )
            except:
                pass
        
        return self._format_response(
            recommandations, 
            rapport_genai, 
            user_id,
            genres_preferes,
            niveau_ouverture
        )
    
    def _format_response(self, recommandations, rapport_genai, user_id, genres_preferes, niveau_ouverture):
        """Formate la réponse pour l'API"""
        return {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'genres_preferes': genres_preferes,
            'niveau_ouverture': niveau_ouverture,
            'recommandations': [
                {
                    'rang': i + 1,
                    'type': r['type'],
                    'id': r['id'],
                    'nom': r['data'].get('nom', r['id']),
                    'artiste': r['data'].get('artiste', '') if r['type'] == 'chanson' else None,
                    'genre': r.get('genre', r['data'].get('genre', '')) if r['type'] == 'chanson' else None,
                    'description': r['data'].get('description', ''),
                    'score_global': round(r['scores']['global'], 3),
                    'details_scores': {
                        'similarite_semantique': round(r['scores']['similarite_semantique'], 3),
                        'mood_match': round(r['scores']['mood_match'], 3),
                        'preferences_likert': round(r['scores']['preferences_likert'], 3),
                        'audio_features': round(r['scores']['audio_features'], 3),
                        'genre_boost': round(r['scores']['genre_boost'], 3)
                    },
                    'caracteristiques': r['data'].get('caracteristiques_moyennes', {}),
                    # Générer un lien Spotify de recherche
                    'spotify_search_url': self._generate_spotify_url(r) if r['type'] == 'chanson' else None
                }
                for i, r in enumerate(recommandations['top_recommandations'])
            ],
            'statistiques': recommandations['statistiques'],
            'rapport_genai': rapport_genai
        }
    
    def _generate_spotify_url(self, recommendation):
        """Génère une URL de recherche Spotify"""
        if recommendation['type'] == 'chanson':
            nom = recommendation['data'].get('nom', '')
            artiste = recommendation['data'].get('artiste', '')
            query = f"{nom} {artiste}".replace(' ', '+')
            return f"https://open.spotify.com/search/{query}"
        return None


# Modèles Pydantic pour la validation des données
class QuestionLikert(BaseModel):
    valeur: int  # 1-5

class ReponseOuverte(BaseModel):
    valeur: Any  # str ou List[str]

class ReponsesUtilisateur(BaseModel):
    likert: Dict[str, int]  # {"q1_energie": 4, "q2_calme": 3, ...}
    ouvertes: Dict[str, Any]  # {"qo1_mood": "calme", "qo4_genres": ["rock", "pop"], ...}


# Endpoints API
@app.get("/")
async def root():
    """Point d'entrée racine"""
    return {
        "message": "Vibeyf-AI API",
        "version": "1.0.0",
        "endpoints": {
            "questionnaire": "/questionnaire",
            "recommend": "/recommend",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état du service"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_enabled": vibey_system.use_gemini if vibey_system else False
    }

@app.get("/questionnaire")
async def get_questionnaire():
    """Récupère la structure complète du questionnaire"""
    if not vibey_system:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "likert": vibey_system.questionnaire.questions_likert,
        "ouvertes": vibey_system.questionnaire.questions_ouvertes
    }

@app.post("/recommend")
async def create_recommendation(reponses: ReponsesUtilisateur):
    """Génère des recommandations basées sur les réponses utilisateur"""
    if not vibey_system:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Convertir le format Pydantic vers le format attendu
        reponses_dict = {
            "likert": reponses.likert,
            "ouvertes": reponses.ouvertes
        }
        
        result = vibey_system.process_recommendation(reponses_dict)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing recommendation: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
