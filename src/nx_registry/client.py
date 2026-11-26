"""Python SDK for the Nexy module registry."""

from __future__ import annotations

import base64
from typing import Any

import httpx

from nx_registry.catalog import Release, checksum_of
from nx_registry.manifest import Manifest

DEFAULT_BASE_URL = "https://registry.nexypy.dev"


class ChecksumMismatchError(ValueError):
    """The downloaded archive does not match the checksum from the service."""


class RegistryClient:
    """Reads and publishes releases through the registry HTTP service."""

    def __init__(
        self, base_url: str = DEFAULT_BASE_URL, client: httpx.Client | None = None
    ) -> None:
        self.base_url = base_url
        self._client = client if client is not None else httpx.Client(base_url=base_url)

    def modules(self, search: str = "") -> tuple[str, ...]:
        response = self._client.get("/modules", params={"q": search})
        response.raise_for_status()
        return tuple(str(name) for name in response.json()["modules"])

    def versions(self, name: str) -> tuple[str, ...]:
        response = self._client.get("/versions", params={"name": name})
        response.raise_for_status()
        return tuple(str(version) for version in response.json()["versions"])

    def release(self, name: str, version: str) -> Release:
        response = self._client.get("/release", params={"name": name, "version": version})
        response.raise_for_status()
        return _release_of(response.json())

    def download(self, name: str, version: str) -> bytes:
        response = self._client.get("/download", params={"name": name, "version": version})
        response.raise_for_status()
        archive = response.content
        if response.headers.get("X-Checksum", "") != checksum_of(archive):
            raise ChecksumMismatchError(f"{name}@{version}")
        return archive

    def publish(self, manifest: str, archive: bytes) -> Release:
        payload = {"manifest": manifest, "archive": base64.b64encode(archive).decode("ascii")}
        response = self._client.post("/releases", json=payload)
        response.raise_for_status()
        return _release_of(response.json())


def _release_of(data: dict[str, Any]) -> Release:
    package = data["package"]
    manifest = Manifest(
        name=str(data["name"]),
        version=str(data["version"]),
        kind=str(data["kind"]),  # type: ignore[arg-type]
        nexy_version=str(data["nexy_version"]),
        python_version=str(data["python_version"]),
        python_dependencies=tuple(str(item) for item in data["python_dependencies"]),
        node_dependencies=tuple(str(item) for item in data["node_dependencies"]),
        files=tuple(str(item) for item in data["files"]),
        package=None if package is None else str(package),
    )
    return Release(manifest=manifest, checksum=str(data["checksum"]), archive=b"")
