<div align="center">

# 🤖 CrowBot

**Le bot Discord ultime — Tout-en-un, puissant et personnalisable**

![Version](https://img.shields.io/badge/version-3.0-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python)
![Discord.py](https://img.shields.io/badge/discord.py-2.0+-5865F2?style=for-the-badge&logo=discord)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

*Musique • Anti-Raid • Casino • Jeux • Tracker • Économie • Dashboard Web*

---

</div>

## 📖 Table des matières

- [✨ Présentation](#-présentation)
- [🎯 Fonctionnalités](#-fonctionnalités)
- [⚙️ Installation](#️-installation)
- [🔑 Configuration](#-configuration)
- [🚀 Lancement](#-lancement)
- [🖥️ Dashboard Web](#️-dashboard-web)
- [📜 Commandes](#-commandes)
- [🛡️ Système Anti-Raid](#️-système-anti-raid)
- [🎵 Système Musique](#-système-musique)
- [🎮 Tracker de jeux](#-tracker-de-jeux)
- [❓ FAQ](#-faq)

---

## ✨ Présentation

**CrowBot** est un bot Discord complet et open-source développé en Python.  
Il regroupe dans un **seul fichier** tout ce dont un serveur Discord a besoin :

- 🛡️ **Protection avancée** contre les raids, le spam et les comportements abusifs
- 🎵 **Lecteur de musique** YouTube & Spotify avec interface graphique
- 🎰 **Casino complet** avec plusieurs jeux d'argent
- 🎮 **Mini-jeux** originaux et innovants
- 📊 **Tracker de stats** pour Valorant, Fortnite, LoL et Apex
- 💰 **Économie complète** avec boutique, travail et crime
- 📈 **Système de niveaux** avec récompenses automatiques
- 🖥️ **Dashboard web** pour gérer le bot depuis ton navigateur
- 🎫 **Tickets de support** avec boutons interactifs
- 🎉 **Giveaways persistants** qui survivent aux redémarrages

---

## 🎯 Fonctionnalités

| Catégorie | Fonctionnalités |
|-----------|----------------|
| 🛡️ **Anti-Raid** | Détection flood, âge de compte, anti-liens, anti-caps, anti-mentions, sanctions progressives |
| 🎵 **Musique** | YouTube, Spotify, playlists, volume, shuffle, skip, barre de progression live |
| 🎰 **Casino** | Slots, Blackjack, Coinflip, Roulette, Dés, Course de chevaux |
| 🎮 **Jeux** | Wordle, TicTacToe, Quiz, Pendu, Akinator, Pierre-Feuille-Ciseaux, Devinettes |
| 📊 **Tracker** | Valorant (rang + stats), Fortnite, League of Legends, Apex Legends |
| 💰 **Économie** | Solde, Daily, Work, Crime, Give, Boutique, Classement |
| 📈 **Niveaux** | XP automatique, level-up, récompenses de rôles, classement |
| 🔨 **Modération** | Ban, Kick, Mute, TempBan, TempMute, Timeout, Warns, Purge, AutoMod |
| 📢 **Communication** | Annonces, Sondages, Suggestions, Tickets, Giveaways |
| ℹ️ **Informations** | Profil serveur, profil membre, avatar, ping, stats bot |
| ✨ **Genshin Impact** | Profil via UID (EnkaNetwork) + builds depuis infographies locales |
| 🖥️ **Dashboard** | Panel web complet pour configurer le bot sans commandes |

---

## ⚙️ Installation

### Prérequis

Avant de commencer, assure-toi d'avoir installé :

- ✅ **Python 3.10 ou supérieur** → [python.org](https://www.python.org/downloads/)
- ✅ **FFmpeg** (obligatoire pour la musique)
- ✅ **Git** (optionnel mais recommandé)

---

### 1. Cloner le projet

```bash
git clone https://github.com/ton-pseudo/crowbot.git
cd crowbot
Ou télécharge le fichier bot.py directement et place-le dans un dossier.

2. Installer FFmpeg
FFmpeg est obligatoire pour la lecture de musique.

<details> <summary>🪟 Windows</summary>
Option A — Chocolatey (recommandé) :

Bash

choco install ffmpeg
Option B — Manuel :

Télécharge FFmpeg sur ffmpeg.org/download.html
Extrais l'archive
Copie le chemin du dossier bin
Ajoute ce chemin dans tes variables d'environnement (PATH)
Vérifie l'installation :

Bash

ffmpeg -version
</details><details> <summary>🐧 Linux / Ubuntu</summary>
Bash

sudo apt update
sudo apt install ffmpeg -y
</details><details> <summary>🍎 macOS</summary>
Bash

brew install ffmpeg
</details>
3. Installer les dépendances Python
Bash

pip install discord.py yt-dlp PyNaCl aiohttp python-dotenv spotipy flask
Ou si tu as un fichier requirements.txt :

Bash

pip install -r requirements.txt
<details> <summary>📄 Contenu du requirements.txt</summary>
text

discord.py>=2.3.0
yt-dlp>=2024.1.0
PyNaCl>=1.5.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
spotipy>=2.23.0
flask>=3.0.0
</details>
4. Créer le bot Discord
Va sur discord.com/developers/applications
Clique sur "New Application" → donne un nom (ex: CrowBot)
Va dans l'onglet "Bot"
Clique sur "Add Bot" puis "Yes, do it!"
Sous le nom du bot, clique sur "Reset Token" et copie le token
Active les Privileged Intents :
✅ Server Members Intent
✅ Message Content Intent
✅ Presence Intent
Va dans "OAuth2" → "URL Generator"
Coche bot et applications.commands
Permissions recommandées : Administrator
Copie le lien généré et invite le bot sur ton serveur
🔑 Configuration
Crée un fichier .env à la racine du projet :

env

# ═══════════════════════════════════
#  OBLIGATOIRE
# ═══════════════════════════════════

DISCORD_TOKEN=ton_token_discord_ici


# ═══════════════════════════════════
#  DASHBOARD WEB
# ═══════════════════════════════════

DASHBOARD_SECRET=une_cle_secrete_aleatoire_longue
DASHBOARD_ADMIN_PASS=ton_mot_de_passe_dashboard
DASHBOARD_PORT=5000


# ═══════════════════════════════════
#  SPOTIFY (optionnel, pour la musique Spotify)
# ═══════════════════════════════════

SPOTIFY_CLIENT_ID=ton_client_id_spotify
SPOTIFY_CLIENT_SECRET=ton_client_secret_spotify


# ═══════════════════════════════════
#  TRACKER DE JEUX (optionnel)
# ═══════════════════════════════════

# Valorant → https://docs.henrikdev.xyz/
HENRIK_API_KEY=HDEV-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# League of Legends → https://developer.riotgames.com/
RIOT_API_KEY=RGAPI-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Apex Legends → https://apexlegendsapi.com/
APEX_API_KEY=ta_cle_apex_ici

# Fortnite → Aucune clé requise !
Comment obtenir les clés API
Service	Lien	Gratuit ?	Notes
Discord Token	developer portal	✅	Obligatoire
Spotify	developer.spotify.com	✅	Pour jouer les liens Spotify
Valorant (Henrik)	docs.henrikdev.xyz	✅	Clé gratuite sur leur Discord
LoL (Riot)	developer.riotgames.com	✅	Clé dev valable 24h, renouvelable
Apex	apexlegendsapi.com	✅	Inscription rapide
Fortnite	—	✅	Aucune clé requise
Structure des dossiers
text

crowbot/
│
├── bot.py                 ← Fichier principal du bot
├── .env                   ← Tes tokens et clés API (ne jamais partager !)
├── requirements.txt       ← Dépendances Python
│
├── data/                  ← Créé automatiquement au premier lancement
│   ├── xp.json            ← Données XP et niveaux
│   ├── economy.json       ← Soldes des membres
│   ├── warns.json         ← Avertissements
│   ├── shop.json          ← Articles de la boutique
│   ├── giveaways.json     ← Giveaways en cours
│   ├── antiraid.json      ← Configuration anti-raid par serveur
│   ├── logs.json          ← Configuration des logs
│   ├── welcome.json       ← Messages de bienvenue
│   └── ...
│
└── builds/                ← (Optionnel) Images de builds Genshin
    ├── raiden.png
    ├── ayaka.png
    └── ...
⚠️ Ne partage JAMAIS ton fichier .env — il contient ton token Discord.
Ajoute .env dans ton .gitignore si tu utilises Git.

🚀 Lancement
Bash

python bot.py
Si tout est correct, tu verras dans la console :

text

🌐 Dashboard démarré sur http://localhost:5000
🔑 Mot de passe: ton_mot_de_passe
✅ Bot prêt : CrowBot#1234
   XX slash commands
💡 Conseil : Pour garder le bot actif en permanence, utilise screen, tmux, pm2 ou un hébergeur comme Railway, DigitalOcean ou un VPS.

🖥️ Dashboard Web
CrowBot inclut un panel d'administration web accessible depuis ton navigateur.

Accès : http://localhost:5000
Mot de passe : celui défini dans DASHBOARD_ADMIN_PASS

Pages disponibles
Page	Description
🏠 Accueil	Vue d'ensemble : serveurs, membres, latence, uptime, musique en cours
🌍 Serveurs	Liste des serveurs avec statut anti-raid et musique
💰 Économie	Classement des 20 membres les plus riches
📈 XP	Classement XP avec barres de progression
🛡️ Modération	Membres les plus warnés, tickets actifs, actions temp
⚙️ Paramètres	Configurer l'Anti-Raid, ajouter des pièces, effacer des warns
API REST
Le dashboard expose également une API JSON :

text

GET  /api/stats              → Statistiques globales du bot
GET  /api/antiraid/<guild_id> → Config anti-raid d'un serveur
POST /api/antiraid/<guild_id> → Modifier la config anti-raid
📜 Commandes
Toutes les commandes utilisent le système Slash Commands (/).

🛡️ Anti-Raid
Commande	Description	Permission
/antiraid setup	Configurer la détection de raid (seuil, action, âge compte)	Admin
/antiraid automod	Anti-liens, anti-caps, anti-mentions, anti-emoji spam	Admin
/antiraid whitelist	Ajouter/retirer un rôle de la whitelist AutoMod	Admin
/antiraid status	Voir la configuration actuelle	Manage Guild
/antiraid unlock	Déverrouiller le serveur après un raid	Admin
/antiraid infractions	Voir les infractions AutoMod d'un membre	Manage Guild
/antiraid reset_infractions	Réinitialiser les infractions d'un membre	Admin
🔨 Administration
Commande	Description	Permission
/admin ban	Bannir un membre	Ban Members
/admin unban	Débannir par ID	Ban Members
/admin kick	Expulser un membre	Kick Members
/admin timeout	Timeout Discord natif	Moderate Members
/admin mute	Muter via rôle Muted	Manage Roles
/admin unmute	Démuter	Manage Roles
/admin tempmute	Muter temporairement (ex: 10m, 2h)	Manage Roles
/admin tempban	Bannir temporairement	Ban Members
/admin warn	Avertir un membre	Kick Members
/admin warns	Voir les warns d'un membre	Kick Members
/admin clearwarn	Effacer les warns	Admin
/admin purge	Supprimer jusqu'à 100 messages	Manage Messages
/admin purge_user	Supprimer les messages d'un utilisateur	Manage Messages
/admin setlogs	Définir le salon des logs	Admin
/admin setwelcome	Configurer le message de bienvenue	Admin
/admin setautorole	Rôle automatique à l'arrivée	Admin
/admin slowmode	Définir le slowmode	Manage Channels
/admin lock	Verrouiller le salon	Manage Channels
/admin unlock	Déverrouiller le salon	Manage Channels
/admin addrole	Donner un rôle	Manage Roles
/admin removerole	Retirer un rôle	Manage Roles
/admin massrole	Donner un rôle à tous les membres	Admin
/admin nickname	Changer le pseudo d'un membre	Manage Nicknames
/admin stats_mod	Statistiques de modération	Manage Guild
📈 Niveaux & XP
Commande	Description
/level rank	Voir ton niveau et ta progression
/level leaderboard	Top 10 des membres les plus actifs
/level setreward	Attribuer un rôle à un niveau (Admin)
/level addxp	Ajouter de l'XP à un membre (Admin)
/level setlevel	Définir le niveau d'un membre (Admin)
💡 L'XP est gagné automatiquement en envoyant des messages (5 à 15 XP aléatoire par message).

💰 Économie
Commande	Description	Cooldown
/eco solde	Voir son solde (ou celui d'un membre)	—
/eco daily	Récupérer 100-500 🪙	24h
/eco work	Travailler pour gagner 50-200 🪙	1h
/eco crime	Tenter un crime risqué pour 200-800 🪙	2h
/eco give	Donner des pièces à un membre	—
/eco leaderboard	Top 10 des plus riches	—
/eco addmoney	Ajouter des pièces (Admin)	—
/eco removemoney	Retirer des pièces (Admin)	—
🛒 Boutique
Commande	Description	Permission
/shop add	Ajouter un rôle en vente	Admin
/shop remove	Retirer un article	Admin
/shop list	Voir les articles disponibles	—
/shop buy	Acheter un article	—
🎰 Casino
Commande	Description
/casino slots	Machine à sous (jusqu'à ×50 la mise !)
/casino blackjack	Blackjack interactif avec boutons
/casino coinflip	Pile ou face
/casino roulette	Roulette (rouge, noir, pair, impair, numéro)
/casino dice	Dés (haut = 4-6 / bas = 1-3)
/casino horse	Course de chevaux avec animation !
🎮 Mini-Jeux
Commande	Description	Récompense
/game quiz	Quiz interactif avec 4 choix	+75 🪙
/game wordle	Devine un mot de 5 lettres en 6 essais	+50-300 🪙
/game wordle_guess	Proposer un mot au Wordle	—
/game tictactoe	Tic-Tac-Toe contre un autre membre	+100 🪙
/game pendu	Jeu du pendu	+100 🪙
/game deviner	Deviner une lettre au pendu	—
/game nombre	Devine un nombre entre 1 et 100	+20-100 🪙
/game shifumi	Pierre, Feuille, Ciseaux	+25 🪙
/game akinator	Devine le personnage mystère	+100 🪙
/game akindice	Obtenir un indice pour l'Akinator	—
/game akinreponse	Donner ta réponse	—
/game devinette	Répondre à une devinette	+50 🪙
/game trivia_score	Voir ton score de quiz	—
🎵 Musique
Commande	Description
/music play	Jouer une musique (YouTube, Spotify, recherche)
/music playlist	Charger une playlist YouTube entière
/music pause	Mettre en pause
/music resume	Reprendre la lecture
/music skip	Passer à la prochaine musique
/music stop	Stopper et vider la file
/music leave	Déconnecter le bot
/music queue	Voir la file d'attente
/music nowplaying	Voir la musique en cours avec progression
/music volume	Régler le volume (0-200%)
/music shuffle	Mélanger la file
/music restore	Réinitialiser complètement la musique (Admin)
🎵 Formats supportés : Liens YouTube, recherche YouTube, playlists YouTube, liens Spotify (convertis automatiquement en recherche YouTube).

📊 Tracker de jeux
Commande	Description	Clé requise
/tracker valorant	Rang, ELO, RR, pic de rang	HENRIK_API_KEY
/tracker valorant_stats	K/D, Win Rate, agent favori (20 derniers matchs)	HENRIK_API_KEY
/tracker fortnite	Wins, K/D, WR, stats Solo/Duo/Squad	❌ Aucune
/tracker lol	SoloQ, FlexQ, LP, Win Rate, Hot Streak	RIOT_API_KEY
/tracker apex	Rang BR, légende, stats temps réel	APEX_API_KEY
✨ Genshin Impact
Commande	Description
/genshin profile	Profil d'un joueur via son UID (EnkaNetwork)
/genshin build	Infographie de build (images locales dans builds/)
💡 Pour /genshin build, place tes images PNG dans un dossier builds/ à côté de bot.py.
Ex: builds/raiden.png, builds/ayaka.png, etc.

📢 Communication
Commande	Description	Permission
/annonce	Créer une annonce stylée avec modal	Manage Guild
/poll	Créer un sondage (oui/non ou choix multiples)	—
/suggestion	Envoyer une suggestion avec vote	—
/giveaway	Créer un giveaway avec modal	Manage Guild
/greroll	Relancer un giveaway	Manage Guild
/ticket	Placer le panel de tickets	Admin
😄 Fun & Utilitaires
Commande	Description
/fun 8ball	La boule magique répond à ta question
/fun citation	Citation inspirante aléatoire
/fun blague	Blague aléatoire (réponse en spoiler)
/fun choose	Choisir aléatoirement entre des options
/fun roll	Lancer un dé (D6 par défaut, jusqu'à D1000)
/fun timer	Minuteur avec notification (max 24h)
/fun encode	Encoder en Base64
/fun decode	Décoder du Base64
/fun morse	Convertir en code Morse
/fun password	Générer un mot de passe sécurisé
/fun urban	Définition Urban Dictionary
/fun catfact	Fait aléatoire sur les chats 🐱
ℹ️ Informations
Commande	Description
/serverinfo	Informations complètes sur le serveur
/userinfo	Profil d'un membre (niveau, solde, rôles…)
/avatar	Voir l'avatar en grand format
/ping	Latence du bot
/botinfo	Stats du bot (uptime, serveurs, chansons jouées…)
/help	Liste complète des commandes
🛡️ Système Anti-Raid
CrowBot inclut un système anti-raid complet configurable par commande ou depuis le dashboard.

Fonctionnement
text

Membre rejoint
      │
      ├─ Âge du compte < minimum ?  → Kick/Ban automatique
      │
      └─ Trop de joins en peu de temps ?
            │
            ├─ Action: LOCK   → Verrouille tous les salons 30s
            ├─ Action: KICK   → Expulse les nouveaux membres
            └─ Action: BAN    → Bannit les nouveaux membres
AutoMod — Sanctions progressives
Infractions	Sanction
1	Avertissement + suppression du message
2	Mute temporaire (60 secondes)
3	Timeout Discord (10 minutes)
5+	Ban automatique
Les infractions diminuent de 1 par jour automatiquement (amnistie progressive).

Filtres disponibles
🔗 Anti-liens — Bloque tous les URLs
🔡 Anti-caps — Limite les messages en majuscules (seuil configurable en %)
📣 Anti-mention spam — Limite les mentions par message
😂 Anti-emoji spam — Limite les emojis par message
🏠 Whitelist rôles — Certains rôles sont exemptés de l'AutoMod
👶 Âge minimum — Rejette les comptes Discord trop récents
🎵 Système Musique
Utilisation basique
text

/music play rickroll            ← Recherche YouTube
/music play https://youtu.be/…  ← Lien direct
/music play https://open.spotify.com/track/…  ← Lien Spotify
/music playlist https://youtube.com/playlist?list=…  ← Playlist complète
Interface graphique
Quand une musique est en lecture, un embed s'affiche avec :

🎵 Titre cliquable
▬▬▬🔘▬▬ Barre de progression en temps réel
⏯️ Bouton Pause/Resume
⏭️ Bouton Skip
⏹️ Bouton Stop
🎮 Tracker de jeux
Valorant
text

/tracker valorant TonPseudo EUW
/tracker valorant_stats TonPseudo EUW competitive
Affiche : Rang actuel, ELO, RR, variation du dernier match, pic de rang, K/D, Win Rate, agent favori.

Fortnite
text

/tracker fortnite TonPseudo epic
Affiche : Victoires, K/D, Win Rate, kills/partie, heures jouées, stats Solo/Duo/Squad.
Aucune clé API requise !

League of Legends
text

/tracker lol TonPseudo euw 1234
Affiche : SoloQ et FlexQ avec rang, LP, W/L, Win Rate, Hot Streak, Vétéran.

Apex Legends
text

/tracker apex TonPseudo PC
Affiche : Rang BR, niveau, légende sélectionnée, stats en temps réel, statut en ligne.

❓ FAQ
<details> <summary><b>Le bot ne répond pas aux commandes slash</b></summary>
Les commandes slash peuvent prendre jusqu'à 1 heure à apparaître après le premier lancement.
Pour forcer la synchronisation, redémarre le bot. Si ça persiste, vérifie que le bot a la permission applications.commands.

</details><details> <summary><b>La musique ne fonctionne pas</b></summary>
Vérifie que FFmpeg est installé : ffmpeg -version
Assure-toi que le bot a la permission de rejoindre et parler dans les salons vocaux
Essaie /music restore pour réinitialiser le système
</details><details> <summary><b>Le dashboard ne s'ouvre pas</b></summary>
Vérifie que le port 5000 n'est pas déjà utilisé
Change le port dans .env : DASHBOARD_PORT=8080
Sur un VPS, ouvre le port dans le pare-feu : ufw allow 5000
</details><details> <summary><b>Les données sont perdues au redémarrage</b></summary>
Les données importantes (XP, économie, warns, giveaways, anti-raid) sont sauvegardées automatiquement dans le dossier data/. Ce dossier est créé au premier lancement. Ne le supprime pas !

</details><details> <summary><b>Comment garder le bot actif 24h/24 ?</b></summary>
Sur un VPS Linux avec screen :

Bash

screen -S crowbot
python bot.py
# Ctrl+A puis D pour détacher
Avec pm2 :

Bash

npm install -g pm2
pm2 start bot.py --interpreter python3
pm2 save
Hébergeurs compatibles : Railway, Render, DigitalOcean, Oracle Cloud (gratuit).

</details><details> <summary><b>Comment ajouter des builds Genshin ?</b></summary>
Crée un dossier builds/ à côté de bot.py
Place tes images PNG dedans en les nommant selon le personnage
Exemples : raiden.png, ayaka.png, hu-tao.png, yae-miko.png
Utilise /genshin build raiden pour afficher l'image
</details>
<div align="center">
CrowBot — Fait avec ❤️ en Python

Si tu as des problèmes ou des suggestions, ouvre une issue sur GitHub.

</div> ```
