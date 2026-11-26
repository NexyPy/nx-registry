import base64

from fastapi.testclient import TestClient

from nx_registry.api import create_app
from nx_registry.catalog import Catalog, checksum_of
from nx_registry.manifest import parse_manifest

_ARCHIVE = b"archive"
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


def _payload(version: str = "1.0.0") -> dict[str, str]:
    manifest = _MANIFEST.replace('version = "1.0.0"', f'version = "{version}"')
    return {"manifest": manifest, "archive": base64.b64encode(_ARCHIVE).decode("ascii")}


def _client(catalog: Catalog | None = None) -> TestClient:
    store = catalog or Catalog()
    return TestClient(create_app(store))


def _published_client() -> TestClient:
    catalog = Catalog()
    catalog.publish(parse_manifest(_MANIFEST), _ARCHIVE)
    return _client(catalog)


class TestApi:
    def test_create_app_uses_an_empty_catalog(self) -> None:
        response = _client().get("/modules")
        assert response.json() == {"modules": []}

    def test_modules_search_filters_by_name(self) -> None:
        response = _published_client().get("/modules", params={"q": "acme"})
        assert response.json() == {"modules": ["@acme/auth"]}

    def test_versions_returns_published_versions(self) -> None:
        response = _published_client().get("/versions", params={"name": "@acme/auth"})
        assert response.json() == {"versions": ["1.0.0"]}

    def test_release_returns_the_metadata(self) -> None:
        response = _published_client().get(
            "/release", params={"name": "@acme/auth", "version": "1.0.0"}
        )
        assert response.json()["checksum"] == checksum_of(_ARCHIVE)

    def test_download_returns_the_archive(self) -> None:
        response = _published_client().get(
            "/download", params={"name": "@acme/auth", "version": "1.0.0"}
        )
        assert response.content == _ARCHIVE

    def test_download_returns_the_checksum_header(self) -> None:
        response = _published_client().get(
            "/download", params={"name": "@acme/auth", "version": "1.0.0"}
        )
        assert response.headers["X-Checksum"] == checksum_of(_ARCHIVE)

    def test_download_rejects_an_unknown_release(self) -> None:
        response = _client().get("/download", params={"name": "@acme/auth", "version": "1.0.0"})
        assert response.status_code == 404

    def test_publish_stores_a_release(self) -> None:
        response = _client().post("/releases", json=_payload())
        assert response.status_code == 201

    def test_publish_rejects_an_invalid_manifest(self) -> None:
        payload = _payload()
        payload["manifest"] = "name ="
        response = _client().post("/releases", json=payload)
        assert response.status_code == 400

    def test_publish_rejects_an_invalid_archive(self) -> None:
        payload = _payload()
        payload["archive"] = "not base64!"
        response = _client().post("/releases", json=payload)
        assert response.status_code == 400

    def test_publish_rejects_an_existing_version(self) -> None:
        client = _client()
        client.post("/releases", json=_payload())
        response = client.post("/releases", json=_payload())
        assert response.status_code == 409
