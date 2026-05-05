#!/usr/bin/env python3
"""Validate a web companion mascot manifest and optional atlas image."""

from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Any


REQUIRED_ATLAS_FIELDS = {
    "path",
    "width",
    "height",
    "columns",
    "rows",
    "cellWidth",
    "cellHeight",
}

CHATBOT_RECOMMENDED_FRAMES = {
    "idle": 10,
    "greeting": 10,
    "listening": 10,
    "thinking": 12,
    "working": 12,
    "answering": 12,
    "success": 10,
    "error": 10,
    "confused": 10,
    "sleeping": 10,
}

CHATBOT_CORE_STATES = {"idle", "thinking", "working", "answering", "success", "error"}
MIN_USED_CELL_COVERAGE = 0.015
STATE_CLARITY_PROFILES = {"pose-only", "semantic-enhancers"}
RENDERING_STYLES = {"codex-pixel-art"}
ANATOMY_CLASSES = {"hands", "paws", "fins-no-hands", "no-limbs", "ambiguous-limbs"}
VISUAL_LANGUAGE_REQUIRED_FIELDS = {"sourceVibe", "motifs", "forbiddenGenericCues"}
NO_GRIP_ANATOMY_CLASSES = {"no-limbs"}
ANATOMY_CONTRACT_RECOMMENDED_CLASSES = {"fins-no-hands", "ambiguous-limbs"}
SEMANTIC_ENHANCER_STATES = {"listening", "thinking", "working", "answering"}
ALLOWED_ENHANCER_ATTACHMENTS = {
    "held",
    "worn",
    "attached",
    "near-head",
    "near-face",
    "near-hand",
    "aura",
    "gesture",
    "body-pose",
}
TEXT_DEPENDENT_KIND_TERMS = {"text", "label", "caption", "word", "question-mark", "punctuation"}
TEXT_NEGATION_TERMS = {"no", "non", "not", "without"}
TEXT_NEGATION_BREAK_TERMS = {"although", "but", "except", "however", "though", "while", "yet"}
RISKY_ANATOMY_ATTACHMENTS = {"held", "near-hand"}
NO_GRIP_ATTACHMENTS = {"held", "near-hand"}
ACTION_TERMS_BY_AFFORDANCE = {
    "face-touch": {
        "chin",
        "chin-touch",
        "face-touch",
        "forehead",
        "hand-to-chin",
        "hand-to-face",
        "touch-face",
        "touching-face",
    },
    "grip": {
        "brace",
        "braced",
        "bracing",
        "grip",
        "gripped",
        "gripping",
        "held",
        "hold",
        "holding",
    },
    "typing": {"keyboard", "type", "typing"},
    "writing": {"pen", "pencil", "quill", "write", "writing"},
    "point": {"point", "pointing"},
    "present": {"present", "presenting"},
    "wave": {"wave", "waving"},
}
AFFORDANCE_GROUP_ALIASES = {
    "face-touch": {"face-touch", "face-touch-safe", "hand-to-face", "hand-to-chin", "chin-touch"},
    "grip": {"grip", "grip-safe", "hold", "hold-safe", "brace", "brace-safe"},
    "typing": {"typing", "typing-safe", "fine-finger", "fine-fingers", "fingered"},
    "writing": {"writing", "writing-safe", "grip", "grip-safe", "fine-finger", "fine-fingers", "fingered"},
    "point": {"point", "point-safe", "present", "gesture"},
    "present": {"present", "present-safe", "point", "gesture"},
    "wave": {"wave", "small-wave", "side-wave", "gesture"},
}
VAGUE_ALLOWED_INTERACTOR_PHRASES = {
    "existing appendages only",
    "existing limbs only",
    "existing visible appendages only",
    "original appendages only",
    "visible appendages only",
}
RISKY_ANATOMY_PROP_TERMS = {
    "book",
    "document",
    "keyboard",
    "laptop",
    "paper",
    "parchment",
    "pen",
    "pencil",
    "quill",
    "slate",
    "tablet",
    "tool",
    "writing",
}
NO_GRIP_PROP_TERMS = RISKY_ANATOMY_PROP_TERMS | {
    "brace",
    "braced",
    "grip",
    "hand",
    "hands",
    "finger",
    "fingers",
    "typing",
}
ALLOWED_PRODUCTION_GENERATION_METHODS = {
    "imagegen-integrated-row-art",
    "user-provided-integrated-row-art",
    "artist-provided-integrated-row-art",
}
DISALLOWED_GENERATION_METHOD_TERMS = {
    "compositor",
    "deterministic",
    "overlay",
    "vector",
    "procedural",
    "pillow",
    "script",
    "css",
    "svg",
    "canvas",
    "hand-authored",
}


def parse_hex_color(value: str) -> tuple[int, int, int]:
    raw = value.strip()
    if raw.startswith("#"):
        raw = raw[1:]
    if len(raw) != 6:
        raise ValueError(f"expected #RRGGBB color, got {value!r}")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((left - right) ** 2 for left, right in zip(a, b)) ** 0.5


def is_key_spill(rgb: tuple[int, int, int], key: tuple[int, int, int], threshold: int) -> bool:
    r, g, b = rgb
    if key == (255, 0, 255):
        return (
            r >= 45
            and b >= 45
            and g <= 135
            and abs(r - b) <= 115
            and (r - g) >= threshold
            and (b - g) >= threshold
        )
    return color_distance(rgb, key) <= max(90, threshold * 2.5)


def has_transparent_neighbor(alpha_pixels: Any, x: int, y: int, width: int, height: int) -> bool:
    for ny in range(max(0, y - 1), min(height, y + 2)):
        for nx in range(max(0, x - 1), min(width, x + 2)):
            if nx == x and ny == y:
                continue
            if not alpha_pixels[nx, ny]:
                return True
    return False


def count_outline_halo_pixels(image: Any, key: tuple[int, int, int], threshold: int) -> int:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    width, height = rgba.size
    pixels = rgba.load()
    alpha_pixels = alpha.load()
    count = 0

    for y in range(height):
        for x in range(width):
            if not alpha_pixels[x, y]:
                continue
            r, g, b, _a = pixels[x, y]
            if is_key_spill((r, g, b), key, threshold) and has_transparent_neighbor(alpha_pixels, x, y, width, height):
                count += 1

    return count


def load_assembly_report(manifest_path: Path) -> dict[str, Any] | None:
    report_path = manifest_path.parent / "qa" / "assembly-report.json"
    if not report_path.exists():
        return None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return report if isinstance(report, dict) else None


def load_quality_report(manifest_path: Path) -> dict[str, Any] | None:
    report_path = manifest_path.parent / "qa" / "quality-report.json"
    if not report_path.exists():
        return None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return report if isinstance(report, dict) else None


def load_art_direction_review(manifest_path: Path) -> dict[str, Any] | None:
    report_path = manifest_path.parent / "qa" / "art-direction-review.json"
    if not report_path.exists():
        return None
    try:
        report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None
    return report if isinstance(report, dict) else None


def validate_art_direction_review(
    manifest_path: Path,
    review: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    qa: dict[str, Any],
) -> None:
    status = review.get("status")
    method = review.get("generationMethod")
    source_reference = review.get("sourceReference")
    production_use = review.get("productionUse")
    blockers = review.get("blockers")

    qa["artDirectionReview"] = {
        "status": status,
        "generationMethod": method,
        "sourceReference": source_reference,
        "productionUse": production_use,
        "blockers": blockers if isinstance(blockers, list) else [],
    }

    if status != "pass":
        errors.append("qa/art-direction-review.json status must be 'pass' for production validation")

    if production_use is not True:
        errors.append("qa/art-direction-review.json productionUse must be true for production validation")

    if isinstance(blockers, list) and blockers:
        for blocker in blockers:
            errors.append(f"art direction blocker: {blocker}")
    elif blockers is not None and not isinstance(blockers, list):
        errors.append("qa/art-direction-review.json blockers must be an array")

    if not isinstance(method, str) or not method.strip():
        errors.append("qa/art-direction-review.json generationMethod must be a non-empty string")
    elif method not in ALLOWED_PRODUCTION_GENERATION_METHODS:
        errors.append(
            "qa/art-direction-review.json generationMethod must be one of: "
            + ", ".join(sorted(ALLOWED_PRODUCTION_GENERATION_METHODS))
        )
    elif any(term in method.lower() for term in DISALLOWED_GENERATION_METHOD_TERMS):
        errors.append(
            f"qa/art-direction-review.json generationMethod {method!r} is not acceptable for production final art"
        )

    if not isinstance(source_reference, str) or not source_reference.strip():
        errors.append("qa/art-direction-review.json sourceReference is required for production validation")
    else:
        source_reference_path = Path(source_reference).expanduser()
        if not source_reference_path.is_absolute():
            source_reference_path = manifest_path.parent / source_reference_path
        if not source_reference_path.exists():
            errors.append(f"qa/art-direction-review.json sourceReference does not exist: {source_reference}")

    checks = review.get("checks")
    required_checks = {
        "referenceQualityMaintained",
        "identityPreserved",
        "stylePreserved",
        "pixelArtStyle",
        "creativeStateReadability",
        "themeNativeStateCues",
        "nativeEnhancers",
        "integratedEnhancers",
        "anatomyPreserved",
        "noExtraAnatomy",
        "believableOcclusion",
        "noPrototypeFlattening",
    }
    if not isinstance(checks, dict):
        errors.append("qa/art-direction-review.json checks must be an object")
        return

    missing = sorted(required_checks - set(checks))
    for key in missing:
        errors.append(f"qa/art-direction-review.json checks.{key} is required")

    for key in sorted(required_checks & set(checks)):
        if checks.get(key) is not True:
            errors.append(f"qa/art-direction-review.json checks.{key} must be true")

    notes = review.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        warnings.append("qa/art-direction-review.json notes should describe why the mascot passes visually")


def inspect_atlas(
    path: Path,
    states: dict[str, Any],
    columns: int | None,
    cell_width: int | None,
    cell_height: int | None,
    key_color: tuple[int, int, int] | None = None,
    spill_threshold: int = 45,
    max_outline_halo_pixels: int = 0,
) -> tuple[dict[str, Any], list[str], list[str]] | None:
    try:
        from PIL import Image
    except Exception:
        return None

    errors: list[str] = []
    warnings: list[str] = []

    with Image.open(path) as image:
        rgba = image.convert("RGBA")
        info: dict[str, Any] = {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "cells": [],
        }

        if columns is None or cell_width is None or cell_height is None:
            return info, errors, warnings

        cell_area = cell_width * cell_height
        for state_name, state in states.items():
            if not isinstance(state, dict):
                continue
            row = state.get("row")
            frames = state.get("frames")
            if not isinstance(row, int) or not isinstance(frames, int):
                continue
            for column in range(columns):
                box = (
                    column * cell_width,
                    row * cell_height,
                    (column + 1) * cell_width,
                    (row + 1) * cell_height,
                )
                if box[2] > rgba.width or box[3] > rgba.height:
                    continue
                cell = rgba.crop(box)
                alpha = cell.getchannel("A")
                nontransparent = sum(1 for value in alpha.tobytes() if value)
                used = column < frames

                edge_pixels = 0
                if nontransparent:
                    top = [alpha.getpixel((x, 0)) for x in range(cell_width)]
                    bottom = [alpha.getpixel((x, cell_height - 1)) for x in range(cell_width)]
                    left = [alpha.getpixel((0, y)) for y in range(cell_height)]
                    right = [alpha.getpixel((cell_width - 1, y)) for y in range(cell_height)]
                    edge_pixels = sum(1 for value in top + bottom + left + right if value)
                outline_halo_pixels = (
                    count_outline_halo_pixels(cell, key_color, spill_threshold)
                    if key_color is not None and used
                    else 0
                )

                info["cells"].append(
                    {
                        "state": state_name,
                        "row": row,
                        "column": column,
                        "used": used,
                        "nontransparentPixels": nontransparent,
                        "edgePixels": edge_pixels,
                        "outlineHaloPixels": outline_halo_pixels,
                    }
                )

                if used and nontransparent == 0:
                    errors.append(f"state {state_name} frame {column} is empty")
                if used and nontransparent and nontransparent < cell_area * MIN_USED_CELL_COVERAGE:
                    warnings.append(f"state {state_name} frame {column} is very sparse")
                if used and edge_pixels:
                    errors.append(f"state {state_name} frame {column} touches the cell edge")
                if used and outline_halo_pixels > max_outline_halo_pixels:
                    errors.append(
                        f"state {state_name} frame {column} has {outline_halo_pixels} key-colored outline/halo pixels"
                    )
                if not used and nontransparent:
                    errors.append(f"state {state_name} unused cell {column} is not transparent")

        return info, errors, warnings


def require_int(errors: list[str], value: Any, name: str, minimum: int = 1) -> int | None:
    if not isinstance(value, int):
        errors.append(f"{name} must be an integer")
        return None
    if value < minimum:
        errors.append(f"{name} must be >= {minimum}")
        return None
    return value


def require_non_empty_string(errors: list[str], value: Any, name: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{name} must be a non-empty string")
        return None
    return value


def is_text_dependent_kind(kind: str) -> bool:
    normalized = kind.lower().replace("_", "-").replace(" ", "-")
    tokens = [token for token in normalized.split("-") if token]
    simple_terms = TEXT_DEPENDENT_KIND_TERMS - {"question-mark"}

    for index, token in enumerate(tokens):
        if token not in simple_terms:
            continue
        previous = tokens[index - 1] if index else ""
        if previous in TEXT_NEGATION_TERMS:
            continue
        return True

    question_indexes = [index for index, token in enumerate(tokens) if token == "question"]
    for index in question_indexes:
        if index + 1 >= len(tokens) or tokens[index + 1] != "mark":
            continue
        previous = tokens[index - 1] if index else ""
        if previous in TEXT_NEGATION_TERMS:
            continue
        return True

    return False


def enhancer_text(value: dict[str, Any]) -> str:
    return " ".join(
        str(value.get(key, "")).lower().replace("_", "-")
        for key in ["kind", "attachment", "description"]
    )


def split_term_clauses(value: str) -> list[list[str]]:
    normalized = value.lower().replace("_", "-").replace("/", "-")
    clauses = re.split(r"[.;:()[\]{}\"']+", normalized)
    return [re.findall(r"[a-z0-9]+", clause) for clause in clauses if clause.strip()]


def clause_has_term(tokens: list[str], term: str) -> int | None:
    term_tokens = re.findall(r"[a-z0-9]+", term.lower().replace("_", "-"))
    if not term_tokens:
        return None
    span = len(term_tokens)
    for index in range(0, len(tokens) - span + 1):
        if tokens[index : index + span] == term_tokens:
            return index
    return None


def has_prior_negation(tokens: list[str], term_index: int) -> bool:
    scoped_tokens = tokens[:term_index]
    for index in range(len(scoped_tokens) - 1, -1, -1):
        if scoped_tokens[index] in TEXT_NEGATION_BREAK_TERMS:
            scoped_tokens = scoped_tokens[index + 1 :]
            break
    return any(token in TEXT_NEGATION_TERMS for token in scoped_tokens)


def has_unnegated_term(value: str, terms: set[str]) -> bool:
    for tokens in split_term_clauses(value):
        for term in terms:
            term_index = clause_has_term(tokens, term)
            if term_index is not None and not has_prior_negation(tokens, term_index):
                return True
    return False


def normalize_label(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def canonical_affordance_group(value: str) -> str | None:
    normalized = value.lower().replace("_", "-").replace(" ", "-")
    for group, aliases in AFFORDANCE_GROUP_ALIASES.items():
        if normalized == group or normalized in aliases:
            return group
    return normalized if normalized in AFFORDANCE_GROUP_ALIASES else None


def infer_required_affordance_groups(value: dict[str, Any]) -> set[str]:
    text = enhancer_text(value)
    groups: set[str] = set()

    if value.get("attachment") == "held":
        groups.add("grip")

    for group, terms in ACTION_TERMS_BY_AFFORDANCE.items():
        if has_unnegated_term(text, terms):
            groups.add(group)

    explicit = value.get("requiredAffordances")
    if isinstance(explicit, list):
        for entry in explicit:
            if isinstance(entry, str):
                group = canonical_affordance_group(entry)
                if group:
                    groups.add(group)

    return groups


def enhancer_has_anatomy_risk(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    attachment = value.get("attachment")
    text = enhancer_text(value)
    return (
        bool(attachment in RISKY_ANATOMY_ATTACHMENTS)
        or has_unnegated_term(text, RISKY_ANATOMY_PROP_TERMS)
        or bool(infer_required_affordance_groups(value))
    )


def is_vague_allowed_interactor(value: str) -> bool:
    normalized = " ".join(value.lower().replace("-", " ").split())
    return normalized in VAGUE_ALLOWED_INTERACTOR_PHRASES


def validate_enhancer(
    errors: list[str],
    warnings: list[str],
    value: Any,
    name: str,
    anatomy_class: str | None = None,
    anatomy_contract: dict[str, Any] | None = None,
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return

    kind = require_non_empty_string(errors, value.get("kind"), f"{name}.kind")
    attachment = require_non_empty_string(errors, value.get("attachment"), f"{name}.attachment")
    require_non_empty_string(errors, value.get("description"), f"{name}.description")

    if kind:
        if is_text_dependent_kind(kind):
            warnings.append(f"{name}.kind appears text-dependent; prefer a visual non-text enhancer")

    if attachment:
        if attachment in {"floating", "detached"}:
            errors.append(f"{name}.attachment must be anchored to the mascot")
        elif attachment not in ALLOWED_ENHANCER_ATTACHMENTS:
            errors.append(
                f"{name}.attachment must be one of: {', '.join(sorted(ALLOWED_ENHANCER_ATTACHMENTS))}"
            )

    required_affordances = value.get("requiredAffordances")
    if required_affordances is not None:
        if not isinstance(required_affordances, list) or not required_affordances:
            errors.append(f"{name}.requiredAffordances must be a non-empty array when present")
        else:
            for index, entry in enumerate(required_affordances):
                if not isinstance(entry, str) or not entry.strip():
                    errors.append(f"{name}.requiredAffordances[{index}] must be a non-empty string")
                elif canonical_affordance_group(entry) is None:
                    warnings.append(
                        f"{name}.requiredAffordances[{index}] uses unknown affordance {entry!r}; "
                        "use common affordances such as face-touch, grip, typing, writing, point, present, or wave"
                    )
    elif infer_required_affordance_groups(value):
        warnings.append(
            f"{name}.requiredAffordances is recommended for appendage-dependent actions so the state card, "
            "manifest, and anatomy contract agree on what the named appendages may do"
        )

    text = enhancer_text(value)
    if anatomy_class in NO_GRIP_ANATOMY_CLASSES:
        if attachment in NO_GRIP_ATTACHMENTS:
            errors.append(
                f"{name}.attachment {attachment!r} is not allowed for style.anatomyClass {anatomy_class!r}; "
                "use attached, near-head, near-face, aura, gesture, worn, or body-pose semantics instead"
            )
        if has_unnegated_term(text, NO_GRIP_PROP_TERMS):
            errors.append(
                f"{name} describes a grip/typing/writing prop that is unsafe for style.anatomyClass {anatomy_class!r}; "
                "use a non-grip enhancer such as a body-surface glyph, processing aura, facial animation, or near-head effect"
            )

    anatomy_risk = enhancer_has_anatomy_risk(value)
    anatomy_guard = value.get("anatomyGuard")
    if anatomy_risk and anatomy_guard is None:
        warnings.append(
            f"{name}.anatomyGuard is recommended for held, near-hand, touched, writing, or work-prop enhancers so QA can reject extra limbs/new anatomy"
        )
    elif anatomy_guard is not None:
        validate_anatomy_guard(errors, warnings, anatomy_guard, f"{name}.anatomyGuard")

    validate_enhancer_affordances(
        errors,
        warnings,
        value,
        name,
        anatomy_contract,
    )


def validate_anatomy_guard(
    errors: list[str],
    warnings: list[str],
    value: Any,
    name: str,
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return

    limb_policy = value.get("limbPolicy")
    if not isinstance(limb_policy, str) or not limb_policy.strip():
        errors.append(f"{name}.limbPolicy must be a non-empty string")
    elif "new" not in limb_policy.lower() and "existing" not in limb_policy.lower():
        warnings.append(f"{name}.limbPolicy should explicitly forbid new anatomy or require existing limbs only")

    for key in ["allowedInteractors", "forbidden"]:
        entries = value.get(key)
        if not isinstance(entries, list) or not entries:
            errors.append(f"{name}.{key} must be a non-empty array")
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, str) or not entry.strip():
                errors.append(f"{name}.{key}[{index}] must be a non-empty string")
                continue
            if key == "allowedInteractors" and is_vague_allowed_interactor(entry):
                warnings.append(
                    f"{name}.allowedInteractors should name exact reference appendages or body parts, not only {entry!r}"
                )


def appendage_reference_labels(appendage: dict[str, Any]) -> set[str]:
    labels: set[str] = set()
    appendage_id = appendage.get("id")
    kind = appendage.get("kind")
    placement = appendage.get("placement")

    for value in [appendage_id, kind, placement]:
        if isinstance(value, str) and value.strip():
            labels.add(normalize_label(value))

    if isinstance(placement, str) and isinstance(kind, str):
        labels.add(normalize_label(f"{placement} {kind}"))
        labels.add(normalize_label(f"{kind} {placement}"))

    return labels


def interactor_matches_appendage(interactor: str, appendage: dict[str, Any]) -> bool:
    normalized = normalize_label(interactor)
    return any(label and (label == normalized or label in normalized or normalized in label) for label in appendage_reference_labels(appendage))


def appendage_affordance_groups(appendage: dict[str, Any]) -> set[str]:
    groups: set[str] = set()
    affordances = appendage.get("affordances")
    if not isinstance(affordances, list):
        return groups
    for entry in affordances:
        if not isinstance(entry, str):
            continue
        group = canonical_affordance_group(entry)
        if group:
            groups.add(group)
    return groups


def matching_contract_appendages(anatomy_contract: dict[str, Any], allowed_interactors: list[str]) -> list[dict[str, Any]]:
    appendages = anatomy_contract.get("appendages")
    if not isinstance(appendages, list):
        return []
    matches: list[dict[str, Any]] = []
    seen: set[int] = set()
    for interactor in allowed_interactors:
        if not isinstance(interactor, str):
            continue
        for appendage in appendages:
            if not isinstance(appendage, dict):
                continue
            if interactor_matches_appendage(interactor, appendage):
                identity = id(appendage)
                if identity not in seen:
                    matches.append(appendage)
                    seen.add(identity)
    return matches


def validate_enhancer_affordances(
    errors: list[str],
    warnings: list[str],
    value: dict[str, Any],
    name: str,
    anatomy_contract: dict[str, Any] | None,
) -> None:
    required_groups = infer_required_affordance_groups(value)
    if not required_groups:
        return
    anatomy_guard = value.get("anatomyGuard")
    if not isinstance(anatomy_guard, dict):
        return
    allowed_interactors = anatomy_guard.get("allowedInteractors")
    if not isinstance(allowed_interactors, list) or not allowed_interactors:
        return
    if not isinstance(anatomy_contract, dict):
        return

    matched = matching_contract_appendages(anatomy_contract, allowed_interactors)
    if not matched:
        warnings.append(
            f"{name}.anatomyGuard.allowedInteractors should match exact style.anatomyContract.appendages entries "
            "when gesture/prop affordances are involved"
        )
        return

    for group in sorted(required_groups):
        if any(group in appendage_affordance_groups(appendage) for appendage in matched):
            continue
        warnings.append(
            f"{name} uses a {group} action, but the matched style.anatomyContract.appendages do not declare a "
            f"compatible affordance; add appendages[].affordances such as {group!r} for mascots that can do it, "
            "or choose safer acting for appendages that cannot"
        )


def validate_anatomy_contract(
    errors: list[str],
    warnings: list[str],
    value: Any,
    name: str,
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return

    for key in ["source", "bodyCore"]:
        field = value.get(key)
        if not isinstance(field, str) or not field.strip():
            errors.append(f"{name}.{key} must be a non-empty string")

    total_appendages = value.get("totalAppendages")
    if not isinstance(total_appendages, int) or total_appendages < 0:
        errors.append(f"{name}.totalAppendages must be an integer >= 0")
        total_appendages = None

    appendages = value.get("appendages")
    counted_appendages = 0
    if not isinstance(appendages, list):
        errors.append(f"{name}.appendages must be an array")
    elif total_appendages != 0 and not appendages:
        errors.append(f"{name}.appendages must list the reference appendages when totalAppendages is greater than 0")
    else:
        for index, appendage in enumerate(appendages):
            item_name = f"{name}.appendages[{index}]"
            if not isinstance(appendage, dict):
                errors.append(f"{item_name} must be an object")
                continue
            for key in ["id", "kind", "placement"]:
                field = appendage.get(key)
                if not isinstance(field, str) or not field.strip():
                    errors.append(f"{item_name}.{key} must be a non-empty string")
            count = appendage.get("count")
            if not isinstance(count, int) or count < 1:
                errors.append(f"{item_name}.count must be an integer >= 1")
            else:
                counted_appendages += count
            affordances = appendage.get("affordances")
            if affordances is not None:
                if not isinstance(affordances, list) or not affordances:
                    errors.append(f"{item_name}.affordances must be a non-empty array when present")
                else:
                    for affordance_index, affordance in enumerate(affordances):
                        if not isinstance(affordance, str) or not affordance.strip():
                            errors.append(
                                f"{item_name}.affordances[{affordance_index}] must be a non-empty string"
                            )

    if total_appendages is not None and isinstance(appendages, list) and counted_appendages != total_appendages:
        errors.append(
            f"{name}.totalAppendages must equal the sum of appendages counts ({counted_appendages})"
        )

    forbidden = value.get("forbiddenAdditions")
    if forbidden is None:
        warnings.append(f"{name}.forbiddenAdditions should list anatomy the generator must not invent")
    elif not isinstance(forbidden, list) or not forbidden:
        errors.append(f"{name}.forbiddenAdditions must be a non-empty array when present")
    else:
        for index, entry in enumerate(forbidden):
            if not isinstance(entry, str) or not entry.strip():
                errors.append(f"{name}.forbiddenAdditions[{index}] must be a non-empty string")


def validate_string_list(
    errors: list[str],
    value: Any,
    name: str,
    *,
    required: bool = False,
) -> None:
    if value is None:
        if required:
            errors.append(f"{name} is required")
        return
    if not isinstance(value, list) or not value:
        errors.append(f"{name} must be a non-empty array")
        return
    for index, entry in enumerate(value):
        if not isinstance(entry, str) or not entry.strip():
            errors.append(f"{name}[{index}] must be a non-empty string")


def validate_visual_language(
    errors: list[str],
    value: Any,
    name: str,
    *,
    required: bool = False,
) -> bool:
    if value is None:
        if required:
            errors.append(f"{name} is required when --require-visual-language is used")
        return False
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return False

    if required:
        for key in sorted(VISUAL_LANGUAGE_REQUIRED_FIELDS - set(value)):
            errors.append(f"{name}.{key} is required")

    source_vibe = value.get("sourceVibe")
    if source_vibe is not None and (not isinstance(source_vibe, str) or not source_vibe.strip()):
        errors.append(f"{name}.sourceVibe must be a non-empty string")
    validate_string_list(errors, value.get("motifs"), f"{name}.motifs", required=required)
    validate_string_list(
        errors,
        value.get("forbiddenGenericCues"),
        f"{name}.forbiddenGenericCues",
        required=required,
    )

    state_cue_rules = value.get("stateCueRules")
    if state_cue_rules is not None:
        if not isinstance(state_cue_rules, dict):
            errors.append(f"{name}.stateCueRules must be an object when present")
        else:
            for state_name, rule in state_cue_rules.items():
                if not isinstance(state_name, str) or not state_name.strip():
                    errors.append(f"{name}.stateCueRules keys must be non-empty strings")
                if not isinstance(rule, str) or not rule.strip():
                    errors.append(f"{name}.stateCueRules.{state_name} must be a non-empty string")

    return True


def validate_style_metadata(
    data: dict[str, Any],
    states: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    qa: dict[str, Any],
    require_state_clarity: bool,
    require_rendering_style: bool,
    require_visual_language: bool,
) -> None:
    style = data.get("style")
    if style is None:
        if require_state_clarity:
            errors.append("style.stateClarity is required when --require-state-clarity is used")
        if require_rendering_style:
            errors.append("style.renderingStyle is required when --require-rendering-style is used")
        if require_visual_language:
            errors.append("style.visualLanguage is required when --require-visual-language is used")
        return
    if not isinstance(style, dict):
        errors.append("style must be an object")
        return

    rendering_style = style.get("renderingStyle")
    if rendering_style is None:
        if require_rendering_style:
            errors.append("style.renderingStyle is required when --require-rendering-style is used")
    elif not isinstance(rendering_style, str):
        errors.append("style.renderingStyle must be a string")
        rendering_style = None
    elif rendering_style not in RENDERING_STYLES:
        errors.append("style.renderingStyle must be codex-pixel-art")

    state_clarity = style.get("stateClarity")
    if state_clarity is None:
        errors.append("style.stateClarity is required when style is present")
        return
    if not isinstance(state_clarity, str):
        errors.append("style.stateClarity must be a string")
        return
    if state_clarity not in STATE_CLARITY_PROFILES:
        errors.append(f"style.stateClarity must be one of: {', '.join(sorted(STATE_CLARITY_PROFILES))}")
        return

    enhancer_theme = style.get("enhancerTheme")
    if enhancer_theme is not None and not isinstance(enhancer_theme, str):
        errors.append("style.enhancerTheme must be a string when present")

    visual_language = style.get("visualLanguage")
    has_visual_language = validate_visual_language(
        errors,
        visual_language,
        "style.visualLanguage",
        required=require_visual_language,
    )

    anatomy_class = style.get("anatomyClass")
    if anatomy_class is not None:
        if not isinstance(anatomy_class, str):
            errors.append("style.anatomyClass must be a string when present")
            anatomy_class = None
        elif anatomy_class not in ANATOMY_CLASSES:
            errors.append(f"style.anatomyClass must be one of: {', '.join(sorted(ANATOMY_CLASSES))}")

    anatomy_contract = style.get("anatomyContract")
    if anatomy_contract is not None:
        validate_anatomy_contract(errors, warnings, anatomy_contract, "style.anatomyContract")

    states_with_enhancers: list[str] = []
    risky_anatomy_states: list[str] = []
    for state_name, state in states.items():
        if not isinstance(state, dict):
            continue
        if "enhancer" in state:
            states_with_enhancers.append(state_name)
            if enhancer_has_anatomy_risk(state.get("enhancer")):
                risky_anatomy_states.append(state_name)
            validate_enhancer(
                errors,
                warnings,
                state.get("enhancer"),
                f"states.{state_name}.enhancer",
                anatomy_class=anatomy_class if isinstance(anatomy_class, str) else None,
                anatomy_contract=anatomy_contract if isinstance(anatomy_contract, dict) else None,
            )
            enhancer = state.get("enhancer")
            visual_language_fit = enhancer.get("visualLanguageFit") if isinstance(enhancer, dict) else None
            if require_visual_language and (not isinstance(visual_language_fit, str) or not visual_language_fit.strip()):
                errors.append(
                    f"states.{state_name}.enhancer.visualLanguageFit is required when --require-visual-language is used"
                )

    if state_clarity == "pose-only" and states_with_enhancers:
        errors.append("style.stateClarity is pose-only but one or more states include enhancer metadata")

    if state_clarity == "semantic-enhancers":
        for state_name in sorted(SEMANTIC_ENHANCER_STATES & set(states)):
            state = states.get(state_name)
            if isinstance(state, dict) and "enhancer" not in state:
                warnings.append(
                    f"states.{state_name}.enhancer metadata is recommended when style.stateClarity is semantic-enhancers"
                )
        if (
            anatomy_contract is None
            and anatomy_class in ANATOMY_CONTRACT_RECOMMENDED_CLASSES
            and states_with_enhancers
        ):
            warnings.append(
                "style.anatomyContract is recommended for "
                f"style.anatomyClass {anatomy_class!r} when enhanced states are used in "
                + ", ".join(sorted(states_with_enhancers))
            )

    qa["stateClarity"] = {
        "profile": state_clarity,
        "renderingStyle": rendering_style,
        "enhancerTheme": enhancer_theme,
        "hasVisualLanguage": has_visual_language,
        "anatomyClass": anatomy_class,
        "hasAnatomyContract": anatomy_contract is not None,
        "statesWithEnhancers": sorted(states_with_enhancers),
        "riskyAnatomyStates": sorted(risky_anatomy_states),
        "recommendedSemanticStates": sorted(SEMANTIC_ENHANCER_STATES & set(states)),
    }


def validate_manifest(
    manifest_path: Path,
    profile: str = "generic",
    require_state_clarity: bool = False,
    require_rendering_style: bool = False,
    require_visual_language: bool = False,
    require_quality_report: bool = False,
    require_art_direction_review: bool = False,
    key_color: str | None = None,
    spill_threshold: int | None = None,
    max_outline_halo_pixels: int = 0,
) -> tuple[dict[str, Any], list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    qa: dict[str, Any] = {}

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {}, [f"could not read manifest JSON: {exc}"], [], qa

    if not isinstance(data, dict):
        return {}, ["manifest root must be an object"], [], qa

    assembly_report = load_assembly_report(manifest_path)
    if assembly_report is None:
        warnings.append("qa/assembly-report.json is missing or unreadable")
    else:
        qa["assemblyReport"] = {
            "ok": assembly_report.get("ok"),
            "outlineImprover": assembly_report.get("outlineImprover"),
        }
        for warning in assembly_report.get("warnings", []):
            warnings.append(f"assembly report warning: {warning}")

    quality_report = load_quality_report(manifest_path)
    if quality_report is None:
        if require_quality_report:
            warnings.append("qa/quality-report.json is missing or unreadable")
    else:
        qa["qualityReport"] = {
            "ok": quality_report.get("ok"),
            "semanticAnchorCheck": quality_report.get("semanticAnchorCheck"),
            "motionQualityCheck": quality_report.get("motionQualityCheck"),
        }
        for error in quality_report.get("errors", []):
            errors.append(f"quality report error: {error}")
        for warning in quality_report.get("warnings", []):
            warnings.append(f"quality report warning: {warning}")

    art_direction_review = load_art_direction_review(manifest_path)
    if art_direction_review is None:
        if require_art_direction_review:
            warnings.append("qa/art-direction-review.json is missing or unreadable")
    else:
        validate_art_direction_review(manifest_path, art_direction_review, errors, warnings, qa)

    if key_color is None and assembly_report:
        report_key_color = assembly_report.get("keyColor")
        key_color = report_key_color if isinstance(report_key_color, str) else None
    if spill_threshold is None and assembly_report:
        report_spill_threshold = assembly_report.get("spillThreshold")
        spill_threshold = report_spill_threshold if isinstance(report_spill_threshold, int) else None
    if key_color is None:
        key_color = "#FF00FF"
    if spill_threshold is None:
        spill_threshold = 45

    try:
        key_color_rgb = parse_hex_color(key_color)
    except ValueError as exc:
        errors.append(str(exc))
        key_color_rgb = None

    for key in ["id", "displayName", "atlas", "states"]:
        if key not in data:
            errors.append(f"missing required key: {key}")

    atlas = data.get("atlas")
    if not isinstance(atlas, dict):
        errors.append("atlas must be an object")
        atlas = {}

    missing_atlas = sorted(REQUIRED_ATLAS_FIELDS - set(atlas))
    for key in missing_atlas:
        errors.append(f"atlas missing required key: {key}")

    atlas_path_raw = atlas.get("path")
    if atlas_path_raw is not None and not isinstance(atlas_path_raw, str):
        errors.append("atlas.path must be a string")

    width = require_int(errors, atlas.get("width"), "atlas.width") if "width" in atlas else None
    height = require_int(errors, atlas.get("height"), "atlas.height") if "height" in atlas else None
    columns = require_int(errors, atlas.get("columns"), "atlas.columns") if "columns" in atlas else None
    rows = require_int(errors, atlas.get("rows"), "atlas.rows") if "rows" in atlas else None
    cell_width = require_int(errors, atlas.get("cellWidth"), "atlas.cellWidth") if "cellWidth" in atlas else None
    cell_height = require_int(errors, atlas.get("cellHeight"), "atlas.cellHeight") if "cellHeight" in atlas else None

    if width and columns and cell_width and width != columns * cell_width:
        errors.append("atlas.width must equal atlas.columns * atlas.cellWidth")
    if height and rows and cell_height and height != rows * cell_height:
        errors.append("atlas.height must equal atlas.rows * atlas.cellHeight")

    states = data.get("states")
    if not isinstance(states, dict) or not states:
        errors.append("states must be a non-empty object")
        states = {}

    if profile == "chatbot":
        missing_core = sorted(CHATBOT_CORE_STATES - set(states))
        for state_name in missing_core:
            warnings.append(f"chatbot profile missing core state: {state_name}")

    validate_style_metadata(
        data,
        states,
        errors,
        warnings,
        qa,
        require_state_clarity,
        require_rendering_style,
        require_visual_language,
    )
    style = data.get("style")
    if (
        isinstance(style, dict)
        and style.get("stateClarity") == "semantic-enhancers"
        and not (manifest_path.parent / "qa" / "state-readability-check.png").exists()
    ):
        warnings.append("semantic-enhancers pack is missing qa/state-readability-check.png")

    seen_rows: dict[int, str] = {}
    for state_name, state in states.items():
        if not isinstance(state_name, str) or not state_name:
            errors.append("state names must be non-empty strings")
            continue
        if not isinstance(state, dict):
            errors.append(f"states.{state_name} must be an object")
            continue

        row = require_int(errors, state.get("row"), f"states.{state_name}.row", minimum=0)
        frames = require_int(errors, state.get("frames"), f"states.{state_name}.frames")
        durations = state.get("durations")

        if not isinstance(durations, list) or not durations:
            errors.append(f"states.{state_name}.durations must be a non-empty array")
        else:
            for index, duration in enumerate(durations):
                require_int(errors, duration, f"states.{state_name}.durations[{index}]")
            if frames is not None and len(durations) != frames:
                errors.append(f"states.{state_name}.frames must equal durations.length")

        if columns is not None and frames is not None and frames > columns:
            errors.append(f"states.{state_name}.frames exceeds atlas.columns")
        if profile == "chatbot" and frames is not None:
            recommended = CHATBOT_RECOMMENDED_FRAMES.get(state_name)
            if recommended and frames < recommended:
                warnings.append(
                    f"states.{state_name}.frames is {frames}; chatbot profile recommends {recommended}+ for smoother motion"
                )
        if rows is not None and row is not None and row >= rows:
            errors.append(f"states.{state_name}.row exceeds atlas.rows")
        if row is not None:
            previous = seen_rows.get(row)
            if previous:
                errors.append(f"states.{state_name}.row duplicates state {previous}")
            seen_rows[row] = state_name

    if profile != "audition" and "idle" not in states:
        warnings.append("manifest has no idle state")

    if atlas_path_raw and isinstance(atlas_path_raw, str):
        atlas_path = Path(atlas_path_raw)
        if not atlas_path.is_absolute():
            atlas_path = manifest_path.parent / atlas_path
        if not atlas_path.exists():
            warnings.append(f"atlas image does not exist at {atlas_path}")
        else:
            image_info = inspect_atlas(
                atlas_path,
                states,
                columns,
                cell_width,
                cell_height,
                key_color=key_color_rgb,
                spill_threshold=spill_threshold,
                max_outline_halo_pixels=max_outline_halo_pixels,
            )
            if image_info is None:
                warnings.append("Pillow is unavailable; skipped atlas image dimension check")
            else:
                info, image_errors, image_warnings = image_info
                qa["atlasImage"] = info
                image_width = info["width"]
                image_height = info["height"]
                mode = info["mode"]
                if width and image_width != width:
                    errors.append(f"atlas image width {image_width} does not match manifest {width}")
                if height and image_height != height:
                    errors.append(f"atlas image height {image_height} does not match manifest {height}")
                if "A" not in mode:
                    warnings.append(f"atlas image mode {mode} has no alpha channel")
                errors.extend(image_errors)
                warnings.extend(image_warnings)

    return data, errors, warnings, qa


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to companion manifest.json")
    parser.add_argument(
        "--profile",
        choices=["generic", "chatbot", "audition"],
        default="generic",
        help="Validation profile. Use audition for strict single-row or partial-pack tests; use chatbot for full website assistant companion packs.",
    )
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--key-color", help="Chroma-key color used by the assembler; defaults to assembly report or #FF00FF")
    parser.add_argument("--spill-threshold", type=int, help="Spill threshold used by the assembler; defaults to assembly report or 45")
    parser.add_argument("--max-outline-halo-pixels", type=int, default=0, help="Maximum key-colored outline pixels allowed per used frame")
    parser.add_argument(
        "--require-state-clarity",
        action="store_true",
        help="Require style.stateClarity metadata for newly generated companion packs",
    )
    parser.add_argument(
        "--require-rendering-style",
        action="store_true",
        help='Require style.renderingStyle metadata and enforce "codex-pixel-art"',
    )
    parser.add_argument(
        "--require-visual-language",
        action="store_true",
        help="Require style.visualLanguage and per-enhancer visualLanguageFit metadata for mascot-native state cues",
    )
    parser.add_argument(
        "--require-quality-report",
        action="store_true",
        help="Require qa/quality-report.json and include quality warnings in strict validation",
    )
    parser.add_argument(
        "--require-art-direction-review",
        action="store_true",
        help="Require qa/art-direction-review.json so production validation includes visual/art-direction acceptance",
    )
    parser.add_argument("--json-out", help="Optional path to write validation JSON")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    _data, errors, warnings, qa = validate_manifest(
        manifest_path,
        profile=args.profile,
        require_state_clarity=args.require_state_clarity,
        require_rendering_style=args.require_rendering_style,
        require_visual_language=args.require_visual_language,
        require_quality_report=args.require_quality_report,
        require_art_direction_review=args.require_art_direction_review,
        key_color=args.key_color,
        spill_threshold=args.spill_threshold,
        max_outline_halo_pixels=args.max_outline_halo_pixels,
    )
    ok = not errors and not (args.strict and warnings)
    result = {
        "ok": ok,
        "manifest": str(manifest_path),
        "profile": args.profile,
        "strict": args.strict,
        "requireStateClarity": args.require_state_clarity,
        "requireRenderingStyle": args.require_rendering_style,
        "requireVisualLanguage": args.require_visual_language,
        "requireQualityReport": args.require_quality_report,
        "requireArtDirectionReview": args.require_art_direction_review,
        "errors": errors,
        "warnings": warnings,
        "qa": qa,
    }

    text = json.dumps(result, indent=2)
    print(text)
    if args.json_out:
        Path(args.json_out).expanduser().resolve().write_text(text + "\n", encoding="utf-8")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
