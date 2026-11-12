"""Scan job payloads / webhook bodies before enqueue."""

from __future__ import annotations

import json
from typing import Any

from fleetkit_api.security_suite.fast_scan import needs_deep_scan
from fleetkit_api.security_suite.ssrf import SSRFBlocked, assert_safe_url


class PayloadRejected(ValueError):
    pass


def _walk_fast(value: Any, *, path: str = "$") -> list[str]:
    """Cheap walk: SSRF URL checks + regex prefilter. Deep detectors only if needed."""
    findings: list[str] = []
    deep_candidates: list[tuple[str, str]] = []

    def visit(node: Any, node_path: str) -> None:
        if isinstance(node, dict):
            for key, item in node.items():
                key_s = str(key)
                if needs_deep_scan(key_s):
                    deep_candidates.append((f"{node_path}.{key_s}", key_s))
                visit(item, f"{node_path}.{key_s}")
            return
        if isinstance(node, list):
            for idx, item in enumerate(node[:100]):
                visit(item, f"{node_path}[{idx}]")
            return
        if isinstance(node, str):
            if node.startswith(("http://", "https://")):
                try:
                    assert_safe_url(node)
                except SSRFBlocked as exc:
                    findings.append(f"{node_path}: {exc}")
            if needs_deep_scan(node):
                deep_candidates.append((node_path, node))

    visit(value, path)
    if deep_candidates:
        from fleetkit_api.security_suite.detectors.registry import scan_text

        for node_path, text in deep_candidates[:40]:
            for hit in scan_text(text):
                if hit.score >= 3:
                    findings.append(f"{node_path}: {hit.reason}")
                    if len(findings) >= 8:
                        return findings
    return findings


def assert_payload_safe(payload: dict[str, Any] | None, *, strict: bool = True) -> list[str]:
    findings = _walk_fast(payload or {})
    if findings and strict:
        raise PayloadRejected("; ".join(findings[:5]))
    return findings


def summarize_payload(payload: dict[str, Any] | None) -> str:
    try:
        raw = json.dumps(payload or {}, ensure_ascii=False)
    except TypeError:
        raw = str(payload)
    return raw[:500]
