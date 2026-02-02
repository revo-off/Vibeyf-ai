# Configuration de l'API Spotify

## Pourquoi Spotify API ?

L'API Spotify permet de récupérer les **images des albums** pour chaque recommandation musicale. Sans ces credentials, l'application utilisera des images placeholder génériques.

## Comment obtenir vos credentials Spotify (gratuit)

### Étape 1: Créer un compte développeur Spotify

1. Allez sur [Spotify for Developers](https://developer.spotify.com/dashboard)
2. Connectez-vous avec votre compte Spotify (ou créez-en un gratuitement)

### Étape 2: Créer une application

1. Cliquez sur **"Create app"**
2. Remplissez les informations:
   - **App name**: `Vibeyf-AI` (ou le nom de votre choix)
   - **App description**: `Application de recommandation musicale`
   - **Redirect URIs**: `http://localhost:8000` (pas utilisé mais obligatoire)
   - **APIs used**: Cochez `Web API`
3. Acceptez les conditions d'utilisation
4. Cliquez sur **"Save"**

### Étape 3: Récupérer vos credentials

1. Une fois l'app créée, cliquez dessus dans votre Dashboard
2. Cliquez sur **"Settings"**
3. Vous verrez:
   - **Client ID**: Une chaîne de caractères (ex: `a1b2c3d4e5f6g7h8i9j0`)
   - **Client Secret**: Cliquez sur "View client secret" pour l'afficher

### Étape 4: Configurer votre application

1. Copiez le fichier `.env.example` vers `.env`:
   ```bash
   copy .env.example .env
   ```

2. Éditez le fichier `.env` et ajoutez vos credentials:
   ```env
   SPOTIFY_CLIENT_ID=votre_client_id_ici
   SPOTIFY_CLIENT_SECRET=votre_client_secret_ici
   ```

3. **IMPORTANT**: Ne partagez jamais votre fichier `.env` ou vos credentials !

### Étape 5: Tester

Relancez votre application. Les images des albums devraient maintenant s'afficher dans les recommandations !

## Fonctionnement sans credentials

Si vous ne configurez pas l'API Spotify, l'application fonctionnera quand même mais affichera des images placeholder génériques (🎵) à la place des vraies pochettes d'album.

## Limites de l'API gratuite

- **Taux limite**: 180 requêtes par minute
- **Pas de limite mensuelle** pour l'authentification Client Credentials
- Parfait pour une utilisation personnelle ou de développement

## Ressources

- [Documentation Spotify API](https://developer.spotify.com/documentation/web-api)
- [Guide d'authentification](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow)
- [Dashboard Spotify Developers](https://developer.spotify.com/dashboard)
