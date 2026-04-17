# 🤖 CrowBot
**Le bot Discord ultime — Tout-en-un, puissant et personnalisable**

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3%2B-orange)
![License](https://img.shields.io/badge/License-MIT-red)

> Musique • Anti-Raid • Casino • Jeux • Tracker • Économie • Dashboard Web

---

## 📖 Table des matières
* [✨ Présentation](#-présentation)
* [🎯 Fonctionnalités](#-fonctionnalités)
* [⚙️ Installation](#-installation)
* [🔑 Configuration](#-configuration)
* [🚀 Lancement](#-lancement)
* [🖥️ Dashboard Web](#-dashboard-web)
* [📜 Commandes](#-commandes)
* [🛡️ Système Anti-Raid](#-système-anti-raid)
* [🎵 Système Musique](#-système-musique)
* [🎮 Tracker de jeux](#-tracker-de-jeux)
* [❓ FAQ](#-faq)

---

## ✨ Présentation
CrowBot est un bot Discord complet et open-source développé en Python. Il regroupe dans un seul fichier tout ce dont un serveur Discord a besoin.

* 🛡️ **Protection avancée** contre les raids, le spam et les comportements abusifs
* 🎵 **Lecteur de musique** YouTube et Spotify avec interface graphique
* 🎰 **Casino complet** avec plusieurs jeux d'argent
* 🎮 **Mini-jeux originaux** et innovants
* 📊 **Tracker de stats** pour Valorant, Fortnite, LoL et Apex
* 💰 **Économie complète** avec boutique, travail et crime
* 📈 **Système de niveaux** avec récompenses automatiques
* 🖥️ **Dashboard web** pour gérer le bot depuis ton navigateur
* 🎫 **Tickets de support** avec boutons interactifs
* 🎉 **Giveaways persistants** qui survivent aux redémarrages

---

## 🎯 Fonctionnalités

| Catégorie | Fonctionnalités |
| :--- | :--- |
| **🛡️ Anti-Raid** | Détection flood, âge de compte, anti-liens, anti-caps, anti-mentions, sanctions progressives |
| **🎵 Musique** | YouTube, Spotify, playlists, volume, shuffle, skip, barre de progression live |
| **🎰 Casino** | Slots, Blackjack, Coinflip, Roulette, Dés, Course de chevaux |
| **🎮 Jeux** | Wordle, TicTacToe, Quiz, Pendu, Akinator, Pierre-Feuille-Ciseaux, Devinettes |
| **📊 Tracker** | Valorant, Fortnite, League of Legends, Apex Legends |
| **💰 Économie** | Solde, Daily, Work, Crime, Give, Boutique, Classement |
| **📈 Niveaux** | XP automatique, level-up, récompenses de rôles, classement |
| **🔨 Modération** | Ban, Kick, Mute, TempBan, TempMute, Timeout, Warns, Purge, AutoMod |
| **📢 Communication** | Annonces, Sondages, Suggestions, Tickets, Giveaways |
| **✨ Genshin Impact** | Profil via UID et builds depuis infographies locales |
| **🖥️ Dashboard** | Panel web complet pour configurer le bot sans commandes |

---

## ⚙️ Installation

### Prérequis
Avant de commencer, assure-toi d'avoir installé ces trois choses sur ta machine.

1. **Python 3.10 ou supérieur** Télécharge-le sur [python.org](https://www.python.org/downloads/) et coche bien la case "Add Python to PATH" pendant l'installation.

2. **FFmpeg** (Obligatoire pour la musique)
   * **Windows (Chocolatey)** : `choco install ffmpeg`
   * **Linux** : `sudo apt install ffmpeg`
   * **macOS** : `brew install ffmpeg`
   * *Vérification* : Tape `ffmpeg -version` dans ton terminal.

3. **Git** (optionnel mais recommandé)
   Télécharge-le sur [git-scm.com](https://git-scm.com/)

### Étape 1 — Récupérer le bot
```bash
git clone [[https://github.com/PoudreuxFeu/CrowBots.git]](https://github.com/PoudreuxFeu/CrowBots.git)
cd crowbots
```
*(Sinon, télécharge simplement le fichier `bot.py` et place-le dans un dossier vide.)*

### Étape 2 — Installer les dépendances Python
```bash
pip install discord.py yt-dlp PyNaCl aiohttp python-dotenv spotipy flask flask-login
```

### Étape 3 — Créer le bot sur Discord
1. Va sur [discord.com/developers/applications](https://discord.com/developers/applications)
2. Clique sur "New Application" et nomme-la **CrowBot**
3. Onglet **Bot** : Clique sur "Add Bot"
4. Clique sur "Reset Token", copie-le et garde-le précieusement
5. Active les options : **Server Members Intent**, **Message Content Intent**, **Presence Intent**
6. Onglet **OAuth2** -> **URL Generator** : Coche `bot` et `applications.commands`
7. Permissions : Coche `Administrator`, copie le lien et invite le bot sur ton serveur

---

## 🔑 Configuration
Crée un fichier nommé `.env` dans le même dossier que `bot.py` :

```env
DISCORD_TOKEN=colle_ton_token_ici
DASHBOARD_SECRET=mets_nimporte_quelle_longue_chaine_aleatoire_ici
DASHBOARD_ADMIN_PASS=ton_mot_de_passe_pour_le_dashboard
DASHBOARD_PORT=5000
SPOTIFY_CLIENT_ID=optionnel
SPOTIFY_CLIENT_SECRET=optionnel
HENRIK_API_KEY=optionnel_pour_valorant
RIOT_API_KEY=optionnel_pour_lol
APEX_API_KEY=optionnel_pour_apex
```

### Où obtenir les clés optionnelles
| Service | Site | Gratuit |
| :--- | :--- | :--- |
| **Spotify** | developer.spotify.com/dashboard | Oui |
| **Valorant** | docs.henrikdev.xyz | Oui |
| **LoL** | developer.riotgames.com | Oui |
| **Apex** | apexlegendsapi.com | Oui |

---

## 🚀 Lancement
Dans ton terminal :
```bash
python bot.py
```
Si tout fonctionne :
```text
🌐 Dashboard démarré sur http://localhost:5000
🔑 Mot de passe: ton_mot_de_passe
✅ Bot prêt : CrowBot#1234
```
*Note : Les commandes slash peuvent mettre jusqu'à une heure à apparaître la première fois.*

---

## 🖥️ Dashboard Web
Ouvre ton navigateur sur `http://localhost:5000`. Connecte-toi avec le mot de passe défini dans ton `.env`.

* **Accueil** : Latence, uptime, musique en cours.
* **Serveurs** : Statut Anti-Raid par serveur.
* **Économie & XP** : Classements complets.
* **Modération** : Gestion des warns et tickets.

---

## 📜 Commandes

### 🛡️ Anti-Raid
| Commande | Description | Permission |
| :--- | :--- | :--- |
| `/antiraid setup` | Configurer la détection de raid | Admin |
| `/antiraid automod` | Anti-liens, anti-caps, anti-mentions | Admin |
| `/antiraid whitelist` | Ajouter un rôle à la whitelist | Admin |
| `/antiraid status` | Voir la configuration actuelle | Manage Guild |

### 🔨 Modération
| Commande | Description | Permission |
| :--- | :--- | :--- |
| `/admin ban` | Bannir un membre | Ban Members |
| `/admin timeout` | Timeout Discord natif | Moderate Members |
| `/admin clearwarn` | Effacer les warns | Admin |
| `/admin purge` | Supprimer des messages | Manage Messages |

### 💰 Économie & Casino
* `/eco solde`, `/eco daily`, `/eco work`, `/eco crime`.
* `/casino slots`, `/casino blackjack`, `/casino roulette`, `/casino horse`.

### 🎵 Musique
* `/music play`, `/music skip`, `/music stop`, `/music queue`, `/music nowplaying`.

---

## 🛡️ Système Anti-Raid
CrowBot surveille l'âge du compte et le flux de nouveaux membres.
1. **Âge du compte** : Expulsion automatique si le compte est trop récent.
2. **Détection Raid** : Si trop de membres rejoignent, le bot passe en mode Lock, Kick ou Ban selon réglage.

**Sanctions AutoMod :**
* 1 Infraction : Avertissement
* 2 Infractions : Mute 60s
* 3 Infractions : Timeout 10m
* 5 Infractions : Ban automatique

---

## 🎮 Tracker de jeux
* **Valorant** : `/tracker valorant [pseudo]#[tag]`
* **Fortnite** : `/tracker fortnite [pseudo]`
* **LoL** : `/tracker lol [RiotID]#[tag]`
* **Apex** : `/tracker apex [pseudo]`

---

## ❓ FAQ
**Commandes invisibles ?** Attends 1h ou redémarre Discord.  
**Musique HS ?** Vérifie FFmpeg avec `ffmpeg -version`.  
**Dashboard inaccessible ?** Vérifie que le port 5000 est libre.  
**Données perdues ?** Ne supprime jamais le dossier `data/`.

---
*Développé par l'équipe CrowBot. Merci d'utiliser notre outil !*
