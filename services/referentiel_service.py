"""
Service de gestion du référentiel musical
Construit à partir des données Spotify et enrichi avec des mappings sémantiques
"""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any
from config.config import DATA_DIR, REFERENTIEL_DIR, MOOD_MAPPINGS, AMBIANCES


class ReferentielMusical:
    """Gère le référentiel de connaissances musicales"""
    
    def __init__(self):
        self.df_spotify = None
        self.genres = {}
        self.artistes = {}
        self.moods = {}
        self.ambiances = {}
        self.playlists = {}
        self._load_spotify_data()
        self._build_referentiel()
    
    def _load_spotify_data(self):
        """Charge les données Spotify"""
        spotify_path = DATA_DIR / "spotify_songs.csv"
        self.df_spotify = pd.read_csv(spotify_path)
    
    def _build_referentiel(self):
        """Construit le référentiel complet"""
        self._extract_genres()
        self._extract_artistes()
        self._build_moods()
        self._build_ambiances()
        self._build_playlists()
        self._save_referentiel()
    
    def _extract_genres(self):
        """Extrait et structure les genres musicaux"""
        genres_counts = self.df_spotify['playlist_genre'].value_counts()
        
        for genre, count in genres_counts.items():
            songs = self.df_spotify[self.df_spotify['playlist_genre'] == genre]
            
            # Prendre les 100 meilleures chansons du genre (ou toutes si moins de 100)
            top_songs = songs.nlargest(min(100, len(songs)), 'track_popularity')
            
            self.genres[genre] = {
                "nom": genre,
                "count": int(count),
                "description": self._generate_genre_description(genre, songs),
                "caracteristiques_moyennes": {
                    "bpm": float(songs['tempo'].mean()),
                    "energy": float(songs['energy'].mean()),
                    "danceability": float(songs['danceability'].mean()),
                    "valence": float(songs['valence'].mean()),
                    "acousticness": float(songs['acousticness'].mean()),
                },
                "chansons": top_songs[['track_id', 'track_name', 'track_artist', 'track_popularity', 
                                       'energy', 'danceability', 'valence', 'acousticness', 'tempo', 
                                       'loudness', 'speechiness', 'instrumentalness', 'liveness']].to_dict('records')
            }
    
    def _extract_artistes(self):
        """Extrait et structure les artistes"""
        artistes_counts = self.df_spotify['track_artist'].value_counts()
        
        # Garder les artistes avec au moins 2 chansons dans le dataset
        for artiste, count in artistes_counts.items():
            if count >= 2:
                songs = self.df_spotify[self.df_spotify['track_artist'] == artiste]
                
                # Extraire l'année depuis track_album_release_date
                songs_copy = songs.copy()
                songs_copy['year'] = pd.to_datetime(songs_copy['track_album_release_date'], errors='coerce').dt.year
                
                self.artistes[artiste] = {
                    "nom": artiste,
                    "genres": songs['playlist_genre'].unique().tolist(),
                    "nombre_titres": int(count),
                    "annees_actives": [int(songs_copy['year'].min()), int(songs_copy['year'].max())],
                    "popularite_moyenne": float(songs['track_popularity'].mean()),
                    "top_titres": songs.nlargest(3, 'track_popularity')[['track_name', 'track_album_release_date', 'playlist_genre']].to_dict('records')
                }
    
    def _build_moods(self):
        """Construit les moods basés sur les caractéristiques audio"""
        for mood_name, criteria in MOOD_MAPPINGS.items():
            # Filtrer les chansons correspondant aux critères du mood
            filtered_songs = self.df_spotify.copy()
            
            for feature, (min_val, max_val) in criteria.items():
                # Mapper les noms de features aux colonnes du nouveau dataset
                if feature == 'bpm':
                    feature = 'tempo'
                # Les autres features ont déjà les bons noms en minuscules
                
                if feature in filtered_songs.columns:
                    filtered_songs = filtered_songs[
                        (filtered_songs[feature] >= min_val) & 
                        (filtered_songs[feature] <= max_val)
                    ]
            
            if len(filtered_songs) > 0:
                self.moods[mood_name] = {
                    "nom": mood_name,
                    "description": self._generate_mood_description(mood_name),
                    "criteres": criteria,
                    "genres_associes": filtered_songs['playlist_genre'].value_counts().head(5).to_dict(),
                    "chansons_representatives": filtered_songs.nlargest(10, 'track_popularity')[
                        ['track_name', 'track_artist', 'playlist_genre', 'track_album_release_date']
                    ].to_dict('records')
                }
    
    def _build_ambiances(self):
        """Construit les ambiances prédéfinies"""
        ambiance_moods_mapping = {
            "soirée_entre_amis": ["joyeux", "festif", "énergique"],
            "concentration": ["calme", "relaxant"],
            "sport": ["énergique", "motivant", "intense"],
            "détente": ["calme", "relaxant"],
            "romantique": ["romantique", "calme"],
            "voyage": ["motivant", "joyeux"],
            "mélancolie": ["triste", "mélancolique"],
            "réveil": ["énergique", "motivant", "joyeux"],
            "nostalgie": ["mélancolique", "romantique"],
            "danse": ["festif", "énergique", "joyeux"]
        }
        
        for ambiance_key, description in AMBIANCES.items():
            moods_list = ambiance_moods_mapping.get(ambiance_key, [])
            
            self.ambiances[ambiance_key] = {
                "nom": ambiance_key.replace("_", " ").title(),
                "description": description,
                "moods_associes": moods_list,
                "texte_semantique": f"{ambiance_key.replace('_', ' ')} {description}"
            }
    
    def _build_playlists(self):
        """Construit des playlists thématiques"""
        # Playlist par décennie
        decades = [2000, 2010]
        for decade in decades:
            # Extraire l'année depuis track_album_release_date
            df_with_year = self.df_spotify.copy()
            df_with_year['year'] = pd.to_datetime(df_with_year['track_album_release_date'], errors='coerce').dt.year
            
            songs = df_with_year[
                (df_with_year['year'] >= decade) & 
                (df_with_year['year'] < decade + 10)
            ]
            
            if len(songs) > 0:
                playlist_name = f"hits_{decade}s"
                self.playlists[playlist_name] = {
                    "nom": f"Hits des années {decade}",
                    "description": f"Les meilleurs titres des années {decade}",
                    "type": "décennie",
                    "nombre_titres": len(songs),
                    "titres": songs.nlargest(20, 'track_popularity')[
                        ['track_name', 'track_artist', 'playlist_genre', 'track_album_release_date']
                    ].to_dict('records')
                }
        
        # Playlists par mood
        for mood_name, mood_data in self.moods.items():
            if mood_data['chansons_representatives']:
                self.playlists[f"playlist_{mood_name}"] = {
                    "nom": f"Playlist {mood_name.title()}",
                    "description": f"Musiques pour une ambiance {mood_name}",
                    "type": "mood",
                    "mood": mood_name,
                    "nombre_titres": len(mood_data['chansons_representatives']),
                    "titres": mood_data['chansons_representatives'][:15]
                }
        
        # Playlists par énergie
        energy_levels = [
            ("chill", 0, 0.4, "Pour se détendre"),
            ("medium", 0.4, 0.7, "Pour une écoute modérée"),
            ("intense", 0.7, 1.0, "Pour s'énergiser")
        ]
        
        for level_name, min_energy, max_energy, desc in energy_levels:
            songs = self.df_spotify[
                (self.df_spotify['energy'] >= min_energy) & 
                (self.df_spotify['energy'] < max_energy)
            ]
            
            if len(songs) > 0:
                self.playlists[f"energie_{level_name}"] = {
                    "nom": f"Énergie {level_name.title()}",
                    "description": desc,
                    "type": "énergie",
                    "niveau_energie": level_name,
                    "nombre_titres": len(songs),
                    "titres": songs.nlargest(15, 'track_popularity')[
                        ['track_name', 'track_artist', 'playlist_genre', 'track_album_release_date']
                    ].to_dict('records')
                }
    
    def _generate_genre_description(self, genre: str, songs: pd.DataFrame) -> str:
        """Génère une description sémantique pour un genre"""
        avg_energy = songs['energy'].mean()
        avg_valence = songs['valence'].mean()
        
        energy_desc = "énergique" if avg_energy > 0.6 else "calme" if avg_energy < 0.4 else "modéré"
        valence_desc = "joyeux" if avg_valence > 0.6 else "mélancolique" if avg_valence < 0.4 else "neutre"
        
        return f"Genre {genre}, caractère {energy_desc} et {valence_desc}"
    
    def _generate_mood_description(self, mood: str) -> str:
        """Génère une description pour un mood"""
        descriptions = {
            "joyeux": "Musique joyeuse et positive pour remonter le moral",
            "triste": "Musique mélancolique pour accompagner les moments de tristesse",
            "énergique": "Musique dynamique et énergisante pour se motiver",
            "calme": "Musique apaisante pour se relaxer et se détendre",
            "mélancolique": "Musique introspective et émotionnelle",
            "motivant": "Musique motivante pour atteindre ses objectifs",
            "romantique": "Musique douce et romantique pour les moments intimes",
            "festif": "Musique festive pour faire la fête",
            "relaxant": "Musique relaxante pour décompresser",
            "intense": "Musique intense et puissante"
        }
        return descriptions.get(mood, f"Musique de mood {mood}")
    
    def _save_referentiel(self):
        """Sauvegarde le référentiel en JSON"""
        referentiel = {
            "genres": self.genres,
            "artistes": self.artistes,
            "moods": self.moods,
            "ambiances": self.ambiances,
            "playlists": self.playlists,
            "metadata": {
                "total_chansons": len(self.df_spotify),
                "total_genres": len(self.genres),
                "total_artistes": len(self.artistes),
                "total_moods": len(self.moods),
                "total_ambiances": len(self.ambiances),
                "total_playlists": len(self.playlists)
            }
        }
        
        output_path = REFERENTIEL_DIR / "referentiel_musical.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(referentiel, f, ensure_ascii=False, indent=2)
    
    def get_all_semantic_texts(self) -> List[Dict[str, Any]]:
        """Retourne tous les textes sémantiques pour l'embedding"""
        texts = []
        
        # Genres
        for genre_id, genre_data in self.genres.items():
            texts.append({
                "type": "genre",
                "id": genre_id,
                "text": f"{genre_data['nom']} {genre_data['description']}",
                "data": genre_data
            })
        
        # Chansons individuelles par genre (100 par genre)
        for genre_id, genre_data in self.genres.items():
            for chanson in genre_data.get('chansons', []):
                # Créer un texte descriptif pour chaque chanson
                song_text = f"{chanson['track_name']} par {chanson['track_artist']} genre {genre_id}"
                texts.append({
                    "type": "chanson",
                    "id": chanson.get('track_id', f"{genre_id}_{chanson['track_name']}"),
                    "genre": genre_id,
                    "text": song_text,
                    "data": {
                        "nom": chanson['track_name'],
                        "artiste": chanson['track_artist'],
                        "genre": genre_id,
                        "popularite": chanson['track_popularity'],
                        "caracteristiques_moyennes": {
                            "energy": chanson['energy'],
                            "danceability": chanson['danceability'],
                            "valence": chanson['valence'],
                            "acousticness": chanson['acousticness'],
                            "tempo": chanson['tempo'],
                            "loudness": chanson['loudness'],
                            "speechiness": chanson['speechiness'],
                            "instrumentalness": chanson['instrumentalness'],
                            "liveness": chanson['liveness']
                        }
                    }
                })
        
        # Moods
        for mood_id, mood_data in self.moods.items():
            texts.append({
                "type": "mood",
                "id": mood_id,
                "text": f"{mood_data['nom']} {mood_data['description']}",
                "data": mood_data
            })
        
        # Ambiances
        for ambiance_id, ambiance_data in self.ambiances.items():
            texts.append({
                "type": "ambiance",
                "id": ambiance_id,
                "text": ambiance_data['texte_semantique'],
                "data": ambiance_data
            })
        
        # Playlists
        for playlist_id, playlist_data in self.playlists.items():
            texts.append({
                "type": "playlist",
                "id": playlist_id,
                "text": f"{playlist_data['nom']} {playlist_data['description']}",
                "data": playlist_data
            })
        
        return texts
    
    def get_songs_by_criteria(self, criteria: Dict) -> pd.DataFrame:
        """Filtre les chansons selon des critères"""
        filtered = self.df_spotify.copy()
        
        for key, value in criteria.items():
            if key in filtered.columns:
                if isinstance(value, tuple):  # Range (min, max)
                    filtered = filtered[
                        (filtered[key] >= value[0]) & 
                        (filtered[key] <= value[1])
                    ]
                else:
                    filtered = filtered[filtered[key] == value]
        
        return filtered

