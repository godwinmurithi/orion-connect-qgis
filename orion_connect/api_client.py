# Thin client for the OrionGIS / GeoNode REST API v2 — the same open API the
# OrionGIS web portal itself uses (see app/src/lib/geonode/*.ts in the
# OrionGIS repo for the reference implementation this mirrors).
#
# Auth: unlike the portal (a confidential OAuth2 client running server-side,
# with a client secret that must never leave the server), Orion Connect is a
# public desktop client distributed to end users — it must not embed any
# confidential secret. Confirmed live against orionterrametrics.com
# (2026-09-13): the API also accepts plain HTTP Basic Auth
# (`WWW-Authenticate: Basic realm="api"` on a 401, and a real structured
# `{"success": false, "errors": ["Invalid username/password."], "code":
# "authentication_failed"}` body on bad credentials — this is genuine
# DRF BasicAuthentication, not a generic gateway 401). So each user signs in
# with their own OrionGIS username/password, sent as a Basic Auth header over
# HTTPS — nothing shared, nothing embedded, no client secret needed.
#
# Read endpoints (catalogue search, dataset detail) are confirmed open and
# unauthenticated, so Basic Auth is only attached when a token is present.

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

DEFAULT_BASE_URL = "https://orionterrametrics.com"
USER_AGENT = "OrionConnect-QGIS-Plugin/0.2.0"


class OrionApiError(Exception):
    def __init__(self, status: int, message: str, body: Any = None):
        super().__init__(f"OrionGIS API error {status}: {message}")
        self.status = status
        self.body = body


@dataclass
class Dataset:
    pk: int
    name: str
    alternate: str  # real WMS/WFS layer name, e.g. "geonode:worldbank_indicators_23"
    title: str
    subtype: str  # "vector" | "raster"
    thumbnail_url: str | None
    abstract: str = ""

    @staticmethod
    def from_raw(raw: dict) -> "Dataset":
        return Dataset(
            pk=raw.get("pk"),
            name=raw.get("name", ""),
            alternate=raw.get("alternate") or f"geonode:{raw.get('name', '')}",
            title=raw.get("title", raw.get("name", "")),
            subtype=raw.get("subtype", "vector"),
            thumbnail_url=raw.get("thumbnail_url"),
            abstract=raw.get("raw_abstract") or raw.get("abstract") or "",
        )


@dataclass
class SearchResult:
    total: int
    datasets: list[Dataset] = field(default_factory=list)


class OrionApiClient:
    """Real GeoNode API v2 client. No confidential secrets embedded — auth
    (when needed, for uploads) is the signed-in user's own Basic Auth
    credentials, held only in memory / QSettings for this session."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, username: str | None = None, password: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password

    # -- internal -----------------------------------------------------

    def _headers(self, has_body: bool = False) -> dict:
        headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
        if has_body:
            headers["Content-Type"] = "application/json"
        if self.username and self.password:
            token = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        return headers

    def _request(self, method: str, path: str, params: dict | list | None = None, json_body: dict | None = None, timeout: int = 20) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            pairs = params.items() if isinstance(params, dict) else params
            query = urllib.parse.urlencode([(k, v) for k, v in pairs if v is not None])
            url = f"{url}?{query}"
        data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=self._headers(has_body=data is not None))
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            body_raw = e.read()
            try:
                body = json.loads(body_raw) if body_raw else None
            except ValueError:
                body = body_raw.decode("utf-8", "replace")
            message = ""
            if isinstance(body, dict):
                message = "; ".join(str(x) for x in body.get("errors", [])) or str(body)
            raise OrionApiError(e.code, message or str(e), body) from e
        except urllib.error.URLError as e:
            raise OrionApiError(0, str(e.reason)) from e

    # -- catalogue ------------------------------------------------------

    def search_datasets(self, query: str = "", page: int = 1, page_size: int = 25) -> SearchResult:
        """GET /api/v2/datasets?search=<q>&search_fields=title&search_fields=abstract
        — server-side search on title/abstract, open/unauthenticated for reads."""
        params: list[tuple[str, Any]] = [("page", page), ("page_size", page_size)]
        if query:
            # GeoNode ignores `search` unless search_fields names the fields
            # (verified live 2026-10-31: without them every dataset matched).
            params += [("search", query), ("search_fields", "title"), ("search_fields", "abstract")]
        raw = self._request("GET", "/api/v2/datasets", params=params)
        datasets = [Dataset.from_raw(d) for d in raw.get("datasets", [])]
        return SearchResult(total=raw.get("total", len(datasets)), datasets=datasets)

    def get_dataset(self, pk: int) -> Dataset:
        raw = self._request("GET", f"/api/v2/datasets/{pk}")
        return Dataset.from_raw(raw.get("dataset", raw))

    # -- WMS/WFS layer URLs ----------------------------------------------
    # Mirrors app/src/lib/geolibre.ts's wmsCapabilitiesUrl/wfsGetFeatureUrl —
    # same GeoServer `ows` endpoint and `alternate` layer-name convention the
    # portal already uses, just built in Python for a QGIS data-source string
    # instead of a browser fetch URL.

    @property
    def geoserver_ows_url(self) -> str:
        return f"{self.base_url}/geoserver/ows"

    def wms_layer_uri(self, dataset: Dataset) -> str:
        """QGIS WMS provider data-source string for QgsRasterLayer."""
        params = {
            "url": self.geoserver_ows_url,
            "layers": dataset.alternate,
            "format": "image/png",
            "crs": "EPSG:4326",
            "version": "1.3.0",
        }
        return "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items())

    def wfs_layer_uri(self, dataset: Dataset) -> str:
        """QGIS WFS provider data-source string for QgsVectorLayer."""
        params = {
            "url": self.geoserver_ows_url,
            "typename": dataset.alternate,
            "version": "1.1.0",
            "srsname": "EPSG:4326",
        }
        return "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in params.items())

    # -- upload -----------------------------------------------------------
    # Mirrors app/src/lib/geonode/uploads.ts's confirmed-live contract:
    # POST /api/v2/uploads/upload (multipart, field "base_file")
    #   -> {"execution_id": "<uuid>"}
    # GET  /api/v2/executionrequest/<id>
    #   -> {"request": {"status": "created"|"running"|"finished"|"failed",
    #                    "geonode_resource": <id>, "log": <str>}}
    # Requires the signed-in user's own credentials (Basic Auth) — there is
    # no shared service-account token embedded in this public client.

    def upload_file(self, file_path: str) -> str:
        if not (self.username and self.password):
            raise OrionApiError(401, "Sign in to OrionGIS first (Orion Connect > Sign In).")

        boundary = "----OrionConnectBoundary7d9a1c"
        filename = file_path.rsplit("/", 1)[-1]
        with open(file_path, "rb") as fh:
            file_bytes = fh.read()

        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="base_file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        headers = self._headers()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

        req = urllib.request.Request(
            f"{self.base_url}/api/v2/uploads/upload",
            data=body,
            method="POST",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_raw = e.read()
            raise OrionApiError(e.code, body_raw.decode("utf-8", "replace")) from e
        execution_id = raw.get("execution_id")
        if not execution_id:
            raise OrionApiError(0, f"Upload response had no execution_id: {raw}")
        return execution_id

    def get_upload_status(self, execution_id: str) -> dict:
        raw = self._request("GET", f"/api/v2/executionrequest/{execution_id}")
        return raw.get("request", raw)
