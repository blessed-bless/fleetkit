"""Detector det_xss_0162: family=xss."""

from __future__ import annotations

from dataclasses import dataclass

NEEDLES = ['<script', 'javascript:', 'onerror=', '<img', 'svg/onload']
MAX_LEN = 805
THRESHOLD = 2
WEIGHT = 2
FAMILY = "xss"
DETECTOR = "det_xss_0162"
LOG4J_MARK = chr(36) + chr(123)  # ${ Avoid f-string clash


@dataclass(frozen=True)
class Finding:
    family: str
    detector: str
    score: int
    matched: tuple[str, ...]
    reason: str


def inspect(value: str) -> Finding | None:
    text = value if isinstance(value, str) else str(value)
    if len(text) > MAX_LEN:
        return Finding(
            family=FAMILY,
            detector=DETECTOR,
            score=WEIGHT * 2,
            matched=("length",),
            reason=f"input longer than {MAX_LEN}",
        )
    lowered = text.lower()
    hits = [n for n in NEEDLES if n.lower() in lowered]
    if len(hits) < THRESHOLD:
        return None
    score = WEIGHT * len(hits)
    if FAMILY == "path_traversal" and ".." in text:
        score += 2
    elif FAMILY == "sqli" and ("--" in text or "#" in text):
        score += 2
    elif FAMILY == "xss" and "<" in text and ">" in text:
        score += 2
    elif FAMILY == "cmdi" and any(ch in text for ch in ("|", ";", "`")):
        score += 2
    elif FAMILY == "log4shell" and LOG4J_MARK in text:
        score += 3
    return Finding(
        family=FAMILY,
        detector=DETECTOR,
        score=score,
        matched=tuple(hits[:8]),
        reason=f"matched {len(hits)} xss indicators",
    )


def is_suspicious(value: str, *, min_score: int = 2) -> bool:
    finding = inspect(value)
    return bool(finding and finding.score >= min_score)
