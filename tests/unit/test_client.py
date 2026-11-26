import base64
import json
from collections.abc import Callable

import httpx
import pytest

from nx_registry.catalog import checksum_of
from nx_registry.client import DEFAULT_BASE_URL, ChecksumMismatchError, RegistryClient

_ARCHIVE = b"archive"
_CHECKSUM = checksum_of(_ARCHIVE)
_RELEASE = {
    "name": "@acme/auth",
    "version": "1.0.0",
    "kind": "source",
    "nexy_version": ">=0.12.0",
    "python_version": ">=3.12",
    "python_dependencies": [],
    "node_dependencies": [],
    "files": ["src/auth.py"],
    "package": None,
    "checksum": _CHECKSUM,
}

Handler = Callable[[httpx.Request], httpx.Response]


def _client(handler: Handler) -> RegistryClient:
    transport = httpx.MockTransport(handler)
    return RegistryClient(client=httpx.Client(transport=transport, base_url="http://test"))


def _json_client(data: object, headers: dict[str, str] | None = None) -> RegistryClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=data, headers=headers, request=request)

    return _client(handler)


class TestRegistryClient:
    def test_client_uses_the_public_registry_url(self) -> None:
        assert RegistryClient().base_url == DEFAULT_BASE_URL

    def test_modules_returns_names_from_the_service(self) -> None:
        client = _json_client({"modules": ["@acme/auth"]})
        assert client.modules() == ("@acme/auth",)

    def test_modules_passes_the_search_query(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, json={"modules": [request.url.params.get("q", "")]}, request=request
            )

        assert _client(handler).modules("auth") == ("auth",)

    def test_versions_returns_versions_from_the_service(self) -> None:
        client = _json_client({"versions": ["1.0.0", "2.0.0"]})
        assert client.versions("@acme/auth") == ("1.0.0", "2.0.0")

    def test_release_returns_the_manifest(self) -> None:
        client = _json_client(_RELEASE)
        assert client.release("@acme/auth", "1.0.0").manifest.name == "@acme/auth"

    def test_release_returns_a_package_name(self) -> None:
        data = dict(_RELEASE, package="nexy_auth")
        client = _json_client(data)
        assert client.release("@acme/auth", "1.0.0").manifest.package == "nexy_auth"

    def test_download_returns_the_archive(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=_ARCHIVE, headers={"X-Checksum": _CHECKSUM}, request=request
            )

        assert _client(handler).download("@acme/auth", "1.0.0") == _ARCHIVE

    def test_download_rejects_a_bad_checksum(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200, content=_ARCHIVE, headers={"X-Checksum": "sha256:bad"}, request=request
            )

        with pytest.raises(ChecksumMismatchError):
            _client(handler).download("@acme/auth", "1.0.0")

    def test_publish_sends_a_base64_archive(self) -> None:
        sent: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            sent.update(json.loads(request.content))
            return httpx.Response(201, json=_RELEASE, request=request)

        _client(handler).publish('name = "@acme/auth"', _ARCHIVE)
        assert sent["archive"] == base64.b64encode(_ARCHIVE).decode("ascii")
