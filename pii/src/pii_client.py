# pii_client.py
from __future__ import annotations

import io
from enum import IntEnum
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

import requests
from requests import Session, Response


class ApiError(RuntimeError):
    """Raised for non-success HTTP responses with helpful context."""
    def __init__(self, message: str, *, status: Optional[HTTPStatus] = None, body: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.body = body


class ProtectedDataLabel(IntEnum):
    # PII
    AccountNumber = 1
    Age = 2
    Date = 3
    DateInterval = 4
    Dob = 5
    DriverLicense = 6
    Duration = 7
    EmailAddress = 8
    Event = 9
    Filename = 10
    IpAddress = 13
    Language = 14
    Location = 15
    LocationAddress = 16
    LocationCity = 17
    LocationCoordinate = 18
    LocationCountry = 19
    LocationState = 20
    LocationZip = 21
    MaritalStatus = 22
    Money = 23
    Name = 24
    NameFamily = 25
    NameGiven = 26
    NumericalPii = 28
    Occupation = 29
    Organization = 30
    Origin = 32
    PassportNumber = 33
    Password = 34
    PhoneNumber = 35
    PoliticalAffiliation = 37
    Religion = 38
    Ssn = 39
    Time = 40
    Url = 41
    Username = 42
    VehicleId = 43
    ZodiacSign = 44
    LocationAddressStreet = 57
    Gender = 58
    Sexuality = 59

    # PHI
    HealthcareNumber = 12
    NameMedicalProfessional = 27
    OrganizationMedicalFacility = 31
    PhysicalAttribute = 36
    BloodType = 45
    Condition = 46
    Dose = 47
    Drug = 48
    Injury = 49
    MedicalProcess = 50
    Statistics = 51

    # PCI
    BankAccount = 52
    CreditCard = 53
    CreditCardExpiration = 54
    Cvv = 55
    RoutingNumber = 56


# Mapping of label categories for visualization and filtering
LABEL_CATEGORY_MAP = {
    **{lbl: "PII" for lbl in [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18,
        19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34,
        35, 37, 38, 39, 40, 41, 42, 43, 44, 57, 58, 59]},
    **{lbl: "PHI" for lbl in [
        12, 31, 36, 45, 46, 47, 48, 49, 50, 51]},
    **{lbl: "PCI" for lbl in [52, 53, 54, 55, 56]},
}


_FileLike = Union[str, bytes, io.BufferedIOBase]


@dataclass
class PiiClient:
    """
    Simple, production-grade client for Votiro DDR PII Detection & Masking (v1).

    Server (per swagger):
      Base URL: https://prod.us.paralus.votiro.com/pii
      Paths:
        - GET  /api/v1/PiiProviderHealthCheck
        - POST /api/v1/DetectPiiInText
        - POST /api/v1/DetectPiiInFile
        - POST /api/v1/MaskPiiInText
        - POST /api/v1/MaskPiiInFile
        - GET  /api/v1/thresholds
        - POST /api/v1/thresholds
    """
    base_url: str
    auth_token: str
    tenant_id: Optional[str] = None
    timeout: float = 30.0
    session: Optional[Session] = None

    _session: Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Always end with a slash for cleaner URL joining
        self.base_url = self.base_url if self.base_url.endswith("/") else self.base_url + "/"
        self._session = self.session or requests.Session()

        # Auto-extract tenant_id from JWT if not provided
        if not self.tenant_id:
            derived = self._extract_tenant_id_from_jwt(self.auth_token)
            if derived:
                self.tenant_id = derived

    # ---------- internals

    def _headers(self, extra: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Accept": "application/json",
        }
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
                return resp.text  # return raw on malformed JSON
        return resp.text if resp.text else None

    def _ensure_success(self, resp: Response) -> Any:
        try:
            status_enum = HTTPStatus(resp.status_code)
        except ValueError:
            status_enum = None

        if status_enum and HTTPStatus.OK <= status_enum < HTTPStatus.MULTIPLE_CHOICES:
            return self._maybe_json(resp)

        status_name = f"{resp.status_code} {getattr(status_enum, 'phrase', '')}".strip()
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

    # ---------- health

    def health_check(self) -> bool:
        result = self._request("GET", "/api/v1/PiiProviderHealthCheck")
        if isinstance(result, bool):
            return result
        # If backend returns text "true"/"false"
        if isinstance(result, str):
            return result.strip().lower() == "true"
        return bool(result)

    # ---------- helpers for multipart

    @staticmethod
    def _file_field(file: _FileLike) -> Tuple[str, Any]:
        if isinstance(file, (str, Path)):
            p = Path(file)
            return (p.name, open(p, "rb"))
        elif isinstance(file, bytes):
            return ("upload.bin", io.BytesIO(file))
        elif isinstance(file, io.BufferedIOBase):
            return ("upload.bin", file)
        else:
            raise TypeError("file must be a path (str/Path), bytes, or file-like")

    # ---------- Detect

    def detect_pii_in_text(
        self,
        text: str,
        *,
        human_readable_response: bool = False,
        labels: Optional[list[int]] = None,
        include_pii: Optional[bool] = None,
        include_phi: Optional[bool] = None,
        include_pci: Optional[bool] = None,
        use_tenant_threshold: Optional[bool] = None,
        global_min_conf: Optional[float] = None,
        per_label_min_conf: Optional[Mapping[str, Optional[float]]] = None,
        custom_label_rules: Optional[list[Mapping[str, Any]]] = None,
    ) -> Any:
        """
        POST /api/v1/DetectPiiInText
        Swagger: 'text' is a query param; other options are multipart form fields.
        """
        params: Dict[str, Any] = {"text": text, "humanReadableResponse": "true" if human_readable_response else "false"}

        form: Dict[str, Any] = {}
        if labels is not None: form["Labels"] = labels
        if include_pii is not None: form["IncludePii"] = include_pii
        if include_phi is not None: form["IncludePhi"] = include_phi
        if include_pci is not None: form["IncludePci"] = include_pci
        if use_tenant_threshold is not None: form["UseTenantThreshold"] = use_tenant_threshold
        if global_min_conf is not None: form["GlobalMinimalConfidence"] = float(global_min_conf)
        if per_label_min_conf is not None: form["PerLabelMinimalConfidence"] = dict(per_label_min_conf)
        if custom_label_rules is not None: form["CustomLabelRules"] = custom_label_rules

        headers = {"Accept": "application/json"}
        return self._request("POST", "/api/v1/DetectPiiInText", params=params, headers=headers, data=form)

    def detect_pii_in_file(
        self,
        file: _FileLike,
        *,
        human_readable_response: bool = False,
        labels: Optional[list[int]] = None,
        include_pii: Optional[bool] = None,
        include_phi: Optional[bool] = None,
        include_pci: Optional[bool] = None,
        use_tenant_threshold: Optional[bool] = None,
        global_min_conf: Optional[float] = None,
        per_label_min_conf: Optional[Mapping[str, Optional[float]]] = None,
        custom_label_rules: Optional[list[Mapping[str, Any]]] = None,
    ) -> Any:
        """
        POST /api/v1/DetectPiiInFile (multipart 'file' plus optional fields).
        """
        params: Dict[str, Any] = {"humanReadableResponse": "true" if human_readable_response else "false"}

        files_payload: Dict[str, Tuple[str, Any]] = {"file": self._file_field(file)}
        data: Dict[str, Any] = {}
        if labels is not None: data["Labels"] = labels
        if include_pii is not None: data["IncludePii"] = include_pii
        if include_phi is not None: data["IncludePhi"] = include_phi
        if include_pci is not None: data["IncludePci"] = include_pci
        if use_tenant_threshold is not None: data["UseTenantThreshold"] = use_tenant_threshold
        if global_min_conf is not None: data["GlobalMinimalConfidence"] = float(global_min_conf)
        if per_label_min_conf is not None: data["PerLabelMinimalConfidence"] = dict(per_label_min_conf)
        if custom_label_rules is not None: data["CustomLabelRules"] = custom_label_rules

        try:
            return self._request("POST", "/api/v1/DetectPiiInFile", params=params, data=data, files=files_payload)
        finally:
            # Close only if we opened the handle
            fh = files_payload.get("file", (None, None))[1]
            if isinstance(file, (str, Path)) and hasattr(fh, "close"):
                try:
                    fh.close()
                except Exception:
                    pass

    # ---------- Mask

    def mask_pii_in_text(
        self,
        text: str,
        *,
        labels: Optional[list[int]] = None,
        include_pii: Optional[bool] = None,
        include_phi: Optional[bool] = None,
        include_pci: Optional[bool] = None,
        use_tenant_threshold: Optional[bool] = None,
        global_min_conf: Optional[float] = None,
        per_label_min_conf: Optional[Mapping[str, Optional[float]]] = None,
        custom_label_rules: Optional[list[Mapping[str, Any]]] = None,
    ) -> str:
        """
        POST /api/v1/MaskPiiInText
        Swagger: 'text' is a query param; other options are multipart form fields.
        Returns masked text (string).
        """
        params: Dict[str, Any] = {"text": text}

        form: Dict[str, Any] = {}
        if labels is not None: form["Labels"] = labels
        if include_pii is not None: form["IncludePii"] = include_pii
        if include_phi is not None: form["IncludePhi"] = include_phi
        if include_pci is not None: form["IncludePci"] = include_pci
        if use_tenant_threshold is not None: form["UseTenantThreshold"] = use_tenant_threshold
        if global_min_conf is not None: form["GlobalMinimalConfidence"] = float(global_min_conf)
        if per_label_min_conf is not None: form["PerLabelMinimalConfidence"] = dict(per_label_min_conf)
        if custom_label_rules is not None: form["CustomLabelRules"] = custom_label_rules

        result = self._request("POST", "/api/v1/MaskPiiInText", params=params, data=form)
        return result if isinstance(result, str) else str(result)

    def mask_pii_in_file(
        self,
        file: _FileLike,
        *,
        labels: Optional[list[int]] = None,
        include_pii: Optional[bool] = None,
        include_phi: Optional[bool] = None,
        include_pci: Optional[bool] = None,
        use_tenant_threshold: Optional[bool] = None,
        global_min_conf: Optional[float] = None,
        per_label_min_conf: Optional[Mapping[str, Optional[float]]] = None,
        custom_label_rules: Optional[list[Mapping[str, Any]]] = None,
    ) -> bytes:
        """
        POST /api/v1/MaskPiiInFile (multipart 'file' plus optional fields).
        Returns masked file (binary).
        """
        files_payload: Dict[str, Tuple[str, Any]] = {"file": self._file_field(file)}
        data: Dict[str, Any] = {}
        if labels is not None: data["Labels"] = labels
        if include_pii is not None: data["IncludePii"] = include_pii
        if include_phi is not None: data["IncludePhi"] = include_phi
        if include_pci is not None: data["IncludePci"] = include_pci
        if use_tenant_threshold is not None: data["UseTenantThreshold"] = use_tenant_threshold
        if global_min_conf is not None: data["GlobalMinimalConfidence"] = float(global_min_conf)
        if per_label_min_conf is not None: data["PerLabelMinimalConfidence"] = dict(per_label_min_conf)
        if custom_label_rules is not None: data["CustomLabelRules"] = custom_label_rules

        try:
            # This endpoint returns the masked file as binary; don't try to parse JSON.
            url = self._url("/api/v1/MaskPiiInFile")
            resp = self._session.request(
                method="POST",
                url=url,
                headers=self._headers(),
                data=data,
                files=files_payload,
                timeout=self.timeout,
            )
            try:
                status_enum = HTTPStatus(resp.status_code)
            except ValueError:
                status_enum = None
            if not (status_enum and HTTPStatus.OK <= status_enum < HTTPStatus.MULTIPLE_CHOICES):
                status_name = f"{resp.status_code} {getattr(status_enum, 'phrase', '')}".strip()
                raise ApiError(
                    f"Request failed: POST {url} -> {status_name}",
                    status=status_enum,
                    body=resp.text,
                )
            return resp.content
        finally:
            fh = files_payload.get("file", (None, None))[1]
            if isinstance(file, (str, Path)) and hasattr(fh, "close"):
                try:
                    fh.close()
                except Exception:
                    pass

    # ---------- Thresholds

    def get_thresholds(self) -> Any:
        """
        GET /api/v1/thresholds
        Returns array[ThresholdConfigurationDto] with label (enum int), minimalConfidence, labelName (readOnly).
        """
        return self._request("GET", "/api/v1/thresholds")

    def post_thresholds(self, *, thresholds: Dict[int, float]) -> Any:
        """
        POST /api/v1/thresholds
    
        The API expects a raw JSON array of threshold objects:
    
            [
              {"label": <int>, "minimalConfidence": <float>},
              ...
            ]
    
        - `label` must be an enum integer.
        - `minimalConfidence` is a float 0–1.
        - Tenant identification is derived from the Bearer token; no tenantId
          should be sent in the payload.
        """
    
        body = [
            {"label": int(k), "minimalConfidence": float(v)}
            for k, v in thresholds.items()
        ]
    
        headers = {"Content-Type": "application/json-patch+json"}
    
        return self._request("POST", "/api/v1/thresholds", headers=headers, json_body=body)


    
    # Utility: convert label ID (int) to label name string
    @staticmethod
    def label_name_from_id(label_id: int) -> str:
        """
        Return the label name (e.g. 'EmailAddress') for a given label ID.
        Falls back to 'Unknown' if the ID is not defined in ProtectedDataLabel.
        """
        try:
            return ProtectedDataLabel(label_id).name
        except ValueError:
            return f"Unknown({label_id})"
    
    # Utility: resolve label ID (int) by labelName
    @staticmethod
    def resolve_label_id(label_name: str) -> Optional[int]:
        """
        Return the integer label ID for a given label name, case-insensitive.
        Checks both the ProtectedDataLabel enum and live threshold data (if available).
        """
        try:
            return ProtectedDataLabel[label_name].value
        except:
            label_name_norm = label_name.strip().lower()
            # Try enum direct match
            for member in ProtectedDataLabel:
                if member.name.lower() == label_name_norm:
                    return int(member.value)
        return None

    # ---------- Notebook-friendly download helpers (OS-agnostic) ----------

    @staticmethod
    def _unique_path(base: "Path", overwrite: bool = False) -> "Path":
        """Return base if available (or overwrite), otherwise append -1, -2, ..."""
        p = Path(base)
        if overwrite or not p.exists():
            return p
        stem, suffix = p.stem, p.suffix
        i = 1
        while True:
            cand = p.with_name(f"{stem}-{i}{suffix}")
            if not cand.exists():
                return cand
            i += 1

    @staticmethod
    def save_and_link(content: bytes, *, filename: str = "masked_output.pdf",
                      directory: str = "downloads", overwrite: bool = False):
        """
        Write bytes exactly as returned by the API (no transformation) and display a
        clickable 'Download file' link in the notebook UI.

        Returns: pathlib.Path of the saved file.
        """
        from IPython.display import FileLink, display  # notebook-only
        
        out_dir = Path(directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        target = PiiClient._unique_path(out_dir / filename, overwrite=overwrite)

        target.write_bytes(content)  # raw bytes, no changes
        display(FileLink(target.as_posix(), result_html_prefix=""))
        return target

    @staticmethod
    def link_file(path: "Path"):
        from IPython.display import FileLink, display  # notebook-only
        display(FileLink(str(path), result_html_prefix=""))

    # ---------- JWT helper ----------

    @staticmethod
    def _extract_tenant_id_from_jwt(auth_token: str) -> Optional[str]:
        """
        Decode the JWT payload (without verifying signature) and return the tenant_id if present.
        Does not require PyJWT; uses safe base64 decode.

        Common claim keys checked: 'tenantId', 'tid', 'tenant_id', 'tenant'
        """
        import base64
        import json

        if not auth_token or "." not in auth_token:
            return None

        try:
            # Split the JWT into 3 parts (header.payload.signature)
            parts = auth_token.split(".")
            if len(parts) < 2:
                return None
            payload_b64 = parts[1]

            # Fix base64 padding if missing
            rem = len(payload_b64) % 4
            if rem:
                payload_b64 += "=" * (4 - rem)

            decoded_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            payload = json.loads(decoded_bytes.decode("utf-8"))

            for key in ("tenantId", "tid", "tenant_id", "tenant"):
                if key in payload:
                    return payload[key]
        except Exception:
            pass
        return None

    # ---------- Notebook preview helper ----------

    @staticmethod
    def preview_file(file_path: Path):
        """
        Display or preview a masked file directly inside a Jupyter notebook.

        - For PDF: shows an inline PDF viewer.
        - For images (png/jpg/jpeg): shows the image inline.
        - For text-like files: prints the first few lines.

        Usage example:
            outp = Path("masked_pii_result.bin")
            PiiClient.preview_masked_file(outp)
        """
        from IPython.display import display, Image, HTML

        suffix = file_path.suffix.lower()
        if not file_path.exists():
            print(f"[preview] File not found: {file_path}")
            return

        if suffix in {".pdf"}:
            # Inline PDF viewer
            display(HTML(f'<embed src="{file_path.as_posix()}" width="800px" height="600px" type="application/pdf">'))

        elif suffix in {".png", ".jpg", ".jpeg"}:
            # Inline image preview
            display(Image(filename=file_path.as_posix()))

        elif suffix in {".txt", ".csv", ".log"}:
            # Print first few lines of text
            text = file_path.read_text(errors="ignore")
            preview = "\n".join(text.splitlines()[:20])
            print("".join([preview, "\n...\n[truncated]" if len(text.splitlines()) > 20 else ""]))

        else:
            # Generic binary or unknown type
            size = file_path.stat().st_size
            print(f"[preview] {file_path.name} ({size:,} bytes) — binary preview not supported")

    @staticmethod
    def show_labels_summary():
        """Display ProtectedDataLabel mapping grouped by category."""
        from IPython.display import display, HTML
        from textwrap import dedent

        rows = []
        for label in ProtectedDataLabel:
            cat = LABEL_CATEGORY_MAP.get(label.value, "Unknown")
            rows.append((cat, label.value, label.name))

        # Sort by category then ID
        rows.sort(key=lambda x: (x[0], x[1]))

        html = "<h4>Personal Information Labels</h4>"
        html += "<table><thead><tr><th>Category</th><th>Label ID</th><th>Label Name</th></tr></thead><tbody>"
        for cat, lid, lname in rows:
            html += f"<tr><td>{cat}</td><td>{lid}</td><td>{lname}</td></tr>"
        html += "</tbody></table>"
        display(HTML(html))