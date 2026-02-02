"""
API Backend pour Vibeyf-AI
FastAPI REST API pour le système de recommandation musicale
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from config.config import RESPONSES_DIR
from services.referentiel_service import ReferentielMusical
from services.questionnaire_service import QuestionnaireService
from services.nlp_service import MoteurNLP
from services.scoring_service import SystemeScoring
from services.gemini_service import GeminiService
from services.spotify_service import SpotifyService

app = FastAPI(title="Vibeyf-AI API", version="1.0.0")

# Configuration CORS pour React
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "*"
    ],
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
        
        # Initialiser le service Spotify (optionnel, avec credentials depuis config)
        try:
            from config.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
            self.spotify = SpotifyService(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
        except (ImportError, AttributeError):
            # Si pas de credentials, utiliser le mode sans auth (placeholder images)
            self.spotify = SpotifyService()
    
    def _save_user_session(self, user_id: str, reponses_utilisateur: dict, result: dict):
        """Sauvegarde la session utilisateur avec réponses et recommandations
        
        Args:
            user_id: Identifiant unique de la session
            reponses_utilisateur: Réponses brutes de l'utilisateur
            result: Résultat complet avec recommandations
        """
        try:
            session_data = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'reponses_utilisateur': reponses_utilisateur,
                'recommandations': result['recommandations'],
                'statistiques': result['statistiques'],
                'genres_preferes': result.get('genres_preferes', []),
                'niveau_ouverture': result.get('niveau_ouverture', 3),
                'rapport_genai': result.get('rapport_genai')
            }
            
            # Sauvegarder dans un fichier JSON
            filename = RESPONSES_DIR / f"session_{user_id}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la session: {e}")
    
    def process_recommendation(self, reponses_utilisateur: dict) -> dict:
        """Traite une demande de recommandation"""
        user_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarder la requête originale (depuis la structure imbriquée)
        qo1_originale = reponses_utilisateur.get('ouvertes', {}).get('qo1_preferences', '') or reponses_utilisateur.get('qo1_preferences', '')
        qo1_enrichie = qo1_originale
        
        print(f"\n[API] Requête originale: '{qo1_originale}' ({len(qo1_originale.split()) if qo1_originale else 0} mots)")
        print(f"[API] use_gemini={self.use_gemini}, gemini={self.gemini is not None}, model={self.gemini.model is not None if self.gemini else False}")
        
        # Améliorer la première question si trop courte (< 10 mots)
        if self.use_gemini and self.gemini and self.gemini.model:
            if qo1_originale:
                try:
                    print(f"[API] Tentative d'amélioration de la requête...")
                    qo1_enrichie = self.gemini.ameliorer_requete_utilisateur(
                        qo1_originale, seuil_mots=10
                    )
                    if qo1_enrichie != qo1_originale:
                        print(f"[API] ✅ Requête enrichie: '{qo1_enrichie[:100]}...'")
                        # Mettre à jour dans la structure imbriquée
                        if 'ouvertes' in reponses_utilisateur:
                            reponses_utilisateur['ouvertes']['qo1_preferences'] = qo1_enrichie
                        else:
                            reponses_utilisateur['qo1_preferences'] = qo1_enrichie
                    else:
                        print(f"[API] ⏸️ Requête non modifiée (>= 10 mots)")
                except Exception as e:
                    print(f"[API] ❌ Erreur amélioration requête: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"[API] ⚠️ Requête vide ou non trouvée")
        else:
            print(f"[API] ⚠️ Gemini non disponible - amélioration désactivée")
        
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
                # Utiliser la version enrichie pour le rapport si disponible
                texte_pour_rapport = qo1_enrichie if qo1_enrichie != qo1_originale else texte_utilisateur
                rapport_genai = self.gemini.generer_rapport_complet(
                    recommandations,
                    texte_pour_rapport,  # Utiliser la version enrichie
                    texte_enrichi
                )
            except:
                pass
        
        result = self._format_response(
            recommandations, 
            rapport_genai, 
            user_id,
            genres_preferes,
            niveau_ouverture,
            qo1_originale,
            qo1_enrichie
        )
        
        # Sauvegarder la session
        self._save_user_session(user_id, reponses_utilisateur, result)
        
        return result
    
    def _format_response(self, recommandations, rapport_genai, user_id, genres_preferes, niveau_ouverture, qo1_originale='', qo1_enrichie=''):
        """Formate la réponse pour l'API"""
        return {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'genres_preferes': genres_preferes,
            'niveau_ouverture': niveau_ouverture,
            'requete_originale': qo1_originale,
            'requete_enrichie': qo1_enrichie if qo1_enrichie != qo1_originale else None,
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
                    'spotify_search_url': self._generate_spotify_url(r) if r['type'] == 'chanson' else None,
                    # Ajout de l'URL de l'image de l'album
                    'album_cover_url': self._generate_album_cover_url(r) if r['type'] == 'chanson' else None
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
    
    def _generate_album_cover_url(self, recommendation):
        """Génère une URL d'image d'album via l'API Spotify
        
        Utilise le track_id pour récupérer l'image ou fait une recherche
        par nom + artiste si le track_id n'est pas disponible
        """
        if recommendation['type'] == 'chanson':
            track_id = recommendation.get('id', '')
            
            # Essayer d'abord avec le track_id
            if track_id and track_id.startswith('spotify:track:'):
                spotify_id = track_id.replace('spotify:track:', '')
                cover_url = self.spotify.get_album_cover_url(spotify_id)
                if cover_url:
                    return cover_url
            
            # Sinon, chercher par nom + artiste
            nom = recommendation['data'].get('nom', '')
            artiste = recommendation['data'].get('artiste', '')
            if nom and artiste:
                return self.spotify.search_track_and_get_cover(nom, artiste)
        
        # Fallback vers placeholder
        return self.spotify._get_placeholder_image()


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
