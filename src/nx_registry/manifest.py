"""The `nx.toml` manifest that every published Nexy module carries."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

_NAME = re.compile(r"@[a-z0-9][a-z0-9-]{0,38}/[a-z0-9][a-z0-9-]{0,48}")
_VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
_UNSAFE = {";", "&", "|", "`", "$", "\n", "\r", "\\"}


class ManifestError(ValueError):
    """The manifest is not a valid Nexy module description."""


@dataclass(frozen=True)
class Manifest:
    """The contract between a module author, the registry and the installer."""

    name: str
    version: str
    kind: Literal["source", "package"]
    nexy_version: str
    python_version: str
    python_dependencies: tuple[str, ...]
    node_dependencies: tuple[str, ...]
    files: tuple[str, ...]
    package: str | None


def parse_manifest(text: str) -> Manifest:
    """Parse and validate one `nx.toml` document."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as problem:
        raise ManifestError("manifest is not valid TOML") from problem
    return _manifest_of(data)


def _manifest_of(data: Mapping[str, Any]) -> Manifest:
    name = _text(data, "name")
    version = _text(data, "version")
    kind = _text(data, "kind")
    _check_name(name)
    _check_version(version)
    if kind not in ("source", "package"):
        raise ManifestError("kind must be source or package")
    compatibility = _table(data, "compatibility")
    dependencies = _table(data, "dependencies")
    files, package = _payload(data, kind)
    return Manifest(
        name=name,
        version=version,
        kind=kind,  # type: ignore[arg-type]
        nexy_version=_text(compatibility, "nexy"),
        python_version=_text(compatibility, "python"),
        python_dependencies=_dependencies(dependencies, "python"),
        node_dependencies=_dependencies(dependencies, "node"),
        files=files,
        package=package,
    )


def _text(data: Mapping[str, Any], key: str) -> str:
    return str(data.get(key, ""))


def _table(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def _payload(data: Mapping[str, Any], kind: str) -> tuple[tuple[str, ...], str | None]:
    source = _table(data, "source")
    if kind == "source":
        files = _files(source)
        if not files:
            raise ManifestError("a source module needs at least one file")
        return files, None
    package = _text(source, "package")
    if not package:
        raise ManifestError("a package module needs a package name")
    return (), package


def _files(source: Mapping[str, Any]) -> tuple[str, ...]:
    value = source.get("files", [])
    items = tuple(str(item) for item in value) if isinstance(value, list) else ()
    for item in items:
        if not item or item.startswith("/") or ".." in item.split("/") or "\\" in item:
            raise ManifestError("a module file must be a relative path inside the module")
    return items


def _dependencies(dependencies: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = dependencies.get(key, [])
    items = tuple(str(item) for item in value) if isinstance(value, list) else ()
    for item in items:
        if not item or any(char in item for char in _UNSAFE):
            raise ManifestError("a dependency is empty or contains an unsafe character")
    return items


def _check_name(name: str) -> None:
    if not _NAME.fullmatch(name):
        raise ManifestError("name must be @scope/name with lowercase letters and hyphens")


def _check_version(version: str) -> None:
    if not _VERSION.fullmatch(version):
        raise ManifestError("version must be three numbers separated by dots")
