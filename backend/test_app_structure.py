import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from main import app


class AppStructureTest(unittest.TestCase):
    def test_root_endpoint_remains_available(self):
        with TestClient(app) as client:
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "online")

    def test_expected_api_modules_exist(self):
        api_dir = Path(__file__).parent / "app" / "api"
        expected = {
            "chat.py",
            "conversations.py",
            "documents.py",
            "memories.py",
            "models.py",
            "settings.py",
            "health.py",
            "deps.py",
        }

        self.assertTrue(expected.issubset({path.name for path in api_dir.iterdir()}))

    def test_main_contains_no_app_route_decorators(self):
        main_source = (Path(__file__).parent / "main.py").read_text()

        self.assertLessEqual(len(main_source.splitlines()), 60)
        self.assertNotIn("@app.", main_source)


if __name__ == "__main__":
    unittest.main()
