#!/usr/bin/env python3
"""Generate a React companion mascot component from a manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def ts_string(value: object) -> str:
    return json.dumps(value, indent=2)


def component_source(manifest: dict) -> str:
    manifest_json = ts_string(manifest)
    default_asset_base = f"/mascots/{manifest.get('id', 'companion')}"
    return f"""import type {{ CSSProperties, PointerEvent as ReactPointerEvent }} from "react";
import {{ useEffect, useMemo, useState }} from "react";

export type CompanionState = keyof typeof companionManifest.states;
export type CompanionPosition = {{ x: number; y: number }};

export const companionManifest = {manifest_json} as const;

type CompanionMascotProps = {{
  state?: CompanionState | string;
  size?: number;
  paused?: boolean;
  assetBase?: string;
  className?: string;
  enableHoverState?: boolean;
  draggable?: boolean;
  dragBounds?: "viewport" | "none";
  position?: CompanionPosition;
  defaultPosition?: CompanionPosition;
  onPositionChange?: (position: CompanionPosition) => void;
  onDragStart?: (position: CompanionPosition) => void;
  onDragEnd?: (position: CompanionPosition) => void;
  onHoverChange?: (hovered: boolean) => void;
  onClick?: () => void;
}};

function hasCompanionState(value: string): value is CompanionState {{
  return value in companionManifest.states;
}}

function usePrefersReducedMotion() {{
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {{
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(media.matches);
    const listener = () => setPrefersReducedMotion(media.matches);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }}, []);

  return prefersReducedMotion;
}}

export function CompanionMascot({{
  state = "idle",
  size = 1,
  paused = false,
  assetBase = "{default_asset_base}",
  className,
  enableHoverState = true,
  draggable = false,
  dragBounds = "viewport",
  position,
  defaultPosition,
  onPositionChange,
  onDragStart,
  onDragEnd,
  onHoverChange,
  onClick,
}}: CompanionMascotProps) {{
  const prefersReducedMotion = usePrefersReducedMotion();
  const [frame, setFrame] = useState(0);
  const [hovered, setHovered] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [internalPosition, setInternalPosition] = useState<CompanionPosition | undefined>(defaultPosition);
  const [dragOffset, setDragOffset] = useState<CompanionPosition>({{ x: 0, y: 0 }});

  const cellWidth = companionManifest.atlas.cellWidth;
  const cellHeight = companionManifest.atlas.cellHeight;
  const renderedWidth = cellWidth * size;
  const renderedHeight = cellHeight * size;
  const effectivePosition = position ?? internalPosition;

  const interactionState =
    dragging && hasCompanionState("dragging")
      ? "dragging"
      : enableHoverState && hovered && hasCompanionState("hover")
        ? "hover"
        : String(state);
  const effectiveState = hasCompanionState(interactionState) ? interactionState : "idle";

  const animation = companionManifest.states[effectiveState];

  useEffect(() => {{
    setFrame(0);
  }}, [effectiveState]);

  useEffect(() => {{
    if (paused || prefersReducedMotion) return;

    const duration = animation.durations[frame] ?? 150;
    const timer = window.setTimeout(() => {{
      setFrame((current) => (current + 1) % animation.frames);
    }}, duration);

    return () => window.clearTimeout(timer);
  }}, [animation, frame, paused, prefersReducedMotion]);

  function clampPosition(next: CompanionPosition): CompanionPosition {{
    if (dragBounds !== "viewport") return next;
    return {{
      x: Math.max(0, Math.min(next.x, window.innerWidth - renderedWidth)),
      y: Math.max(0, Math.min(next.y, window.innerHeight - renderedHeight)),
    }};
  }}

  function updatePosition(next: CompanionPosition) {{
    const clamped = clampPosition(next);
    if (!position) setInternalPosition(clamped);
    onPositionChange?.(clamped);
    return clamped;
  }}

  function handlePointerEnter() {{
    if (dragging) return;
    setHovered(true);
    onHoverChange?.(true);
  }}

  function handlePointerLeave() {{
    if (dragging) return;
    setHovered(false);
    onHoverChange?.(false);
  }}

  function handlePointerDown(event: ReactPointerEvent<HTMLButtonElement>) {{
    if (!draggable) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    const rect = event.currentTarget.getBoundingClientRect();
    const current = effectivePosition ?? {{ x: rect.left, y: rect.top }};
    setDragging(true);
    setHovered(false);
    setDragOffset({{ x: event.clientX - current.x, y: event.clientY - current.y }});
    const next = updatePosition(current);
    onDragStart?.(next);
  }}

  function handlePointerMove(event: ReactPointerEvent<HTMLButtonElement>) {{
    if (!dragging) return;
    updatePosition({{ x: event.clientX - dragOffset.x, y: event.clientY - dragOffset.y }});
  }}

  function endDrag(event: ReactPointerEvent<HTMLButtonElement>) {{
    if (!dragging) return;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {{
      event.currentTarget.releasePointerCapture(event.pointerId);
    }}
    setDragging(false);
    const finalPosition = effectivePosition ?? {{ x: event.clientX - dragOffset.x, y: event.clientY - dragOffset.y }};
    onDragEnd?.(clampPosition(finalPosition));
  }}

  const spriteStyle = useMemo<CSSProperties>(() => ({{
    width: cellWidth,
    height: cellHeight,
    backgroundImage: `url(${{assetBase}}/${{companionManifest.atlas.path}})`,
    backgroundRepeat: "no-repeat",
    backgroundPosition: `-${{frame * cellWidth}}px -${{animation.row * cellHeight}}px`,
    backgroundSize: `${{companionManifest.atlas.width}}px ${{companionManifest.atlas.height}}px`,
    imageRendering: "pixelated",
    transform: `scale(${{size}})`,
    transformOrigin: "bottom center",
  }}), [animation.row, assetBase, cellHeight, cellWidth, frame, size]);

  return (
    <button
      type="button"
      className={{className}}
      onClick={{onClick}}
      onPointerEnter={{handlePointerEnter}}
      onPointerLeave={{handlePointerLeave}}
      onPointerDown={{handlePointerDown}}
      onPointerMove={{handlePointerMove}}
      onPointerUp={{endDrag}}
      onPointerCancel={{endDrag}}
      aria-label={{`${{companionManifest.displayName}} mascot ${{effectiveState}}`}}
      style={{{{
        width: cellWidth * size,
        height: cellHeight * size,
        ...(effectivePosition
          ? {{ position: "fixed", left: effectivePosition.x, top: effectivePosition.y, zIndex: dragging ? 1000 : undefined }}
          : {{}}),
        display: "inline-flex",
        alignItems: "flex-end",
        justifyContent: "center",
        padding: 0,
        border: 0,
        background: "transparent",
        cursor: dragging ? "grabbing" : draggable ? "grab" : onClick ? "pointer" : "default",
        touchAction: draggable ? "none" : undefined,
        userSelect: "none",
      }}}}
    >
      <span aria-hidden="true" style={{spriteStyle}} />
    </button>
  );
}}
"""


def hook_source() -> str:
    return """export type ChatStatus =
  | "idle"
  | "hover"
  | "dragging"
  | "drag-start"
  | "drag-end"
  | "dropped"
  | "chat-opened"
  | "user-typing"
  | "submitted"
  | "retrieving"
  | "tool-call"
  | "streaming"
  | "complete"
  | "error"
  | "unclear"
  | "inactive";

export function toCompanionState(status: ChatStatus): string {
  switch (status) {
    case "hover":
      return "hover";
    case "drag-start":
    case "dragging":
      return "dragging";
    case "drag-end":
    case "dropped":
      return "idle";
    case "chat-opened":
      return "greeting";
    case "user-typing":
      return "listening";
    case "submitted":
      return "thinking";
    case "retrieving":
    case "tool-call":
      return "thinking";
    case "streaming":
      return "answering";
    case "complete":
      return "success";
    case "error":
      return "error";
    case "unclear":
      return "error";
    case "inactive":
      return "sleeping";
    default:
      return "idle";
  }
}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, help="Path to companion manifest.json")
    parser.add_argument("--out-dir", required=True, help="Directory to write React files")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    component_path = out_dir / "CompanionMascot.tsx"
    hook_path = out_dir / "useCompanionState.ts"
    component_path.write_text(component_source(manifest), encoding="utf-8")
    hook_path.write_text(hook_source(), encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "component": str(component_path),
        "hook": str(hook_path),
    }, indent=2))


if __name__ == "__main__":
    main()
