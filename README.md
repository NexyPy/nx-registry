# nx-registry

The module registry for Nexy.

This repository holds the registry service, the `nx.toml` manifest contract and the Python SDK. The
`nx add`, `nx publish` and `nx sign` commands live in the Nexy framework repository and talk to this
service. The registry indexes metadata and archives. It never executes module code.

## Module kinds

A module declares one of two kinds.

- `source`: the installer copies declared files into the project, like shadcn UI. The developer owns
  the copied code and can change it.
- `package`: the installer adds a package with `uv add` and does not copy source files.

Both kinds can declare Python and JavaScript dependencies. The registry only records them. The
installer decides how to install them. Config hooks and migrations belong to the CLI issues in the
Nexy repository and are not part of the service yet.

## Manifest

A module carries an `nx.toml` file at its root.

```toml filename="nx.toml"
name = "@acme/auth"
version = "1.0.0"
kind = "source"

[compatibility]
nexy = ">=0.12.0"
python = ">=3.12"

[dependencies]
python = ["argon2-cffi", "sqlmodel"]
node = []

[source]
files = ["src/auth.py", "src/session.py"]
```

A package module uses `kind = "package"` and declares `package = "nexy_auth"` under `[source]`
instead of `files`.

Names use `@scope/name`, with lowercase letters and hyphens. A version is three numbers separated by
dots. Source files must be relative paths inside the module. Dependencies cannot contain shell
separators, newlines or backslashes. Invalid manifests are rejected before storage.

## HTTP service

Run the service with `uv run uvicorn nx_registry.api:create_app --factory`.

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/modules` | List names, with an optional `q` search parameter |
| GET | `/versions` | List versions of one module, using `name` |
| GET | `/release` | Return release metadata, using `name` and `version` |
| GET | `/download` | Return the archive with an `X-Checksum` header |
| POST | `/releases` | Publish a manifest and a base64 archive |

A version cannot be replaced. A second publish of the same name and version returns HTTP 409. The
service computes the SHA-256 checksum from the archive and returns it with every release.

## Python SDK

```python
from nx_registry.client import RegistryClient

client = RegistryClient()
names = client.modules("auth")
versions = client.versions("@acme/auth")
release = client.release("@acme/auth", "1.0.0")
archive = client.download("@acme/auth", "1.0.0")
```

`RegistryClient` defaults to `https://registry.nexypy.dev`. Pass `base_url` to use another deployment
and `client` to inject an `httpx.Client`. `download` checks the response checksum before returning
the archive. `publish` sends the archive as base64 and returns the published release.

## Trust and policy

A checksum proves that an archive was not changed in transit. It does not prove who published it.
`nx sign` and `nx verify` will add signatures later. `nx add` will decide whether an unsigned release
is allowed.

One owner controls a namespace. A publisher may not claim a namespace owned by another account. A
takedown request removes new installs of a release and marks it deprecated. Existing versions stay
immutable so that pins keep working.

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check src tests
uv run ruff format src tests --check
uv run mypy src tests
uv run bandit -r src -q
```
