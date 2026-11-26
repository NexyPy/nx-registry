"""HTTP service that indexes Nexy module releases."""

from __future__ import annotations

import base64
import binascii

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from nx_registry.catalog import Catalog, Release, UnknownModuleError, VersionExistsError
from nx_registry.manifest import ManifestError, parse_manifest


class PublishRequest(BaseModel):
    """The manifest and archive sent by a module publisher."""

    manifest: str
    archive: str


def create_app(catalog: Catalog | None = None) -> FastAPI:
    """Build the registry application around a catalog."""
    store = catalog or Catalog()
    app = FastAPI(title="nx registry")

    @app.get("/modules")
    def modules(q: str = "") -> dict[str, list[str]]:
        names = store.names()
        if q:
            names = tuple(name for name in names if q in name)
        return {"modules": list(names)}

    @app.get("/versions")
    def versions(name: str) -> dict[str, list[str]]:
        return {"versions": list(store.versions(name))}

    @app.get("/release")
    def release(name: str, version: str) -> dict[str, object]:
        return _release_data(_get(store, name, version))

    @app.get("/download")
    def download(name: str, version: str) -> Response:
        item = _get(store, name, version)
        return Response(
            content=item.archive,
            media_type="application/octet-stream",
            headers={"X-Checksum": item.checksum},
        )

    @app.post("/releases", status_code=201)
    def publish(request: PublishRequest) -> dict[str, object]:
        try:
            manifest = parse_manifest(request.manifest)
        except ManifestError as problem:
            raise HTTPException(status_code=400, detail=str(problem)) from problem
        archive = _archive(request.archive)
        try:
            item = store.publish(manifest, archive)
        except VersionExistsError as problem:
            raise HTTPException(status_code=409, detail=str(problem)) from problem
        return _release_data(item)

    return app


def _get(store: Catalog, name: str, version: str) -> Release:
    try:
        return store.get(name, version)
    except UnknownModuleError as problem:
        raise HTTPException(status_code=404, detail=str(problem)) from problem


def _archive(value: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except binascii.Error as problem:
        raise HTTPException(status_code=400, detail="archive must be base64") from problem


def _release_data(item: Release) -> dict[str, object]:
    return {
        "name": item.manifest.name,
        "version": item.manifest.version,
        "kind": item.manifest.kind,
        "nexy_version": item.manifest.nexy_version,
        "python_version": item.manifest.python_version,
        "python_dependencies": list(item.manifest.python_dependencies),
        "node_dependencies": list(item.manifest.node_dependencies),
        "files": list(item.manifest.files),
        "package": item.manifest.package,
        "checksum": item.checksum,
    }
