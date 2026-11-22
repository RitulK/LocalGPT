import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.services.obsidian_service import (
    ObsidianService,
    normalize_vault_path,
    validate_write_path,
)


class ObsidianPathTest(unittest.TestCase):
    def test_normalize_rejects_traversal_and_config_folder(self):
        with self.assertRaises(ValueError):
            normalize_vault_path("../private.md")
        with self.assertRaises(ValueError):
            normalize_vault_path(".obsidian/plugins/data.json")

    def test_write_path_is_limited_to_allowed_folder(self):
        self.assertEqual(
            validate_write_path("BuddyAI/Notes/Test.md", "BuddyAI/"),
            "BuddyAI/Notes/Test.md",
        )
        with self.assertRaises(ValueError):
            validate_write_path("Private/Test.md", "BuddyAI/")

    def test_open_requires_read_permission(self):
        service = ObsidianService({
            "obsidian_api_address": "https://127.0.0.1:27124",
            "obsidian_api_key": "test-key",
            "obsidian_verify_tls": True,
            "obsidian_allow_read": False,
        })

        with self.assertRaisesRegex(ValueError, "read permission"):
            asyncio.run(service.open("BuddyAI/Test.md"))

    def test_connection_requires_configured_api_key(self):
        service = ObsidianService({
            "obsidian_api_address": "https://127.0.0.1:27124",
            "obsidian_api_key": "",
            "obsidian_verify_tls": True,
        })

        with self.assertRaisesRegex(ValueError, "API key is not configured"):
            asyncio.run(service.test_connection())

    def test_connection_reports_certificate_verification_failure(self):
        service = ObsidianService({
            "obsidian_api_address": "https://127.0.0.1:27124",
            "obsidian_api_key": "test-key",
            "obsidian_verify_tls": True,
        })
        ssl_error = httpx.ConnectError(
            "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed"
        )

        with patch("app.services.obsidian_service.httpx.AsyncClient") as client_class:
            client = MagicMock()
            client.get = AsyncMock(side_effect=ssl_error)
            client_class.return_value.__aenter__ = AsyncMock(return_value=client)
            client_class.return_value.__aexit__ = AsyncMock(return_value=None)

            with self.assertRaisesRegex(ValueError, "certificate verification failed"):
                asyncio.run(service.test_connection())


if __name__ == "__main__":
    unittest.main()
