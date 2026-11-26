"""In memory storage for immutable Nexy module releases."""

from __future__ import annotations

import re
from dataclasses import dataclass

from nx_registry.manifest import Manifest

_CHECKSUM = re.compile(r"sha256:[0-9a-f]{64}")


class VersionExistsError(ValueError):
    """A module version is already published and cannot change."""


class UnknownModuleError(LookupError):
    """No release matches the requested module name and version."""


@dataclass(frozen=True)
class Release:
    """One published version of a module."""

    manifest: Manifest
    checksum: str


class Catalog:
    """Stores releases by module name and version."""

    def __init__(self) -> None:
        self._releases: dict[str, dict[str, Release]] = {}

    def publish(self, manifest: Manifest, checksum: str) -> Release:
        """Store one release and return it."""
        _check_checksum(checksum)
        versions = self._releases.setdefault(manifest.name, {})
        if manifest.version in versions:
            raise VersionExistsError(f"{manifest.name}@{manifest.version}")
        release = Release(manifest=manifest, checksum=checksum)
        versions[manifest.version] = release
        return release

    def get(self, name: str, version: str) -> Release:
        """Return one release or fail before the caller can use it."""
        try:
            return self._releases[name][version]
        except KeyError as problem:
            raise UnknownModuleError(f"{name}@{version}") from problem

    def versions(self, name: str) -> tuple[str, ...]:
        """Return the published versions of one module in order."""
        return tuple(sorted(self._releases.get(name, {})))

    def names(self) -> tuple[str, ...]:
        """Return every published module name in order."""
        return tuple(sorted(self._releases))


def _check_checksum(checksum: str) -> None:
    if not _CHECKSUM.fullmatch(checksum):
        raise ValueError("checksum must be sha256 followed by 64 lowercase hex characters")
