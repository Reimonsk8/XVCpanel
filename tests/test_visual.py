import unittest
from pathlib import Path

from xvcpanel.models.visual import Visual


class VisualManifestTest(unittest.TestCase):
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
