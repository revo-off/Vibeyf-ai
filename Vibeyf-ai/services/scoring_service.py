"""
Système de Scoring et Recommandation (EF3)
Combine les scores sémantiques, les préférences Likert et les caractéristiques audio
"""
import numpy as np
from typing import Dict, List, Any, Tuple
from config.config import WEIGHTS, MOOD_MAPPINGS, TOP_N_RECOMMENDATIONS


class SystemeScoring:
    """Calcule les scores de couverture sémantique et génère des recommandations"""
    
    def __init__(self):
        self.weights = WEIGHTS
    
    def calculer_score_audio_match(
        self, 
        preferences_user: Dict[str, float],
        caracteristiques_element: Dict[str, float]
    ) -> float:
        """
        Calcule le score de correspondance des caractéristiques audio
        
        Args:
            preferences_user: Préférences audio de l'utilisateur (ex: energy, danceability)
            caracteristiques_element: Caractéristiques audio d'un élément musical
            
        Returns:
            Score normalisé entre 0 et 1
        """
        if not preferences_user or not caracteristiques_element:
            return 0.5  # Score neutre par défaut
        
        scores = []
        
        # Comparer les caractéristiques communes
        common_features = set(preferences_user.keys()) & set(caracteristiques_element.keys())
        
        for feature in common_features:
            pref_val = preferences_user[feature]
            elem_val = caracteristiques_element[feature]
            
            # Normaliser selon la feature
            if feature == 'loudness':
                # Loudness: -60 à 0 dB (typiquement -30 à 0)
                diff = abs(pref_val - elem_val)
                score = 1.0 - min(diff / 30.0, 1.0)
            elif feature in ['tempo', 'bpm']:
                # Tempo/BPM: différence acceptable de 40 BPM
                diff = abs(pref_val - elem_val)
                score = 1.0 - min(diff / 40.0, 1.0)
            elif feature == 'duration_ms':
                # Duration: différence acceptable de 2 minutes (120000 ms)
                diff = abs(pref_val - elem_val)
                score = 1.0 - min(diff / 120000.0, 1.0)
            else:
                # Pour les autres features (échelle 0.0-1.0)
                diff = abs(pref_val - elem_val)
                score = 1.0 - diff
            
            scores.append(score)
        
        # Moyenne des scores si on a des correspondances
        return np.mean(scores) if scores else 0.5
    
    def calculer_score_mood_match(
        self,
        texte_user: str,
        mood_element: str,
        moods_recherches: List[str] = None
    ) -> float:
        """
        Calcule le score de correspondance de mood
        
        Args:
            texte_user: Texte de l'utilisateur
            mood_element: Mood de l'élément
            moods_recherches: Liste des moods détectés dans la requête utilisateur
            
        Returns:
            Score entre 0 et 1
        """
        if not moods_recherches:
            # Si pas de moods spécifiques, rechercher dans le texte
            moods_recherches = []
            texte_lower = texte_user.lower()
            for mood in MOOD_MAPPINGS.keys():
                if mood in texte_lower:
                    moods_recherches.append(mood)
        
        # Vérifier si le mood de l'élément correspond
        if mood_element in moods_recherches:
            return 1.0
        
        # Score partiel si des moods similaires
        moods_similaires = {
            'joyeux': ['festif', 'motivant'],
            'triste': ['mélancolique'],
            'énergique': ['motivant', 'intense', 'festif'],
            'calme': ['relaxant'],
            'mélancolique': ['triste', 'romantique'],
            'motivant': ['énergique', 'intense'],
            'romantique': ['calme', 'mélancolique'],
            'festif': ['joyeux', 'énergique'],
            'relaxant': ['calme'],
            'intense': ['énergique', 'motivant']
        }
        
        for mood_recherche in moods_recherches:
            similaires = moods_similaires.get(mood_recherche, [])
            if mood_element in similaires:
                return 0.6
        
        return 0.3  # Score minimum de base
    
    def calculer_score_preference_likert(
        self,
        preferences_user: Dict[str, float],
        caracteristiques_element: Dict[str, float]
    ) -> float:
        """
        Score basé sur les préférences Likert de l'utilisateur
        
        Args:
            preferences_user: Préférences normalisées de l'utilisateur
            caracteristiques_element: Caractéristiques de l'élément
            
        Returns:
            Score entre 0 et 1
        """
        # Utilise le même calcul que audio_match mais pondéré différemment
        return self.calculer_score_audio_match(preferences_user, caracteristiques_element)
    
    def calculer_score_global(
        self,
        similarite_semantique: float,
        score_mood: float,
        score_preferences: float,
        score_audio: float
    ) -> float:
        """
        Calcule le score global pondéré
        
        Args:
            similarite_semantique: Score de similarité SBERT (0-1)
            score_mood: Score de correspondance de mood (0-1)
            score_preferences: Score des préférences Likert (0-1)
            score_audio: Score des caractéristiques audio (0-1)
            
        Returns:
            Score global pondéré (0-1)
        """
        score = (
            self.weights['semantic_similarity'] * similarite_semantique +
            self.weights['mood_match'] * score_mood +
            self.weights['preference_likert'] * score_preferences +
            self.weights['audio_features'] * score_audio
        )
        
        return float(score)
    
    def calculer_scores_elements(
        self,
        elements_avec_similarite: List[Dict[str, Any]],
        preferences_user: Dict[str, float],
        texte_user: str,
        moods_detectes: List[str] = None,
        genres_preferes: List[str] = None,
        niveau_ouverture: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Calcule les scores complets pour tous les éléments
        
        Args:
            elements_avec_similarite: Éléments du référentiel avec leur similarité sémantique
            preferences_user: Préférences audio de l'utilisateur
            texte_user: Texte original de l'utilisateur
            moods_detectes: Moods détectés dans la requête
            genres_preferes: Liste des genres préférés par l'utilisateur
            niveau_ouverture: Niveau d'ouverture à de nouveaux genres (1-5)
            
        Returns:
            Liste des éléments enrichis avec tous les scores
        """
        elements_scores = []
        genres_preferes = genres_preferes or []
        
        # Si l'utilisateur est très fermé (niveau 1-2), on favorise fortement ses genres
        # Si l'utilisateur est ouvert (niveau 4-5), on favorise la découverte
        
        for element in elements_avec_similarite:
            # Récupérer la similarité sémantique (déjà calculée par le moteur NLP)
            similarite_semantique = element.get('similarite_semantique', 0.0)
            
            # Extraire les caractéristiques de l'élément
            data = element.get('data', {})
            
            # Score de mood
            score_mood = 0.5  # Valeur par défaut
            if element['type'] == 'mood':
                score_mood = self.calculer_score_mood_match(
                    texte_user,
                    element['id'],
                    moods_detectes
                )
            elif 'moods_associes' in data:
                # Pour les ambiances avec moods associés
                scores_moods = [
                    self.calculer_score_mood_match(texte_user, mood, moods_detectes)
                    for mood in data['moods_associes']
                ]
                score_mood = max(scores_moods) if scores_moods else 0.5
            
            # Score audio
            score_audio = 0.5  # Valeur par défaut
            if 'caracteristiques_moyennes' in data:
                score_audio = self.calculer_score_audio_match(
                    preferences_user,
                    data['caracteristiques_moyennes']
                )
            
            # Score préférences
            score_preferences = self.calculer_score_preference_likert(
                preferences_user,
                data.get('caracteristiques_moyennes', {})
            )
            
            # Score global
            score_global = self.calculer_score_global(
                similarite_semantique,
                score_mood,
                score_preferences,
                score_audio
            )
            
            # Boost pour le genre préféré (varie selon le niveau d'ouverture)
            # Niveau 1 (fermé): +80% boost
            # Niveau 2: +60% boost
            # Niveau 3 (neutre): +40% boost
            # Niveau 4: +25% boost
            # Niveau 5 (très ouvert): +15% boost
            genre_boost = 0.0
            if genres_preferes and element['type'] == 'chanson':
                element_genre = element.get('genre', '').lower()
                if element_genre in genres_preferes:
                    # Calculer le boost inversement proportionnel à l'ouverture
                    boost_map = {1: 0.80, 2: 0.60, 3: 0.40, 4: 0.25, 5: 0.15}
                    genre_boost = boost_map.get(niveau_ouverture, 0.40)
                    score_global = min(score_global * (1 + genre_boost), 1.0)
            
            # Enrichir l'élément avec tous les scores
            element_enrichi = element.copy()
            element_enrichi['scores'] = {
                'global': score_global,
                'similarite_semantique': similarite_semantique,
                'mood_match': score_mood,
                'preferences_likert': score_preferences,
                'audio_features': score_audio,
                'genre_boost': genre_boost
            }
            
            elements_scores.append(element_enrichi)
        
        # Trier par score global décroissant
        elements_scores.sort(key=lambda x: x['scores']['global'], reverse=True)
        
        return elements_scores
    
    def generer_recommandations(
        self,
        elements_scores: List[Dict[str, Any]],
        top_n: int = TOP_N_RECOMMENDATIONS
    ) -> Dict[str, Any]:
        """
        Génère les recommandations finales sans doublons
        
        Args:
            elements_scores: Éléments avec scores calculés
            top_n: Nombre de recommandations à retourner
            
        Returns:
            Dictionnaire avec les tops recommandations et analyses
        """
        # Déduplication : garder uniquement la première occurrence de chaque chanson/élément
        seen_ids = set()
        elements_uniques = []
        
        for element in elements_scores:
            # Créer une clé unique selon le type
            if element['type'] == 'chanson':
                # Pour les chansons : identifiant unique = nom + artiste
                unique_key = f"{element['data'].get('nom', '')}_{element['data'].get('artiste', '')}".lower()
            else:
                # Pour les autres : utiliser l'ID
                unique_key = f"{element['type']}_{element['id']}"
            
            if unique_key not in seen_ids:
                seen_ids.add(unique_key)
                elements_uniques.append(element)
        
        # Top N recommandations globales (sans doublons)
        top_recommandations = elements_uniques[:top_n]
        
        # Top par type (également dédupliqué)
        top_par_type = {}
        types = set(elem['type'] for elem in elements_uniques)
        
        for type_elem in types:
            elements_type = [e for e in elements_uniques if e['type'] == type_elem]
            top_par_type[type_elem] = elements_type[:min(3, len(elements_type))]
        
        # Identifier les points faibles (scores les plus bas)
        # Pour le plan de progression
        elements_tries_par_score_asc = sorted(
            elements_scores,
            key=lambda x: x['scores']['global']
        )
        
        points_faibles = elements_tries_par_score_asc[:5]
        
        # Statistiques
        scores_globaux = [e['scores']['global'] for e in elements_scores]
        
        recommandations = {
            'top_recommandations': top_recommandations,
            'top_par_type': top_par_type,
            'points_faibles': points_faibles,
            'statistiques': {
                'score_moyen': float(np.mean(scores_globaux)),
                'score_max': float(np.max(scores_globaux)),
                'score_min': float(np.min(scores_globaux)),
                'nombre_elements_evalues': len(elements_scores)
            }
        }
        
        return recommandations
    
    def formater_recommandation_simple(
        self,
        recommandation: Dict[str, Any]
    ) -> str:
        """
        Formate une recommandation pour affichage simple
        
        Args:
            recommandation: Élément de recommandation avec scores
            
        Returns:
            Chaîne formatée
        """
        type_elem = recommandation['type']
        id_elem = recommandation['id']
        scores = recommandation['scores']
        data = recommandation.get('data', {})
        
        # Formater selon le type
        if type_elem == 'chanson':
            nom = data.get('nom', id_elem)
            artiste = data.get('artiste', 'Artiste inconnu')
            genre = data.get('genre', '')
            return f"Chanson: {nom} par {artiste} ({genre})"
        
        elif type_elem == 'genre':
            nom = data.get('nom', id_elem)
            desc = data.get('description', '')
            return f"Genre: {nom} - {desc}"
        
        elif type_elem == 'mood':
            nom = data.get('nom', id_elem)
            desc = data.get('description', '')
            return f"Mood: {nom} - {desc}"
        
        elif type_elem == 'ambiance':
            nom = data.get('nom', id_elem)
            desc = data.get('description', '')
            return f"Ambiance: {nom} - {desc}"
        
        elif type_elem == 'playlist':
            nom = data.get('nom', id_elem)
            desc = data.get('description', '')
            nb_titres = data.get('nombre_titres', 0)
            return f"Playlist: {nom} ({nb_titres} titres) - {desc}"
        
        return f"{type_elem}: {id_elem}"

