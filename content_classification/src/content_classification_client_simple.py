
"""
Content Classification API - Simple Python Client
=================================================

A clean, customer-facing client for the Content Classification service.
- No retries, just straight requests + clear error messages.
- Uses http.HTTPStatus (no hard-coded status codes).
- Friendly in notebooks and scripts.
- Minimal dependency: requests
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from PyPDF2 import PdfReader
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

import requests
from requests import Session, Response


__all__ = ["ContentClassificationClient", "ApiError"]


class ApiError(RuntimeError):
    """Raised for non-success HTTP responses with helpful context."""
    def __init__(self, message: str, *, status: Optional[HTTPStatus] = None, body: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.body = body


_FileLike = Union[str, bytes, io.BufferedIOBase]


@dataclass
class ContentClassificationClient:
    """Simple, production-grade client for the Content Classification API."""

    base_url: str
    auth_token: str
    tenant_id: Optional[str] = None
    timeout: float = 30.0
    session: Optional[Session] = None

    _session: Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.base_url = self.base_url if self.base_url.endswith("/") else self.base_url + "/"
        self._session = self.session or requests.Session()

    # ------ internals

    def _headers(self, extra: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        if self.tenant_id:
            headers["X-TenantId"] = self.tenant_id
        if extra:
            headers.update(extra)
        return headers

    def _url(self, path: str) -> str:
        return f"{self.base_url[:-1]}{path}" if path.startswith("/") else f"{self.base_url}{path}"

    def _maybe_json(self, resp: Response) -> Any:
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "application/json" in ctype:
            try:
                return resp.json()
            except Exception:
                return resp.text
        return resp.text if resp.text else None

    def _ensure_success(self, resp: Response) -> Any:
        if HTTPStatus.OK <= HTTPStatus(resp.status_code) < HTTPStatus.MULTIPLE_CHOICES:
            return self._maybe_json(resp)

        try:
            status_enum = HTTPStatus(resp.status_code)
            status_name = f"{status_enum.value} {status_enum.phrase}"
        except ValueError:
            status_enum = None
            status_name = str(resp.status_code)

        body = None
        try:
            body = resp.text
        except Exception:
            pass

        raise ApiError(
            f"Request failed: {resp.request.method} {resp.request.url} -> {status_name}",
            status=status_enum,
            body=body,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        data: Optional[Any] = None,
        json_body: Optional[Any] = None,
        files: Optional[Mapping[str, Tuple[str, Any]]] = None,
    ) -> Any:
        url = self._url(path)
        resp = self._session.request(
            method=method.upper(),
            url=url,
            headers=self._headers(headers),
            params=params,
            data=data,
            json=json_body,
            files=files,
            timeout=self.timeout,
        )
        return self._ensure_success(resp)

    # ------ Category Inference

    def categorize_text(
        self,
        text: str,
        *,
        languages: Optional[Union[str, Mapping[str, float], Iterable[Mapping[str, float]]]] = None,
        approved_only_filter: Optional[bool] = None,
        global_categories_filter: Optional[str] = None,
        tenant_categories_filter: Optional[str] = None,
        number_of_results: Optional[int] = None,
        tenant_id: Optional[str] = None,
        force_refresh: Optional[bool] = None,
    ) -> Any:
        params: Dict[str, Any] = {}
        if languages is not None:
            params["languages"] = languages if isinstance(languages, str) else json.dumps(languages)
        if approved_only_filter is not None:
            params["approved_only_filter"] = "true" if approved_only_filter else "false"
        if global_categories_filter is not None:
            params["global_categories_filter"] = global_categories_filter
        if tenant_categories_filter is not None:
            params["tenant_categories_filter"] = tenant_categories_filter
        if number_of_results is not None:
            params["number_of_results"] = int(number_of_results)
        if force_refresh is not None:
            params["force_refresh"] = "true" if force_refresh else "false"

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if tenant_id:
            headers["X-TenantId"] = tenant_id

        return self._request("POST", "/inference/text", params=params, headers=headers, json_body=text)

    def categorize_file(
        self,
        file: _FileLike,
        *,
        approved_only_filter: Optional[bool] = None,
        global_categories_filter: Optional[str] = None,
        tenant_categories_filter: Optional[str] = None,
        number_of_results: Optional[int] = None,
        tenant_id: Optional[str] = None,
        force_refresh: Optional[bool] = None,
    ) -> Any:
        params: Dict[str, Any] = {}
        if approved_only_filter is not None:
            params["approved_only_filter"] = "true" if approved_only_filter else "false"
        if global_categories_filter is not None:
            params["global_categories_filter"] = global_categories_filter
        if tenant_categories_filter is not None:
            params["tenant_categories_filter"] = tenant_categories_filter
        if number_of_results is not None:
            params["number_of_results"] = int(number_of_results)
        if force_refresh is not None:
            params["force_refresh"] = "true" if force_refresh else "false"

        files_payload: Dict[str, Tuple[str, Any]] = {}
        if isinstance(file, (str, Path)):
            fp = Path(file)
            files_payload["file"] = (fp.name, open(fp, "rb"))
        elif isinstance(file, bytes):
            files_payload["file"] = ("upload.bin", io.BytesIO(file))
        elif isinstance(file, io.BufferedIOBase):
            files_payload["file"] = ("upload.bin", file)
        else:
            raise TypeError("file must be a path (str/Path), bytes, or file-like")


        headers = {"Accept": "application/json"}
        if tenant_id:
            headers["X-TenantId"] = tenant_id

        try:
            return self._request("POST", "/inference/file", params=params, headers=headers, files=files_payload)
        finally:
            fh = files_payload.get("file", (None, None))[1]
            if isinstance(file, (str, Path)) and hasattr(fh, "close"):
                try:
                    fh.close()
                except Exception:
                    pass

    # ------ Tags Inference

    def extract_tags(self, file: _FileLike, *, custom_tags: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {}
        if custom_tags is not None:
            params["custom_tags"] = custom_tags

        files_payload: Dict[str, Tuple[str, Any]] = {}
        if isinstance(file, (str, Path)):
            fp = Path(file)
            files_payload["file"] = (fp.name, open(fp, "rb"))
        elif isinstance(file, bytes):
            files_payload["file"] = ("upload.bin", io.BytesIO(file))
        elif isinstance(file, io.BufferedIOBase):
            files_payload["file"] = ("upload.bin", file)
        else:
            raise TypeError("file must be a path (str/Path), bytes, or file-like")

        try:
            return self._request("POST", "/tags/get_tags", params=params, files=files_payload)
        finally:
            fh = files_payload.get("file", (None, None))[1]
            if isinstance(file, (str, Path)) and hasattr(fh, "close"):
                try:
                    fh.close()
                except Exception:
                    pass

    # ------ Category Management

    def get_categories(self, *, approved_only_filter: Optional[bool] = None, force_refresh: Optional[bool] = None) -> Any:
        params: Dict[str, Any] = {}
        if approved_only_filter is not None:
            params["approved_only_filter"] = "true" if approved_only_filter else "false"
        if force_refresh is not None:
            params["force_refresh"] = "true" if force_refresh else "false"
        return self._request("GET", "/management/get_categories", params=params)

    def add_categories_from_folders(self, categories_folders_root: str, *, is_approved: Optional[bool] = None, tenant_id: Optional[str] = None) -> Any:
        params: Dict[str, Any] = {"categories_folders_root": categories_folders_root}
        if is_approved is not None:
            params["is_approved"] = "true" if is_approved else "false"
        headers = {"Accept": "application/json"}
        if tenant_id:
            headers["X-TenantId"] = tenant_id
        return self._request("POST", "/management/add_categories_folders", params=params, headers=headers)

    def add_category_file(
        self,
        category_name: str,
        *,
        file: Optional[_FileLike] = None,
        text: Optional[str] = None,
        file_name: Optional[str] = None,
        file_tenant_id: Optional[str] = None,
        file_correlation_id: Optional[str] = None,
        file_item_id: Optional[str] = None,
        is_approved: Optional[bool] = None,
        tenant_id: Optional[str] = None,
    ) -> Any:
        params: Dict[str, Any] = {"category_name": category_name}
        if text is not None:
            params["text"] = text
        if file_name is not None:
            params["file_name"] = file_name
        if file_tenant_id is not None:
            params["file_tenant_id"] = file_tenant_id
        if file_correlation_id is not None:
            params["file_correlation_id"] = file_correlation_id
        if file_item_id is not None:
            params["file_item_id"] = file_item_id
        if is_approved is not None:
            params["is_approved"] = "true" if is_approved else "false"

        headers = {"Accept": "application/json"}
        if tenant_id:
            headers["X-TenantId"] = tenant_id

        files_payload = None
        if file is not None:
            files_payload = {}
            if isinstance(file, (str, Path)):
                fp = Path(file)
                files_payload["file"] = (fp.name, open(fp, "rb"))
            elif isinstance(file, bytes):
                files_payload["file"] = ("upload.bin", io.BytesIO(file))
            elif isinstance(file, io.BufferedIOBase):
                files_payload["file"] = ("upload.bin", file)
            else:
                raise TypeError("file must be a path (str/Path), bytes, or file-like")

        try:
            return self._request("POST", "/management/add_category_file", params=params, headers=headers, files=files_payload)
        finally:
            if files_payload and isinstance(file, (str, Path)):
                fh = files_payload.get("file", (None, None))[1]
                if hasattr(fh, "close"):
                    try:
                        fh.close()
                    except Exception:
                        pass

    def approve_category_file(self, category_file_id: str, *, approve: Optional[bool] = None) -> Any:
        params: Dict[str, Any] = {"category_file_id": category_file_id}
        if approve is not None:
            params["approve"] = "true" if approve else "false"
        return self._request("POST", "/management/approve_category_file", params=params)

    def delete_category_file(self, category_file_id: str) -> Any:
        params = {"category_file_id": category_file_id}
        return self._request("DELETE", "/management/delete_category_file", params=params)

    def update_category_file(
        self,
        category_file_id: str,
        category_name: str,
        *,
        file: Optional[_FileLike] = None,
        text: Optional[str] = None,
        file_name: Optional[str] = None,
        file_tenant_id: Optional[str] = None,
        file_correlation_id: Optional[str] = None,
        file_item_id: Optional[str] = None,
        is_approved: Optional[bool] = None,
    ) -> Any:
        params: Dict[str, Any] = {
            "category_file_id": category_file_id,
            "category_name": category_name,
        }
        if text is not None:
            params["text"] = text
        if file_name is not None:
            params["file_name"] = file_name
        if file_tenant_id is not None:
            params["file_tenant_id"] = file_tenant_id
        if file_correlation_id is not None:
            params["file_correlation_id"] = file_correlation_id
        if file_item_id is not None:
            params["file_item_id"] = file_item_id
        if is_approved is not None:
            params["is_approved"] = "true" if is_approved else "false"

        files_payload = None
        if file is not None:
            files_payload = {}
            if isinstance(file, (str, Path)):
                fp = Path(file)
                files_payload["file"] = (fp.name, open(fp, "rb"))
            elif isinstance(file, bytes):
                files_payload["file"] = ("upload.bin", io.BytesIO(file))
            elif isinstance(file, io.BufferedIOBase):
                files_payload["file"] = ("upload.bin", file)
            else:
                raise TypeError("file must be a path (str/Path), bytes, or file-like")

        try:
            return self._request("POST", "/management/update_category_file", params=params, files=files_payload)
        finally:
            if files_payload and isinstance(file, (str, Path)):
                fh = files_payload.get("file", (None, None))[1]
                if hasattr(fh, "close"):
                    try:
                        fh.close()
                    except Exception:
                        pass

    # ------ Utilities

    def add_categories_from_list(
        self,
        categories: List[Dict[str, str]],
        key_category: str,
        key_text: str,
        key_file_name: str,
        *,
        is_approved: bool = True,
    ) -> List[Any]:
        results: List[Any] = []
        for entry in categories:
            category_name = entry.get(key_category)
            text = entry.get(key_text)
            file_name = entry.get(key_file_name)
            if category_name and text:
                results.append(
                    self.add_category_file(
                        category_name=category_name,
                        text=text,
                        file_name=file_name,
                        is_approved=is_approved,
                    )
                )
        return results

    @staticmethod
    def preview_file(path: Union[str, Path], lines: Optional[int] = None, chars: Optional[int] = None) -> str:
        """
        Preview part of a text file (UTF-8 assumed).
    
        Parameters
        ----------
        path : str | Path
            Path to the file.
        lines : int, optional
            Number of lines to show from the start of the file.
        chars : int, optional
            Number of characters to show from the start of the file.
            Ignored if `lines` is provided.
    
        Returns
        -------
        str
            A string containing the requested preview.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
    
        if lines is not None:
            with p.open("r", encoding="utf-8", errors="replace") as f:
                content = "".join([next(f, "") for _ in range(lines)])
            return content.strip("\n")
    
        elif chars is not None:
            with p.open("r", encoding="utf-8", errors="replace") as f:
                content = f.read(chars)
            return content.strip("\n")
    
        else:
            raise ValueError("You must specify either `lines` or `chars`.")

    @staticmethod
    def preview_pdf(file_path: Union[str, Path, bytes, io.BufferedIOBase], 
                    pages: Optional[int] = 1, 
                    chars: Optional[int] = 1000) -> str:
        """
        Preview text content from the first N pages or first M characters of a PDF file.

        Parameters
        ----------
        file_path : str | Path | bytes | file-like
            Path to the PDF file, bytes content, or file-like object.
        pages : int, optional
            Number of pages to read (default: 1).
        chars : int, optional
            Maximum number of characters to return (default: 1000).

        Returns
        -------
        str
            A truncated preview of the PDF text content.

        Raises
        ------
        FileNotFoundError
            If the given path does not exist.
        ValueError
            If the file is not a valid PDF or has no extractable text.
        """
        try:
            if isinstance(file_path, (str, Path)):
                path = Path(file_path)
                if not path.exists():
                    raise FileNotFoundError(f"PDF file not found: {path}")
                reader = PdfReader(str(path))
            elif isinstance(file_path, bytes):
                reader = PdfReader(io.BytesIO(file_path))
            elif isinstance(file_path, io.BufferedIOBase):
                reader = PdfReader(file_path)
            else:
                raise TypeError("file_path must be str, Path, bytes, or file-like object")

            text_parts = []
            for i, page in enumerate(reader.pages[:pages]):
                text = page.extract_text() or ""
                text_parts.append(text)
                if len("".join(text_parts)) >= chars:
                    break

            preview_text = "".join(text_parts)[:chars].strip()
            if not preview_text:
                raise ValueError("No text could be extracted from the PDF file.")
            return preview_text

        except Exception as e:
            raise ValueError(f"Failed to preview PDF: {e}") from e
