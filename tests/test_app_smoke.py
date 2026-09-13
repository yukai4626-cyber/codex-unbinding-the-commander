import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import components
import config


class AppSmokeTests(unittest.TestCase):
    def setUp(self):
        self.old_mock_mode = config.MOCK_MODE
        self.old_persistence = config.PERSISTENCE_ENABLED
        config.MOCK_MODE = False
        config.PERSISTENCE_ENABLED = False

    def tearDown(self):
        config.MOCK_MODE = self.old_mock_mode
        config.PERSISTENCE_ENABLED = self.old_persistence

    def test_all_navigation_pages_render_without_persistence_network(self):
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=10)
        app.query_params["workspace"] = str(uuid.uuid4())
        with patch.object(components.requests, "get") as get_mock, patch.object(components.requests, "put") as put_mock:
            app.run()
            self.assertEqual(list(app.exception), [])
            expected_labels = [item["name"] for item in config.NAV_ITEMS]
            for label in expected_labels:
                buttons = {button.label: button for button in app.sidebar.button}
                self.assertIn(label, buttons)
                buttons[label].click()
                app.run()
                self.assertEqual(list(app.exception), [], label)
        get_mock.assert_not_called()
        put_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
