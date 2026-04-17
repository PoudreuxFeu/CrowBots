# 🐦 CrowBot - Le Bot Discord Tout-en-Un

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**CrowBot** est un bot Discord polyvalent et puissant écrit en Python. Il combine des fonctionnalités de musique avancées, un système de casino complet, des outils de modération, une protection Anti-Raid et même un Dashboard Web intégré.

---

## 🚀 Fonctionnalités principales

### 🎵 Musique
* **Support complet** : Lecture depuis YouTube et Spotify.
* **Contrôles intuitifs** : `play`, `skip`, `stop`, `queue`, `nowplaying`.
* **Qualité** : Utilisation de `yt-dlp` pour une extraction audio stable.

### 🎰 Casino & Économie
* **Jeux** : `blackjack`, `slots` (machine à sous), `roulette`, `coinflip`.
* **Système quotidien** : Récupérez vos jetons chaque jour avec `/daily`.
* **Classement** : Affichez les utilisateurs les plus riches avec `/leaderboard`.

### 🛡️ Modération & Sécurité (Anti-Raid)
* **Outils classiques** : `kick`, `ban`, `clear`, `mute/unmute`.
* **Système Anti-Raid** : 
    * Verrouillage de salon (`lock/unlock`).
    * Protection contre le spam de mentions.
    * Détection de comptes trop récents.
    * Limitation de l'envoi de liens.

### 📊 Dashboard Web
* Interface d'administration via **Flask**.
* Statistiques en temps réel du bot (latence, serveurs, musique en cours).
* Configuration de l'Anti-Raid directement depuis le navigateur.

### 🎮 Jeux & Utilitaires
* **Stats de jeux** : Tracker pour **Apex Legends**, **Fortnite** et **Valorant**.
* **Fun** : `8ball`, `meme`, `userinfo`.

---

## 🛠️ Installation

### 1. Prérequis
Assurez-vous d'avoir Python 3.8+ installé. FFmpeg est également requis pour la partie musique.

### 2. Cloner le projet
```bash
git clone [https://github.com/votre-utilisateur/crowbot.git](https://github.com/votre-utilisateur/crowbot.git)
cd crowbot
3. Installer les dépendancesBashpip install discord.py yt-dlp PyNaCl aiohttp python-dotenv spotipy flask flask-login
4. Configuration (.env)Créez un fichier .env à la racine du projet et remplissez vos clés :Extrait de codeVOTRE_TOKEN=ton_discord_bot_token
DASHBOARD_SECRET=une_cle_secrete_aleatoire
DASHBOARD_PORT=5000

# API Keys (Optionnel pour les trackers)
HENRIK_API_KEY=ta_cle_valorant
APEX_API_KEY=ta_cle_apex
FORTNITE_API_KEY=ta_cle_fortnite

# Spotify (Pour la lecture de playlists)
SPOTIPY_CLIENT_ID=ton_id
SPOTIPY_CLIENT_SECRET=ton_secret

```
🚦 LancementLancer le bot :Bashpython crowbot.py
Accéder au Dashboard :Rendez-vous sur http://localhost:5000 (ou l'IP de votre VPS).📋 Commandes Slash (Exemples)CatégorieCommandeDescriptionMusique/play [nom/url]Joue une musique ou une playlistCasino/blackjack [mise]Lance une partie de BlackjackModération/ban [membre]Bannit un utilisateur du serveurAnti-Raid/antiraid setupConfigure les protections automatiquesJeux/tracker_apex [pseudo]Affiche les stats d'un joueur Apex🗄️ Structure du Projetcrowbot.py : Le cœur du bot (Commandes, Events, Dashboard).antiraid_config.json : Stockage de la configuration de sécurité.casino_data.json : Base de données de l'économie.templates/ : Fichiers HTML pour le Dashboard Flask.⚠️ Notes importantesFFmpeg : Pour que la musique fonctionne, ffmpeg doit être installé sur votre système et ajouté au PATH.Permissions : Le bot nécessite les privilèges "Administrator" et les "Intents" (Message Content, Guild Members) activés sur le portail développeur Discord.Développé avec ❤️ par CrowBot Team
