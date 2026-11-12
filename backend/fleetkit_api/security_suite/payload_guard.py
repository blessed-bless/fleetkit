"""Scan job payloads / webhook bodies before enqueue."""

from __future__ import annotations

import json
from typing import Any

from fleetkit_api.security_suite.detectors.registry import scan_text
from fleetkit_api.security_suite.ssrf import SSRFBlocked, assert_safe_url


class PayloadRejected(ValueError):
    pass


def _walk(value: Any, *, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(_walk(item, path=f"{path}.{key}"))
            for hit in scan_text(str(key)):
                if hit.score >= 4:
                    findings.append(f"{path}.{key}: {hit.reason}")
        return findings
    if isinstance(value, list):
        for idx, item in enumerate(value[:100]):
            findings.extend(_walk(item, path=f"{path}[{idx}]"))
        return findings
    if isinstance(value, str):
        for hit in scan_text(value):
            if hit.score >= 3:
                findings.append(f"{path}: {hit.reason}")
        if value.startswith(("http://", "https://")):
            try:
                assert_safe_url(value)
            except SSRFBlocked as exc:
                findings.append(f"{path}: {exc}")
    return findings


def assert_payload_safe(payload: dict[str, Any] | None, *, strict: bool = True) -> list[str]:
    findings = _walk(payload or {})
    if findings and strict:
        raise PayloadRejected("; ".join(findings[:5]))
    return findings


def summarize_payload(payload: dict[str, Any] | None) -> str:
    try:
        raw = json.dumps(payload or {}, ensure_ascii=False)
    except TypeError:
        raw = str(payload)
    return raw[:500]
