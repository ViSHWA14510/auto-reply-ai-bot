"""Small helper utilities: text formatting used in user-facing bot messages."""

from html import escape

_SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ',
    'g': 'ɢ', 'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ',
    'm': 'ᴍ', 'n': 'ɴ', 'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ',
    's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ', 'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x',
    'y': 'ʏ', 'z': 'ᴢ',
}


def to_small_caps(text: str) -> str:
    """Convert regular text into unicode 'small caps' style text.

    Emoji, numbers, and punctuation are left untouched — only a-z/A-Z letters
    are mapped. Kept here in case you want to switch back; not used by
    default — handlers currently use bold() instead (see below).
    """
    return "".join(_SMALL_CAPS_MAP.get(ch.lower(), ch) for ch in text)


def bold(text: str) -> str:
    """Wraps text in Telegram HTML bold tags.

    The message must be sent with parse_mode="HTML" for this to render —
    every handler that calls bold() already does this.
    """
    return f"<b>{escape(text)}</b>"
