"""Shared contracts for the web companion mascot production pipeline v3."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

PIPELINE_VERSION = 3
IDENTITY_PATH = Path("references/character-bible.json")
IDENTITY_APPROVAL_PATH = Path("qa/identity-approval.json")
BASE_REVIEW_PATH = Path("qa/canonical-base-review.json")
REVIEW_EVIDENCE_PATH = Path("qa/review-evidence.json")
PROFILE_PATH = Path("references/qa-profiles-v3.json")

PLACEHOLDERS = (
    "replace with",
    "planned during row generation",
    "to be decided",
    "placeholder",
    "unknown",
    "todo",
    "tbd",
    "infer",
)

BASE_REVIEW_CHECKS = (
    "native16BitPixelArt",
    "noSmooth3DRendering",
    "silhouetteReadableAt64px",
    "speciesOrFormReadable",
    "identityMatchesContract",
    "anatomyMatchesContract",
    "faceGrammarMatchesContract",
    "paletteRolesPreserved",
    "animationReadySimplification",
    "noChromaContamination",
)

FRAME_REVIEW_FIELDS = (
    "anatomy",
    "identity",
    "stateRead",
    "eyeGrammar",
    "cueBehavior",
    "pixelArt",
)

ALLOWED_ALLOWANCES: dict[str, set[str]] = {
    "idle": {"subtle-breathing"},
    "hover": {"pointer-lean"},
    "dragging": {"carried-pose", "tail-follow-through"},
    "greeting": {"small-wave", "small-bounce"},
    "listening": {"near-head-overlap-cue"},
    "thinking": {"thinking-lean", "near-head-overlap-cue"},
    "working": {"work-lean", "prop-overlap"},
    "answering": {"speaking-bob", "mouth-origin-overlap-cue"},
    "success": {"celebratory-bounce", "brief-squash-stretch"},
    "error": {"small-recoil", "small-slump"},
    "confused": {"questioning-tilt"},
    "sleeping": {"curled-pose-compression", "tail-wrap"},
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def relative_path(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")


def run_states(manifest: dict[str, Any]) -> list[str]:
    states = manifest.get("states")
    if not isinstance(states, dict):
        return []
    return [name for name, state in states.items() if isinstance(name, str) and isinstance(state, dict)]


def is_placeholder(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return True
    lowered = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
    return any(term in lowered for term in PLACEHOLDERS)


def _need_string(errors: list[str], value: Any, label: str) -> None:
    if is_placeholder(value):
        errors.append(f"{label} must be concrete")


def _need_strings(errors: list[str], value: Any, label: str, minimum: int) -> None:
    if not isinstance(value, list) or len(value) < minimum:
        errors.append(f"{label} must contain at least {minimum} entries")
        return
    for index, item in enumerate(value):
        if is_placeholder(item):
            errors.append(f"{label}[{index}] must be concrete")


def identity_errors(identity: dict[str, Any], states: Iterable[str]) -> list[str]:
    errors: list[str] = []
    if identity.get("schemaVersion") != PIPELINE_VERSION:
        errors.append(f"schemaVersion must be {PIPELINE_VERSION}")
    if identity.get("status") != "approved":
        errors.append("status must be approved")
    if identity.get("pixelArtProfile") != "16-bit-console":
        errors.append("pixelArtProfile must be 16-bit-console")

    _need_string(errors, identity.get("sourceVibe"), "sourceVibe")
    _need_string(errors, identity.get("speciesOrForm"), "speciesOrForm")
    _need_string(errors, identity.get("bodyCore"), "bodyCore")
    _need_strings(errors, identity.get("speciesAnchors"), "speciesAnchors", 3)
    _need_strings(errors, identity.get("silhouetteAnchors"), "silhouetteAnchors", 3)
    _need_strings(errors, identity.get("proportionRules"), "proportionRules", 2)
    _need_strings(errors, identity.get("faceGrammar"), "faceGrammar", 2)
    _need_strings(errors, identity.get("forbiddenMutations"), "forbiddenMutations", 3)
    _need_strings(errors, identity.get("personalityTraits"), "personalityTraits", 3)
    _need_strings(errors, identity.get("motionVocabulary"), "motionVocabulary", 3)

    palette = identity.get("paletteRoles")
    if not isinstance(palette, list) or len(palette) < 3:
        errors.append("paletteRoles must contain at least 3 role/color entries")
    else:
        for index, entry in enumerate(palette):
            if not isinstance(entry, dict):
                errors.append(f"paletteRoles[{index}] must be an object")
                continue
            _need_string(errors, entry.get("role"), f"paletteRoles[{index}].role")
            _need_string(errors, entry.get("color"), f"paletteRoles[{index}].color")

    appendages = identity.get("appendages")
    if not isinstance(appendages, list):
        errors.append("appendages must be an array")
    else:
        seen: set[str] = set()
        for index, item in enumerate(appendages):
            if not isinstance(item, dict):
                errors.append(f"appendages[{index}] must be an object")
                continue
            for key in ("id", "kind", "placement"):
                _need_string(errors, item.get(key), f"appendages[{index}].{key}")
            appendage_id = item.get("id")
            if isinstance(appendage_id, str):
                if appendage_id in seen:
                    errors.append(f"appendages[{index}].id is duplicated")
                seen.add(appendage_id)
            if not isinstance(item.get("count"), int) or int(item["count"]) < 1:
                errors.append(f"appendages[{index}].count must be >= 1")
            if not isinstance(item.get("affordances"), list) or not item["affordances"]:
                errors.append(f"appendages[{index}].affordances must be non-empty")

    rules = identity.get("stateCueRules")
    if not isinstance(rules, dict):
        errors.append("stateCueRules must be an object")
    else:
        for state in states:
            rule = rules.get(state)
            if not isinstance(rule, dict):
                errors.append(f"stateCueRules.{state} must be an object")
                continue
            _need_string(errors, rule.get("acting"), f"stateCueRules.{state}.acting")
            if not isinstance(rule.get("attachment", "none"), str):
                errors.append(f"stateCueRules.{state}.attachment must be a string")
            if rule.get("componentPolicy", "none") not in {
                "none",
                "separate",
                "overlap-ok",
                "integrated-ok",
                "occlusion-ok",
            }:
                errors.append(f"stateCueRules.{state}.componentPolicy is invalid")

    quality = identity.get("qualityProfile")
    if not isinstance(quality, dict):
        errors.append("qualityProfile must be an object")
    else:
        if quality.get("profile") != "production-v3":
            errors.append("qualityProfile.profile must be production-v3")
        allowances = quality.get("stateAllowances")
        if not isinstance(allowances, dict):
            errors.append("qualityProfile.stateAllowances must be an object")
        else:
            for state, values in allowances.items():
                if not isinstance(values, list):
                    errors.append(f"qualityProfile.stateAllowances.{state} must be an array")
                    continue
                allowed = ALLOWED_ALLOWANCES.get(state, set())
                for value in values:
                    if value not in allowed:
                        errors.append(f"unsupported allowance {state}:{value}")
    return errors


def approved_identity(run_dir: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    path = run_dir / IDENTITY_PATH
    if not path.exists():
        return None, [f"missing {IDENTITY_PATH.as_posix()}"]
    identity = read_json(path)
    errors = identity_errors(identity, run_states(manifest))
    style = manifest.get("style") if isinstance(manifest.get("style"), dict) else {}
    binding = style.get("identityContract") if isinstance(style.get("identityContract"), dict) else {}
    if binding.get("status") != "approved":
        errors.append("manifest identity contract is not approved")
    if binding.get("sha256") != sha256_file(path):
        errors.append("manifest identity contract hash is stale")
    return identity, errors


def canonical_base_path(run_dir: Path, manifest: dict[str, Any]) -> Path:
    for key in ("canonicalIdentityReference", "canonical_identity_reference"):
        value = manifest.get(key)
        if isinstance(value, dict) and isinstance(value.get("path"), str):
            path = Path(value["path"])
            return path if path.is_absolute() else run_dir / path
    return run_dir / "references" / "canonical-base.png"


def base_review_errors(run_dir: Path, manifest: dict[str, Any]) -> list[str]:
    path = run_dir / BASE_REVIEW_PATH
    if not path.exists():
        return [f"missing {BASE_REVIEW_PATH.as_posix()}"]
    review = read_json(path)
    errors: list[str] = []
    if review.get("schemaVersion") != PIPELINE_VERSION:
        errors.append("canonical base review schemaVersion must be 3")
    if review.get("status") != "pass" or review.get("productionUse") is not True:
        errors.append("canonical base review must be a production pass")
    checks = review.get("checks")
    if not isinstance(checks, dict):
        errors.append("canonical base review checks are missing")
    else:
        for check in BASE_REVIEW_CHECKS:
            if checks.get(check) is not True:
                errors.append(f"canonical base review check {check} must be true")
    candidates = review.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("canonical base review must compare at least two candidates")
    observations = review.get("observations")
    if not isinstance(observations, dict):
        errors.append("canonical base review observations are missing")
    else:
        for key in ("silhouette", "speciesOrForm", "anatomy", "faceGrammar", "palette", "pixelArt", "smallSize"):
            _need_string(errors, observations.get(key), f"observations.{key}")

    base = canonical_base_path(run_dir, manifest)
    if not base.exists():
        errors.append("canonical base is missing")
    elif review.get("canonicalBaseSha256") != sha256_file(base):
        errors.append("canonical base review is stale")
    identity = run_dir / IDENTITY_PATH
    if identity.exists() and review.get("identityContractSha256") != sha256_file(identity):
        errors.append("canonical base review identity hash is stale")
    return errors


def locked_cue_snapshot(identity: dict[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    rules = identity.get("stateCueRules")
    if not isinstance(rules, dict):
        return result
    for state, rule in rules.items():
        if isinstance(state, str) and isinstance(rule, dict):
            result[state] = {
                "attachment": str(rule.get("attachment", "none")),
                "componentPolicy": str(rule.get("componentPolicy", "none")),
            }
    return result


def manifest_cue_snapshot(manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    states = manifest.get("states")
    if not isinstance(states, dict):
        return result
    for state, value in states.items():
        if not isinstance(state, str) or not isinstance(value, dict):
            continue
        enhancer = value.get("enhancer") if isinstance(value.get("enhancer"), dict) else {}
        result[state] = {
            "attachment": str(enhancer.get("attachment", "none")),
            "componentPolicy": str(enhancer.get("componentPolicy", "none")),
        }
    return result


def gate_blockers(run_dir: Path, job: dict[str, Any], jobs_data: dict[str, Any]) -> list[str]:
    manifest = read_json(run_dir / "manifest.json")
    if int(manifest.get("qualityPipelineVersion") or 0) < PIPELINE_VERSION:
        return []
    _identity, errors = approved_identity(run_dir, manifest)
    blockers = [f"identity: {error}" for error in errors]
    if job.get("kind") != "row-strip":
        return blockers

    base_complete = any(
        isinstance(candidate, dict) and candidate.get("id") == "base" and candidate.get("status") == "complete"
        for candidate in jobs_data.get("jobs", [])
    )
    if not base_complete:
        blockers.append("base job is not complete")
        return blockers
    blockers.extend(f"base review: {error}" for error in base_review_errors(run_dir, manifest))
    if blockers:
        return blockers

    bindings = job.get("quality_gate_bindings")
    if not isinstance(bindings, dict):
        return ["row job has no quality gate bindings"]
    if bindings.get("identityContractSha256") != sha256_file(run_dir / IDENTITY_PATH):
        blockers.append("row identity binding is stale")
    if bindings.get("canonicalBaseReviewSha256") != sha256_file(run_dir / BASE_REVIEW_PATH):
        blockers.append("row base-review binding is stale")
    return blockers


def load_profile(run_dir: Path, manifest: dict[str, Any], name: str) -> tuple[dict[str, Any], str]:
    style = manifest.get("style") if isinstance(manifest.get("style"), dict) else {}
    binding = style.get("qualityProfileV3") if isinstance(style.get("qualityProfileV3"), dict) else {}
    raw_path = binding.get("path", PROFILE_PATH.as_posix())
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = run_dir / path
    data = read_json(path)
    profiles = data.get("profiles")
    if not isinstance(profiles, dict) or not isinstance(profiles.get(name), dict):
        raise ValueError(f"missing locked quality profile {name}")
    profile = profiles[name]
    if profile.get("locked") is not True:
        raise ValueError(f"quality profile {name} is not locked")
    actual_hash = sha256_file(path)
    if binding.get("sha256") != actual_hash:
        raise ValueError("quality profile hash is stale")
    return profile, actual_hash
