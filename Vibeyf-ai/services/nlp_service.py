"""
Moteur NLP Sémantique (EF2)
Utilise SBERT pour les embeddings et calcule la similarité cosinus
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple
import pickle
from pathlib import Path
from config.config import SBERT_MODEL_NAME, REFERENTIEL_DIR


class MoteurNLP:
    """Moteur d'analyse sémantique basé sur SBERT"""
    
    def __init__(self):
        self.model = SentenceTransformer(SBERT_MODEL_NAME)
        self.referentiel_embeddings = None
        self.referentiel_texts = None
        self.embeddings_cache_path = REFERENTIEL_DIR / "embeddings_cache.pkl"
    
    def encoder_textes(self, textes: List[str]) -> np.ndarray:
        """
        Encode une liste de textes en vecteurs d'embeddings
        
        Args:
            textes: Liste de chaînes de caractères à encoder
            
        Returns:
            Matrice numpy d'embeddings (n_textes, embedding_dim)
        """
        if not textes:
            return np.array([])
        
        embeddings = self.model.encode(textes, convert_to_numpy=True, show_progress_bar=False)
        return embeddings
    
    def calculer_similarite_cosinus(
        self, 
        embedding_requete: np.ndarray, 
        embeddings_referentiel: np.ndarray
    ) -> np.ndarray:
        """
        Calcule la similarité cosinus entre une requête et un référentiel
        
        Args:
            embedding_requete: Vecteur d'embedding de la requête (1, embedding_dim)
            embeddings_referentiel: Matrice d'embeddings du référentiel (n, embedding_dim)
            
        Returns:
            Vecteur de scores de similarité (n,)
        """
        if embedding_requete.ndim == 1:
            embedding_requete = embedding_requete.reshape(1, -1)
        
        similarities = cosine_similarity(embedding_requete, embeddings_referentiel)[0]
        return similarities
    
    def preparer_referentiel(self, textes_referentiel: List[Dict[str, Any]]):
        """
        Prépare et encode le référentiel complet
        
        Args:
            textes_referentiel: Liste de dictionnaires avec 'text', 'type', 'id', 'data'
        """
        self.referentiel_texts = textes_referentiel
        
        # Extraire les textes pour l'encoding
        textes_bruts = [item['text'] for item in textes_referentiel]
        
        # Encoder tous les textes
        self.referentiel_embeddings = self.encoder_textes(textes_bruts)
        
        # Sauvegarder le cache
        self._sauvegarder_cache()
    
    def _sauvegarder_cache(self):
        """Sauvegarde les embeddings en cache pour réutilisation"""
        cache_data = {
            'embeddings': self.referentiel_embeddings,
            'texts': self.referentiel_texts
        }
        
        with open(self.embeddings_cache_path, 'wb') as f:
            pickle.dump(cache_data, f)
    
    def charger_cache(self) -> bool:
        """Charge les embeddings depuis le cache si disponible"""
        if not self.embeddings_cache_path.exists():
            return False
        
        try:
            with open(self.embeddings_cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            self.referentiel_embeddings = cache_data['embeddings']
            self.referentiel_texts = cache_data['texts']
            
            return True
        except Exception as e:
            return False
    
    def rechercher_similaires(
        self, 
        requete: str, 
        top_k: int = 10,
        filtre_type: str = None
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Recherche les éléments les plus similaires à une requête
        
        Args:
            requete: Texte de la requête utilisateur
            top_k: Nombre de résultats à retourner
            filtre_type: Filtrer par type ('genre', 'mood', 'ambiance', 'playlist')
            
        Returns:
            Liste de tuples (élément_référentiel, score_similarité)
        """
        if self.referentiel_embeddings is None:
            raise ValueError("Le référentiel n'a pas été préparé. Appelez preparer_referentiel() d'abord.")
        
        # Encoder la requête
        embedding_requete = self.encoder_textes([requete])
        
        # Calculer les similarités
        similarities = self.calculer_similarite_cosinus(
            embedding_requete, 
            self.referentiel_embeddings
        )
        
        # Créer la liste des résultats
        resultats = []
        for i, score in enumerate(similarities):
            element = self.referentiel_texts[i]
            
            # Appliquer le filtre si spécifié
            if filtre_type is None or element['type'] == filtre_type:
                resultats.append((element, float(score)))
        
        # Trier par score décroissant et prendre le top_k
        resultats.sort(key=lambda x: x[1], reverse=True)
        return resultats[:top_k]
    
    def rechercher_par_type(
        self, 
        requete: str, 
        types: List[str],
        top_k_par_type: int = 3
    ) -> Dict[str, List[Tuple[Dict[str, Any], float]]]:
        """
        Recherche les meilleurs éléments pour chaque type
        
        Args:
            requete: Texte de la requête utilisateur
            types: Liste des types à rechercher
            top_k_par_type: Nombre de résultats par type
            
        Returns:
            Dictionnaire {type: [(élément, score), ...]}
        """
        resultats_par_type = {}
        
        for type_element in types:
            resultats = self.rechercher_similaires(
                requete, 
                top_k=top_k_par_type, 
                filtre_type=type_element
            )
            resultats_par_type[type_element] = resultats
        
        return resultats_par_type
    
    def comparer_textes(self, texte1: str, texte2: str) -> float:
        """
        Compare la similarité entre deux textes
        
        Args:
            texte1: Premier texte
            texte2: Deuxième texte
            
        Returns:
            Score de similarité cosinus (0 à 1)
        """
        embeddings = self.encoder_textes([texte1, texte2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)
    
    def obtenir_scores_detailles(
        self, 
        requete: str
    ) -> List[Dict[str, Any]]:
        """
        Obtient les scores détaillés pour tous les éléments du référentiel
        
        Args:
            requete: Texte de la requête utilisateur
            
        Returns:
            Liste de dictionnaires avec toutes les informations et scores
        """
        if self.referentiel_embeddings is None:
            raise ValueError("Le référentiel n'a pas été préparé.")
        
        # Encoder la requête
        embedding_requete = self.encoder_textes([requete])
        
        # Calculer les similarités
        similarities = self.calculer_similarite_cosinus(
            embedding_requete, 
            self.referentiel_embeddings
        )
        
        # Créer la liste détaillée
        resultats = []
        for i, score in enumerate(similarities):
            element = self.referentiel_texts[i].copy()
            element['similarite_semantique'] = float(score)
            resultats.append(element)
        
        # Trier par score
        resultats.sort(key=lambda x: x['similarite_semantique'], reverse=True)
        
        return resultats
    
    def analyser_requete_multi_aspects(
        self, 
        requete: str
    ) -> Dict[str, Any]:
        """
        Analyse multi-aspects d'une requête
        
        Returns:
            Dictionnaire avec les tops par catégorie
        """
        types_analyse = ['genre', 'mood', 'ambiance', 'playlist']
        
        analyse = {
            'requete_originale': requete,
            'tops_par_type': self.rechercher_par_type(requete, types_analyse, top_k_par_type=5)
        }
        
        # Calculer le meilleur match global
        tous_resultats = []
        for type_elem, resultats in analyse['tops_par_type'].items():
            tous_resultats.extend(resultats)
        
        tous_resultats.sort(key=lambda x: x[1], reverse=True)
        analyse['meilleur_match_global'] = tous_resultats[0] if tous_resultats else None
        
        return analyse
