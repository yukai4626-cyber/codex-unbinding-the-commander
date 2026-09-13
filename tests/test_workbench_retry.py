import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pages


class WorkbenchRetryTests(unittest.TestCase):
    def test_gateway_502_retries_once_with_compact_prompt(self):
        fallback = {"lesson_md": "示例"}
        success = {
            "answer": "精炼教案",
            "agent_type": "lesson_design",
            "_real_response": True,
        }
        fake_st = SimpleNamespace(
            session_state={
                "backend_incident": {"status_code": 502},
                "backend_status": ("bad_response", "HTTP 502"),
            }
        )

        def is_agent_response(value):
            return isinstance(value, dict) and value.get("_real_response") is True

        with (
            patch.object(pages, "st", fake_st),
            patch.object(pages.config, "MOCK_MODE", False),
            patch.object(pages.comp, "is_agent_response", side_effect=is_agent_response),
            patch.object(pages.comp, "api_gate", side_effect=[fallback, success]) as api_gate,
        ):
            result = pages._call_workbench_agent("完整请求", "精炼请求", fallback)

        self.assertEqual(result, success)
        self.assertEqual(api_gate.call_count, 2)
        self.assertEqual(api_gate.call_args_list[1].args[1]["question"], "精炼请求")
        self.assertIn("已自动改用精炼生成", fake_st.session_state["backend_status"][1])

    def test_non_retryable_error_does_not_retry(self):
        fallback = {"lesson_md": "示例"}
        fake_st = SimpleNamespace(
            session_state={"backend_incident": {"status_code": 400}}
        )
        with (
            patch.object(pages, "st", fake_st),
            patch.object(pages.config, "MOCK_MODE", False),
            patch.object(pages.comp, "is_agent_response", return_value=False),
            patch.object(pages.comp, "api_gate", return_value=fallback) as api_gate,
        ):
            result = pages._call_workbench_agent("完整请求", "精炼请求", fallback)

        self.assertEqual(result, fallback)
        api_gate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
