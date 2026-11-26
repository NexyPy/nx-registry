import pytest

from nx_registry.manifest import ManifestError, parse_manifest


def _manifest(
    *,
    name: str = "@acme/auth",
    version: str = "1.0.0",
    kind: str = "source",
    files: str = '["src/auth.py"]',
    package: str = "",
    python_deps: str = '["argon2-cffi"]',
    node_deps: str = "[]",
) -> str:
    package_line = f'package = "{package}"' if package else ""
    source_line = f"files = {files}" if kind == "source" else ""
    return f"""name = "{name}"
version = "{version}"
kind = "{kind}"

[compatibility]
nexy = ">=0.12.0"
python = ">=3.12"

[dependencies]
python = {python_deps}
node = {node_deps}

[source]
{source_line}
{package_line}
"""


class TestParseManifest:
    def test_parse_manifest_reads_a_source_module(self) -> None:
        manifest = parse_manifest(_manifest())
        assert manifest.kind == "source"

    def test_parse_manifest_reads_a_package_module(self) -> None:
        manifest = parse_manifest(_manifest(kind="package", files="[]", package="nexy_auth"))
        assert manifest.package == "nexy_auth"

    def test_parse_manifest_reads_compatibility(self) -> None:
        manifest = parse_manifest(_manifest())
        assert manifest.nexy_version == ">=0.12.0"

    def test_parse_manifest_preserves_dependency_order(self) -> None:
        manifest = parse_manifest(_manifest(python_deps='["argon2-cffi", "sqlmodel"]'))
        assert manifest.python_dependencies == ("argon2-cffi", "sqlmodel")

    def test_parse_manifest_rejects_invalid_toml(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest("name = ")

    def test_parse_manifest_rejects_an_unscoped_name(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(name="auth"))

    def test_parse_manifest_rejects_a_bad_version(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(version="1.0.0/../evil"))

    def test_parse_manifest_rejects_an_unknown_kind(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(kind="binary"))

    def test_parse_manifest_rejects_a_path_that_climbs_out(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(files='["../secret.py"]'))

    def test_parse_manifest_rejects_an_absolute_path(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(files='["/etc/passwd"]'))

    def test_parse_manifest_requires_source_files(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(files="[]"))

    def test_parse_manifest_rejects_files_that_are_not_a_list(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(files='"src/auth.py"'))

    def test_parse_manifest_requires_a_package_name(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(kind="package", files="[]"))

    def test_parse_manifest_rejects_a_dependency_with_a_shell_separator(self) -> None:
        with pytest.raises(ManifestError):
            parse_manifest(_manifest(python_deps='["requests; rm -rf /"]'))
