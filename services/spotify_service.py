"""
Service pour interagir avec l'API Spotify et récupérer les images des albums
"""

import base64
import requests
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class SpotifyService:
    """Service pour récupérer les métadonnées Spotify incluant les images"""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialise le service Spotify
        
        Args:
            client_id: ID client Spotify (optionnel)
            client_secret: Secret client Spotify (optionnel)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.base_url = "https://api.spotify.com/v1"
        
        # Authentification si les credentials sont fournis
        if client_id and client_secret:
            self._authenticate()
    
    def _authenticate(self):
        """Authentification via Client Credentials Flow"""
        try:
            auth_url = "https://accounts.spotify.com/api/token"
            auth_header = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            headers = {
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            data = {"grant_type": "client_credentials"}
            
            response = requests.post(auth_url, headers=headers, data=data, timeout=5)
            response.raise_for_status()
            
            self.access_token = response.json().get("access_token")
            logger.info("Authentification Spotify réussie")
            
        except Exception as e:
            logger.warning(f"Échec d'authentification Spotify: {e}")
            self.access_token = None
    
    def get_album_cover_url(self, track_id: str, size: str = "medium") -> Optional[str]:
        """
        Récupère l'URL de la couverture d'album d'une chanson
        
        Args:
            track_id: ID Spotify de la chanson
            size: Taille de l'image ('small'=64px, 'medium'=300px, 'large'=640px)
        
        Returns:
            URL de l'image ou None
        """
        if not self.access_token:
            # Fallback: utiliser une image par défaut ou placeholder
            return self._get_placeholder_image()
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.base_url}/tracks/{track_id}",
                headers=headers,
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                images = data.get("album", {}).get("images", [])
                
                # Sélectionner l'image selon la taille demandée
                size_map = {"small": 2, "medium": 1, "large": 0}
                idx = size_map.get(size, 1)
                
                if images and len(images) > idx:
                    return images[idx]["url"]
                elif images:
                    return images[0]["url"]
            
            return self._get_placeholder_image()
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération de l'image pour {track_id}: {e}")
            return self._get_placeholder_image()
    
    def search_track_and_get_cover(self, track_name: str, artist_name: str) -> Optional[str]:
        """
        Recherche une chanson et récupère sa couverture d'album
        
        Args:
            track_name: Nom de la chanson
            artist_name: Nom de l'artiste
        
        Returns:
            URL de l'image ou None
        """
        if not self.access_token:
            return self._get_placeholder_image()
        
        try:
            query = f"track:{track_name} artist:{artist_name}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            params = {"q": query, "type": "track", "limit": 1}
            
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=3
            )
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("tracks", {}).get("items", [])
                
                if tracks:
                    images = tracks[0].get("album", {}).get("images", [])
                    if images:
                        return images[1]["url"] if len(images) > 1 else images[0]["url"]
            
            return self._get_placeholder_image()
            
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche pour {track_name} - {artist_name}: {e}")
            return self._get_placeholder_image()
    
    def _get_placeholder_image(self) -> str:
        """Retourne une URL d'image placeholder"""
        # Image placeholder musicale générique
        return "https://via.placeholder.com/300x300/1DB954/FFFFFF?text=♪"
    
    def get_album_info(self, album_id: str) -> Optional[Dict]:
        """
        Récupère les informations complètes d'un album
        
        Args:
            album_id: ID Spotify de l'album
        
        Returns:
            Dictionnaire avec les infos de l'album ou None
        """
        if not self.access_token:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.base_url}/albums/{album_id}",
                headers=headers,
                timeout=3
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération de l'album {album_id}: {e}")
            return None
