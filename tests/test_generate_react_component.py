import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATE_PATH = ROOT / "scripts" / "generate_react_component.py"

spec = importlib.util.spec_from_file_location("generate_react_component", GENERATE_PATH)
generate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(generate)


class GenerateReactComponentTests(unittest.TestCase):
    def test_component_supports_hover_and_dragging_interactions(self) -> None:
        manifest = {
            "id": "pointer-pal",
            "displayName": "Pointer Pal",
            "atlas": {
                "path": "atlas.webp",
                "width": 2048,
                "height": 864,
                "columns": 8,
                "rows": 3,
                "cellWidth": 256,
                "cellHeight": 288,
            },
            "states": {
                "idle": {"row": 0, "frames": 8, "durations": [150] * 8, "loop": True},
                "hover": {"row": 1, "frames": 8, "durations": [150] * 8, "loop": True},
                "dragging": {"row": 2, "frames": 8, "durations": [120] * 8, "loop": True},
            },
        }

        source = generate.component_source(manifest)

        self.assertIn("enableHoverState?: boolean", source)
        self.assertIn("draggable?: boolean", source)
        self.assertIn("onPositionChange?: (position: CompanionPosition) => void", source)
        self.assertIn('dragging && hasCompanionState("dragging")', source)
        self.assertIn('hovered && hasCompanionState("hover")', source)
        self.assertIn("onPointerDown={handlePointerDown}", source)
        self.assertIn("onPointerMove={handlePointerMove}", source)
        self.assertIn("touchAction: draggable ? \"none\" : undefined", source)

    def test_hook_maps_pointer_events_without_optional_working_state(self) -> None:
        source = generate.hook_source()

        self.assertIn('| "hover"', source)
        self.assertIn('| "dragging"', source)
        self.assertIn('case "drag-start":', source)
        self.assertIn('return "dragging";', source)
        self.assertIn('case "dropped":', source)
        self.assertIn('case "unclear":', source)
        self.assertIn('return "error";', source)
        self.assertIn('return "thinking";', source)
        self.assertNotIn('return "confused";', source)
        self.assertNotIn('return "working";', source)
