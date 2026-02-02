"""
Script de test pour l'amélioration des requêtes utilisateur courtes avec Gemini
"""

from services.gemini_service import GeminiService
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_amelioration_requetes():
    """Test de l'amélioration automatique des requêtes courtes"""
    
    print("=" * 60)
    print("TEST D'AMÉLIORATION DES REQUÊTES UTILISATEUR")
    print("=" * 60)
    
    # Vérifier la configuration Gemini
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    print(f"\n1. Configuration Gemini:")
    print(f"   API Key: {'✅ Configurée' if gemini_key else '❌ Non configurée'}")
    
    if not gemini_key:
        print("\n⚠️ GEMINI_API_KEY non configurée")
        print("💡 Ajoutez votre clé dans le fichier .env pour tester")
        print("📖 Obtenez une clé sur: https://makersuite.google.com/app/apikey")
        return
    
    # Initialiser le service
    gemini = GeminiService(gemini_key)
    
    if not gemini.model:
        print("\n❌ Impossible d'initialiser le modèle Gemini")
        return
    
    print(f"   ✅ Service Gemini initialisé")
    
    # Cas de test avec des requêtes courtes
    test_cases = [
        {
            "requete": "rap",
            "mots": 1,
            "attendu": "Devrait être améliorée (< 10 mots)"
        },
        {
            "requete": "musique calme pour travailler",
            "mots": 4,
            "attendu": "Devrait être améliorée (< 10 mots)"
        },
        {
            "requete": "j'aime le rock et le metal",
            "mots": 6,
            "attendu": "Devrait être améliorée (< 10 mots)"
        },
        {
            "requete": "Je recherche de la musique énergique et motivante pour faire du sport, avec un tempo rapide",
            "mots": 17,
            "attendu": "Ne devrait PAS être améliorée (>= 10 mots)"
        }
    ]
    
    print(f"\n2. Tests d'amélioration (seuil: 10 mots):")
    print("-" * 60)
    
    for i, test in enumerate(test_cases, 1):
        requete = test["requete"]
        mots = len(requete.split())
        
        print(f"\n   Test {i}: {test['attendu']}")
        print(f"   Requête originale ({mots} mots): \"{requete}\"")
        
        try:
            requete_amelioree = gemini.ameliorer_requete_utilisateur(requete, seuil_mots=10)
            
            if requete_amelioree == requete:
                print(f"   ✅ Aucune amélioration (requête >= 10 mots)")
            else:
                mots_ameliores = len(requete_amelioree.split())
                print(f"   ✅ Requête améliorée ({mots_ameliores} mots):")
                print(f"   → \"{requete_amelioree}\"")
                
                # Vérifier la limite de 100 mots
                if mots_ameliores > 100:
                    print(f"   ⚠️ ATTENTION: Dépasse 100 mots!")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print("\n" + "-" * 60)
    
    # Test avec différents seuils
    print(f"\n3. Test avec différents seuils:")
    requete_test = "jazz et blues"
    
    for seuil in [5, 10, 15]:
        print(f"\n   Seuil: {seuil} mots")
        print(f"   Requête: \"{requete_test}\" ({len(requete_test.split())} mots)")
        
        try:
            resultat = gemini.ameliorer_requete_utilisateur(requete_test, seuil_mots=seuil)
            if resultat == requete_test:
                print(f"   → Aucune amélioration")
            else:
                print(f"   → Améliorée: \"{resultat[:80]}...\"")
        except Exception as e:
            print(f"   → Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("\n✅ Tests terminés!")
    print("\n💡 Intégration dans l'API:")
    print("   - L'amélioration s'applique automatiquement à qo1_preferences")
    print("   - Seuil: 10 mots minimum")
    print("   - Limite: 100 mots maximum")
    print("   - Ne modifie pas les requêtes >= 10 mots")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        test_amelioration_requetes()
    except Exception as e:
        print(f"\n❌ ERREUR GÉNÉRALE: {e}")
        import traceback
        traceback.print_exc()
