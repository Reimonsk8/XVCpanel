import unittest
import os
import tempfile
from pathlib import Path

from xvcpanel.__main__ import add_local_tools
from xvcpanel.models.visual import Visual


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


if __name__ == "__main__":
    unittest.main()
