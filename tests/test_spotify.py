"""
Script de test pour vérifier l'intégration de l'API Spotify
"""

from services.spotify_service import SpotifyService
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_spotify_service():
    """Test du service Spotify"""
    
    print("=" * 50)
    print("TEST DU SERVICE SPOTIFY")
    print("=" * 50)
    
    # Récupérer les credentials depuis l'environnement
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    
    print(f"\n1. Configuration:")
    print(f"   Client ID: {'✅ Configuré' if client_id else '❌ Non configuré'}")
    print(f"   Client Secret: {'✅ Configuré' if client_secret else '❌ Non configuré'}")
    
    # Initialiser le service
    spotify = SpotifyService(client_id, client_secret)
    
    print(f"\n2. Authentification:")
    if spotify.access_token:
        print(f"   ✅ Authentification réussie!")
        print(f"   Token: {spotify.access_token[:20]}...")
    else:
        print(f"   ⚠️ Pas d'authentification (mode placeholder)")
    
    # Test de recherche
    print(f"\n3. Test de recherche d'image:")
    test_cases = [
        ("Blinding Lights", "The Weeknd"),
        ("Shape of You", "Ed Sheeran"),
        ("Bohemian Rhapsody", "Queen")
    ]
    
    for track, artist in test_cases:
        print(f"\n   🎵 {track} - {artist}")
        cover_url = spotify.search_track_and_get_cover(track, artist)
        if cover_url:
            if "placeholder" in cover_url:
                print(f"      ⚠️ Image placeholder: {cover_url}")
            else:
                print(f"      ✅ Image trouvée: {cover_url[:60]}...")
        else:
            print(f"      ❌ Aucune image trouvée")
    
    # Test avec ID Spotify (si disponible)
    print(f"\n4. Test avec ID Spotify:")
    # ID de "Blinding Lights" sur Spotify
    test_id = "0VjIjW4GlUZAMYd2vXMi3b"
    print(f"   Track ID: {test_id}")
    cover_url = spotify.get_album_cover_url(test_id)
    if cover_url and "placeholder" not in cover_url:
        print(f"   ✅ Image trouvée: {cover_url[:60]}...")
    else:
        print(f"   ⚠️ Image placeholder utilisée")
    
    print(f"\n5. Résumé:")
    if spotify.access_token:
        print(f"   ✅ Service Spotify opérationnel")
        print(f"   ✅ Les images d'albums s'afficheront dans l'app")
    else:
        print(f"   ⚠️ Service en mode placeholder")
        print(f"   💡 Configurez vos credentials pour voir les vraies pochettes d'album")
        print(f"   📖 Voir: SPOTIFY_API_SETUP.md")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    try:
        test_spotify_service()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
