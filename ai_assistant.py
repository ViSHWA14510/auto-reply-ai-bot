"""
AI assistant that auto-replies to users when the admin has marked themselves
offline (see /online and /offline commands).

Supports two interchangeable providers — pick one with AI_PROVIDER in config.py:
  - "anthropic"         -> Claude, via the official Anthropic SDK.
  - "openai_compatible" -> OpenAI's own ChatGPT API, OR any OpenAI-compatible
                            endpoint such as Groq or Google Gemini (both have
                            genuinely free tiers) — see config.py for presets.

Conversation history is kept in memory per user, so the AI remembers the last
few exchanges within a session. History resets if the bot process restarts —
that's fine for short support chats; swap _history for a database table if you
need it to survive restarts.
"""

from typing import Optional

from config import (
    AI_PROVIDER,
    AI_SYSTEM_PROMPT,
    AI_MAX_HISTORY_TURNS,
    ANTHROPIC_API_KEY,
    AI_MODEL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)

_history: dict[int, list[dict]] = {}


def _trim_history(user_id: int):
    max_messages = AI_MAX_HISTORY_TURNS * 2  # each turn = 1 user + 1 assistant message
    if len(_history.get(user_id, [])) > max_messages:
        _history[user_id] = _history[user_id][-max_messages:]


def _call_anthropic(history: list[dict]) -> str:
    from anthropic import Anthropic  # imported lazily so the other provider doesn't need this installed

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=AI_MODEL,
        max_tokens=400,
        system=AI_SYSTEM_PROMPT,
        messages=history,
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()


def _call_openai_compatible(history: list[dict]) -> str:
    from openai import OpenAI  # imported lazily so the other provider doesn't need this installed

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=400,
        messages=[{"role": "system", "content": AI_SYSTEM_PROMPT}] + history,
    )
    return (response.choices[0].message.content or "").strip()


def get_ai_reply(user_id: int, user_message: str, user_first_name: str = "") -> Optional[str]:
    """Returns the AI's reply text, or None if the call failed.
    Callers should fall back to forwarding the message to the admin when None.
    """
    history = _history.setdefault(user_id, [])
    history.append({"role": "user", "content": user_message})

    try:
        if AI_PROVIDER == "anthropic":
            reply_text = _call_anthropic(history)
        elif AI_PROVIDER == "openai_compatible":
            reply_text = _call_openai_compatible(history)
        else:
            raise ValueError(f"Unknown AI_PROVIDER in config.py: {AI_PROVIDER!r}")

        if not reply_text:
            history.pop()
            return None

        history.append({"role": "assistant", "content": reply_text})
        _trim_history(user_id)
        return reply_text

    except Exception as e:
        print(f"[ai_assistant] AI call failed (provider={AI_PROVIDER}): {e}")
        if history:
            history.pop()  # remove the unanswered user message
        return None


def reset_history(user_id: int):
    _history.pop(user_id, None)
