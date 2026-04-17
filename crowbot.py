"""
╔══════════════════════════════════════════════════════════════════════════╗
║                           CROWBOT                                        ║
║  Musique | Admin | Casino | Jeux | Modération | Anti-Raid | Dashboard    ║
╚══════════════════════════════════════════════════════════════════════════╝

Installation:
    pip install discord.py yt-dlp PyNaCl aiohttp python-dotenv spotipy flask flask-login

Fichier .env:
    VOTRE_TOKEN=ton_token_ici
    DASHBOARD_SECRET=une_cle_secrete_ici
    DASHBOARD_PORT=5000
    HENRIK_API_KEY=""
    APEX_API_KEY=""
    FORTNITE_API_KEY=""


Lancement:
    python crowbot.py
"""

# ════════════════════════════════════════════════════════════════
#  IMPORTS
# ════════════════════════════════════════════════════════════════
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import datetime
import json
import os
import time
import re
import string
import aiohttp
import yt_dlp
import threading
import hashlib
import secrets
import base64
import html
import urllib.request
import urllib.parse as urlparse
from collections import deque, defaultdict
from dotenv import load_dotenv

# Dashboard (Flask)
from flask import (Flask, render_template_string, request, redirect,
                   url_for, session as flask_session, jsonify, flash)

load_dotenv()

# ════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ════════════════════════════════════════════════════════════════
SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
DASHBOARD_SECRET      = os.getenv("DASHBOARD_SECRET", secrets.token_hex(32))
DASHBOARD_PORT        = int(os.getenv("DASHBOARD_PORT", 5000))
DASHBOARD_ADMIN_PASS  = os.getenv("DASHBOARD_ADMIN_PASS", "admin1234")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ════════════════════════════════════════════════════════════════
#  SYSTÈME DE PERSISTANCE JSON
# ════════════════════════════════════════════════════════════════
class DataManager:
    def __init__(self, filename: str, default_factory=dict):
        self.path = os.path.join(DATA_DIR, filename)
        self.default_factory = default_factory
        self._data = self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self.default_factory()

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2, default=str)
        except IOError as e:
            print(f"[DataManager] Erreur: {e}")

    def get(self, key, default=None): return self._data.get(str(key), default)
    def set(self, key, value): self._data[str(key)] = value; self.save()
    def delete(self, key): self._data.pop(str(key), None); self.save()
    def items(self): return self._data.items()
    def keys(self): return self._data.keys()
    def values(self): return self._data.values()
    def __contains__(self, key): return str(key) in self._data
    def __getitem__(self, key): return self._data[str(key)]
    def __setitem__(self, key, value): self.set(key, value)
    def __delitem__(self, key): self.delete(key)
    def pop(self, key, *args):
        result = self._data.pop(str(key), *args); self.save(); return result
    def all(self): return dict(self._data)

class XPDataManager(DataManager):
    def __getitem__(self, key):
        k = str(key)
        if k not in self._data: self._data[k] = {"xp": 0, "level": 1}
        return self._data[k]
    def __setitem__(self, key, value): self._data[str(key)] = value; self.save()

class EconomyDataManager(DataManager):
    def __getitem__(self, key):
        k = str(key)
        if k not in self._data: self._data[k] = 1000
        return self._data[k]
    def __setitem__(self, key, value): self._data[str(key)] = value; self.save()

class WarnsDataManager(DataManager):
    def __getitem__(self, key):
        k = str(key)
        if k not in self._data: self._data[k] = []
        return self._data[k]
    def __setitem__(self, key, value): self._data[str(key)] = value; self.save()

class ShopDataManager(DataManager):
    def __getitem__(self, key):
        k = str(key)
        if k not in self._data: self._data[k] = []
        return self._data[k]
    def __setitem__(self, key, value): self._data[str(key)] = value; self.save()

# ════════════════════════════════════════════════════════════════
#  BASES DE DONNÉES
# ════════════════════════════════════════════════════════════════
xp_db           = XPDataManager("xp.json")
economy_db      = EconomyDataManager("economy.json")
warns_db        = WarnsDataManager("warns.json")
shop_items      = ShopDataManager("shop.json")
level_roles     = DataManager("level_roles.json")
autorole_config = DataManager("autorole.json")
welcome_config  = DataManager("welcome.json")
logs_config     = DataManager("logs.json")
giveaways_db    = DataManager("giveaways.json")
antiraid_config = DataManager("antiraid.json")    # guild_id -> {enabled, join_threshold, ...}
guild_settings  = DataManager("guild_settings.json")  # guild_id -> various settings
infractions_db  = DataManager("infractions.json") # guild_id -> {user_id: count}
trivia_scores   = DataManager("trivia.json")       # user_id -> score total

# ════════════════════════════════════════════════════════════════
#  MÉMOIRE VIVE
# ════════════════════════════════════════════════════════════════
last_np_messages: dict      = {}
tickets_db: dict            = {}
temp_actions: list          = []
akinator_sessions: dict     = {}
hangman_sessions: dict      = {}
music_queues: dict          = defaultdict(deque)
music_current: dict         = {}
muted_role_cache: dict      = {}
# Anti-Raid
raid_join_log: dict         = defaultdict(list)   # guild_id -> [timestamps]
raid_lock_active: dict      = {}                   # guild_id -> bool
account_age_cache: dict     = {}
# Jeux
wordle_sessions: dict       = {}
tictactoe_sessions: dict    = {}
quiz_sessions: dict         = {}
memory_sessions: dict       = {}
# Stats du bot
bot_stats = {"commands_used": 0, "songs_played": 0, "games_played": 0, "start_time": time.time()}

# ════════════════════════════════════════════════════════════════
#  CONSTANTES
# ════════════════════════════════════════════════════════════════
HANGMAN_WORDS = [
    "python","discord","programmation","algorithme","serveur","musique",
    "moderateur","administrateur","ordinateur","developpeur","application",
    "aventure","mystere","chateau","dragon","guerrier","magicien","tresor",
    "labyrinthe","encyclopedie","bibliotheque","architecture","philosophie",
]
HANGMAN_STAGES = [
    "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
    "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```",
]
SLOT_SYMBOLS = ["🍒","🍋","🍊","🍇","⭐","💎","7️⃣","🃏"]
SLOT_WEIGHTS = [30, 25, 20, 15, 5, 3, 1.5, 0.5]

WORDLE_WORDS = [
    "PIANO","FLEUR","NUAGE","TIGER","PLAGE","OCEAN","FORET","BRISE","CRANE",
    "ECLAT","FROID","GLACE","HERBE","JARDIN","LAINE","MARBRE","NUIT","OMBRE",
    "PERLE","QUART","REINE","SABLE","TAPIS","UNITE","VAPEUR","ZEBRE","AMBRE",
    "BAUME","CITRON","DELTA","EPICE","FABLE","GRACE","IVOIRE","JOKER","KARMA",
]

QUIZ_QUESTIONS = [
    {"q": "Quelle est la capitale de la France ?", "choices": ["Lyon","Paris","Marseille","Bordeaux"], "answer": 1},
    {"q": "Combien font 7 × 8 ?", "choices": ["54","56","58","62"], "answer": 1},
    {"q": "Quel est le plus grand océan du monde ?", "choices": ["Atlantique","Indien","Arctique","Pacifique"], "answer": 3},
    {"q": "En quelle année a été fondé Discord ?", "choices": ["2013","2015","2017","2019"], "answer": 1},
    {"q": "Quel langage utilise ce bot ?", "choices": ["Java","JavaScript","Python","Ruby"], "answer": 2},
    {"q": "Combien de côtés a un hexagone ?", "choices": ["5","6","7","8"], "answer": 1},
    {"q": "Quel est l'élément chimique de symbole 'Au' ?", "choices": ["Argent","Aluminium","Or","Azote"], "answer": 2},
    {"q": "Qui a peint la Joconde ?", "choices": ["Michel-Ange","Picasso","Da Vinci","Raphaël"], "answer": 2},
    {"q": "Combien de planètes dans le système solaire ?", "choices": ["7","8","9","10"], "answer": 1},
    {"q": "Quel pays a le plus grand territoire ?", "choices": ["Canada","Chine","USA","Russie"], "answer": 3},
    {"q": "Quelle est la vitesse de la lumière (km/s) ?", "choices": ["200 000","300 000","400 000","150 000"], "answer": 1},
    {"q": "Quel est le symbole chimique de l'eau ?", "choices": ["HO","H2O","H3O","OH"], "answer": 1},
    {"q": "Combien de secondes dans une heure ?", "choices": ["3000","3200","3600","4000"], "answer": 2},
    {"q": "Quelle est la monnaie du Japon ?", "choices": ["Won","Yuan","Yen","Rupee"], "answer": 2},
    {"q": "Qui a écrit 'Les Misérables' ?", "choices": ["Balzac","Zola","Hugo","Dumas"], "answer": 2},
]

AKINATOR_CHARS = [
    {"nom": "Naruto Uzumaki", "indices": ["anime","manga","ninja","japon","blond","orange","personnage fictif"]},
    {"nom": "Mickey Mouse", "indices": ["dessin animé","disney","souris","oreilles rondes","personnage fictif"]},
    {"nom": "Albert Einstein", "indices": ["scientifique","physicien","réel","théorie de la relativité","moustachu","allemand"]},
    {"nom": "Spider-Man", "indices": ["super-héros","marvel","toile d'araignée","new york","masqué","personnage fictif"]},
    {"nom": "Napoléon Bonaparte", "indices": ["historique","français","empereur","militaire","réel","guerre"]},
    {"nom": "Hermione Granger", "indices": ["harry potter","sorcière","livres","brunette","personnage fictif","femme"]},
    {"nom": "Barack Obama", "indices": ["politique","américain","président","réel","prix nobel","homme"]},
    {"nom": "Sherlock Holmes", "indices": ["détective","britannique","fictif","pipe","londres","watson"]},
    {"nom": "Pikachu", "indices": ["pokemon","jaune","électrique","anime","nintendo","mignon"]},
    {"nom": "Gandalf", "indices": ["sorcier","tolkien","fictif","barbe","vieux","anneau"]},
]

DEVINETTES = [
    ("Plus je sèche, plus je suis mouillée. Que suis-je ?", "une serviette"),
    ("J'ai des dents mais je ne mords pas. Que suis-je ?", "un peigne"),
    ("Je parle sans bouche et j'entends sans oreilles. Que suis-je ?", "un echo"),
    ("Plus je refroidis, plus je m'élève. Que suis-je ?", "un iceberg"),
    ("J'ai un cou mais pas de tête. Que suis-je ?", "une bouteille"),
    ("Je cours mais n'ai pas de jambes. Que suis-je ?", "un ruisseau"),
    ("J'ai des yeux mais je ne vois pas. Que suis-je ?", "une pomme de terre"),
]

# ════════════════════════════════════════════════════════════════
#  BOT + INTENTS
# ════════════════════════════════════════════════════════════════
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

try:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))
except Exception:
    sp = None

# ════════════════════════════════════════════════════════════════
#  HELPERS
# ════════════════════════════════════════════════════════════════
def parse_duration(text: str) -> datetime.timedelta | None:
    match = re.match(r"^(\d+)([smhd])$", text.lower())
    if not match: return None
    val, unit = int(match.group(1)), match.group(2)
    return {"s": datetime.timedelta(seconds=val), "m": datetime.timedelta(minutes=val),
            "h": datetime.timedelta(hours=val),   "d": datetime.timedelta(days=val)}[unit]

def format_delta(td: datetime.timedelta) -> str:
    total = int(td.total_seconds())
    h, r = divmod(total, 3600); m, s = divmod(r, 60)
    parts = []
    if h: parts.append(f"{h}h")
    if m: parts.append(f"{m}m")
    if s: parts.append(f"{s}s")
    return " ".join(parts) or "0s"

def format_time(seconds):
    if seconds is None: return "00:00"
    return f"{int(seconds//60):02d}:{int(seconds%60):02d}"

def embed_base(title: str, desc: str = "", color=discord.Color.blurple()) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=color)
    e.timestamp = datetime.datetime.utcnow()
    return e

async def send_log(guild: discord.Guild, embed: discord.Embed):
    channel_id = logs_config.get(guild.id)
    if channel_id:
        ch = guild.get_channel(int(channel_id))
        if ch:
            try: await ch.send(embed=embed)
            except Exception: pass

async def get_muted_role(guild: discord.Guild) -> discord.Role:
    if guild.id in muted_role_cache:
        role = guild.get_role(muted_role_cache[guild.id])
        if role: return role
    role = discord.utils.get(guild.roles, name="Muted")
    if not role:
        role = await guild.create_role(name="Muted", reason="Auto-création rôle Muted")
        for ch in guild.channels:
            try: await ch.set_permissions(role, send_messages=False, speak=False, add_reactions=False)
            except Exception: pass
    muted_role_cache[guild.id] = role.id
    return role

def get_setting(guild_id, key, default=None):
    s = guild_settings.get(guild_id) or {}
    return s.get(key, default)

def set_setting(guild_id, key, value):
    s = guild_settings.get(str(guild_id)) or {}
    s[key] = value
    guild_settings[str(guild_id)] = s

# ════════════════════════════════════════════════════════════════
#  MUSIC UI
# ════════════════════════════════════════════════════════════════
class MusicControlView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="Pause/Resume", emoji="⏯️", style=discord.ButtonStyle.secondary)
    async def toggle_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if not vc: return
        if vc.is_playing(): vc.pause()
        elif vc.is_paused(): vc.resume()
        await interaction.response.send_message("⏯️ Fait !", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.primary)
    async def skip_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()): vc.stop()
        await interaction.response.send_message("⏭️ Skippé !", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger)
    async def stop_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id in music_queues: music_queues[self.guild_id].clear()
        vc = interaction.guild.voice_client
        if vc: await vc.disconnect()
        await interaction.response.send_message("⏹️ Stoppé !", ephemeral=True)

# ════════════════════════════════════════════════════════════════
#  ANTI-RAID ENGINE
# ════════════════════════════════════════════════════════════════

def get_antiraid_config(guild_id):
    """Retourne la config anti-raid d'un serveur avec les valeurs par défaut."""
    default = {
        "enabled": False,
        "join_threshold": 10,      # X joins en Y secondes
        "join_window": 10,          # secondes
        "action": "lock",           # lock | kick | ban
        "min_account_age": 7,       # jours minimum pour le compte
        "min_account_age_action": "kick",  # action si compte trop récent
        "anti_mention_spam": True,  # bloquer les mass-mentions
        "mention_threshold": 8,     # max mentions par message
        "anti_link": False,         # bloquer les liens
        "anti_caps": False,         # bloquer les messages tout en majuscules
        "caps_threshold": 80,       # % de caps pour bloquer
        "anti_emoji_spam": False,   # limiter le spam d'emoji
        "emoji_threshold": 15,      # max emojis par message
        "whitelist_roles": [],      # rôles exempts
        "log_raids": True,
    }
    cfg = antiraid_config.get(guild_id) or {}
    return {**default, **cfg}

async def handle_raid_detection(guild: discord.Guild):
    """Déclenche les actions anti-raid."""
    cfg = get_antiraid_config(guild.id)
    if raid_lock_active.get(guild.id): return  # Déjà actif
    raid_lock_active[guild.id] = True

    action = cfg.get("action", "lock")

    # Log
    e = embed_base("🚨 RAID DÉTECTÉ", "Un afflux massif de membres a été détecté !", discord.Color.dark_red())
    e.add_field(name="Action", value=action.upper())
    e.add_field(name="Serveur", value=guild.name)
    await send_log(guild, e)

    if action == "lock":
        # Verrouille tous les salons texte
        for channel in guild.text_channels:
            try:
                await channel.set_permissions(guild.default_role, send_messages=False)
            except Exception: pass
        await asyncio.sleep(30)
        # Déverouille après 30s
        for channel in guild.text_channels:
            try:
                await channel.set_permissions(guild.default_role, send_messages=None)
            except Exception: pass
        raid_lock_active[guild.id] = False

    elif action == "kick":
        # Kick les nouveaux membres arrivés dans les dernières secondes
        window = cfg.get("join_window", 10)
        now = time.time()
        for member in guild.members:
            if member.joined_at and (now - member.joined_at.timestamp()) < window:
                try: await member.kick(reason="Anti-Raid automatique")
                except Exception: pass
        raid_lock_active[guild.id] = False

    elif action == "ban":
        window = cfg.get("join_window", 10)
        now = time.time()
        for member in guild.members:
            if member.joined_at and (now - member.joined_at.timestamp()) < window:
                try: await member.ban(reason="Anti-Raid automatique")
                except Exception: pass
        raid_lock_active[guild.id] = False

# ════════════════════════════════════════════════════════════════
#  EVENTS
# ════════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await bot.tree.sync()
    if not check_temp_actions.is_running():   check_temp_actions.start()
    if not check_giveaways.is_running():       check_giveaways.start()
    if not update_music_status.is_running():   update_music_status.start()
    if not daily_reset_task.is_running():      daily_reset_task.start()
    bot_stats["start_time"] = time.time()
    print(f"✅ Bot prêt : {bot.user}")
    print(f"   {len(bot.tree.get_commands())} slash commands")
    print(f"   Dashboard sur http://localhost:{DASHBOARD_PORT}")

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    cfg = get_antiraid_config(guild.id)

    # ── Anti-Raid : flood de joins ──
    if cfg["enabled"]:
        now = time.time()
        window = cfg["join_window"]
        raid_join_log[guild.id].append(now)
        # Nettoie les vieux timestamps
        raid_join_log[guild.id] = [t for t in raid_join_log[guild.id] if now - t < window]
        if len(raid_join_log[guild.id]) >= cfg["join_threshold"]:
            await handle_raid_detection(guild)

        # ── Anti-Raid : compte trop récent ──
        min_age_days = cfg.get("min_account_age", 0)
        if min_age_days > 0:
            age = (datetime.datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
            if age < min_age_days:
                action = cfg.get("min_account_age_action", "kick")
                e = embed_base("🛡️ Compte Trop Récent",
                    f"{member.mention} banni/kické (compte créé il y a {age} jour(s)).",
                    discord.Color.orange())
                await send_log(guild, e)
                try:
                    msg = f"⛔ Tu as été {action}é de **{guild.name}** car ton compte Discord est trop récent ({age} jours). Minimum requis : {min_age_days} jours."
                    await member.send(msg)
                except Exception: pass
                if action == "ban":
                    await member.ban(reason=f"Compte trop récent ({age}j < {min_age_days}j)")
                else:
                    await member.kick(reason=f"Compte trop récent ({age}j < {min_age_days}j)")
                return

    # ── Bienvenue ──
    cfg_w = welcome_config.get(member.guild.id)
    if cfg_w:
        ch = guild.get_channel(int(cfg_w["channel_id"]))
        if ch:
            msg = (cfg_w["message"]
                   .replace("{user}", member.mention)
                   .replace("{server}", guild.name)
                   .replace("{count}", str(guild.member_count)))
            e = embed_base("👋 Bienvenue !", msg, discord.Color.green())
            e.set_thumbnail(url=member.display_avatar.url)
            await ch.send(embed=e)

    # ── Auto-role ──
    role_id = autorole_config.get(guild.id)
    if role_id:
        role = guild.get_role(int(role_id))
        if role:
            try: await member.add_roles(role, reason="Auto-Role")
            except Exception as ex: print(f"[Auto-Role] {ex}")

    # ── Log ──
    age_days = (datetime.datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
    e = embed_base("📥 Membre rejoint", f"{member.mention} a rejoint.", discord.Color.green())
    e.add_field(name="Compte créé le", value=discord.utils.format_dt(member.created_at, "R"))
    e.add_field(name="Âge du compte", value=f"{age_days} jours")
    await send_log(guild, e)

@bot.event
async def on_member_remove(member: discord.Member):
    e = embed_base("📤 Membre parti", f"{member.mention} ({member.name}) a quitté.", discord.Color.orange())
    await send_log(member.guild, e)

@bot.event
async def on_message_delete(message: discord.Message):
    if message.author.bot or not message.guild: return
    e = embed_base("🗑️ Message supprimé", message.content or "*(vide)*", discord.Color.red())
    e.add_field(name="Auteur", value=message.author.mention)
    e.add_field(name="Salon", value=message.channel.mention)
    await send_log(message.guild, e)

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.author.bot or not before.guild or before.content == after.content: return
    e = embed_base("✏️ Message modifié", "", discord.Color.yellow())
    e.add_field(name="Avant", value=before.content[:1024] or "—", inline=False)
    e.add_field(name="Après", value=after.content[:1024] or "—", inline=False)
    e.add_field(name="Auteur", value=before.author.mention)
    e.add_field(name="Salon", value=before.channel.mention)
    await send_log(before.guild, e)

@bot.event
async def on_member_ban(guild, user):
    e = embed_base("🔨 Banni", f"{user.mention} ({user.name}) banni.", discord.Color.dark_red())
    await send_log(guild, e)

@bot.event
async def on_member_unban(guild, user):
    e = embed_base("✅ Débanni", f"{user.name} débanni.", discord.Color.green())
    await send_log(guild, e)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild: return
    bot_stats["commands_used"] += 1

    user_id  = message.author.id
    guild_id = message.guild.id
    cfg      = get_antiraid_config(guild_id)

    # ── Anti-Spam : vérification des rôles whitelist ──
    member_role_ids = [r.id for r in message.author.roles]
    whitelist = cfg.get("whitelist_roles", [])
    is_exempt = any(rid in whitelist for rid in member_role_ids) or message.author.guild_permissions.administrator

    if cfg["enabled"] and not is_exempt:
        content = message.content

        # Anti mass-mentions
        if cfg.get("anti_mention_spam") and len(message.mentions) >= cfg.get("mention_threshold", 8):
            await message.delete()
            await message.channel.send(f"⛔ {message.author.mention} Trop de mentions !", delete_after=5)
            await _automod_action(message.author, message.guild, "mention spam", cfg)
            return

        # Anti-lien
        if cfg.get("anti_link") and re.search(r"https?://|discord\.gg/", content):
            await message.delete()
            await message.channel.send(f"⛔ {message.author.mention} Les liens sont interdits !", delete_after=5)
            return

        # Anti-caps
        if cfg.get("anti_caps") and len(content) > 10:
            caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1) * 100
            if caps_ratio >= cfg.get("caps_threshold", 80):
                await message.delete()
                await message.channel.send(f"⛔ {message.author.mention} Évite les majuscules excessives !", delete_after=5)
                return

        # Anti-emoji spam
        if cfg.get("anti_emoji_spam"):
            emoji_count = len(re.findall(r'<a?:\w+:\d+>|[\U0001F000-\U0001FFFF]', content))
            if emoji_count >= cfg.get("emoji_threshold", 15):
                await message.delete()
                await message.channel.send(f"⛔ {message.author.mention} Trop d'emojis !", delete_after=5)
                return

    # ── XP ──
    data = xp_db[user_id]
    data["xp"] += random.randint(5, 15)
    current_xp  = data["xp"]
    current_lvl = data["level"]
    next_lvl_xp = current_lvl * 100

    if current_xp >= next_lvl_xp:
        data["level"] += 1
        data["xp"] = 0
        xp_db[user_id] = data
        economy_db[user_id] = economy_db[user_id] + current_lvl * 50
        await message.channel.send(
            f"🎊 Bravo {message.author.mention} ! Niveau **{current_lvl + 1}** ! +{current_lvl * 50} 🪙")
        guild_roles_raw = level_roles.get(guild_id, {})
        if str(current_lvl + 1) in guild_roles_raw:
            role = message.guild.get_role(int(guild_roles_raw[str(current_lvl + 1)]))
            if role:
                await message.author.add_roles(role, reason="Récompense de niveau")
    else:
        xp_db[user_id] = data

    await bot.process_commands(message)

async def _automod_action(member, guild, reason, cfg):
    """Applique une sanction automatique progressives selon les infractions."""
    key = f"{guild.id}"
    inf = infractions_db.get(key) or {}
    uid = str(member.id)
    inf[uid] = inf.get(uid, 0) + 1
    infractions_db[key] = inf
    count = inf[uid]

    e = embed_base("🤖 AutoMod", f"{member.mention} sanctionné automatiquement.", discord.Color.orange())
    e.add_field(name="Raison", value=reason)
    e.add_field(name="Infractions", value=str(count))
    await send_log(guild, e)

    if count >= 5:
        try: await member.ban(reason=f"AutoMod: {count} infractions")
        except Exception: pass
    elif count >= 3:
        try: await member.timeout(datetime.timedelta(minutes=10), reason=f"AutoMod: {reason}")
        except Exception: pass
    elif count >= 2:
        try:
            muted = await get_muted_role(guild)
            await member.add_roles(muted)
            await asyncio.sleep(60)
            await member.remove_roles(muted)
        except Exception: pass

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        cid = interaction.data.get("custom_id", "")
        if cid.startswith("ticket_close_"):
            uid = int(cid.split("_")[-1])
            if interaction.user.id == uid or interaction.user.guild_permissions.administrator:
                tickets_db.pop(uid, None)
                await interaction.response.send_message("🔒 Ticket fermé. Suppression dans 5s...")
                await asyncio.sleep(5)
                try: await interaction.channel.delete()
                except Exception: pass
            else:
                await interaction.response.send_message("❌ Permission refusée.", ephemeral=True)

        elif cid.startswith("ttt_"):
            # TicTacToe bouton
            parts = cid.split("_")
            if len(parts) == 4:
                _, gid, sid, pos = parts
                await handle_ttt_click(interaction, int(gid), int(sid), int(pos))

        elif cid.startswith("quiz_"):
            parts = cid.split("_")
            if len(parts) == 3:
                _, uid_str, choice_str = parts
                await handle_quiz_answer(interaction, int(uid_str), int(choice_str))

# ════════════════════════════════════════════════════════════════
#  TÂCHES
# ════════════════════════════════════════════════════════════════
@tasks.loop(seconds=3)
async def update_music_status():
    for guild_id in list(last_np_messages.keys()):
        msg   = last_np_messages[guild_id]
        track = music_current.get(guild_id)
        if not track or not track.get("start_time"): continue
        elapsed  = time.time() - track["start_time"]
        duration = track.get("duration", 0)
        time_str = f"{format_time(elapsed)} / {format_time(duration)}"
        raw_title  = track["title"]
        clean_title = (raw_title[:37] + "..") if len(raw_title) > 40 else raw_title
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.listening, name=f"{clean_title} ({time_str})"))
        bar_len = 15
        if duration > 0:
            progress = min(bar_len, int((elapsed / duration) * bar_len))
            bar = "▬" * progress + "🔘" + "▬" * (bar_len - progress)
        else:
            bar = "🔘" + "▬" * 14
        e = discord.Embed(title="🎵 Lecture en cours",
            description=f"**[{track['title']}]({track['url']})**", color=discord.Color.green())
        e.add_field(name="Progression", value=f"```\n{bar}\n```\n**{time_str}**", inline=False)
        e.add_field(name="📋 File", value=f"**{len(music_queues.get(guild_id, []))}** restantes")
        if track.get("thumbnail"): e.set_thumbnail(url=track["thumbnail"])
        e.set_footer(text=f"Demandé par {track['requester']}")
        try:
            await msg.edit(embed=e, view=MusicControlView(guild_id))
        except Exception:
            last_np_messages.pop(guild_id, None)

@tasks.loop(seconds=30)
async def check_temp_actions():
    now = datetime.datetime.utcnow()
    to_remove = []
    for action in temp_actions:
        until = action["until"]
        if isinstance(until, str): until = datetime.datetime.fromisoformat(until)
        if now >= until:
            guild = bot.get_guild(action["guild_id"])
            if not guild: to_remove.append(action); continue
            try:
                if action["type"] == "tempmute":
                    member = guild.get_member(action["user_id"])
                    if member:
                        role = guild.get_role(action["role_id"])
                        if role and role in member.roles:
                            await member.remove_roles(role, reason="TempMute expiré")
                elif action["type"] == "tempban":
                    await guild.unban(discord.Object(id=action["user_id"]), reason="TempBan expiré")
            except Exception as ex:
                print(f"[TempAction] {ex}")
            to_remove.append(action)
    for a in to_remove:
        if a in temp_actions: temp_actions.remove(a)

@tasks.loop(seconds=30)
async def check_giveaways():
    now = datetime.datetime.utcnow()
    for msg_id, data in list(giveaways_db.items()):
        if data.get("ended"): continue
        try:
            end_time = datetime.datetime.fromisoformat(data["end"])
        except Exception: continue
        if now >= end_time:
            await end_giveaway_logic(int(msg_id))

@tasks.loop(hours=24)
async def daily_reset_task():
    """Réinitialise les infractions légères chaque jour."""
    for key in list(infractions_db.keys()):
        inf = infractions_db.get(key) or {}
        # Réduit de 1 chaque infraction par jour (amnistie progressive)
        new_inf = {k: max(0, v - 1) for k, v in inf.items() if v > 1}
        infractions_db[key] = new_inf

async def end_giveaway_logic(msg_id: int):
    data = giveaways_db.get(msg_id)
    if not data or data.get("ended"): return
    guild   = bot.get_guild(int(data["guild_id"]))
    if not guild: return
    channel = guild.get_channel(int(data["channel_id"]))
    if not channel: return
    try:
        message = await channel.fetch_message(msg_id)
        reaction = discord.utils.get(message.reactions, emoji="🎉")
        users = [u async for u in reaction.users() if not u.bot]
        if users:
            winners = random.sample(users, min(int(data["winners"]), len(users)))
            winners_str = ", ".join(w.mention for w in winners)
            result = f"🎉 Félicitations {winners_str} ! Vous avez gagné **{data['lot']}** !"
        else:
            result = "😢 Personne n'a participé."
        e = discord.Embed(title="🎉 GIVEAWAY TERMINÉ", description=result, color=discord.Color.gold())
        await message.edit(embed=e)
        await channel.send(result)
    except Exception as ex: print(f"[Giveaway] {ex}")
    data["ended"] = True
    giveaways_db[str(msg_id)] = data

# ════════════════════════════════════════════════════════════════
#  MUSIQUE — YTDL + FFmpeg
# ════════════════════════════════════════════════════════════════
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostats -loglevel 0",
    "options": '-vn -filter:a "aresample=async=1" -b:a 192k',
}

async def ytdl_search(query: str, download=False) -> dict | None:
    loop = asyncio.get_event_loop()
    search_query = query

    if "spotify.com" in query:
        try:
            req = urllib.request.Request(query, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req) as resp:
                content = resp.read().decode("utf-8")
                m = re.search(r"<title>(.*?)</title>", content)
                if m:
                    raw = html.unescape(m.group(1)).replace(" | Spotify", "")
                    raw = re.sub(r" - song (and lyrics )?by ", " ", raw)
                    search_query = f"{raw.strip()} audio"
        except Exception: pass

    opts = {
        "format": "bestaudio/best", "noplaylist": False, "quiet": True,
        "no_warnings": True, "extract_flat": not download,
        "default_search": "auto", "source_address": "0.0.0.0",
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    def _extract(q):
        final_q = q if ("://" in q and "spotify" not in q) else f"ytsearch1:{q}"
        with yt_dlp.YoutubeDL(opts) as ydl:
            try: return ydl.extract_info(final_q, download=False)
            except Exception as ex: print(f"[YTDL] {ex}"); return None

    try:
        return await asyncio.wait_for(loop.run_in_executor(None, _extract, search_query), timeout=15.0)
    except Exception: return None

def process_track_info(info, requester_name):
    url = info.get("url") or info.get("webpage_url") or ""
    if not url.startswith("http") and info.get("id"):
        url = f"https://www.youtube.com/watch?v={info['id']}"
    return {
        "title":     info.get("title", "Inconnu"),
        "url":       url,
        "duration":  info.get("duration", 0),
        "thumbnail": info.get("thumbnail", ""),
        "requester": requester_name,
    }

async def play_next(guild_id: int):
    guild = bot.get_guild(guild_id)
    if not guild or not guild.voice_client: return
    queue = music_queues.get(guild_id)
    if not queue or len(queue) == 0:
        music_current.pop(guild_id, None)
        return
    track = queue.popleft()
    track["start_time"] = time.time()
    music_current[guild_id] = track
    info = await ytdl_search(track["url"], download=True)
    if not info: return await play_next(guild_id)
    url = info.get("url") or (info["formats"][-1]["url"] if "formats" in info else None)
    if not url: return await play_next(guild_id)
    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS), volume=0.5)
    def after(error):
        asyncio.run_coroutine_threadsafe(play_next(guild_id), bot.loop)
    guild.voice_client.play(source, after=after)
    bot_stats["songs_played"] += 1

# ════════════════════════════════════════════════════════════════
#  JEUX — TicTacToe
# ════════════════════════════════════════════════════════════════
class TicTacToeView(discord.ui.View):
    def __init__(self, game_data):
        super().__init__(timeout=120)
        self.game = game_data
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        board = self.game["board"]
        for i in range(9):
            label = board[i] if board[i] != " " else "‎"
            style = discord.ButtonStyle.danger if board[i] == "❌" else \
                    (discord.ButtonStyle.success if board[i] == "⭕" else discord.ButtonStyle.secondary)
            btn = discord.ui.Button(label=label, style=style, row=i // 3,
                custom_id=f"ttt_{self.game['guild_id']}_{self.game['session_id']}_{i}",
                disabled=(board[i] != " " or self.game.get("done", False)))
            self.add_item(btn)

def check_ttt_winner(board):
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]
    if " " not in board: return "draw"
    return None

async def handle_ttt_click(interaction: discord.Interaction, guild_id: int, session_id: int, pos: int):
    game = tictactoe_sessions.get(session_id)
    if not game or game.get("done"):
        return await interaction.response.send_message("❌ Partie terminée.", ephemeral=True)

    current_player_id = game["current"]
    if interaction.user.id != current_player_id:
        return await interaction.response.send_message("❌ Ce n'est pas ton tour !", ephemeral=True)

    symbol = "❌" if game["current"] == game["player1"] else "⭕"
    game["board"][pos] = symbol

    winner = check_ttt_winner(game["board"])
    p1 = interaction.guild.get_member(game["player1"])
    p2 = interaction.guild.get_member(game["player2"])

    if winner:
        game["done"] = True
        if winner == "draw":
            desc = "🤝 **Égalité !**"
        else:
            win_id = game["player1"] if symbol == "❌" else game["player2"]
            win_member = interaction.guild.get_member(win_id)
            economy_db[win_id] = economy_db[win_id] + 100
            desc = f"🏆 {win_member.mention} a gagné ! **+100 🪙**"
    else:
        game["current"] = game["player2"] if game["current"] == game["player1"] else game["player1"]
        next_member = interaction.guild.get_member(game["current"])
        desc = f"Tour de {next_member.mention}"

    e = embed_base("❌⭕ Tic-Tac-Toe", desc, discord.Color.blurple())
    if p1: e.add_field(name="❌ Joueur 1", value=p1.mention)
    if p2: e.add_field(name="⭕ Joueur 2", value=p2.mention)

    view = TicTacToeView(game)
    await interaction.response.edit_message(embed=e, view=view)

# ════════════════════════════════════════════════════════════════
#  JEUX — QUIZ INTERACTIF
# ════════════════════════════════════════════════════════════════
class QuizView(discord.ui.View):
    def __init__(self, user_id, question_data):
        super().__init__(timeout=30)
        self.user_id  = user_id
        self.q        = question_data
        self.answered = False
        for i, choice in enumerate(question_data["choices"]):
            style = discord.ButtonStyle.primary
            btn = discord.ui.Button(label=choice, style=style,
                custom_id=f"quiz_{user_id}_{i}", row=i // 2)
            self.add_item(btn)

async def handle_quiz_answer(interaction: discord.Interaction, uid: int, choice: int):
    if interaction.user.id != uid:
        return await interaction.response.send_message("❌ Ce n'est pas ta question !", ephemeral=True)
    session = quiz_sessions.get(uid)
    if not session or session.get("answered"):
        return await interaction.response.send_message("❌ Déjà répondu !", ephemeral=True)
    session["answered"] = True
    q      = session["question"]
    correct = q["answer"]
    won    = (choice == correct)
    if won:
        economy_db[uid] = economy_db[uid] + 75
        score = trivia_scores.get(uid) or 0
        trivia_scores[uid] = score + 1
        result = f"✅ **Bonne réponse !** +75 🪙\nRéponse : **{q['choices'][correct]}**"
        color  = discord.Color.green()
    else:
        result = f"❌ **Mauvaise réponse !**\nBonne réponse : **{q['choices'][correct]}**"
        color  = discord.Color.red()
    e = embed_base("🧠 Quiz", result, color)
    e.add_field(name="Question", value=q["q"], inline=False)
    await interaction.response.edit_message(embed=e, view=None)

# ════════════════════════════════════════════════════════════════
#  JEUX — WORDLE
# ════════════════════════════════════════════════════════════════
def evaluate_wordle_guess(secret: str, guess: str) -> str:
    result = []
    secret_l = list(secret)
    guess_l  = list(guess)
    marks    = [""] * 5
    used     = [False] * 5

    # Verts d'abord
    for i in range(5):
        if guess_l[i] == secret_l[i]:
            marks[i] = "🟩"
            used[i]  = True
        else:
            marks[i] = "⬛"

    # Jaunes
    for i in range(5):
        if marks[i] == "🟩": continue
        for j in range(5):
            if not used[j] and guess_l[i] == secret_l[j] and marks[j] != "🟩":
                marks[i] = "🟨"
                used[j]  = True
                break
    return " ".join(marks) + "  `" + " ".join(guess_l) + "`"

# ════════════════════════════════════════════════════════════════
#  COMMANDES — ANTI-RAID
# ════════════════════════════════════════════════════════════════
antiraid_group = app_commands.Group(name="antiraid", description="Système Anti-Raid")

@antiraid_group.command(name="setup", description="Configurer l'anti-raid du serveur")
@app_commands.checks.has_permissions(administrator=True)
async def antiraid_setup(inter: discord.Interaction,
    activer: bool = True,
    joins_max: int = 10,
    fenetre_secondes: int = 10,
    action: str = "lock",
    age_minimum_compte_jours: int = 7):
    """
    action : lock | kick | ban
    """
    if action not in ("lock", "kick", "ban"):
        return await inter.response.send_message("❌ Action invalide (lock/kick/ban).", ephemeral=True)
    cfg = get_antiraid_config(inter.guild.id)
    cfg.update({
        "enabled": activer,
        "join_threshold": joins_max,
        "join_window": fenetre_secondes,
        "action": action,
        "min_account_age": age_minimum_compte_jours,
    })
    antiraid_config[inter.guild.id] = cfg
    e = embed_base("🛡️ Anti-Raid Configuré", color=discord.Color.green() if activer else discord.Color.orange())
    e.add_field(name="Statut", value="✅ Activé" if activer else "❌ Désactivé")
    e.add_field(name="Seuil", value=f"{joins_max} joins en {fenetre_secondes}s")
    e.add_field(name="Action", value=action.upper())
    e.add_field(name="Âge minimum du compte", value=f"{age_minimum_compte_jours} jours")
    await inter.response.send_message(embed=e)

@antiraid_group.command(name="automod", description="Configurer l'AutoMod (anti-spam, liens, caps…)")
@app_commands.checks.has_permissions(administrator=True)
async def antiraid_automod(inter: discord.Interaction,
    anti_liens: bool = False,
    anti_caps: bool = False,
    anti_emoji_spam: bool = False,
    anti_mention_spam: bool = True,
    seuil_mentions: int = 8,
    seuil_caps_pourcent: int = 80,
    seuil_emojis: int = 15):
    cfg = get_antiraid_config(inter.guild.id)
    cfg.update({
        "anti_link": anti_liens,
        "anti_caps": anti_caps,
        "anti_emoji_spam": anti_emoji_spam,
        "anti_mention_spam": anti_mention_spam,
        "mention_threshold": seuil_mentions,
        "caps_threshold": seuil_caps_pourcent,
        "emoji_threshold": seuil_emojis,
    })
    antiraid_config[inter.guild.id] = cfg
    e = embed_base("🤖 AutoMod Configuré", color=discord.Color.blurple())
    e.add_field(name="Anti-Liens", value="✅" if anti_liens else "❌")
    e.add_field(name="Anti-Caps", value=f"✅ ({seuil_caps_pourcent}%)" if anti_caps else "❌")
    e.add_field(name="Anti-Emoji Spam", value=f"✅ (max {seuil_emojis})" if anti_emoji_spam else "❌")
    e.add_field(name="Anti-Mention Spam", value=f"✅ (max {seuil_mentions})" if anti_mention_spam else "❌")
    await inter.response.send_message(embed=e)

@antiraid_group.command(name="whitelist", description="Ajouter/retirer un rôle de la whitelist AutoMod")
@app_commands.checks.has_permissions(administrator=True)
async def antiraid_whitelist(inter: discord.Interaction, role: discord.Role, action: str = "add"):
    cfg = get_antiraid_config(inter.guild.id)
    wl  = cfg.get("whitelist_roles", [])
    if action == "add":
        if role.id not in wl: wl.append(role.id)
        msg = f"✅ {role.mention} ajouté à la whitelist."
    else:
        wl = [r for r in wl if r != role.id]
        msg = f"✅ {role.mention} retiré de la whitelist."
    cfg["whitelist_roles"] = wl
    antiraid_config[inter.guild.id] = cfg
    await inter.response.send_message(msg)

@antiraid_group.command(name="status", description="Voir la configuration anti-raid actuelle")
@app_commands.checks.has_permissions(manage_guild=True)
async def antiraid_status(inter: discord.Interaction):
    cfg = get_antiraid_config(inter.guild.id)
    e   = embed_base("🛡️ Status Anti-Raid", color=discord.Color.blurple())
    e.add_field(name="Statut", value="✅ Activé" if cfg["enabled"] else "❌ Désactivé")
    e.add_field(name="Seuil de raid", value=f"{cfg['join_threshold']} joins/{cfg['join_window']}s")
    e.add_field(name="Action sur raid", value=cfg["action"].upper())
    e.add_field(name="Âge compte minimum", value=f"{cfg['min_account_age']} jours")
    e.add_field(name="Anti-Liens", value="✅" if cfg.get("anti_link") else "❌")
    e.add_field(name="Anti-Caps", value="✅" if cfg.get("anti_caps") else "❌")
    e.add_field(name="Anti-Emoji Spam", value="✅" if cfg.get("anti_emoji_spam") else "❌")
    e.add_field(name="Anti-Mention Spam", value="✅" if cfg.get("anti_mention_spam") else "❌")
    wl_roles = [inter.guild.get_role(r) for r in cfg.get("whitelist_roles", [])]
    e.add_field(name="Whitelist", value=" ".join(r.mention for r in wl_roles if r) or "Aucun", inline=False)
    await inter.response.send_message(embed=e)

@antiraid_group.command(name="unlock", description="Déverrouiller le serveur manuellement après un raid")
@app_commands.checks.has_permissions(administrator=True)
async def antiraid_unlock(inter: discord.Interaction):
    await inter.response.defer()
    for channel in inter.guild.text_channels:
        try: await channel.set_permissions(inter.guild.default_role, send_messages=None)
        except Exception: pass
    raid_lock_active[inter.guild.id] = False
    await inter.followup.send("✅ Serveur déverrouillé !")

@antiraid_group.command(name="infractions", description="Voir les infractions AutoMod d'un membre")
@app_commands.checks.has_permissions(manage_guild=True)
async def antiraid_infractions(inter: discord.Interaction, membre: discord.Member):
    inf = infractions_db.get(str(inter.guild.id)) or {}
    count = inf.get(str(membre.id), 0)
    e = embed_base(f"⚠️ Infractions de {membre.name}", color=discord.Color.orange())
    e.add_field(name="Total infractions AutoMod", value=str(count))
    e.set_thumbnail(url=membre.display_avatar.url)
    await inter.response.send_message(embed=e)

@antiraid_group.command(name="reset_infractions", description="Réinitialiser les infractions d'un membre")
@app_commands.checks.has_permissions(administrator=True)
async def antiraid_reset_inf(inter: discord.Interaction, membre: discord.Member):
    inf = infractions_db.get(str(inter.guild.id)) or {}
    inf[str(membre.id)] = 0
    infractions_db[str(inter.guild.id)] = inf
    await inter.response.send_message(f"✅ Infractions de {membre.mention} réinitialisées.")

bot.tree.add_command(antiraid_group)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — ADMIN
# ════════════════════════════════════════════════════════════════
admin_group = app_commands.Group(name="admin", description="Administration")

@admin_group.command(name="ban")
@app_commands.checks.has_permissions(ban_members=True)
async def admin_ban(inter, membre: discord.Member, raison: str = "Aucune raison", supprimer_messages: int = 0):
    await membre.ban(reason=f"{inter.user}: {raison}", delete_message_days=min(supprimer_messages, 7))
    e = embed_base("🔨 Ban", f"{membre.mention} banni.", discord.Color.dark_red())
    e.add_field(name="Raison", value=raison); e.add_field(name="Par", value=inter.user.mention)
    await inter.response.send_message(embed=e)

@admin_group.command(name="unban")
@app_commands.checks.has_permissions(ban_members=True)
async def admin_unban(inter, user_id: str, raison: str = "Aucune raison"):
    try:
        user = await bot.fetch_user(int(user_id))
        await inter.guild.unban(user, reason=raison)
        await inter.response.send_message(embed=embed_base("✅ Unbanned", f"{user.name} débanni.", discord.Color.green()))
    except Exception as ex:
        await inter.response.send_message(f"❌ {ex}", ephemeral=True)

@admin_group.command(name="kick")
@app_commands.checks.has_permissions(kick_members=True)
async def admin_kick(inter, membre: discord.Member, raison: str = "Aucune raison"):
    await membre.kick(reason=f"{inter.user}: {raison}")
    e = embed_base("👢 Kick", f"{membre.mention} expulsé.", discord.Color.orange())
    e.add_field(name="Raison", value=raison)
    await inter.response.send_message(embed=e)

@admin_group.command(name="timeout", description="Mettre un membre en timeout (Discord natif)")
@app_commands.checks.has_permissions(moderate_members=True)
async def admin_timeout(inter, membre: discord.Member, duree: str, raison: str = "Aucune raison"):
    td = parse_duration(duree)
    if not td: return await inter.response.send_message("❌ Format invalide.", ephemeral=True)
    await membre.timeout(td, reason=raison)
    e = embed_base("⏰ Timeout", f"{membre.mention} en timeout pour **{format_delta(td)}**.", discord.Color.orange())
    e.add_field(name="Raison", value=raison)
    await inter.response.send_message(embed=e)

@admin_group.command(name="mute")
@app_commands.checks.has_permissions(manage_roles=True)
async def admin_mute(inter, membre: discord.Member, raison: str = "Aucune raison"):
    role = await get_muted_role(inter.guild)
    await membre.add_roles(role, reason=raison)
    e = embed_base("🔇 Mute", f"{membre.mention} muté.", discord.Color.dark_grey())
    e.add_field(name="Raison", value=raison)
    await inter.response.send_message(embed=e)

@admin_group.command(name="unmute")
@app_commands.checks.has_permissions(manage_roles=True)
async def admin_unmute(inter, membre: discord.Member):
    role = await get_muted_role(inter.guild)
    if role in membre.roles:
        await membre.remove_roles(role)
        await inter.response.send_message(embed=embed_base("🔊 Unmute", f"{membre.mention} démuté.", discord.Color.green()))
    else:
        await inter.response.send_message("❌ Pas muté.", ephemeral=True)

@admin_group.command(name="tempmute")
@app_commands.checks.has_permissions(manage_roles=True)
async def admin_tempmute(inter, membre: discord.Member, duree: str, raison: str = "Aucune raison"):
    td = parse_duration(duree)
    if not td: return await inter.response.send_message("❌ Format invalide.", ephemeral=True)
    role = await get_muted_role(inter.guild)
    await membre.add_roles(role, reason=raison)
    until = datetime.datetime.utcnow() + td
    temp_actions.append({"type": "tempmute", "user_id": membre.id, "guild_id": inter.guild.id,
                          "until": until.isoformat(), "role_id": role.id})
    e = embed_base("🔇 TempMute", f"{membre.mention} muté pour **{format_delta(td)}**.", discord.Color.dark_grey())
    e.add_field(name="Raison", value=raison); e.add_field(name="Fin", value=discord.utils.format_dt(until, "R"))
    await inter.response.send_message(embed=e)

@admin_group.command(name="tempban")
@app_commands.checks.has_permissions(ban_members=True)
async def admin_tempban(inter, membre: discord.Member, duree: str, raison: str = "Aucune raison"):
    td = parse_duration(duree)
    if not td: return await inter.response.send_message("❌ Format invalide.", ephemeral=True)
    await membre.ban(reason=f"TempBan {format_delta(td)}: {raison}")
    until = datetime.datetime.utcnow() + td
    temp_actions.append({"type": "tempban", "user_id": membre.id, "guild_id": inter.guild.id,
                          "until": until.isoformat(), "role_id": 0})
    e = embed_base("⏳ TempBan", f"{membre.mention} banni pour **{format_delta(td)}**.", discord.Color.dark_red())
    e.add_field(name="Raison", value=raison); e.add_field(name="Fin", value=discord.utils.format_dt(until, "R"))
    await inter.response.send_message(embed=e)

@admin_group.command(name="warn")
@app_commands.checks.has_permissions(kick_members=True)
async def admin_warn(inter, membre: discord.Member, raison: str):
    w_list = warns_db[membre.id]
    w_list.append({"raison": raison, "par": str(inter.user), "date": str(datetime.date.today())})
    warns_db[membre.id] = w_list
    e = embed_base("⚠️ Avertissement", f"{membre.mention} averti.", discord.Color.yellow())
    e.add_field(name="Raison", value=raison); e.add_field(name="Total", value=str(len(w_list)))
    await inter.response.send_message(embed=e)
    try: await membre.send(f"⚠️ Avertissement sur **{inter.guild.name}** : {raison}")
    except Exception: pass

@admin_group.command(name="warns")
@app_commands.checks.has_permissions(kick_members=True)
async def admin_warns(inter, membre: discord.Member):
    warns = warns_db.get(str(membre.id), [])
    e = embed_base(f"⚠️ Warns de {membre.name}", color=discord.Color.yellow())
    e.description = "\n".join(f"**#{i+1}** [{w['date']}] {w['raison']} (par {w['par']})" for i, w in enumerate(warns)) or "Aucun."
    await inter.response.send_message(embed=e)

@admin_group.command(name="clearwarn")
@app_commands.checks.has_permissions(administrator=True)
async def admin_clearwarn(inter, membre: discord.Member):
    warns_db[membre.id] = []
    await inter.response.send_message(embed=embed_base("✅ Warns effacés", f"Warns de {membre.mention} supprimés.", discord.Color.green()))

@admin_group.command(name="purge")
@app_commands.checks.has_permissions(manage_messages=True)
async def admin_purge(inter, nombre: int):
    if not 1 <= nombre <= 100:
        return await inter.response.send_message("❌ Entre 1 et 100.", ephemeral=True)
    await inter.response.defer(ephemeral=True)
    deleted = await inter.channel.purge(limit=nombre)
    await inter.followup.send(f"✅ {len(deleted)} messages supprimés.", ephemeral=True)

@admin_group.command(name="purge_user", description="Supprimer les messages d'un utilisateur spécifique")
@app_commands.checks.has_permissions(manage_messages=True)
async def admin_purge_user(inter, membre: discord.Member, nombre: int = 50):
    await inter.response.defer(ephemeral=True)
    deleted = await inter.channel.purge(limit=nombre, check=lambda m: m.author.id == membre.id)
    await inter.followup.send(f"✅ {len(deleted)} messages de {membre.mention} supprimés.", ephemeral=True)

@admin_group.command(name="setlogs")
@app_commands.checks.has_permissions(administrator=True)
async def admin_setlogs(inter, salon: discord.TextChannel):
    logs_config[inter.guild.id] = salon.id
    await inter.response.send_message(embed=embed_base("✅ Logs", f"Logs → {salon.mention}.", discord.Color.green()))

@admin_group.command(name="setwelcome")
@app_commands.checks.has_permissions(administrator=True)
async def admin_setwelcome(inter, salon: discord.TextChannel, message: str):
    welcome_config[inter.guild.id] = {"channel_id": salon.id, "message": message}
    await inter.response.send_message(embed=embed_base("✅ Bienvenue", f"Salon: {salon.mention}", discord.Color.green()))

@admin_group.command(name="setautorole")
@app_commands.checks.has_permissions(administrator=True)
async def admin_setautorole(inter, role: discord.Role = None):
    if role is None:
        autorole_config.delete(inter.guild.id)
        return await inter.response.send_message("✅ Auto-role désactivé.")
    autorole_config[inter.guild.id] = role.id
    await inter.response.send_message(f"✅ Auto-role → {role.mention}")

@admin_group.command(name="slowmode")
@app_commands.checks.has_permissions(manage_channels=True)
async def admin_slowmode(inter, secondes: int):
    await inter.channel.edit(slowmode_delay=secondes)
    await inter.response.send_message(f"🐢 Slowmode → **{secondes}s**")

@admin_group.command(name="lock")
@app_commands.checks.has_permissions(manage_channels=True)
async def admin_lock(inter):
    await inter.channel.set_permissions(inter.guild.default_role, send_messages=False)
    await inter.response.send_message(embed=embed_base("🔒 Verrouillé", "", discord.Color.red()))

@admin_group.command(name="unlock")
@app_commands.checks.has_permissions(manage_channels=True)
async def admin_unlock(inter):
    await inter.channel.set_permissions(inter.guild.default_role, send_messages=True)
    await inter.response.send_message(embed=embed_base("🔓 Déverrouillé", "", discord.Color.green()))

@admin_group.command(name="addrole")
@app_commands.checks.has_permissions(manage_roles=True)
async def admin_addrole(inter, membre: discord.Member, role: discord.Role):
    await membre.add_roles(role)
    await inter.response.send_message(embed=embed_base("✅", f"{role.mention} → {membre.mention}", discord.Color.green()))

@admin_group.command(name="removerole")
@app_commands.checks.has_permissions(manage_roles=True)
async def admin_removerole(inter, membre: discord.Member, role: discord.Role):
    await membre.remove_roles(role)
    await inter.response.send_message(embed=embed_base("✅", f"{role.mention} retiré de {membre.mention}", discord.Color.orange()))

@admin_group.command(name="nickname")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def admin_nickname(inter, membre: discord.Member, pseudo: str = ""):
    await membre.edit(nick=pseudo or None)
    await inter.response.send_message("✅ Pseudo modifié.")

@admin_group.command(name="massrole", description="Donner un rôle à tous les membres")
@app_commands.checks.has_permissions(administrator=True)
async def admin_massrole(inter, role: discord.Role):
    await inter.response.defer()
    count = 0
    for member in inter.guild.members:
        if role not in member.roles and not member.bot:
            try: await member.add_roles(role); count += 1
            except Exception: pass
    await inter.followup.send(f"✅ Rôle {role.mention} donné à **{count}** membres.")

@admin_group.command(name="stats_mod", description="Statistiques de modération du serveur")
@app_commands.checks.has_permissions(manage_guild=True)
async def admin_stats_mod(inter):
    total_warns = sum(len(w) for w in warns_db.values())
    inf_data = infractions_db.get(str(inter.guild.id)) or {}
    total_inf = sum(inf_data.values())
    e = embed_base("📊 Stats de Modération", color=discord.Color.blurple())
    e.add_field(name="⚠️ Total Warns", value=str(total_warns))
    e.add_field(name="🤖 Infractions AutoMod", value=str(total_inf))
    e.add_field(name="🎟️ Tickets actifs", value=str(len(tickets_db)))
    bans = [entry async for entry in inter.guild.bans(limit=500)]
    e.add_field(name="🔨 Bannis actuels", value=str(len(bans)))
    await inter.response.send_message(embed=e)

bot.tree.add_command(admin_group)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — LEVEL
# ════════════════════════════════════════════════════════════════
level_group = app_commands.Group(name="level", description="Progression")

@level_group.command(name="rank")
async def level_rank(inter, membre: discord.Member = None):
    m    = membre or inter.user
    data = xp_db[m.id]
    lvl  = data["level"]; xp = data["xp"]; needed = lvl * 100
    bar_filled = int((xp / needed) * 20)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    e = embed_base(f"📊 Rang de {m.name}", color=discord.Color.blue())
    e.add_field(name="Niveau", value=f"**{lvl}**")
    e.add_field(name="XP", value=f"**{xp}/{needed}**")
    e.add_field(name="Progression", value=f"`[{bar}]`", inline=False)
    e.set_thumbnail(url=m.display_avatar.url)
    await inter.response.send_message(embed=e)

@level_group.command(name="leaderboard", description="Top 10 des membres les plus actifs")
async def level_lb(inter):
    data = sorted(xp_db.items(), key=lambda x: (x[1].get("level",1)*100 + x[1].get("xp",0)), reverse=True)[:10]
    e    = embed_base("🏆 Classement XP", color=discord.Color.gold())
    medals = ["🥇","🥈","🥉"]
    lines = []
    for i, (uid, d) in enumerate(data):
        user  = bot.get_user(int(uid))
        name  = user.name if user else f"ID:{uid}"
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        lines.append(f"{medal} **{name}** — Niv. {d.get('level',1)} ({d.get('xp',0)} XP)")
    e.description = "\n".join(lines) or "Vide."
    await inter.response.send_message(embed=e)

@level_group.command(name="setreward")
@app_commands.checks.has_permissions(administrator=True)
async def level_reward(inter, niveau: int, role: discord.Role):
    gr = level_roles.get(inter.guild.id, {})
    gr[str(niveau)] = role.id
    level_roles[inter.guild.id] = gr
    await inter.response.send_message(f"✅ {role.mention} au niveau {niveau}.")

@level_group.command(name="addxp", description="Ajouter de l'XP à un membre (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def level_addxp(inter, membre: discord.Member, quantite: int):
    data = xp_db[membre.id]
    data["xp"] += quantite
    xp_db[membre.id] = data
    await inter.response.send_message(f"✅ +{quantite} XP à {membre.mention}.")

@level_group.command(name="setlevel", description="Définir le niveau d'un membre (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def level_setlevel(inter, membre: discord.Member, niveau: int):
    data = xp_db[membre.id]
    data["level"] = niveau; data["xp"] = 0
    xp_db[membre.id] = data
    await inter.response.send_message(f"✅ Niveau de {membre.mention} → {niveau}.")

bot.tree.add_command(level_group)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — SHOP
# ════════════════════════════════════════════════════════════════
shop_group = app_commands.Group(name="shop", description="Boutique")

@shop_group.command(name="add")
@app_commands.checks.has_permissions(administrator=True)
async def shop_add(inter, nom: str, prix: int, role: discord.Role):
    items = shop_items[inter.guild.id]
    items.append({"name": nom, "price": prix, "role_id": role.id})
    shop_items[inter.guild.id] = items
    await inter.response.send_message(f"✅ **{nom}** ajouté pour {prix} 🪙.")

@shop_group.command(name="remove", description="Retirer un article du shop (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def shop_remove(inter, numero: int):
    items = shop_items.get(str(inter.guild.id), [])
    if numero < 1 or numero > len(items):
        return await inter.response.send_message("❌ Numéro invalide.", ephemeral=True)
    removed = items.pop(numero - 1)
    shop_items[inter.guild.id] = items
    await inter.response.send_message(f"✅ **{removed['name']}** retiré du shop.")

@shop_group.command(name="list")
async def shop_list(inter):
    items = shop_items.get(str(inter.guild.id), [])
    if not items: return await inter.response.send_message("🛒 Shop vide.")
    e = embed_base("🛒 Boutique", "Utilise `/shop buy` pour acheter.", discord.Color.gold())
    for i, item in enumerate(items):
        role = inter.guild.get_role(int(item["role_id"]))
        e.add_field(name=f"#{i+1} — {item['name']}", value=f"Prix: **{item['price']} 🪙** | Rôle: {role.mention if role else 'Supprimé'}", inline=False)
    await inter.response.send_message(embed=e)

@shop_group.command(name="buy")
async def shop_buy(inter, numero: int):
    items = shop_items.get(str(inter.guild.id), [])
    if numero < 1 or numero > len(items):
        return await inter.response.send_message("❌ Numéro invalide.")
    item = items[numero - 1]
    if economy_db[inter.user.id] < item["price"]:
        return await inter.response.send_message(f"❌ Solde insuffisant ({economy_db[inter.user.id]} 🪙 / {item['price']} 🪙).")
    role = inter.guild.get_role(int(item["role_id"]))
    if not role: return await inter.response.send_message("❌ Rôle introuvable.")
    if role in inter.user.roles: return await inter.response.send_message("❌ Tu as déjà ce rôle.")
    economy_db[inter.user.id] = economy_db[inter.user.id] - item["price"]
    await inter.user.add_roles(role)
    await inter.response.send_message(f"🎉 Tu as acheté **{item['name']}** pour **{item['price']} 🪙** !")

bot.tree.add_command(shop_group)



# ════════════════════════════════════════════════════════════════
#  COMMANDES — ÉCONOMIE
# ════════════════════════════════════════════════════════════════
eco_group = app_commands.Group(name="eco", description="Économie")

@eco_group.command(name="solde")
async def eco_solde(inter, membre: discord.Member = None):
    m = membre or inter.user
    e = embed_base(f"💰 Solde de {m.name}", f"**{economy_db[m.id]} 🪙**", discord.Color.gold())
    e.set_thumbnail(url=m.display_avatar.url)
    await inter.response.send_message(embed=e)

daily_cooldowns: dict = {}  # user_id -> last_daily timestamp

@eco_group.command(name="daily")
async def eco_daily(inter):
    uid = inter.user.id
    now = time.time()
    last = daily_cooldowns.get(uid, 0)
    if now - last < 86400:
        remaining = 86400 - (now - last)
        h, m_ = divmod(int(remaining), 3600)
        return await inter.response.send_message(f"❌ Daily dans **{h}h{m_//60}m**.", ephemeral=True)
    daily_cooldowns[uid] = now
    amount = random.randint(100, 500)
    economy_db[uid] = economy_db[uid] + amount
    e = embed_base("💸 Daily", f"Tu as reçu **{amount} 🪙** !", discord.Color.gold())
    e.add_field(name="Solde", value=f"{economy_db[uid]} 🪙")
    await inter.response.send_message(embed=e)

@eco_group.command(name="give")
async def eco_give(inter, membre: discord.Member, montant: int):
    if montant <= 0 or montant > economy_db[inter.user.id]:
        return await inter.response.send_message("❌ Montant invalide.", ephemeral=True)
    economy_db[inter.user.id] = economy_db[inter.user.id] - montant
    economy_db[membre.id]     = economy_db[membre.id] + montant
    await inter.response.send_message(embed=embed_base("💸 Transfert", f"**{montant} 🪙** → {membre.mention}", discord.Color.green()))

@eco_group.command(name="leaderboard")
async def eco_lb(inter):
    top = sorted(economy_db.items(), key=lambda x: x[1], reverse=True)[:10]
    e   = embed_base("🏆 Classement Économie", color=discord.Color.gold())
    medals = ["🥇","🥈","🥉"]
    lines  = []
    for i, (uid, bal) in enumerate(top):
        user  = bot.get_user(int(uid))
        name  = user.name if user else f"ID:{uid}"
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        lines.append(f"{medal} **{name}** — {bal} 🪙")
    e.description = "\n".join(lines) or "Vide."
    await inter.response.send_message(embed=e)

@eco_group.command(name="addmoney", description="Ajouter des pièces à un membre (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def eco_addmoney(inter, membre: discord.Member, montant: int):
    economy_db[membre.id] = economy_db[membre.id] + montant
    await inter.response.send_message(f"✅ +{montant} 🪙 à {membre.mention}.")

@eco_group.command(name="removemoney", description="Retirer des pièces à un membre (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def eco_removemoney(inter, membre: discord.Member, montant: int):
    economy_db[membre.id] = max(0, economy_db[membre.id] - montant)
    await inter.response.send_message(f"✅ -{montant} 🪙 à {membre.mention}.")

@eco_group.command(name="work", description="Travailler pour gagner des pièces (cooldown 1h)")
async def eco_work(inter):
    uid = inter.user.id
    now = time.time()
    last = daily_cooldowns.get(f"work_{uid}", 0)
    if now - last < 3600:
        rem = int(3600 - (now - last))
        return await inter.response.send_message(f"❌ Tu peux retravailler dans **{rem//60}m{rem%60}s**.", ephemeral=True)
    daily_cooldowns[f"work_{uid}"] = now
    jobs = ["coder","streamer","trader","designer","moderateur","compositeur","chef cuisinier"]
    job  = random.choice(jobs)
    gain = random.randint(50, 200)
    economy_db[uid] = economy_db[uid] + gain
    e = embed_base("💼 Travail", f"Tu as travaillé comme **{job}** et gagné **{gain} 🪙** !", discord.Color.green())
    await inter.response.send_message(embed=e)

@eco_group.command(name="crime", description="Commettre un crime (risqué !)")
async def eco_crime(inter):
    uid = inter.user.id
    now = time.time()
    last = daily_cooldowns.get(f"crime_{uid}", 0)
    if now - last < 7200:
        rem = int(7200 - (now - last))
        return await inter.response.send_message(f"❌ Attends **{rem//60}m** avant le prochain crime.", ephemeral=True)
    daily_cooldowns[f"crime_{uid}"] = now
    crimes = ["pickpocket","casse","fraude","racket","vol de voiture"]
    crime  = random.choice(crimes)
    if random.random() < 0.4:  # 40% chance d'échouer
        fine = random.randint(100, 400)
        economy_db[uid] = max(0, economy_db[uid] - fine)
        e = embed_base("🚔 Arrêté !", f"Tu as été pris en flagrant délit de **{crime}** ! Amende : **{fine} 🪙**", discord.Color.red())
    else:
        gain = random.randint(200, 800)
        economy_db[uid] = economy_db[uid] + gain
        e = embed_base("💰 Crime réussi !", f"Tu as réussi ton **{crime}** ! Butin : **{gain} 🪙**", discord.Color.dark_green())
    await inter.response.send_message(embed=e)

bot.tree.add_command(eco_group)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — CASINO
# ════════════════════════════════════════════════════════════════
casino_group = app_commands.Group(name="casino", description="Jeux de casino")

def weighted_spin() -> str:
    total = sum(SLOT_WEIGHTS); r = random.uniform(0, total); cumul = 0
    for sym, w in zip(SLOT_SYMBOLS, SLOT_WEIGHTS):
        cumul += w
        if r <= cumul: return sym
    return SLOT_SYMBOLS[0]

def spin_row() -> list: return [weighted_spin() for _ in range(3)]

def slot_payout(row, mise):
    if row[0] == row[1] == row[2]:
        mult = {"7️⃣":50,"💎":20,"⭐":10,"🃏":8,"🍇":5,"🍊":3,"🍋":2,"🍒":1.5}.get(row[0], 2)
        return int(mise * mult), f"🎰 JACKPOT ×{mult} !"
    if row[0] == row[1] or row[1] == row[2]:
        return int(mise * 1.5), "🎯 Deux identiques ×1.5 !"
    return 0, "😞 Perdu..."

@casino_group.command(name="slots")
async def casino_slots(inter, mise: int):
    if mise <= 0 or mise > economy_db[inter.user.id]:
        return await inter.response.send_message(f"❌ Mise invalide. Solde: {economy_db[inter.user.id]} 🪙", ephemeral=True)
    economy_db[inter.user.id] -= mise
    row = spin_row(); gain, msg = slot_payout(row, mise)
    economy_db[inter.user.id] += gain
    e = discord.Embed(title="🎰 Machine à Sous", color=discord.Color.gold())
    e.description = f"╔══╦══╦══╗\n║ {row[0]} ║ {row[1]} ║ {row[2]} ║\n╚══╩══╩══╝\n\n{msg}"
    e.add_field(name="Mise", value=f"{mise} 🪙"); e.add_field(name="Gain", value=f"{gain} 🪙")
    e.add_field(name="Solde", value=f"{economy_db[inter.user.id]} 🪙")
    await inter.response.send_message(embed=e)

@casino_group.command(name="blackjack")
async def casino_blackjack(inter, mise: int):
    if mise <= 0 or mise > economy_db[inter.user.id]:
        return await inter.response.send_message(f"❌ Mise invalide. Solde: {economy_db[inter.user.id]} 🪙", ephemeral=True)
    economy_db[inter.user.id] -= mise
    deck = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
    random.shuffle(deck)
    player = [deck.pop(), deck.pop()]; dealer = [deck.pop(), deck.pop()]
    def hv(hand):
        total = sum(hand); aces = hand.count(11)
        while total > 21 and aces: total -= 10; aces -= 1
        return total
    def hs(hand, hide=False):
        return f"[{hand[0]}, ?]" if hide else f"[{', '.join(map(str, hand))}] = **{hv(hand)}**"
    view   = discord.ui.View(timeout=30)
    bj     = {"player": player, "dealer": dealer, "deck": deck, "mise": mise, "done": False}
    async def upd(inter2, res=""):
        e = discord.Embed(title="🃏 Blackjack", color=discord.Color.dark_green())
        e.add_field(name="Ton jeu", value=hs(bj["player"]), inline=False)
        e.add_field(name="Dealer",  value=hs(bj["dealer"], hide_second=not bj["done"]), inline=False)
        if res: e.add_field(name="Résultat", value=res, inline=False); e.add_field(name="Solde", value=f"{economy_db[inter.user.id]} 🪙")
        return e
    async def finish(inter2):
        bj["done"] = True
        while hv(bj["dealer"]) < 17: bj["dealer"].append(bj["deck"].pop())
        pv = hv(bj["player"]); dv = hv(bj["dealer"])
        if pv > 21: res = "💥 Bust !"
        elif dv > 21 or pv > dv: economy_db[inter.user.id] += bj["mise"]*2; res = f"🎉 Gagné ! +{bj['mise']*2} 🪙"
        elif pv == dv: economy_db[inter.user.id] += bj["mise"]; res = "🤝 Égalité !"
        else: res = "😞 Dealer gagne."
        view.clear_items()
        await inter2.response.edit_message(embed=await upd(inter2, res), view=view)
    @discord.ui.button(label="🃏 Tirer", style=discord.ButtonStyle.green)
    async def hit(inter2, btn):
        if inter2.user.id != inter.user.id: return
        bj["player"].append(bj["deck"].pop())
        if hv(bj["player"]) > 21:
            bj["done"] = True; view.clear_items()
            await inter2.response.edit_message(embed=await upd(inter2, "💥 Bust !"), view=view)
        else: await inter2.response.edit_message(embed=await upd(inter2), view=view)
    @discord.ui.button(label="✋ Rester", style=discord.ButtonStyle.red)
    async def stand(inter2, btn):
        if inter2.user.id != inter.user.id: return
        await finish(inter2)
    view.add_item(hit); view.add_item(stand)
    await inter.response.send_message(embed=await upd(inter), view=view)

@casino_group.command(name="coinflip")
async def casino_coinflip(inter, mise: int, choix: str):
    choix = choix.lower()
    if choix not in ("pile","face"): return await inter.response.send_message("❌ `pile` ou `face`.", ephemeral=True)
    if mise <= 0 or mise > economy_db[inter.user.id]: return await inter.response.send_message("❌ Mise invalide.", ephemeral=True)
    result = random.choice(["pile","face"]); won = result == choix
    if won: economy_db[inter.user.id] += mise; msg = f"🪙 {result.upper()} ! +{mise} 🪙"
    else:   economy_db[inter.user.id] -= mise; msg = f"🪙 {result.upper()} ! -{mise} 🪙"
    e = embed_base("🪙 Pile ou Face", msg, discord.Color.gold() if won else discord.Color.red())
    e.add_field(name="Solde", value=f"{economy_db[inter.user.id]} 🪙")
    await inter.response.send_message(embed=e)

@casino_group.command(name="roulette")
async def casino_roulette(inter, mise: int, pari: str):
    if mise <= 0 or mise > economy_db[inter.user.id]: return await inter.response.send_message("❌ Mise invalide.", ephemeral=True)
    num  = random.randint(0, 36)
    rouge = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    pari  = pari.lower().strip(); gain = 0
    rname = f"🎡 **{num}** ({'🔴' if num in rouge else ('⚫' if num != 0 else '🟢')})"
    if   pari == "rouge"  and num in rouge:               gain = mise * 2
    elif pari == "noir"   and num not in rouge and num:   gain = mise * 2
    elif pari == "pair"   and num and num % 2 == 0:       gain = mise * 2
    elif pari == "impair" and num % 2 == 1:               gain = mise * 2
    elif pari.isdigit()   and int(pari) == num:           gain = mise * 36
    elif not pari.isdigit():
        return await inter.response.send_message("❌ Pari invalide.", ephemeral=True)
    economy_db[inter.user.id] += gain - mise
    e = embed_base("🎡 Roulette", rname, discord.Color.red() if gain > 0 else discord.Color.dark_grey())
    e.add_field(name="Résultat", value=f"+{gain} 🪙" if gain > 0 else f"-{mise} 🪙")
    e.add_field(name="Solde", value=f"{economy_db[inter.user.id]} 🪙")
    await inter.response.send_message(embed=e)

@casino_group.command(name="dice")
async def casino_dice(inter, mise: int, pari: str):
    if mise <= 0 or mise > economy_db[inter.user.id]: return await inter.response.send_message("❌ Mise invalide.", ephemeral=True)
    if pari.lower() not in ("haut","bas"): return await inter.response.send_message("❌ `haut` ou `bas`.", ephemeral=True)
    num = random.randint(1, 6); won = (pari == "haut" and num >= 4) or (pari == "bas" and num <= 3)
    if won: economy_db[inter.user.id] += mise; msg = f"🎲 **{num}** ! +{mise} 🪙"
    else:   economy_db[inter.user.id] -= mise; msg = f"🎲 **{num}** ! -{mise} 🪙"
    e = embed_base("🎲 Dés", msg, discord.Color.green() if won else discord.Color.red())
    e.add_field(name="Solde", value=f"{economy_db[inter.user.id]} 🪙")
    await inter.response.send_message(embed=e)

@casino_group.command(name="horse", description="Parie sur une course de chevaux !")
async def casino_horse(inter, mise: int, numero: int):
    if numero not in range(1, 5):
        return await inter.response.send_message("❌ Choisir un cheval entre 1 et 4.", ephemeral=True)
    if mise <= 0 or mise > economy_db[inter.user.id]:
        return await inter.response.send_message("❌ Mise invalide.", ephemeral=True)

    await inter.response.defer()
    horses = ["🐎","🦄","🐴","🏇"]; positions = [0, 0, 0, 0]
    e = discord.Embed(title="🏇 Course de Chevaux !", color=discord.Color.green())
    track_len = 10

    # Animation
    msg = None
    for _ in range(8):
        for i in range(4): positions[i] += random.randint(0, 2)
        lines = []
        for i, (h, pos) in enumerate(zip(horses, positions)):
            done = min(pos, track_len)
            rest = track_len - done
            lines.append(f"**#{i+1}** {'▬'*done}{h}{'▬'*rest} 🏁")
        e.description = "\n".join(lines)
        if msg is None:
            await inter.followup.send(embed=e)
            msg = await inter.original_response()
        else:
            await msg.edit(embed=e)
        await asyncio.sleep(0.8)

    winner = positions.index(max(positions)) + 1
    won    = winner == numero
    if won:
        gain = mise * 3
        economy_db[inter.user.id] += gain
        result = f"🎉 Le cheval **#{winner}** gagne ! Tu remportes **{gain} 🪙** !"
    else:
        economy_db[inter.user.id] -= mise
        result = f"😞 Le cheval **#{winner}** gagne. Tu perds **{mise} 🪙**."
    e.add_field(name="Résultat", value=result, inline=False)
    e.add_field(name="Solde", value=f"{economy_db[inter.user.id]} 🪙")
    await msg.edit(embed=e)

bot.tree.add_command(casino_group)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — JEUX INNOVANTS
# ════════════════════════════════════════════════════════════════
games_group = app_commands.Group(name="game", description="Mini-jeux")

@games_group.command(name="tictactoe", description="Jouer au Tic-Tac-Toe contre quelqu'un !")
async def game_ttt(inter, adversaire: discord.Member):
    if adversaire.bot or adversaire.id == inter.user.id:
        return await inter.response.send_message("❌ Adversaire invalide.", ephemeral=True)
    sid = int(time.time() * 1000)
    game = {
        "board":      [" "] * 9,
        "player1":    inter.user.id,
        "player2":    adversaire.id,
        "current":    inter.user.id,
        "guild_id":   inter.guild.id,
        "session_id": sid,
        "done":       False,
    }
    tictactoe_sessions[sid] = game
    e = embed_base("❌⭕ Tic-Tac-Toe", f"Tour de {inter.user.mention}", discord.Color.blurple())
    e.add_field(name="❌ Joueur 1", value=inter.user.mention)
    e.add_field(name="⭕ Joueur 2", value=adversaire.mention)
    await inter.response.send_message(embed=e, view=TicTacToeView(game))
    bot_stats["games_played"] += 1

@games_group.command(name="quiz", description="Quiz interactif avec boutons !")
async def game_quiz(inter):
    q   = random.choice(QUIZ_QUESTIONS)
    uid = inter.user.id
    quiz_sessions[uid] = {"question": q, "answered": False}
    e   = embed_base("🧠 Quiz", q["q"], discord.Color.purple())
    e.set_footer(text="Tu as 30 secondes !")
    await inter.response.send_message(embed=e, view=QuizView(uid, q))
    bot_stats["games_played"] += 1

@games_group.command(name="wordle", description="Jouer au Wordle en français !")
async def game_wordle(inter):
    if inter.user.id in wordle_sessions:
        return await inter.response.send_message("❌ Tu as déjà une partie. Utilise `/game wordle_guess`.", ephemeral=True)
    word = random.choice(WORDLE_WORDS)
    wordle_sessions[inter.user.id] = {"word": word, "attempts": [], "max": 6}
    e = embed_base("🟩 WORDLE", "Devine le mot de 5 lettres !\nUtilise `/game wordle_guess` pour proposer un mot.", discord.Color.green())
    e.add_field(name="Tentatives", value="0/6")
    e.set_footer(text="Vert=bonne place | Jaune=mauvaise place | Noir=absent")
    await inter.response.send_message(embed=e)
    bot_stats["games_played"] += 1

@games_group.command(name="wordle_guess", description="Proposer un mot au Wordle")
async def game_wordle_guess(inter, mot: str):
    session = wordle_sessions.get(inter.user.id)
    if not session:
        return await inter.response.send_message("❌ Pas de partie. Lance `/game wordle`.", ephemeral=True)
    mot = mot.upper().strip()
    if len(mot) != 5 or not mot.isalpha():
        return await inter.response.send_message("❌ Mot de 5 lettres uniquement.", ephemeral=True)
    result   = evaluate_wordle_guess(session["word"], mot)
    session["attempts"].append(result)
    attempts = len(session["attempts"])
    won      = mot == session["word"]
    lost     = attempts >= session["max"] and not won
    e = embed_base("🟩 WORDLE", color=discord.Color.green() if won else discord.Color.blurple())
    e.description = "\n".join(session["attempts"])
    if won:
        del wordle_sessions[inter.user.id]
        bonus = (7 - attempts) * 50
        economy_db[inter.user.id] += bonus
        e.add_field(name="🎉 Gagné !", value=f"Le mot était **{session['word']}** ! +{bonus} 🪙", inline=False)
    elif lost:
        del wordle_sessions[inter.user.id]
        e.add_field(name="💀 Perdu !", value=f"Le mot était **{session['word']}**.", inline=False)
    else:
        e.add_field(name="Tentatives", value=f"{attempts}/{session['max']}")
    await inter.response.send_message(embed=e)

@games_group.command(name="pendu", description="Jouer au pendu")
async def game_pendu(inter):
    if inter.user.id in hangman_sessions:
        return await inter.response.send_message("❌ Partie en cours. Utilise `/game deviner`.", ephemeral=True)
    word = random.choice(HANGMAN_WORDS).upper()
    hangman_sessions[inter.user.id] = {"word": word, "guessed": [], "errors": 0}
    display = " ".join("_" for _ in word)
    e = embed_base("🎮 Pendu", f"{HANGMAN_STAGES[0]}\n\nMot: `{display}`", discord.Color.blurple())
    await inter.response.send_message(embed=e)
    bot_stats["games_played"] += 1

@games_group.command(name="deviner", description="Deviner une lettre au pendu")
async def game_deviner(inter, lettre: str):
    session = hangman_sessions.get(inter.user.id)
    if not session: return await inter.response.send_message("❌ Pas de partie.", ephemeral=True)
    letter = lettre.upper()[0] if lettre else ""
    if not letter.isalpha(): return await inter.response.send_message("❌ Lettre invalide.", ephemeral=True)
    if letter in session["guessed"]: return await inter.response.send_message(f"❌ Déjà proposé : **{letter}**", ephemeral=True)
    session["guessed"].append(letter)
    if letter not in session["word"]: session["errors"] += 1
    word    = session["word"]
    display = " ".join(c if c in session["guessed"] else "_" for c in word)
    stage   = HANGMAN_STAGES[min(session["errors"], 6)]
    if "_" not in display:
        del hangman_sessions[inter.user.id]; economy_db[inter.user.id] += 100
        e = embed_base("🎉 Gagné !", f"Le mot était **{word}** ! +100 🪙", discord.Color.green())
    elif session["errors"] >= 6:
        del hangman_sessions[inter.user.id]
        e = embed_base("💀 Perdu", f"{stage}\n\nMot: **{word}**", discord.Color.red())
    else:
        g = " ".join(session["guessed"])
        e = embed_base("🎮 Pendu", f"{stage}\n\nMot: `{display}`\nLettres: `{g}`\nErreurs: {session['errors']}/6", discord.Color.blurple())
    await inter.response.send_message(embed=e)

@games_group.command(name="nombre", description="Deviner un nombre (1-100)")
async def game_nombre(inter):
    target = random.randint(1, 100)
    await inter.response.send_message(embed=embed_base("🔢 Nombre Mystère", "Devine entre **1** et **100** ! (5 essais)", discord.Color.blurple()))
    check = lambda m: m.author == inter.user and m.channel == inter.channel and m.content.isdigit()
    for attempt in range(1, 6):
        try:
            msg   = await bot.wait_for("message", check=check, timeout=30)
            guess = int(msg.content)
            if guess == target:
                economy_db[inter.user.id] += (6 - attempt) * 20
                await inter.channel.send(embed=embed_base("🎉 Bravo !", f"C'était **{target}** en {attempt} essai(s) ! +{(6-attempt)*20} 🪙", discord.Color.green()))
                return
            await inter.channel.send("📈 Plus grand !" if guess < target else "📉 Plus petit !")
        except asyncio.TimeoutError:
            await inter.channel.send(embed=embed_base("⏰ Temps écoulé", f"C'était **{target}**.", discord.Color.orange()))
            return
    await inter.channel.send(embed=embed_base("❌ Perdu", f"C'était **{target}**.", discord.Color.red()))

@games_group.command(name="shifumi", description="Pierre, Feuille, Ciseaux !")
async def game_shifumi(inter, choix: str):
    opts  = ["pierre","feuille","ciseaux"]
    emojis = {"pierre":"🪨","feuille":"📄","ciseaux":"✂️"}
    choix  = choix.lower()
    if choix not in opts: return await inter.response.send_message("❌ pierre/feuille/ciseaux", ephemeral=True)
    bot_c = random.choice(opts)
    wins  = {"pierre":"ciseaux","feuille":"pierre","ciseaux":"feuille"}
    if choix == bot_c: res, color = "🤝 Égalité !", discord.Color.yellow()
    elif wins[choix] == bot_c: res, color = "🎉 Tu as gagné ! +25 🪙", discord.Color.green(); economy_db[inter.user.id] += 25
    else: res, color = "😞 Tu as perdu !", discord.Color.red()
    e = embed_base("✊ PFC", res, color)
    e.add_field(name="Toi", value=f"{emojis[choix]} {choix.capitalize()}")
    e.add_field(name="Bot", value=f"{emojis[bot_c]} {bot_c.capitalize()}")
    await inter.response.send_message(embed=e)

@games_group.command(name="akinator", description="Devine le personnage secret !")
async def game_akinator(inter):
    char = random.choice(AKINATOR_CHARS)
    akinator_sessions[inter.user.id] = {"char": char, "hints_given": 0}
    e = embed_base("🧞 Akinator", "J'ai choisi un personnage. Devine qui !\n`/game akindice` → indices\n`/game akinreponse` → répondre", discord.Color.purple())
    e.set_footer(text=f"{len(char['indices'])} indices dispo")
    await inter.response.send_message(embed=e)

@games_group.command(name="akindice")
async def game_akindice(inter):
    s = akinator_sessions.get(inter.user.id)
    if not s: return await inter.response.send_message("❌ Pas de partie.", ephemeral=True)
    idx = s["hints_given"]
    if idx >= len(s["char"]["indices"]): return await inter.response.send_message("❌ Plus d'indices !", ephemeral=True)
    s["hints_given"] += 1
    await inter.response.send_message(embed=embed_base("💡 Indice", f"**{idx+1}.** {s['char']['indices'][idx].capitalize()}", discord.Color.yellow()))

@games_group.command(name="akinreponse")
async def game_akinreponse(inter, reponse: str):
    s = akinator_sessions.get(inter.user.id)
    if not s: return await inter.response.send_message("❌ Pas de partie.", ephemeral=True)
    char = s["char"]
    if reponse.lower() in char["nom"].lower() or char["nom"].lower() in reponse.lower():
        del akinator_sessions[inter.user.id]
        economy_db[inter.user.id] += 100
        await inter.response.send_message(embed=embed_base("🎉 Bravo !", f"C'était **{char['nom']}** ! +100 🪙", discord.Color.green()))
    else:
        await inter.response.send_message(embed=embed_base("❌ Faux !", "Continue d'essayer !", discord.Color.red()))

@games_group.command(name="trivia_score", description="Voir ton score de quiz")
async def game_trivia_score(inter, membre: discord.Member = None):
    m     = membre or inter.user
    score = trivia_scores.get(str(m.id)) or 0
    e     = embed_base(f"🧠 Score Quiz de {m.name}", f"**{score}** bonne(s) réponse(s)", discord.Color.purple())
    e.set_thumbnail(url=m.display_avatar.url)
    await inter.response.send_message(embed=e)

@games_group.command(name="devinette")
async def game_devinette(inter):
    q, a = random.choice(DEVINETTES)
    e = embed_base("🧩 Devinette", q, discord.Color.purple())
    e.set_footer(text="30 secondes pour répondre !")
    await inter.response.send_message(embed=e)
    try:
        msg = await bot.wait_for("message", check=lambda m: m.author == inter.user and m.channel == inter.channel, timeout=30)
        if a.lower() in msg.content.lower():
            economy_db[inter.user.id] += 50
            await inter.channel.send(embed=embed_base("✅ Bonne réponse !", f"**{a}** ! +50 🪙", discord.Color.green()))
        else:
            await inter.channel.send(embed=embed_base("❌ Mauvaise réponse", f"C'était **{a}**.", discord.Color.red()))
    except asyncio.TimeoutError:
        await inter.channel.send(embed=embed_base("⏰ Temps écoulé", f"C'était **{a}**.", discord.Color.orange()))

bot.tree.add_command(games_group)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — GIVEAWAY
# ════════════════════════════════════════════════════════════════
class GiveawayModal(discord.ui.Modal, title="🎉 Créer un Giveaway"):
    lot        = discord.ui.TextInput(label="Lot")
    duree      = discord.ui.TextInput(label="Durée (ex: 1h, 30m, 2d)")
    gagnants   = discord.ui.TextInput(label="Nombre de gagnants", default="1", max_length=2)
    conditions = discord.ui.TextInput(label="Conditions (optionnel)", required=False)

    async def on_submit(self, inter: discord.Interaction):
        td = parse_duration(self.duree.value)
        if not td: return await inter.response.send_message("❌ Durée invalide.", ephemeral=True)
        try: nb = int(self.gagnants.value); assert 1 <= nb <= 20
        except: return await inter.response.send_message("❌ Gagnants invalides (1-20).", ephemeral=True)
        end = datetime.datetime.utcnow() + td
        e   = discord.Embed(title="🎉 GIVEAWAY 🎉", color=discord.Color.gold())
        e.add_field(name="🏆 Lot",      value=self.lot.value,   inline=False)
        e.add_field(name="🎟️ Gagnants", value=str(nb))
        e.add_field(name="⏰ Fin",      value=discord.utils.format_dt(end, "R"))
        if self.conditions.value: e.add_field(name="📋 Conditions", value=self.conditions.value, inline=False)
        await inter.response.send_message("✅ Giveaway créé !", ephemeral=True)
        msg = await inter.channel.send(embed=e)
        await msg.add_reaction("🎉")
        giveaways_db[str(msg.id)] = {
            "lot": self.lot.value, "end": end.isoformat(), "winners": nb,
            "channel_id": inter.channel.id, "guild_id": inter.guild.id, "ended": False}

@bot.tree.command(name="giveaway")
@app_commands.checks.has_permissions(manage_guild=True)
async def giveaway_cmd(inter): await inter.response.send_modal(GiveawayModal())

@bot.tree.command(name="greroll")
@app_commands.checks.has_permissions(manage_guild=True)
async def greroll(inter, message_id: str):
    try:
        msg = await inter.channel.fetch_message(int(message_id))
        reaction = discord.utils.get(msg.reactions, emoji="🎉")
        users = [u async for u in reaction.users() if not u.bot]
        if not users: return await inter.response.send_message("❌ Aucun participant.")
        winner = random.choice(users)
        await inter.response.send_message(f"🎉 Nouveau gagnant : {winner.mention} !")
    except Exception as ex: await inter.response.send_message(f"❌ {ex}", ephemeral=True)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — TICKET, POLL, SUGGESTION, ANNONCE
# ════════════════════════════════════════════════════════════════
class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.green, custom_id="ticket_open")
    async def open_ticket(self, inter, button):
        if inter.user.id in tickets_db:
            ch = inter.guild.get_channel(tickets_db[inter.user.id])
            if ch: return await inter.response.send_message(f"❌ Ticket existant : {ch.mention}", ephemeral=True)
        overwrites = {inter.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                      inter.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        for role in inter.guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        ch = await inter.guild.create_text_channel(f"ticket-{inter.user.name}", overwrites=overwrites,
                                                    category=inter.channel.category)
        tickets_db[inter.user.id] = ch.id
        e = embed_base("🎫 Ticket", f"Bonjour {inter.user.mention} ! Décris ton problème.", discord.Color.green())
        cv = discord.ui.View(timeout=None)
        cv.add_item(discord.ui.Button(label="🔒 Fermer", style=discord.ButtonStyle.red,
                                       custom_id=f"ticket_close_{inter.user.id}"))
        await ch.send(inter.user.mention, embed=e, view=cv)
        await inter.response.send_message(f"✅ Ticket : {ch.mention}", ephemeral=True)

@bot.tree.command(name="ticket")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(inter):
    e = embed_base("🎫 Support", "Clique pour ouvrir un ticket.", discord.Color.blurple())
    await inter.response.send_message(embed=e, view=TicketView())

class SuggestionModal(discord.ui.Modal, title="💡 Suggestion"):
    titre   = discord.ui.TextInput(label="Titre", max_length=100)
    contenu = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, max_length=1000)
    def __init__(self, channel): super().__init__(); self.channel = channel
    async def on_submit(self, inter):
        e = discord.Embed(title=f"💡 {self.titre.value}", description=self.contenu.value, color=discord.Color.yellow())
        e.set_author(name=inter.user.name, icon_url=inter.user.display_avatar.url)
        e.set_footer(text="Votez ✅ ou ❌")
        e.timestamp = datetime.datetime.utcnow()
        await inter.response.send_message("✅ Envoyé !", ephemeral=True)
        msg = await self.channel.send(embed=e)
        await msg.add_reaction("✅"); await msg.add_reaction("❌")

@bot.tree.command(name="suggestion")
async def suggestion_cmd(inter, salon: discord.TextChannel = None):
    await inter.response.send_modal(SuggestionModal(salon or inter.channel))

@bot.tree.command(name="poll")
async def poll_cmd(inter, question: str, options: str = ""):
    choices = [o.strip() for o in options.split("|") if o.strip()] if options else []
    emojis  = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    e       = discord.Embed(title=f"📊 {question}", color=discord.Color.blurple())
    e.set_author(name=inter.user.name, icon_url=inter.user.display_avatar.url)
    if not choices:
        e.description = "Vote avec ✅ ou ❌"
        await inter.response.send_message(embed=e)
        msg = await inter.original_response()
        await msg.add_reaction("✅"); await msg.add_reaction("❌")
    else:
        choices = choices[:10]
        e.description = "\n".join(f"{emojis[i]} {c}" for i, c in enumerate(choices))
        await inter.response.send_message(embed=e)
        msg = await inter.original_response()
        for i in range(len(choices)): await msg.add_reaction(emojis[i])

class AnnonceModal(discord.ui.Modal, title="📢 Annonce"):
    titre   = discord.ui.TextInput(label="Titre", max_length=200)
    contenu = discord.ui.TextInput(label="Contenu", style=discord.TextStyle.paragraph, max_length=2000)
    couleur = discord.ui.TextInput(label="Couleur hex", default="#5865F2", required=False)
    mention = discord.ui.TextInput(label="Mention (@here, @everyone...)", required=False)
    def __init__(self, channel): super().__init__(); self.channel = channel
    async def on_submit(self, inter):
        try: color = discord.Color(int(self.couleur.value.lstrip("#"), 16))
        except Exception: color = discord.Color.blurple()
        e = discord.Embed(title=self.titre.value, description=self.contenu.value, color=color)
        e.set_author(name=inter.guild.name, icon_url=inter.guild.icon.url if inter.guild.icon else None)
        e.timestamp = datetime.datetime.utcnow()
        await inter.response.send_message("✅ Envoyé !", ephemeral=True)
        await self.channel.send(content=self.mention.value.strip() or None, embed=e)

@bot.tree.command(name="annonce")
@app_commands.checks.has_permissions(manage_guild=True)
async def annonce_cmd(inter, salon: discord.TextChannel):
    await inter.response.send_modal(AnnonceModal(salon))

# ════════════════════════════════════════════════════════════════
#  COMMANDES — MUSIQUE
# ════════════════════════════════════════════════════════════════
music_group = app_commands.Group(name="music", description="Musique")

@music_group.command(name="play")
async def music_play(inter, query: str):
    vc = inter.guild.voice_client
    is_playing = vc and (vc.is_playing() or vc.is_paused())
    await inter.response.defer(ephemeral=is_playing)
    if not inter.user.voice: return await inter.followup.send("❌ Rejoins un salon vocal !")
    if not vc:
        try: vc = await inter.user.voice.channel.connect(reconnect=True, timeout=20.0)
        except Exception as ex: return await inter.followup.send(f"❌ Connexion impossible : {ex}")
    info = await ytdl_search(query, download=False)
    if not info: return await inter.followup.send("❌ Aucun résultat.")
    guild_id    = inter.guild.id
    tracks_to_add = []
    if guild_id not in music_queues: music_queues[guild_id] = deque()
    if "entries" in info and info["entries"]:
        entries = [e for e in info["entries"] if e][:20]
        for entry in entries: tracks_to_add.append(process_track_info(entry, inter.user.name))
        titre = f"📁 Playlist ({len(tracks_to_add)} titres)"
    else:
        target = info["entries"][0] if "entries" in info and info["entries"] else info
        tracks_to_add.append(process_track_info(target, inter.user.name))
        titre = "🎵 Musique ajoutée"
    started = False
    for i, track in enumerate(tracks_to_add):
        if not is_playing and i == 0:
            music_queues[guild_id].appendleft(track)
            await play_next(guild_id)
            is_playing = True; started = True
        else:
            music_queues[guild_id].append(track)
    first = tracks_to_add[0]
    if started:
        e = discord.Embed(title="🎵 Lecture en cours", description=f"**[{first['title']}]({first['url']})**", color=discord.Color.green())
        if first.get("thumbnail"): e.set_thumbnail(url=first["thumbnail"])
        e.set_footer(text=f"Demandé par {first['requester']}")
        await inter.followup.send(embed=e)
        try:
            msg = await inter.original_response()
            last_np_messages[guild_id] = msg
        except Exception: pass
    else:
        await inter.followup.send(f"✅ **{titre}** ajouté à la file !")

@music_group.command(name="playlist")
async def music_playlist(inter, query: str):
    await inter.response.defer(ephemeral=True)
    guild_id = inter.guild.id
    final_q  = query
    if "list=" in query:
        pid = urlparse.parse_qs(urlparse.urlparse(query).query).get("list", [None])[0]
        if pid: final_q = f"https://www.youtube.com/playlist?list={pid}"
    info = await ytdl_search(final_q, download=False)
    if not info or "entries" not in info:
        return await inter.followup.send("❌ Playlist introuvable.", ephemeral=True)
    entries = [e for e in info["entries"] if e]
    if guild_id not in music_queues: music_queues[guild_id] = deque()
    for entry in entries:
        music_queues[guild_id].append({
            "title": entry.get("title","..."),
            "url":   entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
            "requester": inter.user.name, "duration": entry.get("duration",0)})
    vc = inter.guild.voice_client
    if not vc: vc = await inter.user.voice.channel.connect(reconnect=True)
    if not vc.is_playing() and not vc.is_paused(): await play_next(guild_id)
    await inter.followup.send(f"✅ **{len(entries)}** musiques ajoutées !", ephemeral=True)

@music_group.command(name="pause")
async def music_pause(inter):
    vc = inter.guild.voice_client
    if vc and vc.is_playing(): vc.pause(); await inter.response.send_message(embed=embed_base("⏸️ Pause","",discord.Color.orange()))
    else: await inter.response.send_message("❌ Rien en cours.", ephemeral=True)

@music_group.command(name="resume")
async def music_resume(inter):
    vc = inter.guild.voice_client
    if vc and vc.is_paused(): vc.resume(); await inter.response.send_message(embed=embed_base("▶️ Reprise","",discord.Color.green()))
    else: await inter.response.send_message("❌ Pas en pause.", ephemeral=True)

@music_group.command(name="skip")
async def music_skip(inter):
    vc = inter.guild.voice_client
    if vc and (vc.is_playing() or vc.is_paused()): vc.stop(); await inter.response.send_message(embed=embed_base("⏭️ Skip","",discord.Color.blurple()))
    else: await inter.response.send_message("❌ Rien en cours.", ephemeral=True)

@music_group.command(name="stop")
async def music_stop(inter):
    vc = inter.guild.voice_client
    if vc:
        music_queues[inter.guild.id].clear(); music_current.pop(inter.guild.id, None); vc.stop()
        await inter.response.send_message(embed=embed_base("⏹️ Stop","",discord.Color.red()))
    else: await inter.response.send_message("❌ Pas connecté.", ephemeral=True)

@music_group.command(name="leave")
async def music_leave(inter):
    vc = inter.guild.voice_client
    if vc:
        music_queues[inter.guild.id].clear(); music_current.pop(inter.guild.id, None)
        await vc.disconnect(); await inter.response.send_message(embed=embed_base("👋 Déconnecté","",discord.Color.orange()))
    else: await inter.response.send_message("❌ Pas connecté.", ephemeral=True)

@music_group.command(name="queue")
async def music_queue_cmd(inter):
    queue   = music_queues[inter.guild.id]; current = music_current.get(inter.guild.id)
    e       = embed_base("🎶 File", color=discord.Color.blurple())
    if current: e.add_field(name="▶️ En cours", value=f"**{current['title']}**", inline=False)
    if queue: e.add_field(name=f"📋 Suivant ({len(queue)})", value="\n".join(f"`{i+1}.` {t['title']}" for i,t in enumerate(list(queue)[:10])), inline=False)
    else: e.description = "File vide."
    await inter.response.send_message(embed=e)

@music_group.command(name="volume")
async def music_volume(inter, valeur: int):
    vc = inter.guild.voice_client
    if not vc or not vc.source: return await inter.response.send_message("❌ Rien.", ephemeral=True)
    if not 0 <= valeur <= 200: return await inter.response.send_message("❌ 0-200.", ephemeral=True)
    vc.source.volume = valeur / 100
    await inter.response.send_message(embed=embed_base("🔊 Volume", f"**{valeur}%**", discord.Color.blurple()))

@music_group.command(name="shuffle")
async def music_shuffle(inter):
    q = music_queues[inter.guild.id]
    if len(q) < 2: return await inter.response.send_message("❌ Pas assez.", ephemeral=True)
    lst = list(q); random.shuffle(lst); music_queues[inter.guild.id] = deque(lst)
    await inter.response.send_message(embed=embed_base("🔀 Mélangé", f"{len(lst)} titres.", discord.Color.blurple()))

@music_group.command(name="nowplaying")
async def music_np(inter):
    c = music_current.get(inter.guild.id)
    if not c: return await inter.response.send_message("❌ Rien.", ephemeral=True)
    elapsed = time.time() - c.get("start_time", time.time())
    dur = c.get("duration", 0)
    e   = embed_base("🎵 En cours", f"**{c['title']}**", discord.Color.green())
    e.add_field(name="⏱️ Temps", value=f"{format_time(elapsed)} / {format_time(dur)}")
    if c.get("thumbnail"): e.set_thumbnail(url=c["thumbnail"])
    await inter.response.send_message(embed=e)

@music_group.command(name="restore")
@app_commands.default_permissions(administrator=True)
async def music_restore(inter):
    if inter.guild.id in music_queues: music_queues[inter.guild.id].clear()
    if inter.guild.voice_client: inter.guild.voice_client.stop(); await inter.guild.voice_client.disconnect()
    music_current.pop(inter.guild.id, None)
    await inter.response.send_message("♻️ Système réinitialisé.")

bot.tree.add_command(music_group)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — INFO
# ════════════════════════════════════════════════════════════════
@bot.tree.command(name="serverinfo")
async def serverinfo(inter):
    g = inter.guild
    e = embed_base(f"ℹ️ {g.name}", color=discord.Color.blurple())
    if g.icon: e.set_thumbnail(url=g.icon.url)
    e.add_field(name="👑 Proprio",    value=g.owner.mention if g.owner else "?")
    e.add_field(name="📅 Créé le",   value=discord.utils.format_dt(g.created_at, "D"))
    e.add_field(name="👥 Membres",   value=str(g.member_count))
    e.add_field(name="💬 Salons",    value=str(len(g.channels)))
    e.add_field(name="🎭 Rôles",     value=str(len(g.roles)))
    e.add_field(name="😀 Emojis",    value=str(len(g.emojis)))
    e.add_field(name="🔒 Vérif",     value=str(g.verification_level))
    e.add_field(name="🚀 Boosts",    value=f"{g.premium_subscription_count} (Tier {g.premium_tier})")
    cfg = get_antiraid_config(g.id)
    e.add_field(name="🛡️ Anti-Raid", value="✅ Actif" if cfg["enabled"] else "❌ Inactif")
    await inter.response.send_message(embed=e)

@bot.tree.command(name="userinfo")
async def userinfo(inter, membre: discord.Member = None):
    m = membre or inter.user
    e = embed_base(f"👤 {m.name}", color=m.color)
    e.set_thumbnail(url=m.display_avatar.url)
    e.add_field(name="🆔 ID", value=str(m.id))
    e.add_field(name="🤖 Bot", value="Oui" if m.bot else "Non")
    e.add_field(name="📅 Créé", value=discord.utils.format_dt(m.created_at, "D"))
    e.add_field(name="📥 A rejoint", value=discord.utils.format_dt(m.joined_at, "D") if m.joined_at else "?")
    age = (datetime.datetime.utcnow() - m.created_at.replace(tzinfo=None)).days
    e.add_field(name="📆 Âge compte", value=f"{age} jours")
    data = xp_db[m.id]
    e.add_field(name="📊 Niveau", value=f"Niv.{data['level']} ({data['xp']} XP)")
    e.add_field(name="💰 Solde", value=f"{economy_db[m.id]} 🪙")
    roles = [r.mention for r in reversed(m.roles) if r.name != "@everyone"]
    e.add_field(name=f"🎭 Rôles ({len(roles)})", value=" ".join(roles[:8]) or "Aucun", inline=False)
    await inter.response.send_message(embed=e)

@bot.tree.command(name="avatar")
async def avatar(inter, membre: discord.Member = None):
    m = membre or inter.user
    e = embed_base(f"🖼️ Avatar de {m.name}", color=discord.Color.blurple())
    e.set_image(url=m.display_avatar.url)
    e.description = f"[Télécharger]({m.display_avatar.url})"
    await inter.response.send_message(embed=e)

@bot.tree.command(name="ping")
async def ping(inter):
    await inter.response.send_message(embed=embed_base("🏓 Pong !", f"Latence: **{round(bot.latency*1000)}ms**", discord.Color.green()))

@bot.tree.command(name="botinfo")
async def botinfo(inter):
    uptime = time.time() - bot_stats["start_time"]
    h, r   = divmod(int(uptime), 3600); m_, s = divmod(r, 60)
    e = embed_base("🤖 Infos du Bot", color=discord.Color.blurple())
    e.set_thumbnail(url=bot.user.display_avatar.url)
    e.add_field(name="Serveurs",           value=str(len(bot.guilds)))
    e.add_field(name="Membres totaux",     value=str(sum(g.member_count for g in bot.guilds)))
    e.add_field(name="Latence",            value=f"{round(bot.latency*1000)}ms")
    e.add_field(name="Uptime",             value=f"{h}h {m_}m {s}s")
    e.add_field(name="Chansons jouées",    value=str(bot_stats["songs_played"]))
    e.add_field(name="Parties jouées",     value=str(bot_stats["games_played"]))
    e.add_field(name="Dashboard",          value=f"[Ouvrir](http://localhost:{DASHBOARD_PORT})")
    await inter.response.send_message(embed=e)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — FUN
# ════════════════════════════════════════════════════════════════
fun_group = app_commands.Group(name="fun", description="Fun & Utilitaires")

@fun_group.command(name="8ball")
async def fun_8ball(inter, question: str):
    reps = ["✅ Certainement.","✅ Absolument.","✅ Oui !","✅ Probablement.",
            "🤷 Difficile à dire.","🤷 Redemande plus tard.","🤷 Je ne sais pas.",
            "❌ Non.","❌ Très peu probable.","❌ Ne compte pas dessus."]
    e = embed_base("🎱 Boule Magique", color=discord.Color.dark_blue())
    e.add_field(name="❓", value=question, inline=False)
    e.add_field(name="🔮", value=random.choice(reps), inline=False)
    await inter.response.send_message(embed=e)

@fun_group.command(name="citation")
async def fun_citation(inter):
    citations = [
        ("La vie c'est comme une bicyclette, il faut avancer.", "Einstein"),
        ("Le succès c'est tomber sept fois, se relever huit.", "Proverbe japonais"),
        ("Sois le changement que tu veux voir dans le monde.", "Gandhi"),
        ("L'imagination est plus importante que le savoir.", "Einstein"),
        ("Le seul vrai voyage c'est d'aller vers les autres.", "Proust"),
    ]
    q, a = random.choice(citations)
    await inter.response.send_message(embed=embed_base("💬 Citation", f"*« {q} »*\n— **{a}**", discord.Color.blurple()))

@fun_group.command(name="blague")
async def fun_blague(inter):
    blagues = [
        ("Pourquoi les plongeurs plongent toujours en arrière ?", "Parce que sinon ils tomberaient dans le bateau !"),
        ("Qu'est-ce qu'un crocodile qui surveille les bagages ?", "Un sac à dents !"),
        ("Pourquoi l'épouvantail a reçu un prix ?", "Il était exceptionnel dans son domaine !"),
    ]
    q, r = random.choice(blagues)
    e = discord.Embed(title="😄 Blague", color=discord.Color.yellow())
    e.add_field(name="❓", value=q, inline=False); e.add_field(name="💡", value=f"||{r}||", inline=False)
    await inter.response.send_message(embed=e)

@fun_group.command(name="choose")
async def fun_choose(inter, options: str):
    choices = [o.strip() for o in options.split(",") if o.strip()]
    if len(choices) < 2: return await inter.response.send_message("❌ Au moins 2 options.", ephemeral=True)
    e = embed_base("🎲 Mon Choix", f"**{random.choice(choices)}**", discord.Color.blurple())
    e.set_footer(text=f"Parmi : {', '.join(choices)}")
    await inter.response.send_message(embed=e)

@fun_group.command(name="roll")
async def fun_roll(inter, faces: int = 6):
    if not 2 <= faces <= 1000: return await inter.response.send_message("❌ 2-1000.", ephemeral=True)
    await inter.response.send_message(embed=embed_base(f"🎲 D{faces}", f"Résultat : **{random.randint(1, faces)}**", discord.Color.blurple()))

@fun_group.command(name="timer")
async def fun_timer(inter, duree: str):
    td = parse_duration(duree)
    if not td or td.total_seconds() > 86400: return await inter.response.send_message("❌ Durée invalide (max 24h).", ephemeral=True)
    await inter.response.send_message(embed=embed_base("⏱️ Minuteur", f"Alerte dans **{format_delta(td)}** !", discord.Color.blurple()))
    await asyncio.sleep(td.total_seconds())
    await inter.channel.send(f"⏰ {inter.user.mention} **{format_delta(td)}** écoulé !")

@fun_group.command(name="encode")
async def fun_encode(inter, texte: str):
    encoded = base64.b64encode(texte.encode()).decode()
    await inter.response.send_message(embed=embed_base("🔐 Base64", f"`{encoded}`", discord.Color.blurple()), ephemeral=True)

@fun_group.command(name="decode")
async def fun_decode(inter, texte: str):
    try:
        decoded = base64.b64decode(texte.encode()).decode()
        await inter.response.send_message(embed=embed_base("🔓 Décodé", f"`{decoded}`", discord.Color.green()), ephemeral=True)
    except Exception:
        await inter.response.send_message("❌ Invalide.", ephemeral=True)

@fun_group.command(name="morse")
async def fun_morse(inter, texte: str):
    morse = {"A":".-","B":"-...","C":"-.-.","D":"-..","E":".","F":"..-.","G":"--.","H":"....","I":"..","J":".---","K":"-.-","L":".-..","M":"--","N":"-.","O":"---","P":".--.","Q":"--.-","R":".-.","S":"...","T":"-","U":"..-","V":"...-","W":".--","X":"-..-","Y":"-.--","Z":"--..","0":"-----","1":".----","2":"..---","3":"...--","4":"....-","5":".....","6":"-....","7":"--...","8":"---..","9":"----."," ":"/"}
    result = " ".join(morse.get(c.upper(), "?") for c in texte)
    await inter.response.send_message(embed=embed_base("📡 Morse", f"`{result}`", discord.Color.blurple()))

@fun_group.command(name="password")
async def fun_password(inter, longueur: int = 16):
    if not 8 <= longueur <= 64: return await inter.response.send_message("❌ 8-64.", ephemeral=True)
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    pwd   = "".join(random.choice(chars) for _ in range(longueur))
    await inter.response.send_message(embed=embed_base("🔑 Mot de passe", f"||`{pwd}`||", discord.Color.blurple()), ephemeral=True)

@fun_group.command(name="ascii", description="Convertir du texte en art ASCII")
async def fun_ascii(inter, texte: str):
    if len(texte) > 10: return await inter.response.send_message("❌ Max 10 caractères.", ephemeral=True)
    # Blocs ASCII simples
    big = ""
    for char in texte.upper():
        big += f"**`{char}`** "
    await inter.response.send_message(f"```\n{'  '.join(texte.upper())}\n```")

@fun_group.command(name="urban", description="Définition Urban Dictionary")
async def fun_urban(inter, mot: str):
    await inter.response.defer()
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://api.urbandictionary.com/v0/define?term={mot}") as r:
            if r.status != 200: return await inter.followup.send("❌ Erreur API.")
            data = await r.json()
            if not data.get("list"): return await inter.followup.send("❌ Aucune définition.")
            item = data["list"][0]
            definition = item["definition"][:1000].replace("[","").replace("]","")
            example    = item.get("example","")[:500].replace("[","").replace("]","")
            e = embed_base(f"📖 {mot.capitalize()}", definition, discord.Color.orange())
            if example: e.add_field(name="Exemple", value=f"*{example}*", inline=False)
            e.add_field(name="👍", value=str(item.get("thumbs_up",0)))
            e.add_field(name="👎", value=str(item.get("thumbs_down",0)))
            await inter.followup.send(embed=e)

@fun_group.command(name="catfact", description="Fait aléatoire sur les chats 🐱")
async def fun_catfact(inter):
    await inter.response.defer()
    async with aiohttp.ClientSession() as s:
        async with s.get("https://catfact.ninja/fact") as r:
            if r.status == 200:
                data = await r.json()
                await inter.followup.send(embed=embed_base("🐱 Fait sur les chats", data["fact"], discord.Color.orange()))
            else:
                await inter.followup.send("❌ API indisponible.")

bot.tree.add_command(fun_group)

# ════════════════════════════════════════════════════════════════
#  COMMANDES — GENSHIN
# ════════════════════════════════════════════════════════════════
genshin_group = app_commands.Group(name="genshin", description="Genshin Impact")

@genshin_group.command(name="profile")
async def genshin_profile(inter, uid: str):
    await inter.response.defer()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://enka.network/api/uid/{uid}") as resp:
            if resp.status != 200:
                return await inter.followup.send("❌ UID introuvable.")
            data   = await resp.json()
            player = data.get("playerInfo", {})
            e = embed_base(f"✨ {player.get('nickname','?')}", color=discord.Color.blue())
            e.add_field(name="AR",       value=player.get("level","?"))
            e.add_field(name="Succès",   value=player.get("finishAchievementNum","?"))
            e.add_field(name="Monde",    value=player.get("worldLevel","?"))
            if "signature" in player: e.add_field(name="Signature", value=player["signature"], inline=False)
            e.add_field(name="🔗 Akasha", value=f"[Voir](https://akasha.cv/profile/{uid})", inline=False)
            await inter.followup.send(embed=e)

bot.tree.add_command(genshin_group)

# ════════════════════════════════════════════════════════════════
#  GENSHIN — BUILD
# ════════════════════════════════════════════════════════════════

@genshin_group.command(name="build", description="Affiche l'infographie de build d'un personnage")
@app_commands.describe(personnage="Nom du perso (ex: raiden, ayaka, itto, wanderer)")
async def genshin_build(inter: discord.Interaction, personnage: str):
    await inter.response.defer()

    name = personnage.lower().strip().replace(" ", "-")

    corrections = {
        "ayaka": "ayaka", "raiden": "raiden", "shogun": "raiden", "ei": "raiden",
        "itto": "itto", "nomade": "wanderer", "scaramouche": "wanderer",
        "kazuha": "kazuha", "miko": "yae-miko", "yae": "yae-miko",
        "kokomi": "kokomi", "voyageur": "traveler-anemo",
        "hu tao": "hu-tao", "hutao": "hu-tao",
        "xiao": "xiao", "ganyu": "ganyu", "zhongli": "zhongli",
        "bennett": "bennett", "fischl": "fischl", "xingqiu": "xingqiu",
        "nahida": "nahida", "cyno": "cyno", "nilou": "nilou",
        "yelan": "yelan", "alhaitham": "alhaitham", "baizhu": "baizhu",
    }

    file_name = corrections.get(name, name)
    file_path = f"builds/{file_name}.png"

    if os.path.exists(file_path):
        file = discord.File(file_path, filename=f"{file_name}.png")
        e = discord.Embed(
            title=f"⚔️ Build de {personnage.capitalize()}",
            description="Voici l'infographie complète pour optimiser ton personnage.",
            color=discord.Color.gold()
        )
        e.set_author(
            name="Source : La Gazette de Teyvat",
            url="https://lagazettedeteyvat.fr/",
            icon_url="https://lagazettedeteyvat.fr/wp-content/uploads/2021/10/logo-gazette.png"
        )
        e.set_image(url=f"attachment://{file_name}.png")
        e.set_footer(text="Infographie par La Gazette de Teyvat")
        await inter.followup.send(file=file, embed=e)
    else:
        site_url = f"https://lagazettedeteyvat.fr/personnages/{file_name}/"
        e = discord.Embed(
            title="❌ Fiche non trouvée localement",
            description=(
                f"Pas d'image locale pour **{personnage}**.\n\n"
                f"🔗 [Voir le guide sur La Gazette de Teyvat]({site_url})\n\n"
                f"**Tip :** Place une image `{file_name}.png` dans le dossier `builds/` !"
            ),
            color=discord.Color.red()
        )
        await inter.followup.send(embed=e)

# ════════════════════════════════════════════════════════════════
#  TRACKER — VALORANT
# ════════════════════════════════════════════════════════════════

tracker_group = app_commands.Group(name="tracker", description="Tracker de stats de jeux compétitifs")

# Mapping des rangs Valorant avec leurs couleurs et emojis
VALORANT_RANK_DATA = {
    "Iron":        {"color": 0x6b7280, "emoji": "🩶"},
    "Bronze":      {"color": 0x92400e, "emoji": "🥉"},
    "Silver":      {"color": 0x9ca3af, "emoji": "🥈"},
    "Gold":        {"color": 0xf59e0b, "emoji": "🥇"},
    "Platinum":    {"color": 0x06b6d4, "emoji": "💎"},
    "Diamond":     {"color": 0x8b5cf6, "emoji": "💠"},
    "Ascendant":   {"color": 0x10b981, "emoji": "🌟"},
    "Immortal":    {"color": 0xef4444, "emoji": "⚡"},
    "Radiant":     {"color": 0xfbbf24, "emoji": "☀️"},
    "Unranked":    {"color": 0x374151, "emoji": "❓"},
}

def get_rank_color_emoji(rank_str: str):
    """Retourne la couleur et l'emoji selon le rang."""
    for rank_name, data in VALORANT_RANK_DATA.items():
        if rank_name.lower() in rank_str.lower():
            return data["color"], data["emoji"]
    return 0x5865f2, "🎮"

@tracker_group.command(name="valorant", description="Voir les stats Valorant d'un joueur")
@app_commands.describe(
    pseudo="Pseudo du joueur",
    tag="Tag sans le # (ex: EUW, 1234)"
)
async def tracker_valorant(inter: discord.Interaction, pseudo: str, tag: str):
    await inter.response.defer()

    # Nettoyage du tag (enlève le # si l'user l'a mis)
    tag = tag.lstrip("#")

    async with aiohttp.ClientSession() as session:
        # API Henrik (tracker non-officiel Valorant, gratuite)
        url = f"https://api.henrikdev.xyz/valorant/v2/mmr/eu/{urllib.parse.quote(pseudo)}/{urllib.parse.quote(tag)}"

        headers = {}
        # Si tu as une clé API Henrik, mets-la dans le .env
        henrik_key = os.getenv("HENRIK_API_KEY", "")
        if henrik_key:
            headers["Authorization"] = henrik_key

        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    return await inter.followup.send(
                        embed=embed_base("❌ Joueur introuvable",
                            f"Le joueur **{pseudo}#{tag}** n'existe pas ou n'a jamais joué.\n"
                            "Vérifie le pseudo et le tag.", discord.Color.red()))

                if resp.status == 403:
                    return await inter.followup.send(
                        embed=embed_base("⚠️ Accès refusé",
                            "L'API nécessite une clé. Ajoute `HENRIK_API_KEY=ta_cle` dans le `.env`.\n"
                            f"[Obtenir une clé gratuite](https://docs.henrikdev.xyz/)", discord.Color.orange()))

                if resp.status != 200:
                    return await inter.followup.send(
                        embed=embed_base("❌ Erreur API",
                            f"Code HTTP: {resp.status}. Réessaie plus tard.", discord.Color.red()))

                data = await resp.json()

        except asyncio.TimeoutError:
            return await inter.followup.send(
                embed=embed_base("⏰ Timeout", "L'API met trop de temps à répondre.", discord.Color.orange()))
        except Exception as ex:
            return await inter.followup.send(
                embed=embed_base("❌ Erreur", str(ex), discord.Color.red()))

    # Parse les données
    player_data = data.get("data", {})

    current_data   = player_data.get("current_data", {})
    highest_data   = player_data.get("highest_rank", {})

    current_rank   = current_data.get("currenttierpatched", "Non classé")
    current_rr     = current_data.get("ranking_in_tier", 0)
    current_elo    = current_data.get("elo", 0)
    peak_rank      = highest_data.get("patched_tier", "?")
    peak_episode   = highest_data.get("season", "?")

    mmr_change     = current_data.get("mmr_change_to_last_game", 0)
    rank_img       = current_data.get("images", {}).get("large", "")

    color_int, emoji = get_rank_color_emoji(current_rank)

    # Construction de l'embed
    e = discord.Embed(
        title=f"{emoji} {pseudo}#{tag}",
        description=f"**Profil Valorant**",
        color=discord.Color(color_int)
    )

    e.add_field(
        name="🏆 Rang Actuel",
        value=f"**{current_rank}**\n{current_rr} RR",
        inline=True
    )
    e.add_field(
        name="📊 ELO Total",
        value=f"**{current_elo}**",
        inline=True
    )

    mmr_str = f"`+{mmr_change}`" if mmr_change > 0 else f"`{mmr_change}`"
    mmr_color = "🟢" if mmr_change > 0 else ("🔴" if mmr_change < 0 else "⚪")
    e.add_field(
        name="📈 Dernier match",
        value=f"{mmr_color} {mmr_str} RR",
        inline=True
    )
    e.add_field(
        name="⭐ Pic de rang",
        value=f"**{peak_rank}**\n{peak_episode}",
        inline=True
    )

    if rank_img:
        e.set_thumbnail(url=rank_img)

    e.set_footer(text="Données via HenrikDev API • Non affilié à Riot Games")
    e.timestamp = datetime.datetime.utcnow()

    # Bouton vers tracker.gg
    view = discord.ui.View()
    tracker_url = f"https://tracker.gg/valorant/profile/riot/{urllib.parse.quote(pseudo)}%23{urllib.parse.quote(tag)}/overview"
    view.add_item(discord.ui.Button(
        label="Voir sur Tracker.gg",
        url=tracker_url,
        style=discord.ButtonStyle.link,
        emoji="🔗"
    ))

    await inter.followup.send(embed=e, view=view)


@tracker_group.command(name="valorant_stats", description="Stats détaillées Valorant (Win Rate, K/D...)")
@app_commands.describe(pseudo="Pseudo", tag="Tag (sans #)", mode="Mode de jeu")
@app_commands.choices(mode=[
    app_commands.Choice(name="Compétitif", value="competitive"),
    app_commands.Choice(name="Non-classé", value="unrated"),
    app_commands.Choice(name="Spike Rush", value="spikerush"),
    app_commands.Choice(name="Deathmatch", value="deathmatch"),
])
async def tracker_valo_stats(inter: discord.Interaction, pseudo: str, tag: str,
                              mode: str = "competitive"):
    await inter.response.defer()
    tag = tag.lstrip("#")

    async with aiohttp.ClientSession() as session:
        url = f"https://api.henrikdev.xyz/valorant/v1/lifetime/matches/eu/{urllib.parse.quote(pseudo)}/{urllib.parse.quote(tag)}?mode={mode}&size=20"
        headers = {}
        henrik_key = os.getenv("HENRIK_API_KEY", "")
        if henrik_key:
            headers["Authorization"] = henrik_key

        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return await inter.followup.send(f"❌ Erreur API ({resp.status}). Joueur introuvable ou pas de matchs.")
                data = await resp.json()
        except Exception as ex:
            return await inter.followup.send(f"❌ Erreur: {ex}")

    matches = data.get("data", [])
    if not matches:
        return await inter.followup.send(
            embed=embed_base("📭 Aucun match", f"Aucun match trouvé en **{mode}** pour {pseudo}#{tag}.", discord.Color.orange()))

    # Calcul des stats sur les 20 derniers matchs
    total_kills   = 0
    total_deaths  = 0
    total_assists = 0
    wins          = 0
    total_score   = 0
    agents_used   = {}

    for match in matches:
        stats = match.get("stats", {})
        total_kills   += stats.get("kills", 0)
        total_deaths  += stats.get("deaths", 1)
        total_assists += stats.get("assists", 0)
        total_score   += stats.get("score", 0)
        if stats.get("team", "").lower() == match.get("teams", {}).get("winning_team", "").lower():
            wins += 1
        agent = stats.get("character", {}).get("name", "?")
        agents_used[agent] = agents_used.get(agent, 0) + 1

    n           = len(matches)
    kd          = round(total_kills / max(total_deaths, 1), 2)
    winrate     = round((wins / n) * 100, 1)
    avg_kills   = round(total_kills / n, 1)
    avg_deaths  = round(total_deaths / n, 1)
    avg_assists = round(total_assists / n, 1)
    avg_score   = round(total_score / n)
    fav_agent   = max(agents_used, key=agents_used.get) if agents_used else "?"

    # Couleur selon K/D
    if kd >= 1.5:   color = discord.Color.green()
    elif kd >= 1.0: color = discord.Color.gold()
    else:           color = discord.Color.red()

    e = discord.Embed(
        title=f"📊 Stats de {pseudo}#{tag}",
        description=f"Mode: **{mode}** • {n} derniers matchs",
        color=color
    )
    e.add_field(name="⚔️ K/D",         value=f"**{kd}**",         inline=True)
    e.add_field(name="🏆 Win Rate",     value=f"**{winrate}%**",   inline=True)
    e.add_field(name="💀 Moy. Kills",   value=f"**{avg_kills}**",  inline=True)
    e.add_field(name="☠️ Moy. Deaths",  value=f"**{avg_deaths}**", inline=True)
    e.add_field(name="🤝 Moy. Assists", value=f"**{avg_assists}**",inline=True)
    e.add_field(name="🎯 Moy. Score",   value=f"**{avg_score}**",  inline=True)
    e.add_field(name="🎭 Agent favori", value=f"**{fav_agent}**",  inline=True)
    e.add_field(name="✅ Victoires",    value=f"**{wins}/{n}**",   inline=True)

    # Barre de win rate visuelle
    bar_filled = int((winrate / 100) * 20)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)
    e.add_field(name="📈 Win Rate visuel", value=f"`[{bar}]` {winrate}%", inline=False)

    e.set_footer(text="Sur les 20 derniers matchs • HenrikDev API")
    e.timestamp = datetime.datetime.utcnow()

    view = discord.ui.View()
    tracker_url = f"https://tracker.gg/valorant/profile/riot/{urllib.parse.quote(pseudo)}%23{urllib.parse.quote(tag)}/overview"
    view.add_item(discord.ui.Button(label="Tracker.gg", url=tracker_url, emoji="🔗", style=discord.ButtonStyle.link))

    await inter.followup.send(embed=e, view=view)


# ════════════════════════════════════════════════════════════════
#  TRACKER — FORTNITE
# ════════════════════════════════════════════════════════════════

FORTNITE_RANK_EMOJIS = {
    "Bronze":   "🥉", "Silver": "🥈", "Gold": "🥇",
    "Platinum": "💎", "Diamond": "💠", "Elite": "⚡",
    "Champion": "🏆", "Unreal": "👑",
}

def get_fortnite_rank_emoji(rank: str) -> str:
    for key, emoji in FORTNITE_RANK_EMOJIS.items():
        if key.lower() in rank.lower():
            return emoji
    return "🎮"

@tracker_group.command(name="fortnite", description="Voir les stats Fortnite d'un joueur")
@app_commands.describe(
    pseudo="Pseudo Epic Games",
    plateforme="Plateforme du joueur"
)
@app_commands.choices(plateforme=[
    app_commands.Choice(name="PC / Epic", value="epic"),
    app_commands.Choice(name="PlayStation", value="psn"),
    app_commands.Choice(name="Xbox", value="xbl"),
])
async def tracker_fortnite(inter: discord.Interaction, pseudo: str, plateforme: str = "epic"):
    await inter.response.defer()

    fortnite_key = os.getenv("FORTNITE_API_KEY", "")

    async with aiohttp.ClientSession() as session:
        # API Fortnite-api.com (gratuite, pas de clé requise pour les stats de base)
        url = f"https://fortnite-api.com/v2/stats/br/v2?name={urllib.parse.quote(pseudo)}&accountType={plateforme}&image=all"

        headers = {}
        if fortnite_key:
            headers["Authorization"] = fortnite_key

        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    return await inter.followup.send(
                        embed=embed_base("❌ Joueur introuvable",
                            f"**{pseudo}** est introuvable sur {plateforme}.\n"
                            "Vérifie que les stats sont publiques dans les paramètres Fortnite.",
                            discord.Color.red()))
                if resp.status != 200:
                    return await inter.followup.send(f"❌ Erreur API ({resp.status}).")
                data = await resp.json()
        except asyncio.TimeoutError:
            return await inter.followup.send("⏰ Timeout API Fortnite.")
        except Exception as ex:
            return await inter.followup.send(f"❌ Erreur: {ex}")

    stats  = data.get("data", {})
    account= stats.get("account", {})
    battle_pass = stats.get("battlePass", {})
    all_stats   = stats.get("stats", {}).get("all", {}).get("overall", {})
    solo_stats  = stats.get("stats", {}).get("all", {}).get("solo", {})
    duo_stats   = stats.get("stats", {}).get("all", {}).get("duo", {})
    squad_stats = stats.get("stats", {}).get("all", {}).get("squad", {})

    name        = account.get("name", pseudo)
    bp_level    = battle_pass.get("level", "?")

    # Stats globales
    wins        = all_stats.get("wins", 0)
    kills       = all_stats.get("kills", 0)
    matches     = all_stats.get("matches", 0)
    kd          = round(all_stats.get("kd", 0), 2)
    winrate     = round(all_stats.get("winRate", 0) * 100, 1) if all_stats.get("winRate") else 0
    kills_game  = round(all_stats.get("killsPerMatch", 0), 2)
    top3        = all_stats.get("top3", 0)
    minutes_pl  = all_stats.get("minutesPlayed", 0)
    hours_pl    = round(minutes_pl / 60, 1) if minutes_pl else "?"

    # Niveau de rank ranked (si disponible dans les données)
    ranked_info = stats.get("stats", {}).get("all", {}).get("ranked", {})
    current_rank = ranked_info.get("currentRank", "Non classé") if ranked_info else "Non classé"

    # Couleur selon K/D
    if kd >= 5:     color = discord.Color.red()
    elif kd >= 2.5: color = discord.Color.gold()
    elif kd >= 1.5: color = discord.Color.green()
    else:           color = discord.Color.blurple()

    rank_emoji = get_fortnite_rank_emoji(current_rank)

    e = discord.Embed(
        title=f"🎮 {name}",
        description=f"**Stats Fortnite Battle Royale** • {plateforme.upper()}",
        color=color
    )

    e.add_field(name="🏆 Victoires",     value=f"**{wins:,}**",       inline=True)
    e.add_field(name="💀 K/D",           value=f"**{kd}**",            inline=True)
    e.add_field(name="🎯 Kills/Partie",  value=f"**{kills_game}**",   inline=True)
    e.add_field(name="🎮 Parties",       value=f"**{matches:,}**",    inline=True)
    e.add_field(name="📊 Win Rate",      value=f"**{winrate}%**",     inline=True)
    e.add_field(name="☠️ Total Kills",   value=f"**{kills:,}**",      inline=True)
    e.add_field(name="🥉 Top 3",         value=f"**{top3:,}**",       inline=True)
    e.add_field(name="⏱️ Heures jouées", value=f"**{hours_pl}h**",   inline=True)
    e.add_field(name="📖 Battle Pass",   value=f"Niveau **{bp_level}**", inline=True)

    # Stats par mode
    if solo_stats or duo_stats or squad_stats:
        mode_lines = []
        if solo_stats.get("matches"):
            s_wr = round(solo_stats.get("winRate", 0) * 100, 1)
            mode_lines.append(f"🧍 Solo: **{solo_stats.get('wins',0)}** wins • KD: **{round(solo_stats.get('kd',0),2)}** • WR: **{s_wr}%**")
        if duo_stats.get("matches"):
            d_wr = round(duo_stats.get("winRate", 0) * 100, 1)
            mode_lines.append(f"👥 Duo:  **{duo_stats.get('wins',0)}** wins • KD: **{round(duo_stats.get('kd',0),2)}** • WR: **{d_wr}%**")
        if squad_stats.get("matches"):
            sq_wr = round(squad_stats.get("winRate", 0) * 100, 1)
            mode_lines.append(f"👨‍👩‍👧‍👦 Squad: **{squad_stats.get('wins',0)}** wins • KD: **{round(squad_stats.get('kd',0),2)}** • WR: **{sq_wr}%**")
        if mode_lines:
            e.add_field(name="📋 Détail par mode", value="\n".join(mode_lines), inline=False)

    # Image des stats (si disponible)
    image_url = stats.get("image", "")
    if image_url:
        e.set_image(url=image_url)

    e.set_footer(text="Données via fortnite-api.com • Peut être en retard de quelques heures")
    e.timestamp = datetime.datetime.utcnow()

    view = discord.ui.View()
    tracker_url = f"https://fortnitetracker.com/profile/all/{urllib.parse.quote(pseudo)}"
    view.add_item(discord.ui.Button(label="FortniteTracker", url=tracker_url, emoji="🔗", style=discord.ButtonStyle.link))

    await inter.followup.send(embed=e, view=view)


# ════════════════════════════════════════════════════════════════
#  TRACKER — LEAGUE OF LEGENDS
# ════════════════════════════════════════════════════════════════

LOL_RANK_COLORS = {
    "IRON":        0x6b7280, "BRONZE":    0x92400e,
    "SILVER":      0x9ca3af, "GOLD":      0xf59e0b,
    "PLATINUM":    0x06b6d4, "EMERALD":   0x10b981,
    "DIAMOND":     0x8b5cf6, "MASTER":    0xef4444,
    "GRANDMASTER": 0xf97316, "CHALLENGER":0xfbbf24,
}

LOL_RANK_EMOJIS = {
    "IRON": "🩶", "BRONZE": "🥉", "SILVER": "🥈",
    "GOLD": "🥇", "PLATINUM": "💎", "EMERALD": "🌿",
    "DIAMOND": "💠", "MASTER": "⚡", "GRANDMASTER": "🔥", "CHALLENGER": "👑",
}

LOL_REGIONS = {
    "euw": "euw1", "eune": "eun1", "na": "na1",
    "kr": "kr",    "br": "br1",   "las": "la2",
    "lan": "la1",  "oce": "oc1",  "ru": "ru",  "tr": "tr1",
}

@tracker_group.command(name="lol", description="Voir le rang LoL d'un joueur")
@app_commands.describe(
    pseudo="Pseudo (Riot ID#Tag ou ancien pseudo)",
    tag="Tag Riot (ex: EUW, 1234)",
    region="Région du serveur"
)
@app_commands.choices(region=[
    app_commands.Choice(name="EUW",  value="euw"),
    app_commands.Choice(name="EUNE", value="eune"),
    app_commands.Choice(name="NA",   value="na"),
    app_commands.Choice(name="KR",   value="kr"),
    app_commands.Choice(name="BR",   value="br"),
])
async def tracker_lol(inter: discord.Interaction, pseudo: str, region: str = "euw", tag: str = ""):
    await inter.response.defer()

    riot_key = os.getenv("RIOT_API_KEY", "")
    if not riot_key:
        return await inter.followup.send(
            embed=embed_base("⚠️ Clé API manquante",
                "Ajoute `RIOT_API_KEY=ta_cle` dans le `.env`.\n"
                "[Obtenir une clé](https://developer.riotgames.com/) (gratuit)",
                discord.Color.orange()))

    server = LOL_REGIONS.get(region.lower(), "euw1")
    headers = {"X-Riot-Token": riot_key}

    async with aiohttp.ClientSession() as session:
        try:
            # Étape 1 : Récupérer le PUUID via Riot ID
            if tag:
                tag = tag.lstrip("#")
                # Riot Account API (Europe routing)
                account_url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{urllib.parse.quote(pseudo)}/{urllib.parse.quote(tag)}"
            else:
                # Essai avec l'ancien système (summonerName)
                account_url = f"https://{server}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{urllib.parse.quote(pseudo)}"

            async with session.get(account_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    return await inter.followup.send(
                        embed=embed_base("❌ Joueur introuvable",
                            f"**{pseudo}** introuvable sur {region.upper()}.", discord.Color.red()))
                if resp.status == 403:
                    return await inter.followup.send(
                        embed=embed_base("🔑 Clé API invalide",
                            "Ta clé Riot API est invalide ou expirée.", discord.Color.red()))
                if resp.status != 200:
                    return await inter.followup.send(f"❌ Erreur API ({resp.status}).")
                account_data = await resp.json()

            puuid       = account_data.get("puuid", "")
            summoner_id = account_data.get("id", "")

            # Étape 2 : Récupérer le summoner via PUUID (si on a utilisé Riot ID)
            if tag and puuid:
                summ_url = f"https://{server}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
                async with session.get(summ_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp2:
                    if resp2.status == 200:
                        summ_data   = await resp2.json()
                        summoner_id = summ_data.get("id", "")
                        summ_level  = summ_data.get("summonerLevel", "?")
                        profile_icon= summ_data.get("profileIconId", 1)
                    else:
                        summ_level   = "?"
                        profile_icon = 1
            else:
                summ_level   = account_data.get("summonerLevel", "?")
                profile_icon = account_data.get("profileIconId", 1)

            if not summoner_id:
                return await inter.followup.send("❌ Impossible de récupérer l'ID du joueur.")

            # Étape 3 : Récupérer le rang
            rank_url = f"https://{server}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
            async with session.get(rank_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp3:
                if resp3.status != 200:
                    return await inter.followup.send(f"❌ Impossible de récupérer le rang ({resp3.status}).")
                rank_data = await resp3.json()

        except asyncio.TimeoutError:
            return await inter.followup.send("⏰ Timeout API Riot.")
        except Exception as ex:
            return await inter.followup.send(f"❌ Erreur: {ex}")

    # Parse du rang
    display_name = pseudo if not tag else f"{pseudo}#{tag}"

    # Construction de l'embed
    e = discord.Embed(
        title=f"⚔️ {display_name}",
        description=f"**Profil League of Legends** • {region.upper()}",
        color=discord.Color.blurple()
    )

    icon_url = f"https://ddragon.leagueoflegends.com/cdn/14.1.1/img/profileicon/{profile_icon}.png"
    e.set_thumbnail(url=icon_url)
    e.add_field(name="🎮 Niveau Invocateur", value=f"**{summ_level}**", inline=True)

    if not rank_data:
        e.add_field(name="🏆 Rang", value="**Non classé**", inline=True)
    else:
        for queue in rank_data:
            queue_type = queue.get("queueType", "")
            if queue_type not in ("RANKED_SOLO_5x5", "RANKED_FLEX_SR"):
                continue

            tier   = queue.get("tier", "UNRANKED")
            div    = queue.get("rank", "")
            lp     = queue.get("leaguePoints", 0)
            wins   = queue.get("wins", 0)
            losses = queue.get("losses", 0)
            total  = wins + losses
            wr     = round((wins / total) * 100, 1) if total > 0 else 0
            hot    = queue.get("hotStreak", False)
            veteran= queue.get("veteran", False)

            rank_emoji = LOL_RANK_EMOJIS.get(tier, "🎮")
            rank_color = LOL_RANK_COLORS.get(tier, 0x5865f2)
            e.color    = discord.Color(rank_color)

            queue_label = "SoloQ" if queue_type == "RANKED_SOLO_5x5" else "FlexQ"

            badges = ""
            if hot:     badges += " 🔥 **Hot Streak**"
            if veteran: badges += " 🎖️ **Vétéran**"

            e.add_field(
                name=f"{rank_emoji} {queue_label}",
                value=(
                    f"**{tier} {div}** — {lp} LP\n"
                    f"W/L: **{wins}W/{losses}L** ({wr}%){badges}"
                ),
                inline=False
            )

    e.set_footer(text="Données via Riot Games API • Peut être légèrement en retard")
    e.timestamp = datetime.datetime.utcnow()

    view = discord.ui.View()
    op_url = f"https://www.op.gg/summoners/{region}/{urllib.parse.quote(display_name.replace('#','-'))}"
    view.add_item(discord.ui.Button(label="OP.GG", url=op_url, emoji="🔗", style=discord.ButtonStyle.link))

    await inter.followup.send(embed=e, view=view)


# ════════════════════════════════════════════════════════════════
#  TRACKER — APEX LEGENDS
# ════════════════════════════════════════════════════════════════

APEX_RANK_COLORS = {
    "Rookie":    0x9ca3af, "Bronze":    0x92400e, "Silver": 0xd1d5db,
    "Gold":      0xf59e0b, "Platinum":  0x06b6d4, "Diamond": 0x8b5cf6,
    "Master":    0xef4444, "Predator":  0xf97316,
}

@tracker_group.command(name="apex", description="Voir les stats Apex Legends d'un joueur")
@app_commands.describe(pseudo="Pseudo du joueur", plateforme="Plateforme")
@app_commands.choices(plateforme=[
    app_commands.Choice(name="PC (Origin/EA)", value="PC"),
    app_commands.Choice(name="PlayStation",    value="PS4"),
    app_commands.Choice(name="Xbox",           value="X1"),
    app_commands.Choice(name="Switch",         value="Switch"),
])
async def tracker_apex(inter: discord.Interaction, pseudo: str, plateforme: str = "PC"):
    await inter.response.defer()

    apex_key = os.getenv("APEX_API_KEY", "")
    if not apex_key:
        # Fallback : stats basiques sans clé via tracker.gg
        view = discord.ui.View()
        tracker_url = f"https://apex.tracker.gg/apex/profile/{plateforme.lower()}/{urllib.parse.quote(pseudo)}/overview"
        view.add_item(discord.ui.Button(
            label=f"Voir {pseudo} sur Apex Tracker",
            url=tracker_url, emoji="🔗", style=discord.ButtonStyle.link))
        e = embed_base(
            "⚠️ Clé API Apex manquante",
            f"Ajoute `APEX_API_KEY=ta_cle` dans le `.env` pour les stats détaillées.\n"
            f"[Obtenir une clé gratuite](https://apexlegendsapi.com/)\n\n"
            f"En attendant, tu peux voir le profil de **{pseudo}** via le bouton ⬇️",
            discord.Color.orange()
        )
        return await inter.followup.send(embed=e, view=view)

    async with aiohttp.ClientSession() as session:
        url = f"https://api.mozambiquehe.re/bridge?version=5&platform={plateforme}&player={urllib.parse.quote(pseudo)}"
        headers = {
        "User-Agent": "DiscordBot-ApexTracker/1.0",
        "auth": apex_key  # L'API accepte "auth" en header ou en paramètre d'URL
    }

        try:
            async with session.get(url, headers=headers) as resp:
                # <--- Encore un nouveau décalage ici pour le contenu du GET
                data = await resp.json()
                if resp.status == 404:
                    return await inter.followup.send(
                        embed=embed_base("❌ Joueur introuvable",
                            f"**{pseudo}** introuvable sur {plateforme}.", discord.Color.red()))
                if resp.status != 200:
                    return await inter.followup.send(f"❌ Erreur API ({resp.status}).")
                data = await resp.json()
        except asyncio.TimeoutError:
            return await inter.followup.send("⏰ Timeout.")
        except Exception as ex:
            return await inter.followup.send(f"❌ Erreur: {ex}")

    if "Error" in data:
        return await inter.followup.send(
            embed=embed_base("❌ Erreur", data["Error"], discord.Color.red()))

    global_data = data.get("global", {})
    legend_data = data.get("legends", {}).get("selected", {})
    realtime    = data.get("realtime", {})

    name      = global_data.get("name", pseudo)
    level     = global_data.get("level", "?")
    rank_data = global_data.get("rank", {})
    br_rank   = rank_data.get("rankName", "Non classé")
    br_div    = rank_data.get("rankDiv", "")
    br_rp     = rank_data.get("rankScore", 0)
    rank_img  = rank_data.get("rankImg", "")

    # Arena rank
    arena_data = global_data.get("arena", {})
    arena_rank = arena_data.get("rankName", "")

    # Légende sélectionnée
    legend_name   = legend_data.get("LegendName", "?")
    legend_img    = legend_data.get("ImgAssets", {}).get("icon", "")
    legend_stats  = legend_data.get("data", [])

    # Stats en temps réel
    online     = realtime.get("isOnline", 0)
    in_game    = realtime.get("isInGame", 0)
    current_state = realtime.get("currentStateAsText", "?")

    rank_full  = f"{br_rank} {br_div}".strip() if br_div else br_rank
    rank_color = next((v for k, v in APEX_RANK_COLORS.items() if k.lower() in br_rank.lower()), 0x5865f2)

    status_str = "🟢 En ligne" if online else "⚫ Hors ligne"
    if online and in_game: status_str = "🎮 En partie"

    e = discord.Embed(
        title=f"🎮 {name}",
        description=f"**Stats Apex Legends** • {plateforme} • {status_str}",
        color=discord.Color(rank_color)
    )

    e.add_field(name="🏆 Rang BR",     value=f"**{rank_full}**\n{br_rp:,} RP", inline=True)
    e.add_field(name="⭐ Niveau",      value=f"**{level}**",                    inline=True)
    e.add_field(name="🎭 Légende",     value=f"**{legend_name}**",              inline=True)

    if arena_rank:
        e.add_field(name="🏟️ Rang Arenas", value=f"**{arena_rank}**", inline=True)

    # Stats de la légende sélectionnée
    if legend_stats:
        stats_lines = []
        for stat in legend_stats[:4]:
            stats_lines.append(f"**{stat.get('name','?')}:** {stat.get('value','?'):,}")
        e.add_field(name=f"📊 Stats {legend_name}", value="\n".join(stats_lines), inline=False)

    if rank_img:     e.set_thumbnail(url=rank_img)
    if legend_img:   e.set_author(name=f"Légende: {legend_name}", icon_url=legend_img)

    e.set_footer(text="Données via ApexLegendsAPI")
    e.timestamp = datetime.datetime.utcnow()

    view = discord.ui.View()
    tracker_url = f"https://apex.tracker.gg/apex/profile/{plateforme.lower()}/{urllib.parse.quote(pseudo)}/overview"
    view.add_item(discord.ui.Button(label="Apex Tracker", url=tracker_url, emoji="🔗", style=discord.ButtonStyle.link))

    await inter.followup.send(embed=e, view=view)


# ════════════════════════════════════════════════════════════════
#  TRACKER — Enregistrement du groupe
# ════════════════════════════════════════════════════════════════

bot.tree.add_command(tracker_group)

# ════════════════════════════════════════════════════════════════
#  HELP
# ════════════════════════════════════════════════════════════════
@bot.tree.command(name="help")
async def help_cmd(inter):
    e = discord.Embed(title="📖 Aide", color=discord.Color.blurple())
    e.set_thumbnail(url=bot.user.display_avatar.url)
    cats = {
        "🎵 Musique":         "`/music play/pause/resume/skip/stop/leave/queue/volume/shuffle/nowplaying`",
        "🛡️ Anti-Raid":       "`/antiraid setup/automod/whitelist/status/unlock/infractions`",
        "🔨 Administration":  "`/admin ban/unban/kick/timeout/mute/unmute/tempmute/tempban/warn/purge/massrole/stats_mod`",
        "🎰 Casino":          "`/casino slots/blackjack/coinflip/roulette/dice/horse`",
        "💰 Économie":        "`/eco solde/daily/give/leaderboard/work/crime/addmoney`",
        "🎮 Jeux":            "`/game quiz/wordle/tictactoe/pendu/nombre/shifumi/akinator/devinette/trivia_score`",
        "😄 Fun":             "`/fun 8ball/citation/blague/choose/roll/timer/encode/decode/morse/password/urban/catfact`",
        "📈 Niveaux":         "`/level rank/leaderboard/setreward/addxp/setlevel`",
        "🛒 Shop":            "`/shop add/remove/list/buy`",
        "💸 Économie admin":  "`/eco addmoney/removemoney`",
        "🎉 Giveaway":        "`/giveaway` `/greroll`",
        "💡 Suggestion":      "`/suggestion`",
        "📢 Annonce":         "`/annonce`",
        "📊 Sondage":         "`/poll`",
        "🎫 Ticket":          "`/ticket`",
        "ℹ️ Info":            "`/serverinfo/userinfo/avatar/ping/botinfo`",
        "🖥️ Dashboard":       f"[Ouvrir le panel](http://localhost:{DASHBOARD_PORT})",
    }
    for cat, cmds in cats.items():
        e.add_field(name=cat, value=cmds, inline=False)
    await inter.response.send_message(embed=e, ephemeral=True)

# ════════════════════════════════════════════════════════════════
#  DASHBOARD FLASK
# ════════════════════════════════════════════════════════════════
flask_app = Flask(__name__)
flask_app.secret_key = DASHBOARD_SECRET

# ── Template HTML complet ──
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🤖 Bot Dashboard</title>
<style>
  :root {
    --bg: #0d1117; --bg2: #161b22; --bg3: #21262d;
    --accent: #58a6ff; --accent2: #3fb950; --danger: #f85149;
    --warn: #d29922; --text: #c9d1d9; --border: #30363d;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:'Segoe UI',sans-serif; min-height:100vh; }
  .navbar { background:var(--bg2); border-bottom:1px solid var(--border); padding:12px 24px;
            display:flex; align-items:center; justify-content:space-between; position:sticky; top:0; z-index:100; }
  .navbar h1 { color:var(--accent); font-size:1.4rem; }
  .navbar .nav-links a { color:var(--text); text-decoration:none; margin-left:20px; padding:6px 14px;
                          border-radius:6px; transition:.2s; }
  .navbar .nav-links a:hover { background:var(--bg3); color:var(--accent); }
  .container { max-width:1200px; margin:0 auto; padding:24px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:16px; margin-bottom:24px; }
  .card { background:var(--bg2); border:1px solid var(--border); border-radius:12px; padding:20px; }
  .card h2 { font-size:1rem; color:var(--accent); margin-bottom:12px; display:flex; align-items:center; gap:8px; }
  .stat { font-size:2rem; font-weight:bold; color:var(--text); }
  .stat-label { font-size:.8rem; color:#8b949e; margin-top:4px; }
  .badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:.75rem; font-weight:600; }
  .badge-green { background:#1a3a1a; color:var(--accent2); }
  .badge-red { background:#3a1a1a; color:var(--danger); }
  .badge-blue { background:#1a2a3a; color:var(--accent); }
  .badge-warn { background:#3a2a1a; color:var(--warn); }
  table { width:100%; border-collapse:collapse; }
  th, td { padding:10px 14px; text-align:left; border-bottom:1px solid var(--border); font-size:.9rem; }
  th { color:var(--accent); font-weight:600; background:var(--bg3); }
  tr:hover { background:var(--bg3); }
  .form-group { margin-bottom:16px; }
  .form-group label { display:block; margin-bottom:6px; font-size:.9rem; color:#8b949e; }
  .form-group input, .form-group select, .form-group textarea {
    width:100%; background:var(--bg3); border:1px solid var(--border); border-radius:8px;
    padding:10px 14px; color:var(--text); font-size:.9rem; outline:none; }
  .form-group input:focus, .form-group select:focus { border-color:var(--accent); }
  .btn { display:inline-flex; align-items:center; gap:6px; padding:8px 18px; border:none;
         border-radius:8px; cursor:pointer; font-size:.9rem; font-weight:600; transition:.2s; text-decoration:none; }
  .btn-primary { background:var(--accent); color:#000; }
  .btn-primary:hover { background:#79c0ff; }
  .btn-danger { background:var(--danger); color:#fff; }
  .btn-danger:hover { background:#ff7b72; }
  .btn-success { background:var(--accent2); color:#000; }
  .btn-success:hover { background:#56d364; }
  .btn-warn { background:var(--warn); color:#000; }
  .alert { padding:12px 16px; border-radius:8px; margin-bottom:16px; font-size:.9rem; }
  .alert-success { background:#1a3a1a; color:var(--accent2); border:1px solid #2ea043; }
  .alert-danger  { background:#3a1a1a; color:var(--danger);  border:1px solid var(--danger); }
  .tabs { display:flex; gap:8px; margin-bottom:20px; flex-wrap:wrap; }
  .tab { padding:8px 18px; border-radius:8px; cursor:pointer; background:var(--bg2); border:1px solid var(--border); transition:.2s; color:var(--text); font-size:.9rem; }
  .tab.active, .tab:hover { background:var(--accent); color:#000; border-color:var(--accent); }
  .tab-content { display:none; } .tab-content.active { display:block; }
  .progress-bar { height:8px; background:var(--bg3); border-radius:4px; overflow:hidden; }
  .progress-fill { height:100%; background:var(--accent); border-radius:4px; transition:width .3s; }
  .login-container { max-width:400px; margin:100px auto; }
  .login-container .card { text-align:center; }
  .login-container h2 { color:var(--accent); margin-bottom:24px; font-size:1.5rem; }
  .server-card { display:flex; align-items:center; gap:12px; padding:12px; background:var(--bg3);
                 border-radius:8px; margin-bottom:8px; border:1px solid var(--border); }
  .server-card img { width:40px; height:40px; border-radius:50%; }
  .server-card .info { flex:1; }
  .server-card .info h3 { font-size:.95rem; }
  .server-card .info p { font-size:.8rem; color:#8b949e; }
  @media(max-width:600px) { .grid { grid-template-columns:1fr; } .navbar { flex-direction:column; gap:12px; } }
</style>
</head>
<body>
{% if not session.get('logged_in') %}
<div class="login-container">
  <div class="card">
    <h2>🤖 Bot Dashboard</h2>
    {% for msg in get_flashed_messages() %}
    <div class="alert alert-danger">{{ msg }}</div>
    {% endfor %}
    <form method="POST" action="/login">
      <div class="form-group"><label>Mot de passe admin</label>
        <input type="password" name="password" placeholder="••••••••" required></div>
      <button type="submit" class="btn btn-primary" style="width:100%">Se connecter</button>
    </form>
  </div>
</div>
{% else %}
<div class="navbar">
  <h1>🤖 Bot Dashboard</h1>
  <div class="nav-links">
    <a href="/">🏠 Accueil</a>
    <a href="/servers">🌍 Serveurs</a>
    <a href="/economy">💰 Économie</a>
    <a href="/xp">📈 XP</a>
    <a href="/moderation">🛡️ Modération</a>
    <a href="/settings">⚙️ Paramètres</a>
    <a href="/logout">🚪 Déconnexion</a>
  </div>
</div>
<div class="container">
  {% for msg in get_flashed_messages(with_categories=true) %}
  <div class="alert alert-{{ msg[0] if msg[0] in ['success','danger'] else 'success' }}">{{ msg[1] }}</div>
  {% endfor %}
  {{ content | safe }}
</div>
{% endif %}

<script>
function showTab(tabName) {
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById(tabName).classList.add('active');
  event.target.classList.add('active');
}
</script>
</body>
</html>
"""

def render(content):
    from flask import render_template_string
    return render_template_string(DASHBOARD_HTML, content=content)

def require_login(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not flask_session.get("logged_in"):
            return redirect("/")
        return f(*args, **kwargs)
    return decorated

@flask_app.route("/", methods=["GET"])
def dashboard_home():
    if not flask_session.get("logged_in"):
        return render("")
    
    guilds     = bot.guilds
    total_mem  = sum(g.member_count for g in guilds)
    uptime     = time.time() - bot_stats["start_time"]
    h, r       = divmod(int(uptime), 3600); m_, s = divmod(r, 60)
    latency    = round(bot.latency * 1000)

    # --- CORRECTION ICI : On génère le HTML des musiques AVANT ---
    music_html = ""
    if music_current:
        for gid, track in music_current.items():
            guild = bot.get_guild(int(gid))
            g_name = guild.name if guild else f"ID: {gid}"
            music_html += f"""
            <div class="server-card">
                <div class="info">
                    <h3>{g_name}</h3>
                    <p>{track['title']} | Demandé par {track['requester']}</p>
                </div>
            </div>"""
    else:
        music_html = '<p style="color:#8b949e">Aucune musique en cours.</p>'

    # --- FIN DE LA CORRECTION ---

    content = f"""
    <h2 style="margin-bottom:20px;color:var(--accent)">📊 Vue d'ensemble</h2>
    <div class="grid">
      <div class="card">
        <h2>🌍 Serveurs</h2>
        <div class="stat">{len(guilds)}</div>
        <div class="stat-label">Serveurs Discord</div>
      </div>
      <div class="card">
        <h2>👥 Membres</h2>
        <div class="stat">{total_mem}</div>
        <div class="stat-label">Total tous serveurs</div>
      </div>
      <div class="card">
        <h2>🏓 Latence</h2>
        <div class="stat">{latency}ms</div>
        <div class="stat-label">Ping WebSocket</div>
      </div>
      <div class="card">
        <h2>⏱️ Uptime</h2>
        <div class="stat">{h}h{m_}m</div>
        <div class="stat-label">Depuis le dernier démarrage</div>
      </div>
      <div class="card">
        <h2>🎵 Chansons jouées</h2>
        <div class="stat">{bot_stats['songs_played']}</div>
        <div class="stat-label">Depuis le démarrage</div>
      </div>
      <div class="card">
        <h2>🎮 Parties jouées</h2>
        <div class="stat">{bot_stats['games_played']}</div>
        <div class="stat-label">Depuis le démarrage</div>
      </div>
    </div>

    <div class="card">
      <h2>🎵 Musique en cours</h2>
      {music_html}
    </div>
    """
    return render(content)

@flask_app.route("/login", methods=["POST"])
def login():
    if request.form.get("password") == DASHBOARD_ADMIN_PASS:
        flask_session["logged_in"] = True
        return redirect("/")
    flash("Mot de passe incorrect !", "danger")
    return redirect("/")

@flask_app.route("/logout")
def logout():
    flask_session.clear()
    return redirect("/")

@flask_app.route("/servers")
@require_login
def servers():
    guilds = bot.guilds
    cards  = ""
    for g in guilds:
        icon_url = g.icon.url if g.icon else "https://cdn.discordapp.com/embed/avatars/0.png"
        cfg      = get_antiraid_config(g.id)
        music_active = g.id in music_current
        cards += f"""
        <div class="server-card">
          <img src="{icon_url}" alt="icon">
          <div class="info">
            <h3>{g.name}</h3>
            <p>{g.member_count} membres • {len(g.channels)} salons • {len(g.roles)} rôles</p>
          </div>
          <span class="badge {'badge-green' if cfg['enabled'] else 'badge-red'}">
            {'🛡️ Anti-Raid ON' if cfg['enabled'] else '⚠️ Anti-Raid OFF'}
          </span>
          {'<span class="badge badge-blue" style="margin-left:8px">🎵 Musique</span>' if music_active else ''}
        </div>"""
    content = f"""
    <h2 style="margin-bottom:20px;color:var(--accent)">🌍 Serveurs ({len(guilds)})</h2>
    <div class="card">{cards or '<p style="color:#8b949e">Aucun serveur.</p>'}</div>"""
    return render(content)

@flask_app.route("/economy")
@require_login
def economy():
    top = sorted(economy_db.items(), key=lambda x: x[1], reverse=True)[:20]
    rows = ""
    for i, (uid, bal) in enumerate(top, 1):
        user = bot.get_user(int(uid))
        name = user.name if user else f"ID:{uid}"
        medal = "🥇" if i==1 else ("🥈" if i==2 else ("🥉" if i==3 else str(i)))
        rows += f"<tr><td>{medal}</td><td>{name}</td><td><b>{bal:,} 🪙</b></td></tr>"
    content = f"""
    <h2 style="margin-bottom:20px;color:var(--accent)">💰 Économie</h2>
    <div class="card">
      <h2>🏆 Top 20 les plus riches</h2>
      <table><thead><tr><th>#</th><th>Joueur</th><th>Solde</th></tr></thead>
      <tbody>{rows or '<tr><td colspan=3>Aucune donnée.</td></tr>'}</tbody></table>
    </div>"""
    return render(content)

@flask_app.route("/xp")
@require_login
def xp_page():
    data = sorted(xp_db.items(), key=lambda x: (x[1].get("level",1)*100 + x[1].get("xp",0)), reverse=True)[:20]
    rows = ""
    for i, (uid, d) in enumerate(data, 1):
        user = bot.get_user(int(uid))
        name = user.name if user else f"ID:{uid}"
        lvl  = d.get("level", 1); xp = d.get("xp", 0); needed = lvl * 100
        pct  = int((xp / needed) * 100)
        medal = "🥇" if i==1 else ("🥈" if i==2 else ("🥉" if i==3 else str(i)))
        rows += f"""<tr>
          <td>{medal}</td><td>{name}</td>
          <td><span class="badge badge-blue">Niv. {lvl}</span></td>
          <td>{xp}/{needed}
            <div class="progress-bar" style="margin-top:4px">
              <div class="progress-fill" style="width:{pct}%"></div>
            </div>
          </td>
        </tr>"""
    content = f"""
    <h2 style="margin-bottom:20px;color:var(--accent)">📈 Classement XP</h2>
    <div class="card">
      <h2>🏆 Top 20 les plus actifs</h2>
      <table><thead><tr><th>#</th><th>Joueur</th><th>Niveau</th><th>XP</th></tr></thead>
      <tbody>{rows or '<tr><td colspan=4>Aucune donnée.</td></tr>'}</tbody></table>
    </div>"""
    return render(content)

@flask_app.route("/moderation")
@require_login
def moderation():
    # Top warns
    warn_data = sorted(warns_db.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    rows = ""
    for uid, warns in warn_data:
        if not warns: continue
        user = bot.get_user(int(uid))
        name = user.name if user else f"ID:{uid}"
        rows += f"<tr><td>{name}</td><td><span class='badge badge-warn'>{len(warns)} warns</span></td></tr>"
    content = f"""
    <h2 style="margin-bottom:20px;color:var(--accent)">🛡️ Modération</h2>
    <div class="grid">
      <div class="card">
        <h2>⚠️ Membres les plus warnés</h2>
        <table><thead><tr><th>Membre</th><th>Warns</th></tr></thead>
        <tbody>{rows or '<tr><td colspan=2>Aucun warn.</td></tr>'}</tbody></table>
      </div>
      <div class="card">
        <h2>🎟️ Tickets actifs</h2>
        <div class="stat">{len(tickets_db)}</div>
        <div class="stat-label">Tickets ouverts en ce moment</div>
      </div>
      <div class="card">
        <h2>⏰ Actions temporaires</h2>
        <div class="stat">{len(temp_actions)}</div>
        <div class="stat-label">TempMute/TempBan actifs</div>
      </div>
    </div>"""
    return render(content)





@flask_app.route("/settings", methods=["GET","POST"])
@require_login
def settings():
    guilds = bot.guilds
    guild_options = "".join(f'<option value="{g.id}">{g.name}</option>' for g in guilds)

    if request.method == "POST":
        action   = request.form.get("action")
        guild_id = request.form.get("guild_id")
        if not guild_id: flash("Sélectionne un serveur.", "danger"); return redirect("/settings")

        if action == "toggle_antiraid":
            cfg = get_antiraid_config(guild_id)
            cfg["enabled"] = not cfg["enabled"]
            antiraid_config[guild_id] = cfg
            status = "activé" if cfg["enabled"] else "désactivé"
            flash(f"✅ Anti-Raid {status} sur {bot.get_guild(int(guild_id)).name if bot.get_guild(int(guild_id)) else guild_id}.", "success")

        elif action == "set_antiraid":
            cfg = get_antiraid_config(guild_id)
            cfg["join_threshold"] = int(request.form.get("join_threshold", 10))
            cfg["join_window"]    = int(request.form.get("join_window", 10))
            cfg["action"]         = request.form.get("ar_action", "lock")
            cfg["min_account_age"]= int(request.form.get("min_age", 7))
            cfg["anti_link"]      = "anti_link" in request.form
            cfg["anti_caps"]      = "anti_caps" in request.form
            cfg["anti_mention_spam"] = "anti_mention_spam" in request.form
            antiraid_config[guild_id] = cfg
            flash("✅ Anti-Raid mis à jour !", "success")

        elif action == "add_economy":
            uid    = request.form.get("user_id")
            amount = int(request.form.get("amount", 0))
            if uid and amount > 0:
                economy_db[uid] = economy_db[uid] + amount
                flash(f"✅ +{amount} 🪙 ajoutés à ID:{uid}.", "success")

        elif action == "clear_warns":
            uid = request.form.get("user_id")
            if uid:
                warns_db[uid] = []
                flash(f"✅ Warns de ID:{uid} effacés.", "success")

        return redirect("/settings")

    content = f"""
    <h2 style="margin-bottom:20px;color:var(--accent)">⚙️ Paramètres</h2>
    <div class="tabs">
      <div class="tab active" onclick="showTab('tab-antiraid')">🛡️ Anti-Raid</div>
      <div class="tab" onclick="showTab('tab-economy')">💰 Économie</div>
      <div class="tab" onclick="showTab('tab-warns')">⚠️ Warns</div>
    </div>

    <div id="tab-antiraid" class="tab-content active">
      <div class="card">
        <h2>🛡️ Configuration Anti-Raid</h2>
        <form method="POST">
          <input type="hidden" name="action" value="set_antiraid">
          <div class="form-group">
            <label>Serveur</label>
            <select name="guild_id">{guild_options}</select>
          </div>
          <div class="grid" style="grid-template-columns:1fr 1fr;">
            <div class="form-group"><label>Joins maximum</label>
              <input type="number" name="join_threshold" value="10" min="2" max="100"></div>
            <div class="form-group"><label>Fenêtre (secondes)</label>
              <input type="number" name="join_window" value="10" min="1" max="60"></div>
          </div>
          <div class="form-group"><label>Action sur raid</label>
            <select name="ar_action">
              <option value="lock">🔒 Lock (verrouiller les salons)</option>
              <option value="kick">👢 Kick (expulser)</option>
              <option value="ban">🔨 Ban (bannir)</option>
            </select>
          </div>
          <div class="form-group"><label>Âge minimum du compte (jours)</label>
            <input type="number" name="min_age" value="7" min="0" max="365"></div>
          <div class="form-group">
            <label><input type="checkbox" name="anti_link" style="width:auto;margin-right:8px">Anti-Liens</label><br>
            <label><input type="checkbox" name="anti_caps" style="width:auto;margin-right:8px">Anti-Caps (majuscules excessives)</label><br>
            <label><input type="checkbox" name="anti_mention_spam" checked style="width:auto;margin-right:8px">Anti-Mention Spam</label>
          </div>
          <button type="submit" class="btn btn-primary">💾 Sauvegarder</button>
        </form>
        <br>
        <form method="POST" style="display:inline">
          <input type="hidden" name="action" value="toggle_antiraid">
          <div class="form-group"><label>Serveur pour toggle</label>
            <select name="guild_id">{guild_options}</select></div>
          <button type="submit" class="btn btn-warn">⚡ Toggle Anti-Raid</button>
        </form>
      </div>
    </div>

    <div id="tab-economy" class="tab-content">
      <div class="card">
        <h2>💰 Ajouter des pièces</h2>
        <form method="POST">
          <input type="hidden" name="action" value="add_economy">
          <div class="form-group"><label>Serveur (contexte)</label>
            <select name="guild_id">{guild_options}</select></div>
          <div class="form-group"><label>ID Discord de l'utilisateur</label>
            <input type="text" name="user_id" placeholder="123456789012345678"></div>
          <div class="form-group"><label>Montant à ajouter</label>
            <input type="number" name="amount" value="1000" min="1"></div>
          <button type="submit" class="btn btn-success">💸 Ajouter</button>
        </form>
      </div>
    </div>

    <div id="tab-warns" class="tab-content">
      <div class="card">
        <h2>⚠️ Effacer des warns</h2>
        <form method="POST">
          <input type="hidden" name="action" value="clear_warns">
          <div class="form-group"><label>Serveur (contexte)</label>
            <select name="guild_id">{guild_options}</select></div>
          <div class="form-group"><label>ID Discord de l'utilisateur</label>
            <input type="text" name="user_id" placeholder="123456789012345678"></div>
          <button type="submit" class="btn btn-danger">🗑️ Effacer les warns</button>
        </form>
      </div>
    </div>
    """
    return render(content)

@flask_app.route("/api/stats")
@require_login
def api_stats():
    return jsonify({
        "guilds":        len(bot.guilds),
        "members":       sum(g.member_count for g in bot.guilds),
        "latency_ms":    round(bot.latency * 1000),
        "songs_played":  bot_stats["songs_played"],
        "games_played":  bot_stats["games_played"],
        "uptime_seconds":int(time.time() - bot_stats["start_time"]),
        "music_current": {str(k): v["title"] for k, v in music_current.items()},
        "queue_sizes":   {str(k): len(v) for k, v in music_queues.items()},
    })

@flask_app.route("/api/antiraid/<guild_id>", methods=["GET","POST"])
@require_login
def api_antiraid(guild_id):
    if request.method == "POST":
        data = request.get_json()
        cfg  = get_antiraid_config(guild_id)
        cfg.update(data)
        antiraid_config[guild_id] = cfg
        return jsonify({"ok": True})
    return jsonify(get_antiraid_config(guild_id))

def run_dashboard():
    """Lance Flask dans un thread séparé."""
    flask_app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=False, use_reloader=False)






# ════════════════════════════════════════════════════════════════
#  LANCEMENT
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    token = os.getenv("VOTRE_TOKEN")

    # Lance le dashboard dans un thread séparé
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    print(f"🌐 Dashboard démarré sur http://localhost:{DASHBOARD_PORT}")
    print(f"🔑 Mot de passe: {DASHBOARD_ADMIN_PASS}")

    # Lance le bot Discord
    bot.run(token)
