"""Strip what a model writes but nobody should hear.

Small models narrate. Asked to be warm, a 4B will hand you ``*chuckles* Sure,
we're open till eight`` or ``Haha, of course!`` -- text that reads fine and
speaks badly. What happens next depends entirely on the backend, which is why
this cannot live in one of them:

  Kokoro reads it as words. The caller hears the syllables "chuckles".
  Qwen3-TTS *performs* it. Laughter tokens and emotional stage directions are
  inside what an instruct-tuned model renders as real paralinguistic audio, so
  the caller hears an actual laugh -- from a clinic receptionist, unprompted.

Both are wrong, so the cleaning happens server-side, once, before segmentation,
and every backend benefits.

Conservative on purpose. An earlier version stripped any ``*...*`` span and ate
``**tomorrow**`` out of "we can book you **tomorrow** at four" -- emphasis
markdown, not a stage direction. So a bracketed span is removed only when it
*names* a direction and is short enough to be one. When in doubt it is left
alone: speaking a stray asterisk is a much cheaper failure than deleting the
appointment day.
"""

import re

# Things a model writes to describe delivery rather than to be said.
_DIRECTION = (
    r"laugh(s|ing|ter)?|chuckl(e|es|ing)|giggl(e|es|ing)|snicker(s|ing)?"
    r"|sigh(s|ing)?|gasp(s|ing)?|cough(s|ing)?|sniff(s|ing)?|hum(s|ming)?"
    r"|breath(e|es|ing)?|inhal(e|es|ing)|exhal(e|es|ing)"
    r"|smil(e|es|ing)|grin(s|ning)?|nod(s|ding)?|shrug(s|ging)?"
    r"|paus(e|es|ing)|beat|silence|hesitat(e|es|ing|ion)"
    r"|whisper(s|ing)?|mutter(s|ing)?|clears? (his |her |their )?throat"
    r"|warmly|softly|gently|brightly|cheerfully|apologetically"
    # Devanagari: a Hindi-prompted model writes its cues in Hindi. Without these
    # the hi-en persona keeps every stage direction the en-US one drops.
    r"|हंस|हँस|मुस्कुरा|मुस्करा|ठहर|ठहराव|साँस|सांस|खाँस|खांस|धीरे|चुपचाप|फुसफुसा"
)
_DIRECTION_RE = re.compile(_DIRECTION, re.IGNORECASE)

# A bracketed span this long is prose the model meant to say, not a cue.
_MAX_DIRECTION_WORDS = 5

# *asterisks*, (parens) and [brackets] -- the three ways models mark a cue.
_SPANS = re.compile(r"\*{1,3}([^*\n]+?)\*{1,3}|\(([^)\n]+?)\)|\[([^\]\n]+?)\]")

# Written-out laughter, as a whole token: "haha", "hehe", "ha ha ha", "lol".
_LAUGH_TOKEN = re.compile(
    r"(?<![\w'])(?:(?:ha|he|he?h|heh){2,}|(?:ha|ho)(?:\s+(?:ha|ho)){1,}|lol|lmao)"
    r"(?![\w'])",
    re.IGNORECASE,
)

# Removing a word can strand punctuation that belonged to it: "Sure! Haha, we"
# loses "Haha" and leaves "Sure!, we". Collapse the weaker mark into the stronger.
_DOUBLED_PUNCT = re.compile(r"([.!?।॥])\s*[,;:]+")
_REPEATED_COMMA = re.compile(r",(\s*,)+")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.!?;:।॥])")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_ORPHAN_PUNCT = re.compile(r"^[\s,.!?;:—-]+")


def _looks_like_direction(inner: str) -> bool:
    """Named as a delivery cue, and short enough to actually be one."""
    inner = inner.strip()
    if not inner or len(inner.split()) > _MAX_DIRECTION_WORDS:
        return False
    return bool(_DIRECTION_RE.search(inner))


def speakable(text: str) -> str:
    """Text as it should be heard. Never raises; worst case returns the input."""
    if not text:
        return text

    def _drop(m: re.Match[str]) -> str:
        inner = next((g for g in m.groups() if g is not None), "")
        return "" if _looks_like_direction(inner) else m.group(0)

    out = _SPANS.sub(_drop, text)
    out = _LAUGH_TOKEN.sub("", out)

    out = _DOUBLED_PUNCT.sub(r"\1", out)
    out = _REPEATED_COMMA.sub(",", out)
    out = _SPACE_BEFORE_PUNCT.sub(r"\1", out)
    out = _MULTI_SPACE.sub(" ", out)
    out = _ORPHAN_PUNCT.sub("", out)
    return out.strip()
