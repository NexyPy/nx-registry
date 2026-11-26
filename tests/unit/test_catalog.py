import pytest

from nx_registry.catalog import (
    Catalog,
    UnknownModuleError,
    VersionExistsError,
    checksum_of,
)
from nx_registry.manifest import Manifest, parse_manifest

_ARCHIVE = b"archive"
_CHECKSUM = checksum_of(_ARCHIVE)
_MANIFEST = """name = "@acme/auth"
version = "1.0.0"
kind = "source"

[compatibility]
nexy = ">=0.12.0"
python = ">=3.12"

[dependencies]
python = []
node = []

[source]
files = ["src/auth.py"]
"""


def _manifest(version: str = "1.0.0", name: str = "@acme/auth") -> Manifest:
    text = _MANIFEST.replace('version = "1.0.0"', f'version = "{version}"')
    return parse_manifest(text.replace("@acme/auth", name))


class TestCatalog:
    def test_publish_returns_the_release(self) -> None:
        catalog = Catalog()
        release = catalog.publish(_manifest(), _ARCHIVE)
        assert release.manifest.name == "@acme/auth"

    def test_publish_computes_the_checksum_from_the_archive(self) -> None:
        catalog = Catalog()
        release = catalog.publish(_manifest(), _ARCHIVE)
        assert release.checksum == _CHECKSUM

    def test_publish_keeps_the_archive(self) -> None:
        catalog = Catalog()
        release = catalog.publish(_manifest(), _ARCHIVE)
        assert release.archive == _ARCHIVE

    def test_publish_rejects_an_existing_version(self) -> None:
        catalog = Catalog()
        catalog.publish(_manifest(), _ARCHIVE)
        with pytest.raises(VersionExistsError):
            catalog.publish(_manifest(), _ARCHIVE)

    def test_get_returns_the_published_release(self) -> None:
        catalog = Catalog()
        catalog.publish(_manifest(), _ARCHIVE)
        assert catalog.get("@acme/auth", "1.0.0").checksum == _CHECKSUM

    def test_get_rejects_an_unknown_release(self) -> None:
        catalog = Catalog()
        with pytest.raises(UnknownModuleError):
            catalog.get("@acme/auth", "1.0.0")

    def test_versions_are_sorted(self) -> None:
        catalog = Catalog()
        catalog.publish(_manifest("2.0.0"), _ARCHIVE)
        catalog.publish(_manifest("1.0.0"), _ARCHIVE)
        assert catalog.versions("@acme/auth") == ("1.0.0", "2.0.0")

    def test_versions_ignore_other_modules(self) -> None:
        catalog = Catalog()
        catalog.publish(_manifest(name="@acme/other"), _ARCHIVE)
        assert catalog.versions("@acme/auth") == ()

    def test_names_are_unique(self) -> None:
        catalog = Catalog()
        catalog.publish(_manifest("2.0.0"), _ARCHIVE)
        catalog.publish(_manifest("1.0.0"), _ARCHIVE)
        assert catalog.names() == ("@acme/auth",)
