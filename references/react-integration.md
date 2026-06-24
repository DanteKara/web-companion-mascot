# React Integration

## Asset Placement

For Vite, Create React App, and many Next.js setups, place mascot assets under `public`:

```text
public/
  mascots/
    tridy/
      atlas.webp
      manifest.json
```

Then use browser paths:

```text
/mascots/tridy/atlas.webp
/mascots/tridy/manifest.json
```

Do not reference local machine paths such as `C:\Users\...` in deployed React code.

## Component API

Recommended props:

```ts
type CompanionMascotProps = {
  state: string;
  manifest: CompanionManifest;
  size?: number;
  paused?: boolean;
  className?: string;
  enableHoverState?: boolean;
  draggable?: boolean;
  position?: { x: number; y: number };
  defaultPosition?: { x: number; y: number };
  onPositionChange?: (position: { x: number; y: number }) => void;
  onDragStart?: (position: { x: number; y: number }) => void;
  onDragEnd?: (position: { x: number; y: number }) => void;
  onHoverChange?: (hovered: boolean) => void;
  onClick?: () => void;
};
```

## Pointer Interaction Priority

For website companions, interaction rows should take priority over backend chat state while the pointer is active:

```ts
const effectiveState =
  dragging && manifest.states.dragging
    ? "dragging"
    : hovered && manifest.states.hover
      ? "hover"
      : state;
```

Use `hover` for pointer enter/focus-like attention and `dragging` from pointer down through pointer up/cancel while the component follows the pointer. On drop, return to the current app state, usually `idle`, `success`, or the active chatbot state. Do not require a separate `dropped` row unless the product explicitly wants a landing/placement animation.

## Animation Logic

Use JavaScript timers for frame durations. CSS `steps()` is fine only when every frame in a row has the same duration.

Core loop:

```ts
useEffect(() => {
  if (paused || prefersReducedMotion) return;
  const animation = manifest.states[effectiveState] ?? manifest.states.idle;
  const duration = animation.durations[frame] ?? 150;
  const timer = window.setTimeout(() => {
    setFrame((current) => (current + 1) % animation.frames);
  }, duration);
  return () => window.clearTimeout(timer);
}, [effectiveState, frame, paused, prefersReducedMotion, manifest]);
```

Sprite style:

```ts
{
  width: manifest.atlas.cellWidth,
  height: manifest.atlas.cellHeight,
  backgroundImage: `url(${assetBase}/${manifest.atlas.path})`,
  backgroundPosition: `-${frame * cellWidth}px -${row * cellHeight}px`,
  backgroundSize: `${atlas.width}px ${atlas.height}px`,
  imageRendering: "pixelated"
}
```

Keep `imageRendering: "pixelated"` enabled for production assets from this skill. The atlas should already be native Codex-style pixel art; React should preserve the crisp pixel edges rather than smoothing them with browser scaling.

## Chatbot State Hook

Use a small adapter layer instead of passing raw backend statuses into the mascot:

```ts
export type ChatStatus =
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
```

## Drag And Drop

Implement drag/drop with pointer events rather than HTML5 drag images. Keep the sprite in the same atlas state system while dragging:

```ts
<CompanionMascot
  state={toCompanionState(chatStatus)}
  draggable
  defaultPosition={{ x: 24, y: 24 }}
  onPositionChange={setMascotPosition}
/>
```

Use `touch-action: none` on the interactive button while draggable so touch dragging works on mobile. Clamp to the viewport unless the app intentionally allows the mascot to leave the visible area.

## Reduced Motion

Respect the user preference:

```ts
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
```

When reduced motion is on, show frame 0 of the requested state or the idle state.
