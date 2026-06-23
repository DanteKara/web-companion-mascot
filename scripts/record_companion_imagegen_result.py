#!/usr/bin/env python3
"""Record a selected $imagegen output for a web companion mascot generation job."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CANONICAL_BASE_PATH = "references/canonical-base.png"
USER_ART_PROVENANCE = {
    "user-provided-integrated-row-art",
    "artist-provided-integrated-row-art",
}
BUILT_IN_CHROMA_CLEANUP_PROVENANCE = "built-in-imagegen-chroma-cleanup"
CODEX_APP_IMAGEGEN_PROVENANCE = "codex-app-imagegen"
CODEX_APP_CHROMA_CLEANUP_PROVENANCE = "codex-app-imagegen-chroma-cleanup"
CODEX_APP_PROVENANCES = {
    CODEX_APP_IMAGEGEN_PROVENANCE,
    CODEX_APP_CHROMA_CLEANUP_PROVENANCE,
}
CHROMA_CLEANUP_PROVENANCES = {
    BUILT_IN_CHROMA_CLEANUP_PROVENANCE,
    CODEX_APP_CHROMA_CLEANUP_PROVENANCE,
}
PALETTE_COMPLEXITY_WARNING = "smooth_or_overdetailed_foreground_palette"
ROW_SOURCE_BLOCKING_WARNING_CODES = {
    "fake_checkerboard_transparency_background",
    "non_uniform_chroma_key_background",
    "no_foreground_sprite_detected",
}


def load_jobs(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"job manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def job_list(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("invalid imagegen-jobs.json: jobs must be a list")
    return [job for job in jobs if isinstance(job, dict)]


def find_job(manifest: dict[str, Any], job_id: str) -> dict[str, Any]:
    for job in job_list(manifest):
        if job.get("id") == job_id:
            return job
    raise SystemExit(f"unknown job id: {job_id}")


def image_metadata(path: Path) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
        }


def parse_hex_color(value: str) -> tuple[int, int, int]:
    text = value.strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) != 6:
        raise ValueError(f"invalid hex color: {value}")
    return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)


def chroma_key_rgb_from_data(data: dict[str, Any]) -> tuple[int, int, int] | None:
    chroma_key = data.get("chromaKey")
    if not isinstance(chroma_key, dict):
        style = data.get("style")
        if isinstance(style, dict):
            chroma_key = style.get("chromaKey")
    if not isinstance(chroma_key, dict):
        return None
    rgb = chroma_key.get("rgb")
    if isinstance(rgb, list) and len(rgb) == 3:
        return tuple(int(channel) for channel in rgb)
    hex_value = chroma_key.get("hex")
    if isinstance(hex_value, str):
        return parse_hex_color(hex_value)
    return None


def read_chroma_key_rgb(run_dir: Path) -> tuple[int, int, int]:
    for filename in ("companion_request.json", "manifest.json"):
        path = run_dir / filename
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        rgb = chroma_key_rgb_from_data(data)
        if rgb is not None:
            return rgb
    return (255, 0, 255)


def close_to_rgb(left: tuple[int, int, int], right: tuple[int, int, int], tolerance: int) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(left, right))


def quantized_rgb(rgb: tuple[int, int, int], step: int = 16) -> tuple[int, int, int]:
    return tuple(channel // step for channel in rgb)


def add_style_warning(
    warnings: list[dict[str, Any]],
    *,
    code: str,
    message: str,
    details: dict[str, Any],
) -> None:
    warnings.append(
        {
            "code": code,
            "message": message,
            "details": details,
        }
    )


def analyze_base_style(path: Path, chroma_key_rgb: tuple[int, int, int]) -> dict[str, Any]:
    from PIL import Image

    with Image.open(path) as raw_image:
        image = raw_image.convert("RGBA")
        width, height = image.size
        pixels = image.load()

        border_rgbs: list[tuple[int, int, int]] = []
        border_alphas: list[int] = []
        for x in range(width):
            border_rgbs.append(pixels[x, 0][:3])
            border_alphas.append(pixels[x, 0][3])
            border_rgbs.append(pixels[x, height - 1][:3])
            border_alphas.append(pixels[x, height - 1][3])
        for y in range(1, max(1, height - 1)):
            border_rgbs.append(pixels[0, y][:3])
            border_alphas.append(pixels[0, y][3])
            border_rgbs.append(pixels[width - 1, y][:3])
            border_alphas.append(pixels[width - 1, y][3])

        border_count = max(1, len(border_rgbs))
        dominant_rgb, dominant_count = Counter(border_rgbs).most_common(1)[0]
        exact_key_count = sum(1 for rgb in border_rgbs if rgb == chroma_key_rgb)
        close_key_count = sum(1 for rgb in border_rgbs if close_to_rgb(rgb, chroma_key_rgb, 3))
        transparent_border_count = sum(1 for alpha in border_alphas if alpha == 0)
        transparent_border_ratio = transparent_border_count / border_count
        light_gray_border_count = sum(
            1
            for red, green, blue in border_rgbs
            if 220 <= min(red, green, blue) <= 255 and max(red, green, blue) - min(red, green, blue) <= 6
        )
        light_gray_border_ratio = light_gray_border_count / border_count

        background_like_rgbs: list[tuple[int, int, int]] = []
        foreground_rgbs: list[tuple[int, int, int]] = []
        transparent_pixels = 0
        for y in range(height):
            for x in range(width):
                red, green, blue, alpha = pixels[x, y]
                rgb = (red, green, blue)
                if alpha == 0:
                    transparent_pixels += 1
                    continue
                if close_to_rgb(rgb, chroma_key_rgb, 40):
                    background_like_rgbs.append(rgb)
                    continue
                foreground_rgbs.append(rgb)

    foreground_unique = set(foreground_rgbs)
    foreground_quantized = {quantized_rgb(rgb) for rgb in foreground_rgbs}
    background_like_count = max(1, len(background_like_rgbs))
    background_like_exact_count = sum(1 for rgb in background_like_rgbs if rgb == chroma_key_rgb)
    background_like_close_count = sum(1 for rgb in background_like_rgbs if close_to_rgb(rgb, chroma_key_rgb, 3))
    warnings: list[dict[str, Any]] = []
    exact_key_ratio = exact_key_count / border_count
    close_key_ratio = close_key_count / border_count
    dominant_ratio = dominant_count / border_count
    background_like_exact_ratio = background_like_exact_count / background_like_count
    background_like_close_ratio = background_like_close_count / background_like_count
    transparent_background = transparent_border_ratio >= 0.985 and transparent_pixels > 0

    if not transparent_background and light_gray_border_ratio >= 0.8 and close_key_ratio < 0.2:
        add_style_warning(
            warnings,
            code="fake_checkerboard_transparency_background",
            message=(
                "Source sprite appears to use fake checkerboard or light-gray transparency pixels; "
                "reject fake transparency backgrounds and require real alpha or the run chroma key."
            ),
            details={
                "lightGrayBorderRatio": round(light_gray_border_ratio, 4),
                "closeKeyRatio": round(close_key_ratio, 4),
                "transparentBorderRatio": round(transparent_border_ratio, 4),
            },
        )

    if not transparent_background and (
        close_key_ratio < 0.985
        or exact_key_ratio < 0.975
        or background_like_close_ratio < 0.985
        or background_like_exact_ratio < 0.975
    ):
        add_style_warning(
            warnings,
            code="non_uniform_chroma_key_background",
            message=(
                "Source sprite background is not a perfectly flat chroma key; reject "
                "vignettes, lighting falloff, texture, shadows, or background glow before accepting the source."
            ),
            details={
                "exactKeyRatio": round(exact_key_ratio, 4),
                "closeKeyRatio": round(close_key_ratio, 4),
                "backgroundLikeExactKeyRatio": round(background_like_exact_ratio, 4),
                "backgroundLikeCloseKeyRatio": round(background_like_close_ratio, 4),
                "dominantBorderRgb": list(dominant_rgb),
                "dominantBorderRatio": round(dominant_ratio, 4),
                "transparentBorderRatio": round(transparent_border_ratio, 4),
            },
        )

    if not foreground_rgbs:
        add_style_warning(
            warnings,
            code="no_foreground_sprite_detected",
            message="Source sprite analysis did not find a non-chroma-key foreground sprite.",
            details={"foregroundPixels": 0},
        )
    elif len(foreground_unique) > 64 or len(foreground_quantized) > 48:
        add_style_warning(
            warnings,
            code=PALETTE_COMPLEXITY_WARNING,
            message=(
                "Source sprite foreground has too many color steps for native pixel art; "
                "reject smooth gradients, glossy app-icon shading, airbrushed highlights, "
                "or over-detailed antialiasing before accepting the source."
            ),
            details={
                "foregroundPixels": len(foreground_rgbs),
                "uniqueRgbCount": len(foreground_unique),
                "quantizedColorCount": len(foreground_quantized),
                "uniqueRgbLimit": 64,
                "quantizedColorLimit": 48,
            },
        )

    return {
        "ok": not warnings,
        "warnings": warnings,
        "background": {
            "expectedRgb": list(chroma_key_rgb),
            "borderPixels": border_count,
            "exactKeyRatio": round(exact_key_ratio, 4),
            "closeKeyRatio": round(close_key_ratio, 4),
            "backgroundLikePixels": len(background_like_rgbs),
            "backgroundLikeExactKeyRatio": round(background_like_exact_ratio, 4),
            "backgroundLikeCloseKeyRatio": round(background_like_close_ratio, 4),
            "dominantBorderRgb": list(dominant_rgb),
            "dominantBorderRatio": round(dominant_ratio, 4),
            "transparentBorderRatio": round(transparent_border_ratio, 4),
            "lightGrayBorderRatio": round(light_gray_border_ratio, 4),
            "transparentBackground": transparent_background,
            "transparentPixels": transparent_pixels,
        },
        "foreground": {
            "pixels": len(foreground_rgbs),
            "uniqueRgbCount": len(foreground_unique),
            "quantizedColorCount": len(foreground_quantized),
            "uniqueRgbLimit": 64,
            "quantizedColorLimit": 48,
        },
    }


def blocking_base_style_warnings(
    analysis: dict[str, Any],
    *,
    source_provenance: str,
) -> list[dict[str, Any]]:
    warnings = [warning for warning in analysis.get("warnings", []) if isinstance(warning, dict)]
    # Palette complexity is a visual-review advisory: keep it in the analysis
    # record, but do not block an otherwise clean base solely on color count.
    return [
        warning
        for warning in warnings
        if warning.get("code") != PALETTE_COMPLEXITY_WARNING
    ]


def blocking_row_source_style_warnings(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    warnings = [warning for warning in analysis.get("warnings", []) if isinstance(warning, dict)]
    return [
        warning
        for warning in warnings
        if warning.get("code") in ROW_SOURCE_BLOCKING_WARNING_CODES
    ]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_relative(path: Path, run_dir: Path) -> str:
    return str(path.resolve().relative_to(run_dir.resolve()))


def completed_job_ids(manifest: dict[str, Any]) -> set[str]:
    return {
        str(job["id"])
        for job in job_list(manifest)
        if job.get("status") == "complete" and isinstance(job.get("id"), str)
    }


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def default_generated_images_root() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser().resolve()
    return codex_home / "generated_images"


def is_builtin_imagegen_source(path: Path) -> bool:
    generated_root = default_generated_images_root()
    return is_relative_to(path, generated_root) and path.name.startswith("ig_")


def validate_source_path(
    *,
    source: Path,
    run_dir: Path,
    requested_provenance: str,
    allow_synthetic_test_source: bool,
    chroma_cleanup_source: Path | None = None,
) -> str:
    if allow_synthetic_test_source:
        return "synthetic-test"
    if is_relative_to(source, run_dir):
        raise SystemExit(
            "source image is inside the companion run directory; record the original "
            "$imagegen output from $CODEX_HOME/generated_images/.../ig_*.png instead"
        )
    if requested_provenance in USER_ART_PROVENANCE:
        return requested_provenance
    if requested_provenance == CODEX_APP_IMAGEGEN_PROVENANCE:
        return requested_provenance
    if requested_provenance == CODEX_APP_CHROMA_CLEANUP_PROVENANCE:
        if chroma_cleanup_source is None:
            raise SystemExit(
                "codex-app-imagegen-chroma-cleanup provenance requires --chroma-cleanup-source "
                "pointing at the original captured Codex app imagegen PNG"
            )
        if not chroma_cleanup_source.is_file():
            raise SystemExit(f"chroma cleanup original source not found: {chroma_cleanup_source}")
        if is_relative_to(chroma_cleanup_source, run_dir):
            raise SystemExit(
                "chroma cleanup original source is inside the companion run directory; "
                "capture Codex app imagegen outputs to a separate workspace folder first"
            )
        if source.resolve() == chroma_cleanup_source.resolve():
            raise SystemExit("chroma cleanup source must be separate from the cleaned output")
        return CODEX_APP_CHROMA_CLEANUP_PROVENANCE
    if requested_provenance == BUILT_IN_CHROMA_CLEANUP_PROVENANCE:
        if chroma_cleanup_source is None:
            raise SystemExit(
                "built-in-imagegen-chroma-cleanup provenance requires --chroma-cleanup-source "
                "pointing at the original $CODEX_HOME/generated_images/.../ig_*.png"
            )
        if not chroma_cleanup_source.is_file():
            raise SystemExit(f"chroma cleanup original source not found: {chroma_cleanup_source}")
        if not is_builtin_imagegen_source(chroma_cleanup_source):
            generated_root = default_generated_images_root()
            raise SystemExit(
                "chroma cleanup original source does not look like a built-in $imagegen output; "
                f"expected {generated_root}/.../ig_*.png"
            )
        if source.resolve() == chroma_cleanup_source.resolve():
            raise SystemExit("chroma cleanup source must be separate from the cleaned output")
        return BUILT_IN_CHROMA_CLEANUP_PROVENANCE
    generated_root = default_generated_images_root()
    if not is_builtin_imagegen_source(source):
        raise SystemExit(
            "source image does not look like a built-in $imagegen output; expected "
            f"{generated_root}/.../ig_*.png. Do not ingest locally drawn, post-processed, "
            "or composited row strips as production visual job outputs."
        )
    return "built-in-imagegen"


def default_codex_app_capture_metadata_path(source: Path) -> Path:
    return source.with_name(source.name + ".codex-imagegen.json")


def validate_codex_app_imagegen_metadata(
    *,
    source_provenance: str,
    source: Path,
    metadata_path: Path | None,
) -> dict[str, Any] | None:
    if source_provenance not in CODEX_APP_PROVENANCES:
        if metadata_path is not None:
            raise SystemExit("--codex-app-capture-metadata requires Codex app imagegen provenance")
        return None

    resolved_metadata_path = (
        metadata_path.expanduser().resolve()
        if metadata_path is not None
        else default_codex_app_capture_metadata_path(source)
    )
    if not resolved_metadata_path.is_file():
        raise SystemExit(
            "codex-app-imagegen provenance requires capture metadata; run "
            "scripts/capture_codex_app_imagegen_result.py and keep the .codex-imagegen.json sidecar"
        )

    metadata = json.loads(resolved_metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise SystemExit(f"invalid Codex app imagegen metadata: {resolved_metadata_path}")
    if metadata.get("source") != CODEX_APP_IMAGEGEN_PROVENANCE:
        raise SystemExit("Codex app imagegen metadata must contain source=codex-app-imagegen")
    expected_hash = metadata.get("sha256")
    actual_hash = file_sha256(source)
    if expected_hash != actual_hash:
        raise SystemExit(
            "Codex app imagegen metadata hash does not match source image: "
            f"expected {expected_hash}, got {actual_hash}"
        )
    output_path = metadata.get("outputPath")
    if isinstance(output_path, str) and Path(output_path).expanduser().resolve() != source.resolve():
        raise SystemExit("Codex app imagegen metadata outputPath does not match --source")

    return {
        "metadataPath": str(resolved_metadata_path),
        "sessionPath": metadata.get("sessionPath"),
        "lineNumber": metadata.get("lineNumber"),
        "callId": metadata.get("callId"),
        "status": metadata.get("status"),
        "timestamp": metadata.get("timestamp"),
        "sha256": actual_hash,
        "bytes": metadata.get("bytes"),
        "revisedPrompt": metadata.get("revisedPrompt"),
    }


def chroma_cleanup_metadata(
    *,
    source_provenance: str,
    original_source: Path | None,
) -> dict[str, Any] | None:
    if source_provenance not in CHROMA_CLEANUP_PROVENANCES:
        if original_source is not None:
            raise SystemExit("--chroma-cleanup-source requires chroma-cleanup source provenance")
        return None
    if original_source is None:
        raise SystemExit(f"{source_provenance} provenance requires --chroma-cleanup-source")
    return {
        "method": "$imagegen chroma-key helper",
        "originalSourcePath": str(original_source.resolve()),
        "originalSourceProvenance": (
            CODEX_APP_IMAGEGEN_PROVENANCE
            if source_provenance == CODEX_APP_CHROMA_CLEANUP_PROVENANCE
            else "built-in-imagegen"
        ),
        "originalSourceSha256": file_sha256(original_source),
    }


def validate_required_grounding(job: dict[str, Any], run_dir: Path) -> None:
    if job.get("allow_prompt_only_generation") is not False:
        return
    inputs = job.get("input_images")
    if not isinstance(inputs, list) or not inputs:
        raise SystemExit(
            f"job {job.get('id')} does not list input_images; grounded companion row jobs must attach references"
        )
    missing = []
    for item in inputs:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise SystemExit(f"job {job.get('id')} has an invalid input image entry")
        path = run_dir / item["path"]
        if not path.is_file():
            missing.append(str(path))
    if missing:
        raise SystemExit(
            f"job {job.get('id')} is missing required grounding image(s): " + ", ".join(missing)
        )


def update_manifest_canonical_base(
    *,
    run_dir: Path,
    reference: dict[str, Any],
) -> None:
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(manifest, dict):
        manifest["canonicalIdentityReference"] = reference
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def update_request_canonical_base(
    *,
    run_dir: Path,
    reference: dict[str, Any],
) -> None:
    request_path = run_dir / "companion_request.json"
    if not request_path.exists():
        return
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if isinstance(request, dict):
        request["canonicalIdentityReference"] = reference
        request_path.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")


def update_base_canonical_reference(
    *,
    run_dir: Path,
    output: Path,
    manifest: dict[str, Any],
    job: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    if job.get("id") != "base":
        return

    canonical = run_dir / CANONICAL_BASE_PATH
    canonical.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, canonical)
    reference = {
        "path": manifest_relative(canonical, run_dir),
        "source_job": "base",
        "sha256": file_sha256(canonical),
        "metadata": metadata,
    }
    job["canonical_reference_path"] = reference["path"]
    manifest["canonical_identity_reference"] = reference
    update_manifest_canonical_base(run_dir=run_dir, reference=reference)
    update_request_canonical_base(run_dir=run_dir, reference=reference)


def record_result(
    *,
    run_dir: Path,
    job_id: str,
    source: Path,
    source_provenance: str,
    force: bool,
    allow_synthetic_test_source: bool,
    strict_base_style: bool = False,
    strict_row_style: bool = False,
    chroma_cleanup_source: Path | None = None,
    codex_app_capture_metadata: Path | None = None,
) -> dict[str, Any]:
    if not source.is_file():
        raise SystemExit(f"source image not found: {source}")
    if chroma_cleanup_source is not None:
        chroma_cleanup_source = chroma_cleanup_source.expanduser().resolve()
    source_provenance = validate_source_path(
        source=source,
        run_dir=run_dir,
        requested_provenance=source_provenance,
        allow_synthetic_test_source=allow_synthetic_test_source,
        chroma_cleanup_source=chroma_cleanup_source,
    )
    codex_metadata_source = (
        chroma_cleanup_source
        if source_provenance == CODEX_APP_CHROMA_CLEANUP_PROVENANCE
        else source
    )
    codex_app_imagegen = validate_codex_app_imagegen_metadata(
        source_provenance=source_provenance,
        source=codex_metadata_source,
        metadata_path=codex_app_capture_metadata,
    )
    chroma_cleanup = chroma_cleanup_metadata(
        source_provenance=source_provenance,
        original_source=chroma_cleanup_source,
    )

    manifest_path = run_dir / "imagegen-jobs.json"
    manifest = load_jobs(manifest_path)
    job = find_job(manifest, job_id)

    missing_deps = [
        dep
        for dep in job.get("depends_on", [])
        if isinstance(dep, str) and dep not in completed_job_ids(manifest)
    ]
    if missing_deps:
        raise SystemExit(f"job {job_id} is not ready; missing dependency result(s): {', '.join(missing_deps)}")
    validate_required_grounding(job, run_dir)

    output_raw = job.get("output_path")
    if not isinstance(output_raw, str):
        raise SystemExit(f"job {job_id} has no output_path")
    output = run_dir / output_raw
    if output.exists() and not force:
        raise SystemExit(f"{output} already exists; pass --force to replace it")

    base_style_analysis = None
    if job_id == "base":
        base_style_analysis = analyze_base_style(source, read_chroma_key_rgb(run_dir))
        blocking_warnings = blocking_base_style_warnings(
            base_style_analysis,
            source_provenance=source_provenance,
        )
        if strict_base_style and blocking_warnings:
            warning_codes = ", ".join(str(warning["code"]) for warning in blocking_warnings)
            raise SystemExit(f"base style analysis failed for canonical base: {warning_codes}")

    row_source_style_analysis = None
    if job.get("kind") == "row-strip":
        row_source_style_analysis = analyze_base_style(source, read_chroma_key_rgb(run_dir))
        blocking_warnings = blocking_row_source_style_warnings(row_source_style_analysis)
        if strict_row_style and blocking_warnings:
            warning_codes = ", ".join(str(warning["code"]) for warning in blocking_warnings)
            raise SystemExit(f"row source style analysis failed for {job_id}: {warning_codes}")

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)
    metadata = image_metadata(output)

    job["status"] = "complete"
    job["source_path"] = str(source)
    job["source_provenance"] = source_provenance
    job["source_sha256"] = file_sha256(source)
    job["output_sha256"] = file_sha256(output)
    if source_provenance == "synthetic-test":
        job["synthetic_test_source"] = True
    else:
        job.pop("synthetic_test_source", None)
    job["completed_at"] = datetime.now(timezone.utc).isoformat()
    job["metadata"] = metadata
    job.pop("cli_fallback", None)
    if codex_app_imagegen is not None:
        job["codex_app_imagegen"] = codex_app_imagegen
    else:
        job.pop("codex_app_imagegen", None)
    if chroma_cleanup is not None:
        job["chroma_cleanup"] = chroma_cleanup
    else:
        job.pop("chroma_cleanup", None)
    if base_style_analysis is not None:
        job["base_style_analysis"] = base_style_analysis
        job["base_style_strict_blocking_warning_codes"] = [
            str(warning.get("code"))
            for warning in blocking_base_style_warnings(
                base_style_analysis,
                source_provenance=source_provenance,
            )
        ]
    if row_source_style_analysis is not None:
        job["row_source_style_analysis"] = row_source_style_analysis
        job["row_source_style_strict_blocking_warning_codes"] = [
            str(warning.get("code"))
            for warning in blocking_row_source_style_warnings(row_source_style_analysis)
        ]
    for key in ["last_error", "secondary_fallback", "repair_reason", "queued_at"]:
        job.pop(key, None)

    update_base_canonical_reference(
        run_dir=run_dir,
        output=output,
        manifest=manifest,
        job=job,
        metadata=metadata,
    )

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    result = {
        "ok": True,
        "job_id": job_id,
        "output": str(output),
        "source_provenance": source_provenance,
        "metadata": metadata,
    }
    if base_style_analysis is not None:
        result["base_style_analysis"] = base_style_analysis
        result["base_style_strict_blocking_warning_codes"] = [
            str(warning.get("code"))
            for warning in blocking_base_style_warnings(
                base_style_analysis,
                source_provenance=source_provenance,
            )
        ]
    if codex_app_imagegen is not None:
        result["codex_app_imagegen"] = codex_app_imagegen
    if chroma_cleanup is not None:
        result["chroma_cleanup"] = chroma_cleanup
    if row_source_style_analysis is not None:
        result["row_source_style_analysis"] = row_source_style_analysis
        result["row_source_style_strict_blocking_warning_codes"] = [
            str(warning.get("code"))
            for warning in blocking_row_source_style_warnings(row_source_style_analysis)
        ]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument(
        "--source-provenance",
        choices=[
            "auto",
            "built-in-imagegen",
            CODEX_APP_IMAGEGEN_PROVENANCE,
            BUILT_IN_CHROMA_CLEANUP_PROVENANCE,
            CODEX_APP_CHROMA_CLEANUP_PROVENANCE,
            "user-provided-integrated-row-art",
            "artist-provided-integrated-row-art",
        ],
        default="auto",
        help=(
            "Use codex-app-imagegen for PNGs captured from the Codex app built-in $imagegen "
            "session result, codex-app-imagegen-chroma-cleanup for a local alpha PNG produced "
            "from a captured Codex app imagegen source, auto/built-in-imagegen for direct "
            "$CODEX_HOME/generated_images outputs, "
            "built-in-imagegen-chroma-cleanup for a local alpha PNG produced from a raw "
            "$CODEX_HOME/generated_images/.../ig_*.png via the $imagegen chroma-key helper, "
            "or explicitly mark finished user/artist integrated row art."
        ),
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--strict-base-style",
        action="store_true",
        help="Fail base recording when chroma-key or native pixel-art style analysis reports warnings.",
    )
    parser.add_argument(
        "--strict-row-style",
        action="store_true",
        help="Fail row recording when source chroma-key cleanup analysis reports blocking warnings.",
    )
    parser.add_argument(
        "--chroma-cleanup-source",
        type=Path,
        help=(
            "Original raw built-in $imagegen source or captured Codex app imagegen source used "
            "for a chroma-cleanup recording."
        ),
    )
    parser.add_argument(
        "--codex-app-capture-metadata",
        type=Path,
        help=(
            "Metadata sidecar from capture_codex_app_imagegen_result.py; defaults to "
            "<source>.codex-imagegen.json for codex-app-imagegen provenance."
        ),
    )
    parser.add_argument("--allow-synthetic-test-source", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    result = record_result(
        run_dir=Path(args.run_dir).expanduser().resolve(),
        job_id=args.job_id,
        source=Path(args.source).expanduser().resolve(),
        source_provenance=args.source_provenance,
        force=args.force,
        allow_synthetic_test_source=args.allow_synthetic_test_source,
        strict_base_style=args.strict_base_style,
        strict_row_style=args.strict_row_style,
        chroma_cleanup_source=args.chroma_cleanup_source,
        codex_app_capture_metadata=args.codex_app_capture_metadata,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
