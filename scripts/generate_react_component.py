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
    return f"""import type {{ CSSProperties }} from "react";
import {{ useEffect, useMemo, useState }} from "react";

export type CompanionState = keyof typeof companionManifest.states;

export const companionManifest = {manifest_json} as const;

type CompanionMascotProps = {{
  state?: CompanionState | string;
  size?: number;
  paused?: boolean;
  assetBase?: string;
  className?: string;
  onClick?: () => void;
}};

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
  onClick,
}}: CompanionMascotProps) {{
  const prefersReducedMotion = usePrefersReducedMotion();
  const [frame, setFrame] = useState(0);

  const animation =
    companionManifest.states[state as CompanionState] ?? companionManifest.states.idle;

  useEffect(() => {{
    setFrame(0);
  }}, [state]);

  useEffect(() => {{
    if (paused || prefersReducedMotion) return;

    const duration = animation.durations[frame] ?? 150;
    const timer = window.setTimeout(() => {{
      setFrame((current) => (current + 1) % animation.frames);
    }}, duration);

    return () => window.clearTimeout(timer);
  }}, [animation, frame, paused, prefersReducedMotion]);

  const cellWidth = companionManifest.atlas.cellWidth;
  const cellHeight = companionManifest.atlas.cellHeight;

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
      aria-label={{`${{companionManifest.displayName}} mascot ${{state}}`}}
      style={{{{
        width: cellWidth * size,
        height: cellHeight * size,
        display: "inline-flex",
        alignItems: "flex-end",
        justifyContent: "center",
        padding: 0,
        border: 0,
        background: "transparent",
        cursor: onClick ? "pointer" : "default",
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
    case "chat-opened":
      return "greeting";
    case "user-typing":
      return "listening";
    case "submitted":
      return "thinking";
    case "retrieving":
    case "tool-call":
      return "working";
    case "streaming":
      return "answering";
    case "complete":
      return "success";
    case "error":
      return "error";
    case "unclear":
      return "confused";
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
