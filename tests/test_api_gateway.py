import copy
import time
import unittest
from contextlib import nullcontext
from unittest.mock import Mock, patch

import requests

import components
import config


class _FakeStreamlit:
    def __init__(self):
        self.session_state = {}

    @staticmethod
    def spinner(_message):
        return nullcontext()


class _Response:
    def __init__(self, status_code=200, data=None, headers=None, json_error=False):
        self.status_code = status_code
        self._data = data
        self.headers = headers or {}
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("invalid json")
        return copy.deepcopy(self._data)


class ApiGatewayTests(unittest.TestCase):
    def setUp(self):
        self.fake_st = _FakeStreamlit()
        self.st_patch = patch.object(components, "st", self.fake_st)
        self.st_patch.start()
        self.old_config = {
            "MOCK_MODE": config.MOCK_MODE,
            "PERSISTENCE_ENABLED": config.PERSISTENCE_ENABLED,
            "SESSION_REQUESTS_PER_HOUR": config.SESSION_REQUESTS_PER_HOUR,
            "MIN_REQUEST_INTERVAL_SECONDS": config.MIN_REQUEST_INTERVAL_SECONDS,
        }
        config.MOCK_MODE = False
        config.PERSISTENCE_ENABLED = False
        config.SESSION_REQUESTS_PER_HOUR = 20
        config.MIN_REQUEST_INTERVAL_SECONDS = 0

    def tearDown(self):
        self.st_patch.stop()
        for key, value in self.old_config.items():
            setattr(config, key, value)

    def _call(self, agent_type="learning_support", question="测试问题", mock_result=None):
        return components.api_gate(
            "/api/agent-chat",
            {"question": question, "agent_type": agent_type},
            {"mock": True} if mock_result is None else mock_result,
        )

    def test_all_agent_types_accept_valid_contract(self):
        for agent_type in config.AGENT_TYPES.values():
            with self.subTest(agent_type=agent_type):
                response = _Response(
                    data={"answer": "服务可用", "agent_type": agent_type, "sources": ["课程标准"]},
                    headers={"X-Fc-Request-Id": "fc-test-id"},
                )
                with patch.object(components.requests, "request", return_value=response):
                    result = self._call(agent_type=agent_type)
                self.assertTrue(result["_real_response"])
                self.assertEqual(result["agent_type"], agent_type)
                self.assertEqual(self.fake_st.session_state["backend_status"][0], "ok")
                self.assertIsNone(self.fake_st.session_state["backend_incident"])

    def test_timeout_records_safe_incident_without_question(self):
        secret_question = "课堂材料-不得写入日志"
        with self.assertLogs("stem.backend", level="WARNING") as captured:
            with patch.object(components.requests, "request", side_effect=requests.Timeout("upstream secret")):
                result = self._call(question=secret_question)
        self.assertEqual(result, {"mock": True})
        self.assertEqual(self.fake_st.session_state["backend_status"][0], "down")
        self.assertNotIn(secret_question, "\n".join(captured.output))
        self.assertNotIn("upstream secret", "\n".join(captured.output))

    def test_connection_failure_records_safe_incident(self):
        with patch.object(components.requests, "request", side_effect=requests.ConnectionError("private network detail")):
            result = self._call()
        self.assertEqual(result, {"mock": True})
        self.assertEqual(self.fake_st.session_state["backend_incident"]["kind"], "ConnectionError")
        self.assertNotIn("private network detail", self.fake_st.session_state["backend_status"][1])

    def test_http_error_uses_safe_detail_and_request_id(self):
        for status_code in (400, 503):
            with self.subTest(status_code=status_code):
                self.fake_st.session_state.clear()
                response = _Response(
                    status_code=status_code,
                    data={"detail": "模型服务暂时不可用"},
                    headers={"X-Fc-Request-Id": f"fc-{status_code}-id"},
                )
                with patch.object(components.requests, "request", return_value=response):
                    result = self._call()
                self.assertEqual(result, {"mock": True})
                incident = self.fake_st.session_state["backend_incident"]
                self.assertEqual(incident["status_code"], status_code)
                self.assertEqual(incident["request_id"], f"fc-{status_code}-id")
                self.assertIn("模型服务暂时不可用", self.fake_st.session_state["backend_status"][1])

    def test_http_200_business_error_is_rejected(self):
        response = _Response(status_code=200, data={"success": False, "detail": "暂时不可用"})
        with patch.object(components.requests, "request", return_value=response):
            result = self._call()
        self.assertEqual(result, {"mock": True})
        self.assertIn("暂时不可用", self.fake_st.session_state["backend_status"][1])

    def test_html_error_detail_is_not_echoed(self):
        response = _Response(status_code=500, data={"detail": "<html>internal</html>"})
        with patch.object(components.requests, "request", return_value=response):
            self._call()
        self.assertNotIn("<html>", self.fake_st.session_state["backend_status"][1])

    def test_invalid_json_is_reported(self):
        response = _Response(status_code=200, json_error=True)
        with patch.object(components.requests, "request", return_value=response):
            self._call()
        self.assertIn("无法解析", self.fake_st.session_state["backend_status"][1])

    def test_empty_answer_and_agent_mismatch_are_contract_errors(self):
        cases = [
            {"answer": "", "agent_type": "learning_support"},
            {"answer": "有效", "agent_type": "lesson_design"},
            {"answer": "有效", "agent_type": "learning_support", "sources": [1]},
        ]
        for data in cases:
            with self.subTest(data=data):
                self.fake_st.session_state.clear()
                with patch.object(components.requests, "request", return_value=_Response(data=data)):
                    self._call()
                self.assertEqual(self.fake_st.session_state["backend_status"][0], "bad_response")
                self.assertIn("字段异常", self.fake_st.session_state["backend_status"][1])

    def test_twenty_first_request_is_rate_limited(self):
        now = time.time()
        self.fake_st.session_state["backend_request_times"] = [now - index for index in range(20)]
        with patch.object(components.requests, "request") as request_mock:
            result = self._call()
        request_mock.assert_not_called()
        self.assertEqual(result, {"mock": True})
        self.assertEqual(self.fake_st.session_state["backend_status"][0], "rate_limited")

    def test_minimum_interval_and_in_flight_lock(self):
        now = time.time()
        config.MIN_REQUEST_INTERVAL_SECONDS = 3
        self.fake_st.session_state["backend_request_times"] = [now]
        self.assertIn("请求过于频繁", components._begin_backend_request(now + 1))
        self.fake_st.session_state["backend_request_times"] = []
        self.fake_st.session_state["backend_request_started_at"] = now
        self.assertIn("正在处理", components._begin_backend_request(now + 1))

    def test_disabled_persistence_never_calls_network(self):
        with patch.object(components.requests, "get") as get_mock:
            self.assertIsNone(components._load_persistent_state("00000000-0000-0000-0000-000000000000"))
        get_mock.assert_not_called()
        with patch.object(components.requests, "put") as put_mock:
            self.assertFalse(components._save_persistent_state())
        put_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
