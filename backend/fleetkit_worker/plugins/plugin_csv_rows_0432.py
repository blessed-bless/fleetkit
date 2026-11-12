"""Plugin plugin_csv_rows_0432: operation=csv_rows."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Any

from fleetkit_worker.handlers import job

OP = "csv_rows"
SALT = 46
JOB_NAME = "plugin.csv_rows.0432"


def _apply(text: str) -> Any:
    if OP == "reverse":
        return text[::-1]
    if OP == "upper":
        return text.upper()
    if OP == "lower":
        return text.lower()
    if OP == "title":
        return text.title()
    if OP == "slug":
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if OP == "b64":
        return base64.b64encode(text.encode()).decode()
    if OP == "hex":
        return text.encode().hex()
    if OP == "sha1":
        return hashlib.sha1(f"{SALT}:{text}".encode()).hexdigest()
    if OP == "sha256":
        return hashlib.sha256(f"{SALT}:{text}".encode()).hexdigest()
    if OP == "words":
        return [w for w in text.split() if w]
    if OP == "lines":
        return text.splitlines()
    if OP == "json_keys":
        data = json.loads(text)
        return list(data) if isinstance(data, dict) else []
    if OP == "csv_rows":
        return [row.split(",") for row in text.splitlines() if row.strip()]
    if OP == "trim":
        return "\n".join(line.strip() for line in text.splitlines())
    if OP == "dedupe":
        seen = set()
        out = []
        for line in text.splitlines():
            if line not in seen:
                seen.add(line)
                out.append(line)
        return out
    if OP == "sort_lines":
        return sorted(text.splitlines())
    if OP == "rot13":
        return text.translate(
            str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
            )
        )
    if OP == "count_bytes":
        return len(text.encode("utf-8"))
    if OP == "wrap_json":
        return {"salt": SALT, "text": text}
    if OP == "extract_ints":
        return [int(x) for x in re.findall(r"-?\d+", text)]
    raise ValueError(f"unknown op {OP}")


@job(JOB_NAME)
async def run(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("text")
    if raw is None and "data" in payload:
        raw = json.dumps(payload["data"], ensure_ascii=False)
    if not isinstance(raw, str):
        raise ValueError("payload.text must be string (or provide data)")
    result = _apply(raw)
    return {"op": OP, "plugin": "plugin_csv_rows_0432", "salt": SALT, "result": result}
