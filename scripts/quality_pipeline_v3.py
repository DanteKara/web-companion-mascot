#!/usr/bin/env python3
"""Shared helpers for production quality pipeline v3."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
V3_PROFILE_PATH = REPO_ROOT / "references" / "qa-profiles-v3.json"
IDENTITY_PATH = "references/character-bible.json"
BASE_REVIEW_PATH = "qa/canonical-base-review.json"
CANONICAL_BASE_PATH = "references/canonical-base.png"


def read_json(path: Path | str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} must contain a JSON object")
    return data


def write_json(path: Path | str, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_states(manifest: dict[str, Any]) -> list[str]:
    states = manifest.get("states", {})
    if not isinstance(states, dict):
        return []
    return [
        name
        for name, _state in sorted(
            states.items(),
            key=lambda item: int(item[1].get("row", 0)) if isinstance(item[1], dict) else 0,
        )
        if isinstance(name, str)
    ]


def _parse_hex(value: str) -> tuple[int, int, int]:
    raw = value.strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) != 6:
        raise ValueError(f"invalid color: {value}")
    return int(raw[:2], 16), int(raw[2:4], 16), int(raw[4:], 16)


def _rgb_from_chroma(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, dict):
        return None
    rgb = value.get("rgb")
    if isinstance(rgb, list) and len(rgb) == 3:
        return tuple(int(channel) for channel in rgb)
    hex_value = value.get("hex")
    if isinstance(hex_value, str):
        return _parse_hex(hex_value)
    return None


def chroma_key_from_run(run_dir: Path | str) -> tuple[int, int, int]:
    run_dir = Path(run_dir)
    for filename in ("manifest.json", "companion_request.json"):
        path = run_dir / filename
        if not path.exists():
            continue
        data = read_json(path)
        style = data.get("style")
        if isinstance(style, dict):
            rgb = _rgb_from_chroma(style.get("chromaKey"))
            if rgb is not None:
                return rgb
        rgb = _rgb_from_chroma(data.get("chromaKey"))
        if rgb is not None:
            return rgb
    return (255, 0, 255)


def _count_list(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def identity_contract_errors(identity: dict[str, Any], states: list[str]) -> list[str]:
    errors: list[str] = []
    exact = {
        "schemaVersion": 3,
        "status": "approved",
        "pixelArtProfile": "16-bit-console",
    }
    for key, expected in exact.items():
        if identity.get(key) != expected:
            errors.append(f"{key} must be {expected!r}")
    for key in ("sourceVibe", "speciesOrForm", "bodyCore"):
        if not isinstance(identity.get(key), str) or not identity[key].strip():
            errors.append(f"{key} must be a non-empty string")
    minimums = {
        "speciesAnchors": 3,
        "silhouetteAnchors": 3,
        "proportionRules": 2,
        "faceGrammar": 2,
        "forbiddenMutations": 3,
        "personalityTraits": 3,
        "motionVocabulary": 3,
    }
    for key, minimum in minimums.items():
        if _count_list(identity.get(key)) < minimum:
            errors.append(f"{key} must contain at least {minimum} items")
    palette_roles = identity.get("paletteRoles")
    if _count_list(palette_roles) < 3:
        errors.append("paletteRoles must contain at least 3 role/color objects")
    else:
        for index, item in enumerate(palette_roles):
            if not isinstance(item, dict) or not item.get("role") or not item.get("color"):
                errors.append(f"paletteRoles[{index}] must contain role and color")
    appendages = identity.get("appendages")
    if not isinstance(appendages, list):
        errors.append("appendages must be a list")
    else:
        for index, item in enumerate(appendages):
            if not isinstance(item, dict):
                errors.append(f"appendages[{index}] must be an object")
                continue
            for key in ("id", "kind", "count", "placement", "affordances"):
                if key not in item:
                    errors.append(f"appendages[{index}].{key} is required")
    state_rules = identity.get("stateCueRules")
    if not isinstance(state_rules, dict):
        errors.append("stateCueRules must be an object")
    else:
        for state in states:
            if state not in state_rules or not isinstance(state_rules[state], dict):
                errors.append(f"stateCueRules.{state} is required")
    quality = identity.get("qualityProfile")
    if not isinstance(quality, dict):
        errors.append("qualityProfile must be an object")
    else:
        if quality.get("profile") != "production-v3":
            errors.append("qualityProfile.profile must be production-v3")
        if not isinstance(quality.get("stateAllowances"), dict):
            errors.append("qualityProfile.stateAllowances must be an object")
    return errors


def load_approved_identity(run_dir: Path | str, manifest: dict[str, Any]) -> tuple[dict[str, Any], Path, str]:
    run_dir = Path(run_dir)
    contract = (manifest.get("style") or {}).get("identityContract") if isinstance(manifest.get("style"), dict) else None
    path = run_dir / IDENTITY_PATH
    expected_sha = None
    if isinstance(contract, dict):
        expected_sha = contract.get("sha256")
        if isinstance(contract.get("path"), str):
            path = run_dir / contract["path"]
    if not path.exists():
        raise SystemExit("approved identity contract is missing")
    identity = read_json(path)
    actual_sha = sha256_file(path)
    if expected_sha and expected_sha != actual_sha:
        raise SystemExit("approved identity contract hash does not match manifest")
    errors = identity_contract_errors(identity, run_states(manifest))
    if errors:
        raise SystemExit("approved identity contract is invalid: " + "; ".join(errors))
    return identity, path, actual_sha


def canonical_base_path(run_dir: Path | str, manifest: dict[str, Any]) -> Path:
    run_dir = Path(run_dir)
    ref = manifest.get("canonicalIdentityReference") or manifest.get("canonical_identity_reference")
    if isinstance(ref, dict) and isinstance(ref.get("path"), str):
        return run_dir / ref["path"]
    return run_dir / CANONICAL_BASE_PATH


def base_review_errors(run_dir: Path | str, manifest: dict[str, Any]) -> list[str]:
    run_dir = Path(run_dir)
    errors: list[str] = []
    review_path = run_dir / BASE_REVIEW_PATH
    if not review_path.exists():
        return ["canonical base review is missing"]
    review = read_json(review_path)
    if review.get("status") != "pass":
        errors.append("canonical base review status must be pass")
    if review.get("productionUse") is not True:
        errors.append("canonical base review productionUse must be true")
    try:
        _identity, _identity_path, identity_sha = load_approved_identity(run_dir, manifest)
    except SystemExit as exc:
        errors.append(str(exc))
        identity_sha = None
    if identity_sha and review.get("identityContractSha256") != identity_sha:
        errors.append("canonical base review identity hash is stale")
    base_path = canonical_base_path(run_dir, manifest)
    if not base_path.exists():
        errors.append("canonical base image is missing")
    elif review.get("canonicalBaseSha256") != sha256_file(base_path):
        errors.append("canonical base review image hash is stale")
    return errors


def _close_rgb(left: tuple[int, int, int], right: tuple[int, int, int], tolerance: int = 3) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(left, right))


def _is_background(pixel: tuple[int, int, int, int], chroma_key: tuple[int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return alpha == 0 or _close_rgb((red, green, blue), chroma_key, 6)


def _quantized(rgb: tuple[int, int, int], step: int = 16) -> tuple[int, int, int]:
    return tuple(channel // step for channel in rgb)


def analyze_source_style(path: Path | str, chroma_key: tuple[int, int, int]) -> dict[str, Any]:
    path = Path(path)
    blocking: list[str] = []
    advisory: list[str] = []
    with Image.open(path) as raw:
        image = raw.convert("RGBA")
    width, height = image.size
    pixels = image.load()

    border = []
    for x in range(width):
        border.extend([pixels[x, 0], pixels[x, height - 1]])
    for y in range(height):
        border.extend([pixels[0, y], pixels[width - 1, y]])
    border_count = max(1, len(border))
    background_border_ratio = sum(1 for pixel in border if _is_background(pixel, chroma_key)) / border_count
    exact_border_ratio = sum(1 for pixel in border if pixel[3] == 0 or pixel[:3] == chroma_key) / border_count
    light_gray_ratio = sum(
        1
        for red, green, blue, alpha in border
        if alpha and 220 <= min(red, green, blue) and max(red, green, blue) - min(red, green, blue) <= 8
    ) / border_count
    if light_gray_ratio > 0.7 and background_border_ratio < 0.3:
        blocking.append("fake_checkerboard_transparency_background")
    if background_border_ratio < 0.985 or exact_border_ratio < 0.975:
        blocking.append("non_uniform_chroma_key_background")

    foreground: list[tuple[int, int, int, int]] = []
    partial_alpha = 0
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if _is_background(pixel, chroma_key):
                continue
            foreground.append(pixel)
            if 0 < pixel[3] < 255:
                partial_alpha += 1
    if not foreground:
        blocking.append("no_foreground_sprite_detected")

    raw_rgbs = [pixel[:3] for pixel in foreground]
    raw_unique = set(raw_rgbs)
    quantized_unique = {_quantized(rgb) for rgb in raw_rgbs}
    if len(raw_unique) > 64:
        advisory.append("high_raw_unique_rgb_count")
    if len(quantized_unique) > 48:
        advisory.append("high_quantized_color_count")
    if foreground and partial_alpha / len(foreground) > 0.08:
        blocking.append("excessive_partial_alpha_antialiasing")

    same_pairs = 0
    small_delta_pairs = 0
    hard_delta_pairs = 0
    pair_count = 0
    fg_lookup = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if not _is_background(pixels[x, y], chroma_key)
    }
    for x, y in fg_lookup:
        for nx, ny in ((x + 1, y), (x, y + 1)):
            if (nx, ny) not in fg_lookup:
                continue
            left = pixels[x, y][:3]
            right = pixels[nx, ny][:3]
            delta = math.dist(left, right)
            pair_count += 1
            if delta == 0:
                same_pairs += 1
            elif delta <= 18:
                small_delta_pairs += 1
            elif delta >= 45:
                hard_delta_pairs += 1
    pair_count = max(1, pair_count)
    flat_ratio = same_pairs / pair_count
    small_delta_ratio = small_delta_pairs / pair_count
    hard_delta_ratio = hard_delta_pairs / pair_count
    ramp_ratio = flat_ratio + small_delta_ratio
    smooth_risk = (
        len(raw_unique) > 64
        and len(quantized_unique) <= max(64, int(len(raw_unique) * 0.35))
        and ramp_ratio >= 0.75
        and hard_delta_ratio < 0.25
    )
    if smooth_risk:
        blocking.append("smooth_gradient_or_painterly_render_risk")

    return {
        "ok": not blocking,
        "blockingWarningCodes": sorted(set(blocking)),
        "advisoryWarningCodes": sorted(set(advisory)),
        "background": {
            "borderBackgroundRatio": round(background_border_ratio, 4),
            "borderExactRatio": round(exact_border_ratio, 4),
            "lightGrayBorderRatio": round(light_gray_ratio, 4),
        },
        "foreground": {
            "pixels": len(foreground),
            "rawUniqueRgbCount": len(raw_unique),
            "quantizedColorCount": len(quantized_unique),
            "partialAlphaRatio": round(partial_alpha / max(1, len(foreground)), 4),
            "flatNeighborRatio": round(flat_ratio, 4),
            "smallDeltaRampRatio": round(small_delta_ratio, 4),
            "sameOrSmallDeltaRampRatio": round(ramp_ratio, 4),
            "hardTransitionRatio": round(hard_delta_ratio, 4),
        },
    }


def _protected_foreground_mask(image: Image.Image, chroma_key: tuple[int, int, int]) -> set[tuple[int, int]]:
    pixels = image.load()
    width, height = image.size
    mask = {
        (x, y)
        for y in range(height)
        for x in range(width)
        if not _is_background(pixels[x, y], chroma_key)
    }
    protected = set(mask)
    for x, y in list(mask):
        for nx in range(max(0, x - 1), min(width, x + 2)):
            for ny in range(max(0, y - 1), min(height, y + 2)):
                if (nx, ny) not in mask:
                    protected.discard((x, y))
                    break
            if (x, y) not in protected:
                break
    return protected or mask


def verify_background_only_cleanup(
    original_path: Path | str,
    cleaned_path: Path | str,
    chroma_key: tuple[int, int, int],
) -> dict[str, Any]:
    original_path = Path(original_path)
    cleaned_path = Path(cleaned_path)
    with Image.open(original_path) as raw_original:
        original = raw_original.convert("RGBA")
    with Image.open(cleaned_path) as raw_cleaned:
        cleaned = raw_cleaned.convert("RGBA")

    blocking: list[str] = []
    if original.size != cleaned.size:
        return {
            "ok": False,
            "blockingWarningCodes": ["cleanup_dimensions_changed"],
            "originalSize": list(original.size),
            "cleanedSize": list(cleaned.size),
        }

    original_pixels = original.load()
    cleaned_pixels = cleaned.load()
    protected = _protected_foreground_mask(original, chroma_key)
    changed_palette = 0
    removed = 0
    alpha_changed = 0
    for x, y in protected:
        original_rgba = original_pixels[x, y]
        cleaned_rgba = cleaned_pixels[x, y]
        if cleaned_rgba[3] == 0:
            removed += 1
        if original_rgba[:3] != cleaned_rgba[:3]:
            changed_palette += 1
        if abs(original_rgba[3] - cleaned_rgba[3]) > 2:
            alpha_changed += 1
    protected_count = max(1, len(protected))
    if changed_palette / protected_count > 0.002:
        blocking.append("cleanup_changed_foreground_palette")
    if removed / protected_count > 0.002:
        blocking.append("cleanup_removed_foreground_pixels")
    if alpha_changed / protected_count > 0.002:
        blocking.append("cleanup_changed_foreground_alpha")

    original_mask = {
        (x, y)
        for y in range(original.height)
        for x in range(original.width)
        if not _is_background(original_pixels[x, y], chroma_key)
    }
    cleaned_mask = {
        (x, y)
        for y in range(cleaned.height)
        for x in range(cleaned.width)
        if cleaned_pixels[x, y][3] != 0 and not _close_rgb(cleaned_pixels[x, y][:3], chroma_key, 6)
    }
    symmetric = original_mask.symmetric_difference(cleaned_mask)
    if len(symmetric) / max(1, len(original_mask)) > 0.03:
        blocking.append("cleanup_changed_foreground_geometry")

    return {
        "ok": not blocking,
        "blockingWarningCodes": sorted(set(blocking)),
        "protectedForegroundPixels": len(protected),
        "changedProtectedForegroundRgbPixels": changed_palette,
        "removedProtectedForegroundPixels": removed,
        "changedProtectedForegroundAlphaPixels": alpha_changed,
        "geometryDifferencePixels": len(symmetric),
    }


def load_locked_profile(run_dir: Path | str, manifest: dict[str, Any], profile_name: str) -> tuple[dict[str, Any], Path, str]:
    run_dir = Path(run_dir)
    profile_path = run_dir / "references" / "qa-profiles-v3.json"
    if not profile_path.exists():
        profile_path = V3_PROFILE_PATH
    profiles_data = read_json(profile_path)
    profile = (profiles_data.get("profiles") or {}).get(profile_name)
    if not isinstance(profile, dict):
        raise SystemExit(f"locked QA profile not found: {profile_name}")
    if profile.get("locked") is not True:
        raise SystemExit(f"QA profile {profile_name} must be locked")
    profile_sha = sha256_file(profile_path)
    expected = ((manifest.get("style") or {}).get("qualityProfileV3") or {}).get("sha256")
    if expected and profile_path.name == "qa-profiles-v3.json" and expected != profile_sha:
        raise SystemExit("qualityProfileV3 sha does not match locked profile")
    return profile, profile_path, profile_sha


def jobs_data(run_dir: Path | str) -> dict[str, Any]:
    return read_json(Path(run_dir) / "imagegen-jobs.json")


def job_list(jobs: dict[str, Any]) -> list[dict[str, Any]]:
    raw = jobs.get("jobs")
    if not isinstance(raw, list):
        raise SystemExit("imagegen-jobs.json jobs must be a list")
    return [job for job in raw if isinstance(job, dict)]


def find_job(jobs: dict[str, Any], job_id: str) -> dict[str, Any]:
    for job in job_list(jobs):
        if job.get("id") == job_id:
            return job
    raise SystemExit(f"unknown job id: {job_id}")


def write_jobs(run_dir: Path | str, jobs: dict[str, Any]) -> None:
    write_json(Path(run_dir) / "imagegen-jobs.json", jobs)
