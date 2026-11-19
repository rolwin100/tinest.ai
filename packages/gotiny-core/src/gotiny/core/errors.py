"""Error taxonomy. The distinctions here map to how we *respond*, not to HTTP codes."""


class GotinyError(Exception):
    """Base class. Never raised directly."""


class ProviderError(GotinyError):
    """A model server failed. Retryable at the call level; may warrant failover."""


class ProviderUnavailable(ProviderError):
    """Model server unreachable or unhealthy. Distinct because it should trip a breaker."""


class UnsupportedLanguage(ProviderError):
    """Provider does not claim this language.

    Separate from ProviderError because it is a *routing* bug, not a transient
    fault: retrying the same provider will always fail. Conformance asserts that
    providers raise this rather than silently synthesising something wrong.
    """


class UnsupportedCapability(ProviderError):
    """e.g. cloning requested from a fixed-voice backend like Kokoro."""


class Cancelled(GotinyError):
    """Barge-in. Not an error condition — the user interrupted, which is correct behaviour."""
