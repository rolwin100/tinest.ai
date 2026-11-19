"""The registry is what lets `GROUP BY provider` tell the truth."""

import pytest

from gotiny.providers import registry


def test_rejects_unversioned_keys() -> None:
    for bad in ["kokoro", "Kokoro@1.0", "kokoro@1", "kokoro@v1.0", ""]:
        with pytest.raises(registry.RegistryError):
            registry.register(bad, "tts")


def test_rejects_duplicate_keys() -> None:
    key = "dupe-test@9.9"
    registry.register(key, "tts")(type("A", (), {}))
    with pytest.raises(registry.RegistryError):
        registry.register(key, "tts")(type("B", (), {}))


def test_unknown_key_lists_what_is_available() -> None:
    with pytest.raises(registry.RegistryError, match="registered:"):
        registry.get("does-not-exist@1.0")
