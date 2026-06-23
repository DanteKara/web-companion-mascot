#!/usr/bin/env python3
"""Capture a Codex app built-in imagegen result from session JSONL as a PNG file."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser().resolve()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def default_sidecar_path(out: Path) -> Path:
    return out.with_name(out.name + ".codex-imagegen.json")


def session_files(codex_home: Path) -> list[Path]:
    sessions_root = codex_home / "sessions"
    if not sessions_root.exists():
        return []
    return sorted(
        sessions_root.rglob("rollout-*.jsonl"),
        key=lambda path: path.stat().st_mtime,
    )


def image_generation_calls(value: Any, *, timestamp: str | None = None) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        if value.get("type") == "image_generation_call" and isinstance(value.get("result"), str):
            call = dict(value)
            if timestamp is not None and not isinstance(call.get("timestamp"), str):
                call["timestamp"] = timestamp
            yield call
        for child in value.values():
            yield from image_generation_calls(child, timestamp=timestamp)
    elif isinstance(value, list):
        for child in value:
            yield from image_generation_calls(child, timestamp=timestamp)


def calls_from_session(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if "image_generation_call" not in line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            timestamp = item.get("timestamp") if isinstance(item, dict) else None
            for call in image_generation_calls(item, timestamp=timestamp):
                call["_sessionPath"] = str(path.resolve())
                call["_lineNumber"] = line_number
                yield call


def decode_png_result(result: str) -> bytes:
    payload = result.strip()
    if "," in payload and payload.lower().startswith("data:image/"):
        payload = payload.split(",", 1)[1]
    try:
        data = base64.b64decode(payload, validate=True)
    except Exception as exc:
        raise ValueError(f"image_generation_call result is not valid base64: {exc}") from exc
    if not data.startswith(PNG_HEADER):
        raise ValueError("image_generation_call result is not a PNG image")
    return data


def find_result(*, session: Path | None, call_id: str | None, codex_home: Path) -> tuple[dict[str, Any], bytes]:
    paths = [session.expanduser().resolve()] if session is not None else session_files(codex_home)
    if not paths:
        raise SystemExit(f"no Codex app session files found under {codex_home / 'sessions'}")

    rejected: list[str] = []
    selected: tuple[dict[str, Any], bytes] | None = None
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"session file not found: {path}")
        for call in calls_from_session(path):
            current_id = call.get("id")
            if call_id is not None and current_id != call_id:
                continue
            try:
                data = decode_png_result(str(call["result"]))
            except ValueError as exc:
                rejected.append(f"{path}:{call.get('_lineNumber')}: {exc}")
                continue
            selected = (call, data)

    if selected is None:
        if call_id:
            detail = f" for call id {call_id!r}"
        else:
            detail = ""
        reason = "; ".join(rejected[-3:])
        suffix = f" Last rejected candidates: {reason}" if reason else ""
        raise SystemExit(f"no PNG image_generation_call result found{detail}.{suffix}")
    return selected


def capture_result(
    *,
    session: Path | None,
    out: Path,
    call_id: str | None,
    json_out: Path | None,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    resolved_out = out.expanduser().resolve()
    resolved_codex_home = codex_home.expanduser().resolve() if codex_home is not None else default_codex_home()
    call, data = find_result(
        session=session,
        call_id=call_id,
        codex_home=resolved_codex_home,
    )

    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_bytes(data)
    metadata = {
        "source": "codex-app-imagegen",
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "sessionPath": call.get("_sessionPath"),
        "lineNumber": call.get("_lineNumber"),
        "callId": call.get("id"),
        "status": call.get("status"),
        "timestamp": call.get("timestamp"),
        "revisedPrompt": call.get("revised_prompt"),
        "outputPath": str(resolved_out),
        "sha256": sha256_bytes(data),
        "bytes": len(data),
    }

    sidecar = json_out.expanduser().resolve() if json_out is not None else default_sidecar_path(resolved_out)
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    metadata["metadataPath"] = str(sidecar)
    return metadata


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="PNG file to write")
    parser.add_argument("--session", type=Path, help="Specific Codex app rollout JSONL to read")
    parser.add_argument("--call-id", help="Specific image_generation_call id to capture")
    parser.add_argument("--json-out", type=Path, help="Metadata sidecar path")
    parser.add_argument("--codex-home", type=Path, help="Codex home directory; defaults to CODEX_HOME or ~/.codex")
    args = parser.parse_args(argv)

    result = capture_result(
        session=args.session,
        out=args.out,
        call_id=args.call_id,
        json_out=args.json_out,
        codex_home=args.codex_home,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
