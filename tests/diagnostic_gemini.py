"""
Script de diagnostic rapide pour vérifier la configuration Gemini
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

print("=" * 60)
print("DIAGNOSTIC CONFIGURATION GEMINI")
print("=" * 60)

# Vérifier la variable d'environnement
gemini_key = os.getenv("GEMINI_API_KEY", "")
print(f"\n1. Variable d'environnement GEMINI_API_KEY:")
if gemini_key and gemini_key != "":
    print(f"   ✅ Configurée: {gemini_key[:15]}...")
else:
    print(f"   ❌ NON CONFIGURÉE ou VIDE")
    print(f"   Valeur actuelle: '{gemini_key}'")

# Vérifier le fichier .env
print(f"\n2. Fichier .env:")
if os.path.exists(".env"):
    print(f"   ✅ Fichier .env existe")
    with open(".env", "r") as f:
        content = f.read()
        if "GEMINI_API_KEY" in content:
            print(f"   ✅ GEMINI_API_KEY présente dans .env")
            lines = [l for l in content.split('\n') if 'GEMINI_API_KEY' in l and not l.strip().startswith('#')]
            if lines:
                print(f"   Ligne trouvée: {lines[0][:50]}...")
        else:
            print(f"   ❌ GEMINI_API_KEY absente du fichier .env")
else:
    print(f"   ❌ Fichier .env n'existe pas")
    print(f"   💡 Créez-le à partir de .env.example")

# Tester l'import du service
print(f"\n3. Test d'import du GeminiService:")
try:
    from services.gemini_service import GeminiService
    print(f"   ✅ Import réussi")
    
    # Tester l'initialisation
    print(f"\n4. Test d'initialisation:")
    gemini = GeminiService()
    
    if gemini.model:
        print(f"   ✅ Service Gemini initialisé avec succès")
        
        # Tester une amélioration simple
        print(f"\n5. Test d'amélioration de requête:")
        test_requete = "sport"
        print(f"   Requête test: '{test_requete}'")
        
        try:
            resultat = gemini.ameliorer_requete_utilisateur(test_requete, seuil_mots=10)
            if resultat != test_requete:
                print(f"   ✅ Amélioration réussie!")
                print(f"   Résultat: '{resultat}'")
            else:
                print(f"   ⚠️ Requête non modifiée (résultat identique)")
        except Exception as e:
            print(f"   ❌ Erreur lors du test: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ❌ Model Gemini = None (pas de clé API valide)")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("\n💡 SOLUTION:")
print("   1. Créez un fichier .env à la racine du projet")
print("   2. Ajoutez la ligne: GEMINI_API_KEY=votre_cle_ici")
print("   3. Obtenez une clé sur: https://makersuite.google.com/app/apikey")
print("   4. Relancez l'API: python api.py")
print("\n" + "=" * 60)
