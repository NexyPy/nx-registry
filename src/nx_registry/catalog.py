"""In memory storage for immutable Nexy module releases."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from nx_registry.manifest import Manifest


class VersionExistsError(ValueError):
    """A module version is already published and cannot change."""


class UnknownModuleError(LookupError):
    """No release matches the requested module name and version."""


@dataclass(frozen=True)
class Release:
    """One published version of a module."""

    manifest: Manifest
    checksum: str
    archive: bytes


def checksum_of(archive: bytes) -> str:
    """Return the canonical checksum of a release archive."""
    return f"sha256:{hashlib.sha256(archive).hexdigest()}"


class Catalog:
    """Stores releases by module name and version."""

    def __init__(self) -> None:
        self._releases: dict[str, dict[str, Release]] = {}

    def publish(self, manifest: Manifest, archive: bytes) -> Release:
        """Store one release and return it."""
        versions = self._releases.setdefault(manifest.name, {})
        if manifest.version in versions:
            raise VersionExistsError(f"{manifest.name}@{manifest.version}")
        release = Release(manifest=manifest, checksum=checksum_of(archive), archive=archive)
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
