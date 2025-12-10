"""
Service de questionnaire hybride (EF1)
Collecte les préférences utilisateur via questions Likert et questions ouvertes
"""
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
from config.config import RESPONSES_DIR


class QuestionnaireService:
    """Gère la collecte des réponses utilisateur"""
    
    def __init__(self):
        self.questions_likert = self._init_questions_likert()
        self.questions_ouvertes = self._init_questions_ouvertes()
    
    def _init_questions_likert(self) -> List[Dict[str, Any]]:
        """Initialise les questions sur échelle de Likert (1-5)"""
        return [
            {
                "id": "q1_energie",
                "question": "À quel point aimez-vous la musique énergique et dynamique ?",
                "dimension": "énergie",
                "echelle": "1 (Pas du tout) à 5 (Énormément)"
            },
            {
                "id": "q2_calme",
                "question": "À quel point appréciez-vous la musique calme et relaxante ?",
                "dimension": "calme",
                "echelle": "1 (Pas du tout) à 5 (Énormément)"
            },
            {
                "id": "q3_danse",
                "question": "À quel point aimez-vous la musique dansante ?",
                "dimension": "danceability",
                "echelle": "1 (Pas du tout) à 5 (Énormément)"
            },
            {
                "id": "q4_joyeux",
                "question": "Préférez-vous la musique joyeuse et positive ?",
                "dimension": "valence",
                "echelle": "1 (Non, plutôt mélancolique) à 5 (Oui, très joyeuse)"
            },
            {
                "id": "q5_acoustique",
                "question": "Appréciez-vous la musique acoustique et instrumentale ?",
                "dimension": "acousticness",
                "echelle": "1 (Pas du tout) à 5 (Énormément)"
            },
            {
                "id": "q6_intensite",
                "question": "Quel niveau d'intensité sonore préférez-vous ?",
                "dimension": "loudness",
                "echelle": "1 (Très doux) à 5 (Très intense)"
            },
            {
                "id": "q7_rythme",
                "question": "Préférez-vous un rythme rapide ou lent ?",
                "dimension": "bpm",
                "echelle": "1 (Très lent) à 5 (Très rapide)"
            },
            {
                "id": "q8_nouveaute",
                "question": "Êtes-vous ouvert à découvrir de nouveaux genres musicaux ?",
                "dimension": "ouverture",
                "echelle": "1 (Non, je préfère mes styles) à 5 (Oui, j'adore découvrir)"
            }
        ]
    
    def _init_questions_ouvertes(self) -> List[Dict[str, Any]]:
        """Initialise les questions ouvertes"""
        return [
            {
                "id": "qo1_mood",
                "question": "Décrivez l'ambiance ou le mood musical que vous recherchez actuellement",
                "type": "texte_libre",
                "placeholder": "Ex: Je cherche quelque chose de mélancolique mais motivant pour travailler..."
            },
            {
                "id": "qo2_contexte",
                "question": "Dans quel contexte allez-vous écouter cette musique ?",
                "type": "texte_libre",
                "placeholder": "Ex: Pendant mes séances de sport, en conduisant, pour me concentrer..."
            },
            {
                "id": "qo3_artistes",
                "question": "Quels sont vos artistes ou groupes préférés ? (séparés par des virgules)",
                "type": "liste",
                "placeholder": "Ex: Coldplay, Adele, The Killers"
            },
            {
                "id": "qo4_genres",
                "question": "Quels genres musicaux écoutez-vous habituellement ? (séparés par des virgules)",
                "type": "liste",
                "placeholder": "Ex: rock, pop, électro, jazz"
            },
            {
                "id": "qo5_emotions",
                "question": "Quelles émotions souhaitez-vous ressentir en écoutant de la musique ?",
                "type": "texte_libre",
                "placeholder": "Ex: Nostalgie, joie, énergie, sérénité..."
            }
        ]
    
    def collecter_reponses_dict(self, reponses_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collecte les réponses depuis un dictionnaire (mode API/backend)
        
        Format attendu:
        {
            "likert": {
                "q1_energie": 4,
                "q2_calme": 3,
                ...
            },
            "ouvertes": {
                "qo1_mood": "musique calme pour travailler",
                "qo2_contexte": "au bureau",
                "qo3_artistes": ["Coldplay", "Adele"],
                ...
            }
        }
        """
        reponses_structurees = {
            "timestamp": datetime.now().isoformat(),
            "likert": {},
            "ouvertes": {}
        }
        
        # Valider et structurer les réponses Likert
        for q in self.questions_likert:
            if q["id"] in reponses_dict.get("likert", {}):
                valeur = reponses_dict["likert"][q["id"]]
                if isinstance(valeur, int) and 1 <= valeur <= 5:
                    reponses_structurees["likert"][q["id"]] = {
                        "valeur": valeur,
                        "dimension": q["dimension"]
                    }
        
        # Valider et structurer les réponses ouvertes
        for q in self.questions_ouvertes:
            if q["id"] in reponses_dict.get("ouvertes", {}):
                valeur = reponses_dict["ouvertes"][q["id"]]
                
                # Convertir en liste si nécessaire
                if q["type"] == "liste" and isinstance(valeur, str):
                    valeur = [item.strip() for item in valeur.split(",") if item.strip()]
                
                reponses_structurees["ouvertes"][q["id"]] = {
                    "valeur": valeur,
                    "type": q["type"]
                }
        
        return reponses_structurees
    
    def sauvegarder_reponses(self, reponses: Dict[str, Any], user_id: str = None) -> Path:
        """Sauvegarde les réponses en JSON"""
        if user_id is None:
            user_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = f"reponses_{user_id}.json"
        filepath = RESPONSES_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(reponses, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def charger_reponses(self, user_id: str) -> Dict[str, Any]:
        """Charge les réponses depuis un fichier JSON"""
        filename = f"reponses_{user_id}.json"
        filepath = RESPONSES_DIR / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Fichier de réponses introuvable : {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def extraire_preferences_audio(self, reponses: Dict[str, Any]) -> Dict[str, float]:
        """
        Extrait les préférences audio numériques depuis les réponses Likert
        Normalise les scores de 1-5 vers des valeurs appropriées (échelle 0.0-1.0 pour la plupart)
        """
        preferences = {}
        
        likert_responses = reponses.get("likert", {})
        
        # Mapper les dimensions aux valeurs normalisées
        for q_id, data in likert_responses.items():
            dimension = data["dimension"]
            valeur = data["valeur"]  # 1-5
            
            # Normaliser selon la dimension (échelle 0.0-1.0 pour features Spotify)
            if dimension == "énergie":
                preferences["energy"] = (valeur - 1) / 4.0  # 0.0-1.0
            elif dimension == "calme":
                preferences["calmness"] = (valeur - 1) / 4.0  # 0.0-1.0
            elif dimension == "danceability":
                preferences["danceability"] = (valeur - 1) / 4.0  # 0.0-1.0
            elif dimension == "valence":
                preferences["valence"] = (valeur - 1) / 4.0  # 0.0-1.0
            elif dimension == "acousticness":
                preferences["acousticness"] = (valeur - 1) / 4.0  # 0.0-1.0
            elif dimension == "loudness":
                # Loudness est en dB (typiquement -60 à 0, mais souvent -20 à 0)
                preferences["loudness"] = -30 + (valeur - 1) * 7.5  # -30 à 0
            elif dimension == "bpm":
                # BPM typique de 60 à 180
                preferences["tempo"] = 60 + (valeur - 1) * 30  # 60 à 180
            elif dimension == "ouverture":
                preferences["openness"] = valeur / 5.0  # 0.2 à 1.0
        
        return preferences
    
    def extraire_texte_semantique(self, reponses: Dict[str, Any]) -> str:
        """
        Extrait et combine tous les textes pour l'analyse sémantique
        """
        textes = []
        
        ouvertes = reponses.get("ouvertes", {})
        
        # Mood et contexte
        if "qo1_mood" in ouvertes:
            valeur = ouvertes["qo1_mood"]["valeur"]
            if valeur:
                textes.append(str(valeur))
        
        if "qo2_contexte" in ouvertes:
            valeur = ouvertes["qo2_contexte"]["valeur"]
            if valeur:
                textes.append(str(valeur))
        
        # Émotions
        if "qo5_emotions" in ouvertes:
            valeur = ouvertes["qo5_emotions"]["valeur"]
            if valeur:
                textes.append(str(valeur))
        
        # Artistes et genres (pour contexte)
        if "qo3_artistes" in ouvertes:
            artistes = ouvertes["qo3_artistes"]["valeur"]
            if isinstance(artistes, list) and artistes:
                # Filtrer les valeurs vides et convertir en string
                artistes_str = [str(a).strip() for a in artistes if a]
                if artistes_str:
                    textes.append("J'aime les artistes comme " + ", ".join(artistes_str))
            elif artistes:
                textes.append(f"J'aime {str(artistes)}")
        
        if "qo4_genres" in ouvertes:
            genres = ouvertes["qo4_genres"]["valeur"]
            if isinstance(genres, list) and genres:
                # Filtrer les valeurs vides et convertir en string
                genres_str = [str(g).strip() for g in genres if g]
                if genres_str:
                    textes.append("J'écoute principalement " + ", ".join(genres_str))
            elif genres:
                textes.append(f"J'écoute {str(genres)}")
        
        return " ".join(textes)
    
    def extraire_genres_preferes(self, reponses: Dict[str, Any]) -> List[str]:
        """
        Extrait la liste des genres musicaux préférés depuis les réponses ouvertes
        
        Returns:
            Liste des genres préférés (en minuscules pour matching)
        """
        genres_preferes = []
        
        ouvertes = reponses.get("ouvertes", {})
        
        if "qo4_genres" in ouvertes:
            genres = ouvertes["qo4_genres"]["valeur"]
            if isinstance(genres, list):
                genres_preferes = [str(g).strip().lower() for g in genres if g]
            elif genres:
                genres_preferes = [str(genres).strip().lower()]
        
        return genres_preferes
    
    def extraire_niveau_ouverture(self, reponses: Dict[str, Any]) -> int:
        """
        Extrait le niveau d'ouverture à de nouveaux genres (question q8_nouveaute)
        
        Returns:
            Valeur entre 1 et 5 (1 = fermé, 5 = très ouvert)
        """
        likert_responses = reponses.get("likert", {})
        
        if "q8_nouveaute" in likert_responses:
            return likert_responses["q8_nouveaute"]["valeur"]
        
        return 3  # Valeur neutre par défaut

