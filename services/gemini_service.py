"""
Service d'intégration GenAI avec l'API Gemini (EF4)
Enrichissement des entrées, génération de justifications et synthèses
"""
import google.generativeai as genai
from typing import Dict, List, Any
from config.config import GEMINI_API_KEY, MIN_WORDS_FOR_ENRICHMENT


class GeminiService:
    """Service d'intégration avec l'API Gemini de Google"""
    
    def __init__(self, api_key: str = None):
        """
        Initialise le service Gemini
        
        Args:
            api_key: Clé API Gemini (utilise GEMINI_API_KEY par défaut)
        """
        self.api_key = api_key or GEMINI_API_KEY
        
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            self.model = None
        else:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def _verifier_disponibilite(self):
        """Vérifie si le service est disponible"""
        if self.model is None:
            raise ValueError(
                "Service Gemini non disponible. "
                "Veuillez configurer GEMINI_API_KEY dans le fichier .env"
            )
    
    def enrichir_texte_court(self, texte: str) -> str:
        """
        EF4.1: Enrichit les phrases courtes avec du contexte (usage conditionnel)
        
        Args:
            texte: Texte d'entrée utilisateur
            
        Returns:
            Texte enrichi ou texte original si assez long
        """
        # Vérifier si enrichissement nécessaire
        mots = texte.strip().split()
        if len(mots) >= MIN_WORDS_FOR_ENRICHMENT:
            return texte  # Pas besoin d'enrichissement
        
        self._verifier_disponibilite()
        
        prompt = f"""Tu es un assistant musical expert. Un utilisateur a décrit ses préférences musicales de manière très brève.

Texte utilisateur: "{texte}"

Ta tâche: Enrichir cette description courte en ajoutant du contexte musical pertinent, des termes techniques et des descriptions qui aideront un système de recommandation à mieux comprendre ce que l'utilisateur recherche.

Règles:
- Garde le sens original intact
- Ajoute des termes musicaux pertinents (tempo, ambiance, énergie, etc.)
- Reste concis (maximum 3-4 phrases)
- Utilise un style descriptif et technique
- Ne pose pas de questions, formule des affirmations

Texte enrichi:"""

        try:
            response = self.model.generate_content(prompt)
            texte_enrichi = response.text.strip()
            return texte_enrichi
        
        except Exception as e:
            return texte  # Retourner le texte original en cas d'erreur
    
    def generer_plan_progression(
        self,
        recommandations: Dict[str, Any],
        texte_utilisateur: str,
        points_faibles: List[Dict[str, Any]]
    ) -> str:
        """
        EF4.2: Génère un plan de progression personnalisé
        
        Args:
            recommandations: Dictionnaire des recommandations
            texte_utilisateur: Texte original de l'utilisateur
            points_faibles: Éléments avec les scores les plus faibles
            
        Returns:
            Texte du plan de progression
        """
        self._verifier_disponibilite()
        
        # Préparer les informations pour le prompt
        top_reco = recommandations['top_recommandations'][:3]
        stats = recommandations['statistiques']
        
        tops_text = "\n".join([
            f"- {i+1}. [{r['type'].upper()}] {r['id']} (Score: {r['scores']['global']:.2f})"
            for i, r in enumerate(top_reco)
        ])
        
        faibles_text = "\n".join([
            f"- [{p['type'].upper()}] {p['id']} (Score: {p['scores']['global']:.2f})"
            for p in points_faibles[:3]
        ])
        
        prompt = f"""Tu es un expert en recommandation musicale et en découverte musicale.

CONTEXTE UTILISATEUR:
"{texte_utilisateur}"

TOP RECOMMANDATIONS (ce qui correspond le mieux):
{tops_text}

DOMAINES À EXPLORER (scores faibles - opportunités de découverte):
{faibles_text}

STATISTIQUES:
- Score moyen: {stats['score_moyen']:.2f}
- Nombre d'éléments évalués: {stats['nombre_elements_evalues']}

Ta tâche: Créer un plan de progression musicale personnalisé qui:
1. Identifie les éléments prioritaires à développer ou à explorer
2. Explique pourquoi ces découvertes seraient bénéfiques pour l'utilisateur
3. Propose un chemin d'évolution musical progressif
4. Suggère comment élargir les horizons musicaux

Format souhaité:
- Un paragraphe d'introduction
- 3-4 recommandations d'exploration concrètes
- Une conclusion motivante

Ton: Expert mais accessible, encourageant la découverte musicale.

Plan de progression:"""

        try:
            response = self.model.generate_content(prompt)
            plan = response.text.strip()
            return plan
        
        except Exception as e:
            return "Plan de progression non disponible (erreur API)."
    
    def generer_synthese_recommandations(
        self,
        recommandations: Dict[str, Any],
        texte_utilisateur: str
    ) -> str:
        """
        EF4.3: Génère une synthèse explicative des recommandations
        
        Args:
            recommandations: Dictionnaire des recommandations
            texte_utilisateur: Texte original de l'utilisateur
            
        Returns:
            Synthèse en style Executive Summary
        """
        self._verifier_disponibilite()
        
        # Préparer les informations
        top_reco = recommandations['top_recommandations'][:3]
        stats = recommandations['statistiques']
        
        # Formater les tops par type
        top_par_type_text = []
        for type_elem, elements in recommandations['top_par_type'].items():
            if elements:
                meilleur = elements[0]
                top_par_type_text.append(
                    f"  {type_elem.upper()}: {meilleur['id']} (Score: {meilleur['scores']['global']:.2f})"
                )
        
        tops_text = "\n".join([
            f"{i+1}. [{r['type'].upper()}] {r['id']}\n"
            f"   Score global: {r['scores']['global']:.2f}\n"
            f"   - Similarité sémantique: {r['scores']['similarite_semantique']:.2f}\n"
            f"   - Mood match: {r['scores']['mood_match']:.2f}"
            for i, r in enumerate(top_reco)
        ])
        
        prompt = f"""Tu es un expert en recommandation musicale qui rédige des synthèses exécutives.

DEMANDE UTILISATEUR:
"{texte_utilisateur}"

TOP 3 RECOMMANDATIONS GLOBALES:
{tops_text}

MEILLEURS PAR CATÉGORIE:
{chr(10).join(top_par_type_text)}

STATISTIQUES:
- Score moyen de pertinence: {stats['score_moyen']:.2f}/1.00
- Analyse de {stats['nombre_elements_evalues']} éléments musicaux

Ta tâche: Rédiger une synthèse executive qui:
1. Explique brièvement pourquoi ces recommandations correspondent à la demande
2. Met en évidence les points forts de l'analyse
3. Justifie les choix avec des arguments musicaux concrets
4. Propose une mise en contexte de l'univers musical recommandé

Format: Executive Summary professionnel
- 2-3 paragraphes maximum
- Style clair, précis et persuasif
- Utilise des termes musicaux appropriés

Synthèse:"""

        try:
            response = self.model.generate_content(prompt)
            synthese = response.text.strip()
            return synthese
        
        except Exception as e:
            return "Synthèse non disponible (erreur API)."
    
    def generer_rapport_complet(
        self,
        recommandations: Dict[str, Any],
        texte_utilisateur: str,
        texte_enrichi: str = None
    ) -> Dict[str, str]:
        """
        Génère un rapport complet avec synthèse et plan de progression
        
        Args:
            recommandations: Dictionnaire des recommandations
            texte_utilisateur: Texte original de l'utilisateur
            texte_enrichi: Texte enrichi (optionnel)
            
        Returns:
            Dictionnaire contenant synthèse et plan
        """
        self._verifier_disponibilite()
        
        # Synthèse
        synthese = self.generer_synthese_recommandations(
            recommandations,
            texte_enrichi or texte_utilisateur
        )
        
        # Plan de progression
        plan = self.generer_plan_progression(
            recommandations,
            texte_utilisateur,
            recommandations.get('points_faibles', [])
        )
        
        return {
            'synthese': synthese,
            'plan_progression': plan
        }

