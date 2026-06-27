# Telegram Bot — Welcome, Channel Links, Broadcast, AI Support & Railway Hosting

A ready-to-deploy Telegram bot that:
- Greets new users with a photo welcome message and saves them to a database
- Hands out **personal, one-time, auto-expiring invite links** to your channels/groups
- **Forwards user messages to you**, or **auto-replies with AI** (Claude, ChatGPT, Groq, or Gemini) whenever you mark yourself offline
- Lets you **broadcast** any message to every user who has started the bot, with a live progress counter
- Deploys to **Railway** in a few minutes for free 24/7 hosting

---

## Table of contents
- [Commands](#commands)
- [How it behaves](#how-it-behaves)
- [Project structure](#project-structure)
- [Setup](#setup)
- [Run locally](#run-locally)
- [Deploy to Railway](#deploy-to-railway)
- [Environment variables reference](#environment-variables-reference)
- [AI assistant details](#ai-assistant-details)
- [How the auto-expiring links work](#how-the-auto-expiring-links-work)

---

## Commands

### User commands
| Command | What it does |
|---|---|
| `/start` | Sends the welcome photo + caption, saves the user to the database, and shows a "Get Channel Links 🔗" button. |
| `/link` | Generates a fresh, **personal, single-use** invite link for every channel/group in your config, shown as tappable buttons. Each link expires after 1 hour (configurable) or after first use, whichever comes first. |
| *(any plain text)* | Not a command — just a regular message. It's forwarded to the admin(s), **or** answered instantly by the AI assistant if you're marked `/offline`. The user always gets a reply either way. |

> There's no `/reply` command — to answer a specific user, reply (in Telegram) to their forwarded notification message. See [How it behaves](#how-it-behaves).

### Admin-only commands
*(Restricted to the Telegram user IDs listed in `ADMIN_IDS`. Silently ignored for everyone else.)*

| Command | What it does |
|---|---|
| `/broadcast` | Reply to any message with this command to send that message to **every** user who has ever pressed `/start`. Shows a live-updating status (total / sent / blocked / failed) and automatically removes users who blocked the bot. |
| `/stats` | Shows the total number of users currently stored in the database. |
| `/online` | Marks you as online. New user messages are forwarded to you as usual; the AI stays silent. |
| `/offline` | Marks you as offline. New user messages get an **instant AI reply**, and you're still notified of every exchange so you can step in anytime. |
| `/status` | Shows whether you're currently marked online or offline. This is saved in the database, so it survives restarts and redeploys. |

---

## How it behaves

- **New user** sends `/start` → saved to the database, sees the welcome photo and a button for channel links.
- **User asks something in plain text:**
  - If you're online (default) → the message is forwarded to all `ADMIN_IDS`, and the user gets a polite "we'll get back to you" reply.
  - If you're `/offline` and the AI assistant is enabled → the user gets an instant AI-generated reply, *and* you're still notified of the question and the AI's answer (tagged 🤖) so you stay in the loop.
  - If the AI call fails for any reason (bad key, rate limit, no internet) → it automatically falls back to forwarding to you. The user is never left without a response.
- **Replying to a user:** Telegram won't let you message a random user ID directly, so the bot relays it for you — just hit **Reply** on any forwarded notification (or AI auto-reply notification) and type your answer. It's sent straight to that user, and you get a "✅ Sent to user" confirmation. Works for photos, documents, etc. too, not just text. This works even after the AI has already answered — handy for following up personally. (Internally, the bot remembers which notification message maps to which user; this mapping is pruned automatically after 30 days.)
- **You reply to a message with `/broadcast`** → that exact message (text, photo, video, etc. — anything `copy_message` supports) is sent to every stored user, with a live progress message that updates as it sends.

---

## Project structure
```
telegram_bot/
├── bot.py              # entry point — run this
├── config.py           # all settings, read from environment variables
├── database.py         # SQLite user storage + admin online/offline status
├── utils.py            # small-caps text converter used in user-facing copy
├── ai_assistant.py      # Claude / OpenAI-compatible auto-replies
├── handlers/
│   ├── start.py         # /start
│   ├── link.py          # /link + auto-expiring invite links
│   ├── broadcast.py     # /broadcast (with live progress), /stats
│   ├── admin.py         # /online, /offline, /status
│   └── messages.py      # handles free-text user queries (AI or forward-to-admin)
├── requirements.txt
├── Procfile             # tells Railway how to run the bot
├── railway.json         # Railway deploy configuration
├── .env.example         # template for local environment variables
└── .gitignore
```

---

## Setup

### 1. Get a bot token
Message **[@BotFather](https://t.me/BotFather)** on Telegram → `/newbot` → follow the prompts → copy the token it gives you.

### 2. Get your admin (user) ID
Message **[@userinfobot](https://t.me/userinfobot)** → it replies with your numeric Telegram ID. Use this for `ADMIN_IDS`.

### 3. Get your channel/group IDs
1. Add your bot to the channel/group **as an admin**, with "Invite Users via Link" permission enabled.
2. Forward any message from that channel to **[@JsonDumpBot](https://t.me/JsonDumpBot)** — it shows the chat's numeric ID (looks like `-1001234567890`).

All configuration now lives in **environment variables** (read by `config.py`), so the same code runs unchanged locally and on Railway.

---

## Run locally

1. Copy the example env file and fill in your values:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```
   BOT_TOKEN=123456789:ABC...
   ADMIN_IDS=987654321
   CHANNELS_JSON={"📢 Main Channel": -1001234567890, "💬 Discussion Group": -1009876543210}
   WELCOME_PHOTO=https://your-image-url.jpg
   ```

2. Install dependencies and run:
   ```bash
   pip install -r requirements.txt
   python bot.py
   ```
   You should see `Bot is running...`. Message your bot on Telegram and try `/start`.

> `config.py` loads `.env` automatically via `python-dotenv` — you never need to edit `config.py` itself. (You *can* still hardcode values directly in `config.py` if you prefer; environment variables simply take priority when present.)

---

## Deploy to Railway

This bot uses long-polling (`app.run_polling()`), so it needs to run as an **always-on background worker** — not a web service waiting for HTTP requests. Railway handles this well and has a free trial tier.

### 1. Push the project to GitHub
Create a new repo and push this folder to it (`.gitignore` already excludes secrets and the local database).

### 2. Create a new Railway project
1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select your repo.
2. Railway auto-detects Python via `requirements.txt` (using Nixpacks) and uses the start command from `railway.json` / `Procfile` (`python bot.py`) — no build configuration needed.

### 3. Set your environment variables
In the Railway project → your service → **Variables** tab, add each variable from `.env.example` that you need. At minimum:
```
BOT_TOKEN=123456789:ABC...
ADMIN_IDS=987654321
CHANNELS_JSON={"📢 Main Channel": -1001234567890, "💬 Discussion Group": -1009876543210}
WELCOME_PHOTO=https://your-image-url.jpg
AI_PROVIDER=openai_compatible
OPENAI_API_KEY=your_groq_key
```
(See [Environment variables reference](#environment-variables-reference) below for the full list.)

### 4. Persisting the database on Railway
Railway's default filesystem is **ephemeral** — it can be wiped on redeploy. Since `bot_database.db` stores your users and online/offline status, attach a **Volume** so it survives:

1. In your Railway service → **Settings** → **Volumes** → **Add Volume**.
2. Mount it at, e.g., `/data`.
3. Set the environment variable:
   ```
   DATABASE_PATH=/data/bot_database.db
   ```

### 5. Deploy
Railway deploys automatically on every push to your connected branch. Check the **Deploy Logs** for `Bot is running... Press Ctrl+C to stop.` to confirm it's live, then message your bot on Telegram.

> **Don't use serverless/sleeping platforms** (e.g. free-tier Vercel/Netlify functions) for this bot — long-polling needs a continuously running process. Railway, Render, or any small VPS work well.

---

## Environment variables reference

| Variable | Required | Default | Notes |
|---|---|---|---|
| `BOT_TOKEN` | Yes | — | From @BotFather |
| `ADMIN_IDS` | Yes | — | Comma-separated numeric Telegram IDs, e.g. `111,222` |
| `CHANNELS_JSON` | Recommended | built-in placeholder channels | JSON object: `{"label": chat_id, ...}` |
| `LINK_EXPIRY_SECONDS` | No | `3600` | How long each `/link` invite stays valid |
| `WELCOME_PHOTO` | No | placeholder image URL | Public image URL or local file path |
| `DATABASE_PATH` | No | `bot_database.db` | Point this at a mounted Volume path on Railway |
| `AI_ENABLED` | No | `true` | `true`/`false` master switch for the AI assistant |
| `AI_PROVIDER` | No | `openai_compatible` | `openai_compatible` or `anthropic` |
| `ANTHROPIC_API_KEY` | Only if using Claude | — | From console.anthropic.com |
| `AI_MODEL` | No | `claude-sonnet-4-6` | Used only with the `anthropic` provider |
| `OPENAI_API_KEY` | Only if using openai_compatible | — | Groq / OpenAI / Gemini key, depending on `OPENAI_BASE_URL` |
| `OPENAI_BASE_URL` | No | Groq's endpoint | Swap for OpenAI's or Gemini's endpoint — see `.env.example` |
| `OPENAI_MODEL` | No | `llama-3.3-70b-versatile` | Model name for whichever `OPENAI_BASE_URL` you're using |
| `AI_SYSTEM_PROMPT` | No | generic support-assistant prompt | The AI's tone/instructions — edit to match your community's style |
| `AI_KNOWLEDGE_BASE` | No | empty | Particular facts/messages the AI should know and use (pricing, hours, rules, links, promos). Kept separate from `AI_SYSTEM_PROMPT` so you can update facts without touching tone/instructions |
| `AI_MAX_HISTORY_TURNS` | No | `6` | How many past exchanges per user the AI remembers (in-memory, resets on restart) |

---

## AI assistant details

**Set up for Groq by default** — fast, and genuinely free with no credit card. To activate it:
1. Sign up at [console.groq.com](https://console.groq.com).
2. Create an API key there.
3. Set it as `OPENAI_API_KEY`. `AI_PROVIDER` and the Groq URL/model are already correct by default.

| `AI_PROVIDER` | Uses | Free? |
|---|---|---|
| `openai_compatible` → Groq (**default**) | Llama 3.3 70B, very fast | **Yes** — no credit card |
| `openai_compatible` → Google Gemini | Gemini Flash | **Yes** — no credit card |
| `openai_compatible` → OpenAI | ChatGPT | No — pay-per-token |
| `anthropic` | Claude | No — pay-per-token |

**To switch to Claude:** set `AI_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=...`.

**To switch to ChatGPT or Gemini instead of Groq:** keep `AI_PROVIDER=openai_compatible`, just overwrite `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `OPENAI_MODEL` with the preset shown in `.env.example` — no code changes needed, since Groq, Gemini, and OpenAI all speak the same API format.

### Managing what the AI says

Two separate variables control this, on purpose:

- **`AI_SYSTEM_PROMPT`** — the AI's *tone and behavior*: how friendly/formal it is, what it should never do, when to defer to a human. Change this rarely.
- **`AI_KNOWLEDGE_BASE`** — *specific facts* you want it to know and use: pricing, hours, rules, refund policy, links, promos. Put each fact on its own line. Update this often, as your facts change, without touching `AI_SYSTEM_PROMPT` at all.

Example `AI_KNOWLEDGE_BASE`:
```
Subscription price: $10/month, 7-day free trial.
Support hours: 9am-6pm IST, Mon-Sat.
Refunds: full refund within 48 hours of purchase, no questions asked.
Our main channel link: https://t.me/yourchannel
```
The AI is told to use this information when relevant and not contradict it — but it will still say "I'm not sure" for anything not covered here, rather than guessing.

You don't need to redeploy code to change either variable — on Railway, edit the Variable and the bot picks it up on its next restart (Railway restarts the service automatically after a variable change).

**Behavior notes:**
- `/offline` → users get instant AI replies; you're still notified of every question and answer.
- `/online` → back to forward-only, no AI.
- `/status` → check your current mode. Saved in the database, so it survives restarts/redeploys.
- AI call failure of any kind → automatic fallback to forwarding the message to you.
- Conversation memory is per-user, in-memory, and resets on restart (fine for short support chats).
- Every message that reaches you shows the sender's name, username, and a tap-to-copy Telegram ID.
- The AI's own replies are sent as plain text, not bolded/small-caps — only the bot's static messages (welcome, links, acknowledgement) use that styling. See below.

### Message styling

The bot's static user-facing text (welcome message, channel-links message, "thanks for reaching out" acknowledgement) is styled **bold + small caps** together, via `utils.bold()` wrapping `utils.to_small_caps()`. Button labels stay small-caps only (Telegram buttons can't render bold/HTML). To change this, edit the relevant handler in `handlers/` — e.g. drop `bold(...)` to go back to small-caps only, or drop `to_small_caps(...)` to go fully plain-bold.

---

## How the auto-expiring links work

Each time a user sends `/link` (or taps the "Get Channel Links" button), the bot calls Telegram's API to create a **brand-new invite link** for every configured channel, with:
- `member_limit=1` → only that one user can use it
- `expire_date` → 1 hour from now by default (`LINK_EXPIRY_SECONDS`), enforced by Telegram itself
- A scheduled background job that also explicitly revokes the link after expiry, as a safety net

So even if a link is shared further, it stops working after the first join or after expiry — whichever comes first.
