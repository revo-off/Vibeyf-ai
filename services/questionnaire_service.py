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
        self.questions_ouvertes = self._init_questions_ouvertes()
        self.questions_likert = self._init_questions_likert()
    
    def _init_questions_likert(self) -> List[Dict[str, Any]]:
        """Initialise les questions sur échelle de Likert (1-5)"""
        return [
            {
                "id": "q1_energie",
                "question": "Quel niveau d'énergie recherchez-vous dans votre musique ?",
                "dimension": "énergie",
                "echelle": "1 (Très calme) à 5 (Très énergique)"
            },
            {
                "id": "q2_humeur",
                "question": "Quelle ambiance émotionnelle préférez-vous ?",
                "dimension": "valence",
                "echelle": "1 (Mélancolique/Sombre) à 5 (Joyeuse/Positive)"
            },
            {
                "id": "q3_ouverture",
                "question": "Êtes-vous ouvert à découvrir de nouveaux genres musicaux ?",
                "dimension": "ouverture",
                "echelle": "1 (Non, je préfère mes styles) à 5 (Oui, j'adore découvrir)"
            }
        ]
    
    def _init_questions_ouvertes(self) -> List[Dict[str, Any]]:
        """Initialise les questions ouvertes"""
        return [
            {
                "id": "qo1_preferences",
                "question": "Décrivez vos préférences musicales : genres que vous aimez, ambiance recherchée, artistes préférés, émotions souhaitées...",
                "type": "texte_libre",
                "placeholder": "Ex: J'aime le rock alternatif et la pop mélancolique, des artistes comme Radiohead ou Lana Del Rey. Je cherche quelque chose d'introspectif mais motivant pour travailler..."
            },
            {
                "id": "qo2_contexte",
                "question": "Dans quel contexte allez-vous écouter cette musique ?",
                "type": "texte_libre",
                "placeholder": "Ex: Pendant mes séances de sport, en conduisant, pour me concentrer..."
            },
            {
                "id": "qo3_artistes",
                "question": "Y a-t-il des artistes ou groupes spécifiques à mentionner ? (optionnel, séparés par des virgules)",
                "type": "liste",
                "placeholder": "Ex: Coldplay, Adele, The Killers"
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
            elif dimension == "valence":
                preferences["valence"] = (valeur - 1) / 4.0  # 0.0-1.0
            elif dimension == "ouverture":
                preferences["openness"] = valeur / 5.0  # 0.2 à 1.0
        
        return preferences
    
    def extraire_texte_semantique(self, reponses: Dict[str, Any]) -> str:
        """
        Extrait et combine tous les textes pour l'analyse sémantique
        """
        textes = []
        
        ouvertes = reponses.get("ouvertes", {})
        
        # Préférences principales (inclut genres, artistes, mood, émotions)
        if "qo1_preferences" in ouvertes:
            valeur = ouvertes["qo1_preferences"]["valeur"]
            if valeur:
                textes.append(str(valeur))
        
        # Contexte
        if "qo2_contexte" in ouvertes:
            valeur = ouvertes["qo2_contexte"]["valeur"]
            if valeur:
                textes.append(str(valeur))
        
        # Artistes supplémentaires (optionnel)
        if "qo3_artistes" in ouvertes:
            artistes = ouvertes["qo3_artistes"]["valeur"]
            if isinstance(artistes, list) and artistes:
                # Filtrer les valeurs vides et convertir en string
                artistes_str = [str(a).strip() for a in artistes if a]
                if artistes_str:
                    textes.append("Artistes mentionnés : " + ", ".join(artistes_str))
            elif artistes:
                textes.append(f"Artistes : {str(artistes)}")
        
        return " ".join(textes)
    
    def extraire_genres_preferes(self, reponses: Dict[str, Any]) -> List[str]:
        """
        Extrait la liste des genres musicaux préférés depuis le texte des préférences
        
        Returns:
            Liste des genres préférés (en minuscules pour matching)
        """
        genres_preferes = []
        genres_connus = ['rock', 'pop', 'rap', 'hip-hop', 'jazz', 'classical', 'electro', 'electronic', 
                        'edm', 'metal', 'folk', 'country', 'reggae', 'r&b', 'rnb', 'soul', 'funk', 
                        'blues', 'indie', 'alternative', 'punk', 'techno', 'house', 'latin', 'disco']
        
        ouvertes = reponses.get("ouvertes", {})
        
        # Extraire depuis qo1_preferences
        if "qo1_preferences" in ouvertes:
            texte = str(ouvertes["qo1_preferences"]["valeur"]).lower()
            
            # Rechercher les genres connus dans le texte
            for genre in genres_connus:
                if genre in texte:
                    genres_preferes.append(genre)
        
        return list(set(genres_preferes))  # Dédupliquer
    
    def extraire_niveau_ouverture(self, reponses: Dict[str, Any]) -> int:
        """
        Extrait le niveau d'ouverture à de nouveaux genres (question q3_ouverture)
        
        Returns:
            Valeur entre 1 et 5 (1 = fermé, 5 = très ouvert)
        """
        likert_responses = reponses.get("likert", {})
        
        if "q3_ouverture" in likert_responses:
            return likert_responses["q3_ouverture"]["valeur"]
        
        return 3  # Valeur neutre par défaut

