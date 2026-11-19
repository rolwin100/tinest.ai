"""Types shared across planes. Keep this small and boring — it is imported everywhere."""

from enum import StrEnum

from pydantic import BaseModel


class Language(StrEnum):
    """Languages we serve.

    ``HINGLISH`` is not an ISO code and that is deliberate: Hindi/English
    code-switching is a distinct synthesis and recognition target for us, it is
    the dominant register on Indian phone calls, and every model gets scored on
    it separately. Treating it as "Hindi" hides the thing we are being judged on.
    """

    HINDI = "hi"
    HINGLISH = "hi-en"
    ENGLISH_IN = "en-IN"
    ENGLISH_US = "en-US"
    TAMIL = "ta"
    TELUGU = "te"
    MARATHI = "mr"
    BENGALI = "bn"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    ODIA = "or"
    ASSAMESE = "as"


class AudioFormat(BaseModel):
    """Raw PCM only on the wire. Container formats are a storage concern."""

    sample_rate: int = 24_000
    channels: int = 1
    encoding: str = "pcm_s16le"

    @property
    def bytes_per_second(self) -> int:
        return self.sample_rate * self.channels * 2

    def duration_ms(self, n_bytes: int) -> float:
        return (n_bytes / self.bytes_per_second) * 1_000


# The telephony path. 8 kHz is not a downgrade we tolerate — it is the target
# condition for most of our traffic, so it is a named constant, not a magic number.
TELEPHONY = AudioFormat(sample_rate=8_000)
STUDIO = AudioFormat(sample_rate=24_000)
