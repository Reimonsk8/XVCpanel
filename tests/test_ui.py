import unittest
from pathlib import Path

from textual.widgets import DataTable

from xvcpanel.ui.tui import XVCpanel


class AppStartupTest(unittest.IsolatedAsyncioTestCase):
    async def test_library_loads_in_control_surface(self):
        app = XVCpanel(Path("library"))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            self.assertGreaterEqual(len(app.visuals), 8)
            self.assertEqual(app.query_one("#visual-table", DataTable).row_count, len(app.visuals))


if __name__ == "__main__":
    unittest.main()
