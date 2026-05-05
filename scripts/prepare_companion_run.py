#!/usr/bin/env python3
"""Prepare a web companion mascot run with state cue plans and row prompts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_STATES = [
    "idle",
    "greeting",
    "listening",
    "thinking",
    "working",
    "answering",
    "success",
    "error",
    "confused",
    "sleeping",
]

SEMANTIC_STATES = {"listening", "thinking", "working", "answering", "success", "error", "confused"}
LONG_STATES = {"thinking", "working", "answering"}
STATE_PURPOSES = {
    "idle": "default calm presence",
    "greeting": "chat opens or first welcome",
    "listening": "user is typing or speaking",
    "thinking": "assistant is planning before output",
    "working": "assistant is using tools, retrieval, search, files, or backend work",
    "answering": "assistant is streaming a response",
    "success": "task or answer completed successfully",
    "error": "recoverable failure or warning",
    "confused": "input is unclear or needs clarification",
    "sleeping": "inactive, minimized, or offline",
}

STATE_ACTING = {
    "idle": "slow breathing, soft blink, tiny posture settle",
    "greeting": "friendly anticipation, small wave or body bounce, warm smile, return to rest",
    "listening": "attentive lean toward the user, eyes tracking, small blink hold",
    "thinking": "curious head tilt, eyes up or to the side, blink hold, small pondering mouth",
    "working": "focused-but-friendly concentration, eye tracking, lean-in, faster purposeful body or prop motion",
    "answering": "speaking mouth shapes, bright eyes, rhythmic face/body beats",
    "success": "cheerful bounce, proud hold, bright face, return to loop",
    "error": "worried recognition, small recoil or slump, recovery beat",
    "confused": "squint, head tilt, uncertain mouth, small recovery",
    "sleeping": "closed eyes, slow breathing, sleepy settle",
}

STATE_VISUAL_AIDS = {
    "listening": "small attached sound rings or attentive pose only when needed",
    "thinking": "compact side-origin thought puff, idea orb, or hand-to-chin only when anatomy supports it",
    "working": "existing work prop when anatomy supports it; otherwise a tiny processing/work cue with purposeful cycling motion that clearly reads as active work",
    "answering": "mouth shapes first; tiny no-text voice pixels or breath puffs close to the face when needed",
    "success": "small check/glint, proud pose, or raised existing prop",
    "error": "attached tear, warning charm, prop droop, or small attached smoke/stars",
    "confused": "tiny question cue only if expression and tilt are not enough",
}

STATE_REJECTS = {
    "working": "anger, hostile eyes, decorative particles that do not read as work, unsupported held tools",
    "answering": "speech panels, text, punctuation, generic chat UI, mouthless talking cues",
    "thinking": "generic icon straight above the head, static dots, face-touch by unsupported appendages",
    "listening": "microphone props for non-voice apps, detached sound clutter",
    "success": "large confetti, loose sparkles, text labels",
    "error": "red X labels, detached symbols, scenery",
    "confused": "text labels or large punctuation panels",
}

ANATOMY_GUIDANCE = {
    "hands": (
        "Visible hands may point, present, hold, touch the face, type, or write when the reference supports it. "
        "Keep exactly the original hands/arms; no duplicates."
    ),
    "paws": (
        "Paws may gesture, brace chunky props, or present broadly. Avoid finger-dependent typing/writing unless "
        "the reference clearly has fingers."
    ),
    "fins-no-hands": (
        "Fins stay side-attached with side-bob, tilt, tuck, or tiny wave. Do not turn fins into hands, fingers, "
        "detached mitts, arms, or front-body appendage patches."
    ),
    "no-limbs": (
        "Use face, body posture, breathing, attached marks, aura, or near-head effects. Do not use held, "
        "near-hand, typing, writing, tablet, slate, keyboard, paper, pencil, quill, or tool props."
    ),
    "ambiguous-limbs": (
        "Treat appendages conservatively until the reference audit proves their affordances. Prefer face/body "
        "acting and small anchored aids over risky grip or face-touch poses."
    ),
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "companion"


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def frame_count_for(state: str, compact: bool) -> int:
    if compact:
        return 6 if state in LONG_STATES else 6
    return 12 if state in LONG_STATES else 10


def durations_for(state: str, frames: int) -> list[int]:
    if state in {"working", "answering"}:
        base = [110, 100, 110, 120]
    elif state in {"thinking", "listening"}:
        base = [140, 120, 140, 180]
    elif state == "sleeping":
        base = [260, 320, 420, 320]
    else:
        base = [150, 130, 150, 190]
    durations = [base[index % len(base)] for index in range(frames)]
    durations[-1] = max(durations[-1], 180)
    return durations


def visual_aid_mode_for(state: str, state_clarity: str) -> str:
    if state_clarity == "pose-only" or state not in SEMANTIC_STATES:
        return "pose-only"
    return "use only if acting alone would be unclear at 64-96 px"


def build_visual_language(args: argparse.Namespace) -> dict[str, Any]:
    motifs = args.motif or ["infer mascot-native motifs from the reference"]
    forbidden = args.forbid_cue or [
        "generic UI symbols that do not fit the reference",
        "text labels",
        "speech panels",
        "decorative particles that do not communicate the state",
    ]
    return {
        "sourceVibe": args.source_vibe or "Infer from the reference before choosing state cues.",
        "motifs": motifs,
        "forbiddenGenericCues": forbidden,
    }


def build_state_plan(state: str, anatomy_class: str, state_clarity: str) -> dict[str, str]:
    visual_aid = STATE_VISUAL_AIDS.get(state, "none unless the pose is unclear")
    if state == "thinking" and anatomy_class in {"fins-no-hands", "no-limbs", "ambiguous-limbs"}:
        visual_aid = "compact side-origin thought puff or idea orb; use eyes, tilt, and blink timing, not hand-to-chin"
    if anatomy_class == "no-limbs" and state == "working":
        visual_aid = "face/body acting plus tiny attached or near-head processing cue with purposeful cycling motion; no held or near-hand props"
    if anatomy_class in {"fins-no-hands", "ambiguous-limbs"} and state == "working":
        visual_aid = "focused face/body acting plus tiny attached or near-head processing cue; no held props in the draft plan"
    if state_clarity == "pose-only":
        visual_aid = "none; communicate through acting, timing, and existing identity props only"
    return {
        "state": state,
        "semanticRead": STATE_PURPOSES.get(state, state),
        "actingFirst": STATE_ACTING.get(state, "clear face, posture, and timing"),
        "visualAidDecision": visual_aid_mode_for(state, state_clarity),
        "suggestedVisualAid": visual_aid,
        "rejectIf": STATE_REJECTS.get(state, "unclear state read, off-vibe symbol, identity drift, extra anatomy"),
    }


def build_prompt(
    *,
    name: str,
    state: str,
    state_plan: dict[str, str],
    anatomy_class: str,
    frame_count: int,
    cell_width: int,
    cell_height: int,
    source_vibe: str,
) -> str:
    anatomy = ANATOMY_GUIDANCE.get(anatomy_class, ANATOMY_GUIDANCE["ambiguous-limbs"])
    return f"""# {name} {state} row prompt

Use the provided reference image(s) as the identity source. Infer the mascot's vibe from the reference before choosing the pose or visual aid.

Create one horizontal sprite row strip with exactly {frame_count} separated frames on a flat removable chroma-key background.

Style lock: Codex digital-pet pixel art, compact chibi sprite, visible stepped pixel edges, thick dark 1-2 px outline, limited palette, flat cel shading, hard-edged sprite effects. No smooth illustration, glossy rendering, 3D, painterly gradients, vector-flat icons, text, labels, scenery, shadows, or UI panels.

Identity lock: preserve the same mascot species/body type, face, palette, markings, outline weight, proportions, appendage count, and silhouette from the reference. Do not redesign the character.

State: {state}
Semantic read: {state_plan["semanticRead"]}
Acting first: {state_plan["actingFirst"]}
Visual aid decision: {state_plan["visualAidDecision"]}
Suggested visual aid when needed: {state_plan["suggestedVisualAid"]}
Vibe fit: {source_vibe}
Anatomy class: {anatomy_class}
Anatomy guidance: {anatomy}
Reject if: {state_plan["rejectIf"]}

Semantic ladder:
1. Make the face, eyes, mouth, posture, timing, and original appendages perform the state.
2. Use existing identity props or appendages only when the reference supports that action.
3. Add one tiny attached or anchored visual aid only if the state is still unclear at website size.
4. Reject a pretty motif-native effect when it does not communicate the state.

Visual aid rule: if a visual aid is used, make it a small visual verb with a state-specific motion path, not a decorative symbol. For working, the cue should look like purposeful processing, sorting, checking, gathering, or tool activity while the face stays focused-but-friendly. For answering, the cue should support mouth/voice motion rather than become a speech panel.

Frame layout: keep each pose fully inside an implied {cell_width}x{cell_height} cell with safe padding. Keep body center, top-of-head height, bottom edge, silhouette scale, and appendage count stable across the row. Every frame must have a meaningful change in face, pose, body motion, prop, or visual aid.
"""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--companion-name", required=True, help="Mascot display name")
    parser.add_argument("--description", default="", help="One-sentence companion description")
    parser.add_argument("--reference", action="append", default=[], help="Reference image path used for grounding")
    parser.add_argument("--output-dir", required=True, help="Run directory to create")
    parser.add_argument("--states", default=",".join(DEFAULT_STATES), help="Comma-separated state list")
    parser.add_argument("--state-clarity", choices=["pose-only", "semantic-enhancers"], default="semantic-enhancers")
    parser.add_argument("--anatomy-class", choices=sorted(ANATOMY_GUIDANCE), default="ambiguous-limbs")
    parser.add_argument("--source-vibe", help="Optional inferred vibe note; omit to make prompts infer from reference")
    parser.add_argument("--motif", action="append", default=[], help="Mascot-native motif; can be repeated")
    parser.add_argument("--forbid-cue", action="append", default=[], help="Generic/off-vibe cue to avoid; can be repeated")
    parser.add_argument("--cell-width", type=int, default=256)
    parser.add_argument("--cell-height", type=int, default=288)
    parser.add_argument("--columns", type=int, default=12)
    parser.add_argument("--compact", action="store_true", help="Use 6-frame audition rows")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing run directory")
    parser.add_argument("--quiet", action="store_true", help="Do not print the output summary")
    args = parser.parse_args(argv)

    states = parse_csv(args.states)
    unknown_states = [state for state in states if state not in DEFAULT_STATES]
    if unknown_states:
        parser.error("unknown states: " + ", ".join(unknown_states))

    out_dir = Path(args.output_dir).expanduser().resolve()
    if out_dir.exists() and any(out_dir.iterdir()) and not args.force:
        parser.error(f"output directory is not empty; use --force to overwrite: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prompts").mkdir(exist_ok=True)
    (out_dir / "generated").mkdir(exist_ok=True)
    (out_dir / "qa").mkdir(exist_ok=True)

    visual_language = build_visual_language(args)
    frames_by_state = {state: frame_count_for(state, args.compact) for state in states}
    columns = max(args.columns, max(frames_by_state.values()))

    manifest: dict[str, Any] = {
        "id": slugify(args.companion_name),
        "displayName": args.companion_name,
        "description": args.description,
        "references": [str(Path(path).expanduser()) for path in args.reference],
        "style": {
            "renderingStyle": "codex-pixel-art",
            "stateClarity": args.state_clarity,
            "anatomyClass": args.anatomy_class,
            "visualLanguage": visual_language,
        },
        "atlas": {
            "path": "atlas.webp",
            "width": columns * args.cell_width,
            "height": len(states) * args.cell_height,
            "columns": columns,
            "rows": len(states),
            "cellWidth": args.cell_width,
            "cellHeight": args.cell_height,
        },
        "states": {},
    }

    plan: dict[str, Any] = {
        "companionName": args.companion_name,
        "stateClarity": args.state_clarity,
        "anatomyClass": args.anatomy_class,
        "visualLanguage": visual_language,
        "states": {},
        "notes": [
            "This is a prompt/state-cue plan, not final art acceptance.",
            "After row generation, update enhancer metadata to match the actual accepted visual aid.",
            "Reject rows where the state read is unclear even if the effect matches the mascot vibe.",
        ],
    }

    for row, state in enumerate(states):
        frames = frames_by_state[state]
        state_plan = build_state_plan(state, args.anatomy_class, args.state_clarity)
        manifest_state: dict[str, Any] = {
            "row": row,
            "frames": frames,
            "durations": durations_for(state, frames),
            "loop": True,
        }
        if args.state_clarity == "semantic-enhancers" and state in SEMANTIC_STATES:
            manifest_state["enhancer"] = {
                "kind": "planned during row generation",
                "attachment": "body-pose",
                "description": state_plan["suggestedVisualAid"],
                "visualLanguageFit": "Prompt requires the row to infer a mascot-native cue and reject decorative ambiguity.",
            }
        manifest["states"][state] = manifest_state
        plan["states"][state] = state_plan
        (out_dir / "prompts" / f"{state}.md").write_text(
            build_prompt(
                name=args.companion_name,
                state=state,
                state_plan=state_plan,
                anatomy_class=args.anatomy_class,
                frame_count=frames,
                cell_width=args.cell_width,
                cell_height=args.cell_height,
                source_vibe=visual_language["sourceVibe"],
            ),
            encoding="utf-8",
        )

    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "qa" / "state-cue-plan.json", plan)
    if not args.quiet:
        print(
            json.dumps(
                {
                    "ok": True,
                    "runDir": str(out_dir),
                    "manifest": str(out_dir / "manifest.json"),
                    "stateCuePlan": str(out_dir / "qa" / "state-cue-plan.json"),
                    "promptsDir": str(out_dir / "prompts"),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
