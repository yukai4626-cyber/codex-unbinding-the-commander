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

    def test_home_renders_before_browser_workspace_id_when_persistence_is_disabled(self):
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=10)
        stored_id = str(uuid.uuid4())

        with patch.object(components, "_browser_workspace_id", side_effect=[None, stored_id]):
            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertIn("main_nav_01", [button.key for button in app.sidebar.button])
            self.assertNotIn("workspace", app.query_params)
            self.assertNotIn("workspace_id", app.session_state)

            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertEqual(app.query_params["workspace"], [stored_id])
            self.assertEqual(app.session_state["workspace_id"], stored_id)

    def test_remote_restore_waits_for_browser_workspace_id(self):
        config.PERSISTENCE_ENABLED = True
        app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py", default_timeout=10)
        stored_id = str(uuid.uuid4())

        with (
            patch.object(components, "_browser_workspace_id", side_effect=[None, stored_id, stored_id]),
            patch.object(components, "_load_persistent_state", return_value={"nav_radio": "04"}) as restore,
            patch.object(components.requests, "put") as save,
        ):
            save.return_value.status_code = 200
            save.return_value.json.return_value = {"success": True}
            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertFalse(list(app.sidebar.button))
            restore.assert_not_called()
            save.assert_not_called()

            app.run()
            self.assertEqual(list(app.exception), [])
            self.assertEqual(app.session_state["nav_radio"], "04")
            self.assertEqual(app.session_state["workspace_id"], stored_id)

            app.run()
            self.assertEqual(list(app.exception), [])
            restore.assert_called_once_with(stored_id)

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
