"""
Configuration file for the Telegram Bot.

Every setting below can be supplied as an ENVIRONMENT VARIABLE (this is how
you configure the bot on Railway — see README.md) and falls back to the
hardcoded default on the right if that variable isn't set. That means:
  - Running locally: either edit the defaults below directly, OR put the
    same values in a local .env file (see .env.example).
  - Running on Railway: set these as Variables in the Railway dashboard.
    Nothing in this file needs to change.
"""

import os
import json

# Loads a local .env file if present (harmless/no-op on Railway, where
# variables are injected directly into the environment instead).
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# Get this from @BotFather on Telegram (the /newbot command)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# Telegram user ID(s) allowed to use admin commands (/broadcast, /stats, /online, /offline, /status).
# Get your own numeric ID by messaging @userinfobot on Telegram.
# Env var format: comma-separated, e.g. ADMIN_IDS="123456789,987654321"
_admin_ids_raw = os.environ.get("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()]

# SQLite database file (created automatically on first run, no setup needed).
# On Railway, point this at a path inside a mounted Volume so it survives
# redeploys — see the "Persisting the database on Railway" section in README.md.
DATABASE_PATH = os.environ.get("DATABASE_PATH", "bot_database.db")

# Channels/groups to share via the /link command.
#   Key   = button label shown to the user (emoji optional)
#   Value = channel/group chat_id — must be the NEGATIVE numeric ID, e.g. -1001234567890
#           (NOT the @username). Forward any message from the channel to @JsonDumpBot
#           to find this ID, or add @userinfobot to the channel as admin temporarily.
#
# IMPORTANT: The bot itself must be an ADMIN of each channel/group, with the
# "Invite Users via Link" permission enabled, or link creation will fail.
#
# Env var format: a JSON object, e.g.
#   CHANNELS_JSON={"📢 Main Channel": -1001234567890, "💬 Discussion Group": -1009876543210}
_channels_raw = os.environ.get("CHANNELS_JSON")
if _channels_raw:
    CHANNELS = {label: int(chat_id) for label, chat_id in json.loads(_channels_raw).items()}
else:
    CHANNELS = {
        "📢 Main Channel": -1001234567890,
        "💬 Discussion Group": -1009876543210,
    }

# How long (in seconds) a generated invite link stays valid. Default = 1 hour.
LINK_EXPIRY_SECONDS = int(os.environ.get("LINK_EXPIRY_SECONDS", "3600"))

# Welcome photo shown on /start.
# Can be a public direct image URL ("https://...jpg") or a local file path ("welcome.jpg").
WELCOME_PHOTO = os.environ.get("WELCOME_PHOTO", "https://i.imgur.com/your-welcome-image.jpg")

# ---- AI Assistant (auto-replies to users while the admin is offline) ----

# Master switch. If False, the bot always forwards messages to the admin
# (the AI is never used), regardless of online/offline status.
AI_ENABLED = _get_bool("AI_ENABLED", True)

# Which AI provider to use: "anthropic" (Claude) or "openai_compatible"
# (OpenAI's own ChatGPT API, OR any OpenAI-compatible endpoint — currently
# set up for Groq below, since it's fast and genuinely free).
AI_PROVIDER = os.environ.get("AI_PROVIDER", "openai_compatible")

# --- Provider: anthropic (Claude) ---
# Only used if AI_PROVIDER = "anthropic" above.
# Get this from https://console.anthropic.com -> API Keys
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "PUT_YOUR_ANTHROPIC_API_KEY_HERE")
# claude-sonnet-4-6 is a strong default. For very high message volume, swap
# to "claude-haiku-4-5-20251001" — faster and cheaper, slightly less nuanced.
AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-4-6")

# --- Provider: openai_compatible — currently configured for GROQ (free) ---
# Groq setup (2 steps):
#   1. Sign up at https://console.groq.com (no credit card needed)
#   2. Create an API key there and set it as OPENAI_API_KEY
# That's it — AI_PROVIDER is already set to use it above.
#
# llama-3.3-70b-versatile is a solid all-rounder. For max speed on simple
# queries, swap OPENAI_MODEL to "llama-3.1-8b-instant".
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "PUT_YOUR_GROQ_API_KEY_HERE")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "llama-3.3-70b-versatile")

# --- Want ChatGPT or Gemini instead of Groq? ---
# Just overwrite the 3 variables above with one of these (same OPENAI_* names
# are reused for any OpenAI-compatible provider — no code changes needed):
#
#   ChatGPT (OpenAI — heads up, no real free tier, pay-per-token like Claude):
#     OPENAI_BASE_URL = "https://api.openai.com/v1"
#     OPENAI_MODEL    = "gpt-4.1-mini"     (check platform.openai.com for current models)
#     OPENAI_API_KEY  = your OpenAI key, from platform.openai.com
#
#   Google Gemini (also free, no credit card):
#     OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
#     OPENAI_MODEL    = "gemini-2.5-flash"
#     OPENAI_API_KEY  = your Gemini key, from aistudio.google.com

# Edit this to match your channel/brand — these are the AI's instructions
# (tone, what it should/shouldn't do). Shared by both providers.
AI_SYSTEM_PROMPT = os.environ.get(
    "AI_SYSTEM_PROMPT",
    "You are a friendly, professional support assistant for our Telegram channel. "
    "Answer the user's question concisely and politely, in a few sentences. "
    "If you don't know something specific to this community (exact rules, prices, "
    "schedules, etc.), say you're not sure and that a human admin will follow up "
    "soon — never make up specifics you don't actually know.",
)

# Particular facts/messages you want the AI to know and use when relevant —
# pricing, hours, rules, links, promo text, anything specific to your
# community. Kept separate from AI_SYSTEM_PROMPT on purpose: that variable is
# the AI's *tone and behavior*, this one is *what it knows*. Update this
# whenever your facts change, without touching the instructions above.
#
# Put each fact on its own line. Example:
#   AI_KNOWLEDGE_BASE="Subscription price: $10/month, 7-day free trial.
#   Support hours: 9am-6pm IST, Mon-Sat.
#   Refunds: full refund within 48 hours of purchase, no questions asked.
#   Our main channel link: https://t.me/yourchannel"
AI_KNOWLEDGE_BASE = os.environ.get("AI_KNOWLEDGE_BASE", "")

# How many previous user/assistant exchanges to remember per user, for more
# coherent multi-turn conversations. Higher = more context, more tokens used.
AI_MAX_HISTORY_TURNS = int(os.environ.get("AI_MAX_HISTORY_TURNS", "6"))
