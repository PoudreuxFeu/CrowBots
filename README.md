# 🤖 CrowBot
**Le bot Discord ultime — Tout-en-un, puissant et personnalisable**

![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![Discord.py](https://img.shields.io/badge/Discord.py-2.3%2B-orange)
![License](https://img.shields.io/badge/License-MIT-red)

> Musique • Anti-Raid • Casino • Jeux • Tracker • Économie • Dashboard Web

---

## 📖 Table des matières
1. [✨ Présentation](#-présentation)
2. [🎯 Fonctionnalités](#-fonctionnalités)
3. [⚙️ Installation](#-installation)
4. [🔑 Configuration](#-configuration)
5. [🚀 Lancement](#-lancement)
6. [🖥️ Dashboard Web](#-dashboard-web)
7. [📜 Commandes](#-commandes)
8. [🛡️ Système Anti-Raid](#-système-anti-raid)
9. [🎵 Système Musique](#-système-musique)
10. [🎮 Tracker de jeux](#-tracker-de-jeux)
11. [❓ FAQ](#-faq)

---

## ✨ Présentation
**CrowBot** est un bot Discord complet et open-source développé en Python. Il regroupe dans un seul fichier tout ce dont un serveur Discord a besoin.

* 🛡️ **Protection avancée** contre les raids, le spam et les comportements abusifs.
* 🎵 **Lecteur de musique** YouTube et Spotify avec interface graphique.
* 🎰 **Casino complet** avec plusieurs jeux d'argent.
* 🎮 **Mini-jeux originaux** et innovants.
* 📊 **Tracker de stats** pour Valorant, Fortnite, LoL et Apex.
* 💰 **Économie complète** avec boutique, travail et crime.
* 📈 **Système de niveaux** avec récompenses automatiques.
* 🖥️ **Dashboard web** pour gérer le bot depuis ton navigateur.
* 🎫 **Tickets de support** avec boutons interactifs.
* 🎉 **Giveaways persistants** qui survivent aux redémarrages.

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
| **🖥️ Dashboard** | Panel web complet pour configurer le bot sans commandes |

---

## ⚙️ Installation

### Prérequis
* **Python 3.10 ou supérieur**
* **FFmpeg** (Obligatoire pour la musique) :
    * *Windows* : `choco install ffmpeg`
    * *Linux* : `sudo apt install ffmpeg`
* **Git** (Optionnel)

### Étape 1 — Récupérer le bot
```bash
git clone [https://github.com/ton-pseudo/crowbot.git](https://github.com/ton-pseudo/crowbot.git)
cd crowbot
```

### Étape 2 — Installer les dépendances
```bash
pip install discord.py yt-dlp PyNaCl aiohttp python-dotenv spotipy flask flask-login
```

### Étape 3 — Créer le bot sur Discord
1.  Va sur [Discord Developers](https://discord.com/developers/applications).
2.  Crée une application, va dans l'onglet **Bot**.
3.  Active les **Privileged Gateway Intents** (Members, Presence, Message Content).
4.  Récupère ton **Token**.

---

## 🔑 Configuration
Crée un fichier `.env` à la racine :
```env
DISCORD_TOKEN=votre_token_ici
DASHBOARD_SECRET=cle_aleatoire
DASHBOARD_ADMIN_PASS=votre_mot_de_passe
DASHBOARD_PORT=5000
```

---

## 🚀 Lancement
```bash
python crowbot.py
```
Le bot affichera l'URL du Dashboard (par défaut `http://localhost:5000`).

---

## 📜 Commandes (Extraits)

### 🛡️ Anti-Raid
| Commande | Description | Permission |
| :--- | :--- | :--- |
| `/antiraid setup` | Configurer la détection de raid | Admin |
| `/antiraid status` | Voir la configuration actuelle | Manage Guild |
| `/antiraid unlock` | Déverrouiller le serveur | Admin |

### 🎵 Musique
| Commande | Description |
| :--- | :--- |
| `/music play` | Jouer une musique (YouTube/Spotify) |
| `/music queue` | Voir la file d'attente |
| `/music nowplaying` | Barre de progression en direct |

*(Consultez l'aide en jeu `/help` pour la liste complète des 100+ commandes)*

---

## 🛡️ Système Anti-Raid
CrowBot vérifie automatiquement l'âge du compte et le flux de nouveaux membres.
* **Sanctions progressives :**
    1. Avertissement
    2. Mute (1m)
    3. Timeout (10m)
    4. Ban automatique (après 5 infractions)

---

## 🎮 Tracker de jeux
* **Valorant :** `/tracker valorant [pseudo]#[tag]`
* **Apex :** `/tracker apex [pseudo] [plateforme]`
* **Fortnite :** `/tracker fortnite [pseudo]`

---

## ❓ FAQ
**Les commandes slash n'apparaissent pas ?** Discord peut mettre jusqu'à une heure pour propager les commandes globales. Redémarrez le bot et patientez.

**La musique ne se lance pas ?** Vérifiez que FFmpeg est bien dans votre PATH système.

---
*Développé par l'équipe CrowBot. Merci d'utiliser notre outil !*
