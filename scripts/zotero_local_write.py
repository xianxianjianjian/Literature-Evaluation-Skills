#!/usr/bin/env python3
"""Zotero 10+ Local API write and full-file-upload primitives.

This module implements the documented Zotero Web API v3-compatible local write
flow. Authorization keys are requested from Zotero Desktop at runtime and are
kept in memory only; they are never printed or persisted by this helper.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

DEFAULT_API_BASE_URL = "http://127.0.0.1:23119/api"
DEFAULT_TIMEOUT = 3.0
DEFAULT_APP_NAME = "Literature Evaluation Skills"
DEFAULT_USER_AGENT = "Literature-Evaluation-Skills/1.0"
MAX_HELPER_UPLOAD_BYTES = 256 * 1024 * 1024
LIBRARY_PREFIX_PATTERN = re.compile(r"^(?:users/0|groups/\d+)$")


class LocalAPIError(RuntimeError):
    """Raised when a Zotero Local API write/upload contract cannot be satisfied."""


def normalize_library_prefix(value: str) -> str:
    prefix = value.strip().strip("/")
    if not LIBRARY_PREFIX_PATTERN.fullmatch(prefix):
        raise LocalAPIError(
            "library prefix must be 'users/0' or 'groups/<numeric-group-id>'."
        )
    return prefix


def header_value(headers: dict[str, str], name: str) -> str | None:
    target = name.casefold()
    for key, value in headers.items():
        if key.casefold() == target:
            return value
    return None


def http_result(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[int, bytes, dict[str, str]]:
    request_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        request_headers.update(headers)
    request = Request(url, data=data, headers=request_headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            status = int(getattr(response, "status", response.getcode()))
            return (
                status,
                response.read(),
                {key: value for key, value in response.headers.items()},
            )
    except HTTPError as exc:
        return (
            int(exc.code),
            exc.read(),
            {key: value for key, value in exc.headers.items()} if exc.headers else {},
        )
    except URLError as exc:
        raise LocalAPIError(f"Cannot reach Zotero Local API: {exc.reason}") from exc
    except OSError as exc:
        raise LocalAPIError(f"Zotero Local API request failed: {exc}") from exc


def decode_body(body: bytes) -> str:
    return body.decode("utf-8", errors="replace")


def json_body(body: bytes, label: str) -> Any:
    try:
        return json.loads(decode_body(body))
    except json.JSONDecodeError as exc:
        raise LocalAPIError(f"{label} returned invalid JSON.") from exc


def unauthenticated_json(
    api_base_url: str,
    path: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    server_id: str | None = None,
) -> dict[str, Any]:
    url = api_base_url.rstrip("/") + "/" + path.lstrip("/")
    headers = {"Accept": "application/json", "Zotero-API-Version": "3"}
    if server_id:
        headers["Zotero-Server-ID"] = server_id
    status, body, _ = http_result(
        url,
        headers=headers,
        timeout=timeout,
    )
    if status == 412 and server_id:
        raise LocalAPIError(
            "Zotero-Server-ID changed during verification; discard cached identity and retry."
        )
    if status != 200:
        raise LocalAPIError(
            f"Local API GET {path} returned HTTP {status}: {decode_body(body)[:300]}"
        )
    value = json_body(body, f"Local API GET {path}")
    if not isinstance(value, dict):
        raise LocalAPIError(f"Local API GET {path} returned a non-object payload.")
    return value


def discover_server(
    api_base_url: str = DEFAULT_API_BASE_URL,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, str]:
    url = api_base_url.rstrip("/") + "/"
    status, body, headers = http_result(
        url,
        headers={"Accept": "application/json", "Zotero-API-Version": "3"},
        timeout=timeout,
    )
    if status != 200:
        raise LocalAPIError(
            f"Local API discovery returned HTTP {status}: {decode_body(body)[:300]}"
        )
    server_id = header_value(headers, "Zotero-Server-ID")
    api_version = header_value(headers, "Zotero-API-Version")
    if not server_id:
        raise LocalAPIError(
            "Zotero-Server-ID is missing. Durable local writes require Zotero 10+ Local API."
        )
    if api_version and api_version != "3":
        raise LocalAPIError(f"Unsupported Local API version: {api_version}")
    return {"server_id": server_id, "api_version": api_version or "3"}


def authorize_write(
    api_base_url: str,
    server_id: str,
    *,
    app_name: str = DEFAULT_APP_NAME,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[str, bool]:
    url = api_base_url.rstrip("/") + "/local/authorize"
    status, body, _ = http_result(
        url,
        method="POST",
        data=json.dumps({"appName": app_name}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Zotero-API-Version": "3",
            "Zotero-Server-ID": server_id,
        },
        timeout=timeout,
    )
    if status == 403:
        raise LocalAPIError("Zotero Local API write authorization was denied by the user.")
    if status == 429:
        raise LocalAPIError("Zotero Local API authorization is rate-limited; try again later.")
    if status != 200:
        raise LocalAPIError(
            f"Local write authorization returned HTTP {status}: {decode_body(body)[:300]}"
        )
    payload = json_body(body, "Local write authorization")
    if not isinstance(payload, dict):
        raise LocalAPIError("Local write authorization returned a non-object payload.")
    key = payload.get("key")
    if not isinstance(key, str) or not key.strip():
        raise LocalAPIError("Local write authorization did not return a usable key.")
    return key.strip(), bool(payload.get("remember"))


@dataclass
class LocalWriteClient:
    api_base_url: str
    server_id: str
    timeout: float = DEFAULT_TIMEOUT
    app_name: str = DEFAULT_APP_NAME
    api_key: str | None = None
    remembered: bool = False

    @classmethod
    def connect(
        cls,
        api_base_url: str = DEFAULT_API_BASE_URL,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        app_name: str = DEFAULT_APP_NAME,
    ) -> "LocalWriteClient":
        info = discover_server(api_base_url, timeout=timeout)
        return cls(
            api_base_url=api_base_url,
            server_id=info["server_id"],
            timeout=timeout,
            app_name=app_name,
        )

    def ensure_authorized(self) -> None:
        if self.api_key:
            return
        self.api_key, self.remembered = authorize_write(
            self.api_base_url,
            self.server_id,
            app_name=self.app_name,
            timeout=self.timeout,
        )

    def request(
        self,
        path: str,
        *,
        method: str,
        data: bytes | None,
        headers: dict[str, str] | None = None,
        expected_statuses: set[int],
    ) -> tuple[int, bytes, dict[str, str]]:
        url = self.api_base_url.rstrip("/") + "/" + path.lstrip("/")
        last_status = 0
        last_body = b""
        for attempt in range(2):
            self.ensure_authorized()
            request_headers = {
                "Accept": "application/json",
                "Zotero-API-Version": "3",
                "Zotero-Server-ID": self.server_id,
                "Zotero-API-Key": self.api_key or "",
            }
            if headers:
                request_headers.update(headers)
            status, body, response_headers = http_result(
                url,
                method=method,
                data=data,
                headers=request_headers,
                timeout=self.timeout,
            )
            last_status, last_body = status, body
            if status in expected_statuses:
                if not self.remembered:
                    self.api_key = None
                return status, body, response_headers
            if status == 401 and attempt == 0:
                self.api_key = None
                self.remembered = False
                continue
            if status == 412:
                raise LocalAPIError(
                    "Zotero-Server-ID or write precondition no longer matches; refresh local identity before retrying."
                )
            raise LocalAPIError(
                f"Authorized Local API {method} {path} returned HTTP {status}: "
                f"{decode_body(body)[:300]}"
            )
        raise LocalAPIError(
            f"Authorized Local API request failed after reauthorization: "
            f"HTTP {last_status}: {decode_body(last_body)[:300]}"
        )


def extract_created_key(payload: Any) -> str:
    if not isinstance(payload, dict):
        raise LocalAPIError("Item-create response must be an object.")
    bucket = payload.get("successful")
    if not isinstance(bucket, dict):
        bucket = payload.get("success")
    if not isinstance(bucket, dict):
        raise LocalAPIError(f"Item-create response has no success bucket: {payload}")
    entry = bucket.get("0")
    if entry is None:
        entry = bucket.get(0)
    if isinstance(entry, str) and entry.strip():
        return entry.strip()
    if isinstance(entry, dict):
        key = entry.get("key")
        if not key and isinstance(entry.get("data"), dict):
            key = entry["data"].get("key")
        if isinstance(key, str) and key.strip():
            return key.strip()
    failed = payload.get("failed")
    raise LocalAPIError(f"Item creation did not return a key; failed={failed!r}")


def create_item(
    client: LocalWriteClient,
    library_prefix: str,
    item: dict[str, Any],
) -> str:
    prefix = normalize_library_prefix(library_prefix)
    token = secrets.token_hex(16)
    _, body, _ = client.request(
        f"/{prefix}/items",
        method="POST",
        data=json.dumps([item], ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Zotero-Write-Token": token,
        },
        expected_statuses={200},
    )
    return extract_created_key(json_body(body, "Item-create response"))


def create_attachment_item(
    client: LocalWriteClient,
    library_prefix: str,
    *,
    parent_key: str,
    title: str,
) -> str:
    parent_key = parent_key.strip()
    title = title.strip()
    if not parent_key or not title:
        raise LocalAPIError("parent_key and attachment title are required.")
    return create_item(
        client,
        library_prefix,
        {
            "itemType": "attachment",
            "parentItem": parent_key,
            "linkMode": "imported_file",
            "title": title,
            "tags": [],
            "relations": {},
        },
    )


def file_descriptor(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise LocalAPIError(f"Attachment file does not exist: {path}")
    stat = path.stat()
    if stat.st_size <= 0:
        raise LocalAPIError("Attachment file is empty.")
    if stat.st_size > MAX_HELPER_UPLOAD_BYTES:
        raise LocalAPIError(
            f"Attachment exceeds the helper safety limit of {MAX_HELPER_UPLOAD_BYTES} bytes."
        )
    digest = hashlib.md5()  # noqa: S324 - Zotero upload protocol explicitly requires MD5.
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return {
        "path": path,
        "filename": path.name,
        "filesize": stat.st_size,
        "mtime": stat.st_mtime_ns // 1_000_000,
        "md5": digest.hexdigest(),
        "content_type": content_type,
    }


def upload_authorization(
    client: LocalWriteClient,
    library_prefix: str,
    attachment_key: str,
    descriptor: dict[str, Any],
) -> dict[str, Any]:
    prefix = normalize_library_prefix(library_prefix)
    body = urlencode(
        {
            "md5": descriptor["md5"],
            "filename": descriptor["filename"],
            "filesize": str(descriptor["filesize"]),
            "mtime": str(descriptor["mtime"]),
        }
    ).encode("ascii")
    _, response_body, _ = client.request(
        f"/{prefix}/items/{attachment_key}/file",
        method="POST",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "If-None-Match": "*",
        },
        expected_statuses={200},
    )
    payload = json_body(response_body, "File-upload authorization")
    if not isinstance(payload, dict):
        raise LocalAPIError("File-upload authorization returned a non-object payload.")
    return payload


def send_authorized_upload(
    api_base_url: str,
    descriptor: dict[str, Any],
    authorization: dict[str, Any],
    *,
    timeout: float,
) -> str | None:
    if authorization.get("exists") == 1:
        return None
    upload_url = authorization.get("url")
    upload_key = authorization.get("uploadKey")
    if not isinstance(upload_url, str) or not upload_url.strip():
        raise LocalAPIError("File-upload authorization did not return an upload URL.")
    if not isinstance(upload_key, str) or not upload_key.strip():
        raise LocalAPIError("File-upload authorization did not return an uploadKey.")
    upload_url = urljoin(api_base_url.rstrip("/") + "/", upload_url)
    prefix = str(authorization.get("prefix", ""))
    suffix = str(authorization.get("suffix", ""))
    payload = prefix.encode("utf-8") + descriptor["path"].read_bytes() + suffix.encode("utf-8")
    content_type = str(authorization.get("contentType") or descriptor["content_type"])
    status, body, _ = http_result(
        upload_url,
        method="POST",
        data=payload,
        headers={"Content-Type": content_type},
        timeout=timeout,
    )
    if status != 201:
        raise LocalAPIError(
            f"Local file-byte upload returned HTTP {status}: {decode_body(body)[:300]}"
        )
    return upload_key.strip()


def register_upload(
    client: LocalWriteClient,
    library_prefix: str,
    attachment_key: str,
    upload_key: str,
) -> None:
    prefix = normalize_library_prefix(library_prefix)
    body = urlencode({"upload": upload_key}).encode("ascii")
    client.request(
        f"/{prefix}/items/{attachment_key}/file",
        method="POST",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "If-None-Match": "*",
        },
        expected_statuses={204},
    )


def read_item(
    api_base_url: str,
    library_prefix: str,
    item_key: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    server_id: str | None = None,
) -> dict[str, Any]:
    prefix = normalize_library_prefix(library_prefix)
    return unauthenticated_json(
        api_base_url,
        f"/{prefix}/items/{item_key.strip()}",
        timeout=timeout,
        server_id=server_id,
    )


def verify_attachment(
    api_base_url: str,
    library_prefix: str,
    attachment_key: str,
    *,
    parent_key: str,
    descriptor: dict[str, Any],
    timeout: float = DEFAULT_TIMEOUT,
    server_id: str | None = None,
) -> dict[str, Any]:
    item = read_item(
        api_base_url,
        library_prefix,
        attachment_key,
        timeout=timeout,
        server_id=server_id,
    )
    data = item.get("data")
    if not isinstance(data, dict):
        raise LocalAPIError("Attachment verification returned no item data.")
    checks = {
        "item_type": data.get("itemType") == "attachment",
        "parent": str(data.get("parentItem", "")) == parent_key,
        "link_mode": data.get("linkMode") in {"imported_file", "imported_url"},
        "filename": str(data.get("filename", "")) == descriptor["filename"],
        "md5": str(data.get("md5", "")).casefold() == descriptor["md5"].casefold(),
    }
    if not all(checks.values()):
        raise LocalAPIError(f"Attachment post-upload verification failed: {checks}")
    return item


def upload_file_to_attachment(
    client: LocalWriteClient,
    library_prefix: str,
    attachment_key: str,
    path: Path,
    *,
    parent_key: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    descriptor = file_descriptor(path)
    authorization = upload_authorization(
        client,
        library_prefix,
        attachment_key,
        descriptor,
    )
    upload_key = send_authorized_upload(
        client.api_base_url,
        descriptor,
        authorization,
        timeout=client.timeout,
    )
    if upload_key is not None:
        register_upload(client, library_prefix, attachment_key, upload_key)
    verified = verify_attachment(
        client.api_base_url,
        library_prefix,
        attachment_key,
        parent_key=parent_key,
        descriptor=descriptor,
        timeout=client.timeout,
        server_id=client.server_id,
    )
    return descriptor, verified