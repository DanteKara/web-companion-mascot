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
  onClick?: () => void;
};
```

## Animation Logic

Use JavaScript timers for frame durations. CSS `steps()` is fine only when every frame in a row has the same duration.

Core loop:

```ts
useEffect(() => {
  if (paused || prefersReducedMotion) return;
  const animation = manifest.states[state] ?? manifest.states.idle;
  const duration = animation.durations[frame] ?? 150;
  const timer = window.setTimeout(() => {
    setFrame((current) => (current + 1) % animation.frames);
  }, duration);
  return () => window.clearTimeout(timer);
}, [state, frame, paused, prefersReducedMotion, manifest]);
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
export function toCompanionState(status: ChatStatus): string {
  switch (status) {
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
    default:
      return "idle";
  }
}
```

## Reduced Motion

Respect the user preference:

```ts
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
```

When reduced motion is on, show frame 0 of the requested state or the idle state.
