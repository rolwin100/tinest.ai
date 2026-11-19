"""name@semver -> provider factory.

Why a registry rather than direct imports: the conformance suite parametrises
over everything registered, so it can test providers that did not exist when the
suite was written — including our own Phase 2 weights.
"""

import re
from collections.abc import Callable
from typing import Any

from gotiny.providers.caps import Modality

_KEY = re.compile(r"^[a-z0-9][a-z0-9-]*@\d+\.\d+(\.\d+)?$")

_REGISTRY: dict[str, tuple[Modality, Callable[..., Any]]] = {}


class RegistryError(Exception):
    pass


def register(key: str, modality: Modality) -> Callable[[type], type]:
    """Decorator. ``key`` must be 'name@semver' — the same string written to
    every ``turn`` row, so a quality regression is a GROUP BY query."""
    if not _KEY.match(key):
        raise RegistryError(f"{key!r} is not 'name@semver' (e.g. 'indicf5@0.3')")

    def deco(cls: type) -> type:
        if key in _REGISTRY:
            raise RegistryError(f"{key!r} already registered")
        _REGISTRY[key] = (modality, cls)
        return cls

    return deco


def get(key: str) -> Callable[..., Any]:
    try:
        return _REGISTRY[key][1]
    except KeyError:
        raise RegistryError(f"unknown provider {key!r}; registered: {sorted(_REGISTRY)}") from None


def available(modality: Modality | None = None) -> list[str]:
    return sorted(k for k, (m, _) in _REGISTRY.items() if modality is None or m == modality)


def clear() -> None:
    """Test-only."""
    _REGISTRY.clear()
