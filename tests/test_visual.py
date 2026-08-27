import unittest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from xvcpanel.__main__ import add_local_tools
from xvcpanel.loader.runner import _minimal_path
from xvcpanel.models.visual import Framework, Visual


class VisualManifestTest(unittest.TestCase):
    def test_local_tools_are_added_to_path(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory, ".tools", "runtime", "tool.exe")
            executable.parent.mkdir(parents=True)
            executable.touch()
            original = os.environ.get("PATH", "")
            try:
                add_local_tools(Path(directory))
                self.assertIn(str(executable.parent), os.environ["PATH"].split(os.pathsep))
            finally:
                os.environ["PATH"] = original

    def test_outputs_and_parameters_are_parsed_and_clamped(self):
        visual = Visual.from_dict({
            "name": "Test",
            "outputs": [
                {"name": "Preview"},
                {"name": "Resolume", "protocol": "spout", "run_cmd": "run-spout"},
            ],
            "osc": {"port": 9001},
            "parameters": [{
                "name": "Speed", "address": "/speed", "min": 0, "max": 2, "default": 1,
            }],
        }, Path("."))

        self.assertEqual(visual.select_next_output().protocol, "spout")
        self.assertEqual(visual.osc_port, 9001)
        visual.parameters[0].set_value(3)
        self.assertEqual(visual.parameters[0].value, 2)

    def test_vj_framework_labels_are_parsed(self):
        visual = Visual.from_dict({"framework": "touchdesigner"}, Path("."))
        self.assertEqual(visual.framework, Framework.TOUCHDESIGNER)

    def test_runner_path_finds_project_local_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tool = root / ".tools" / "glslViewer" / "glslViewer.exe"
            tool.parent.mkdir(parents=True)
            tool.touch()
            visual_path = root / "library" / "glsl" / "effect"
            visual_path.mkdir(parents=True)
            with patch("xvcpanel.loader.runner.IS_WINDOWS", True):
                self.assertIn(str(tool.parent), _minimal_path(visual_path).split(";"))


if __name__ == "__main__":
    unittest.main()
