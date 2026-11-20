"""Tests for Gemini Flash and AI Client logic."""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure src is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.gemma_client import GemmaClient, AIClient


class TestGemmaClient(unittest.TestCase):

    def test_client_initialization_defaults(self):
        client = GemmaClient(mode="cloud", api_key="dummy-key")
        self.assertEqual(client.mode, "cloud")
        self.assertEqual(client.cloud_model, "gemini-2.5-flash")
        self.assertIn("gemini-2.0-flash", client.cloud_model_fallbacks)
        self.assertEqual(client.api_key, "dummy-key")

    def test_alias(self):
        self.assertIs(AIClient, GemmaClient)

    def test_custom_cloud_model(self):
        client = GemmaClient(mode="gemini", api_key="dummy-key", cloud_model="gemini-2.0-flash")
        self.assertEqual(client.cloud_model, "gemini-2.0-flash")

    def test_active_provider_info(self):
        client = GemmaClient(mode="cloud", api_key="dummy-key")
        info = client.get_active_provider_info()
        self.assertEqual(info["mode"], "cloud")
        self.assertEqual(info["model"], "gemini-2.5-flash")
        self.assertTrue(info["has_gemini_key"])

    @patch("utils.gemma_client.genai")
    def test_cloud_dispatch_success(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Enhanced prompt output"
        mock_client.models.generate_content.return_value = mock_response

        client = GemmaClient(mode="cloud", api_key="test-key")
        result = client.enhance_prompt("Raw prompt", style="cinematic")

        self.assertEqual(result, "Enhanced prompt output")
        mock_client.models.generate_content.assert_called_once()
        args, kwargs = mock_client.models.generate_content.call_args
        self.assertEqual(kwargs["model"], "gemini-2.5-flash")
        self.assertEqual(kwargs["contents"], "Raw prompt")

    @patch("utils.gemma_client.genai")
    def test_cloud_json_mode_schema_pass(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = '{"score": 9, "reasoning": "great", "recommendation": "keep", "fixed_prompt": ""}'
        mock_client.models.generate_content.return_value = mock_response

        client = GemmaClient(mode="cloud", api_key="test-key")
        result = client.audit_prompt("Sample prompt")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["score"], 9)
        self.assertEqual(result["recommendation"], "keep")

        args, kwargs = mock_client.models.generate_content.call_args
        config = kwargs["config"]
        self.assertEqual(config.response_mime_type, "application/json")

    @patch("utils.gemma_client.genai")
    def test_cloud_model_fallback(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "Fallback success"

        # First call fails, second succeeds
        mock_client.models.generate_content.side_effect = [
            RuntimeError("Primary model quota exceeded"),
            mock_response,
        ]

        client = GemmaClient(mode="cloud", api_key="test-key")
        result = client.generate("Hello world")

        self.assertEqual(result, "Fallback success")
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    @patch("utils.gemma_client.genai")
    def test_character_markdown_prompt_generation(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "### Test Character\n**Gender:** F\n**Signature Color:** #123456"
        mock_client.models.generate_content.return_value = mock_response

        client = GemmaClient(mode="cloud", api_key="test-key")
        result = client.generate_character_markdown("A test warrior")

        self.assertIn("### Test Character", result)
        self.assertIn("**Gender:** F", result)

    @patch("utils.gemma_client.genai")
    def test_direct_scene(self, mock_genai):
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = '{"scene_description": "Rainy cafe", "action_notes": "Laughing over coffee", "color_pairing": "Maroon & Khaki", "director_notes": "Warm contrast"}'
        mock_client.models.generate_content.return_value = mock_response

        client = GemmaClient(mode="cloud", api_key="test-key")
        chars = [{"name": "Priya", "outfit": "Casual", "pose_preset": "Seated"}]
        result = client.direct_scene(chars, user_directive="Coffee chat with maroon and khaki contrast")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["scene_description"], "Rainy cafe")
        self.assertEqual(result["color_pairing"], "Maroon & Khaki")


if __name__ == "__main__":
    unittest.main()
