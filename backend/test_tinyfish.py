import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.tinyfish.service import TinyFishService


class TinyFishServiceTest(unittest.IsolatedAsyncioTestCase):
    async def test_run_requires_api_key(self):
        service = TinyFishService(api_key="")

        result = await service.run("https://example.com", "Read the page")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "TinyFish is not configured")

    @patch("app.infrastructure.tinyfish.service.httpx.AsyncClient")
    async def test_run_sends_expected_request(self, client_cls):
        response = MagicMock()
        response.json.return_value = {"status": "COMPLETED", "result": {"answer": "ok"}}
        response.raise_for_status.return_value = None

        client = AsyncMock()
        client.post.return_value = response
        client_cls.return_value.__aenter__.return_value = client

        service = TinyFishService(
            api_key="test-key",
            base_url="https://agent.example/v1/automation",
        )
        result = await service.run("https://example.com", "Read the page")

        self.assertEqual(result["status"], "COMPLETED")
        client.post.assert_awaited_once_with(
            "https://agent.example/v1/automation/run",
            headers={
                "X-API-Key": "test-key",
                "Content-Type": "application/json",
            },
            json={"url": "https://example.com", "goal": "Read the page"},
        )

    async def test_execute_validates_tool_arguments(self):
        service = TinyFishService(api_key="test-key")

        result = await service.execute("fetch_content", {})

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"], "URL is required")

    @patch("app.infrastructure.tinyfish.service.httpx.AsyncClient")
    async def test_run_normalizes_failed_terminal_status(self, client_cls):
        response = MagicMock()
        response.json.return_value = {"status": "FAILED", "error": "Blocked by site"}
        response.raise_for_status.return_value = None

        client = AsyncMock()
        client.post.return_value = response
        client_cls.return_value.__aenter__.return_value = client

        result = await TinyFishService(api_key="test-key").run(
            "https://example.com", "Read the page"
        )

        self.assertEqual(
            result,
            {
                "status": "error",
                "error": "Blocked by site",
                "run_status": "FAILED",
            },
        )


if __name__ == "__main__":
    unittest.main()
