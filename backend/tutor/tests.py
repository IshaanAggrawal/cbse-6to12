"""
tutor/tests.py — Tests for all major API endpoints.

All external calls (Groq, Pinecone) are mocked so tests run
fully offline without any API keys.

Run:
    python manage.py test tutor --verbosity=2
"""

from unittest.mock import MagicMock, patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status


class HealthCheckTest(TestCase):
    """GET /api/health/ should return 200 with {'status': 'ok'}."""

    def setUp(self):
        self.client = APIClient()

    def test_health_ok(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("service", data)


class AskViewTest(TestCase):
    """POST /api/ask/ — main tutor endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/ask/"

    @patch("tutor.views.retrieve_context", return_value=[])
    @patch("tutor.views.stream_response")
    def test_ask_streaming_returns_200(self, mock_stream, mock_retrieve):
        """Valid question returns 200 streaming response."""
        mock_stream.return_value = iter(["Hello", " world"])

        response = self.client.post(self.url, {
            "question": "What is photosynthesis?",
            "stream": True,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/plain")

    @patch("tutor.views.retrieve_context", return_value=[])
    @patch("tutor.views.get_response", return_value=("Photosynthesis is…", "llama-3.1-8b-instant"))
    def test_ask_non_streaming_returns_200(self, mock_get, mock_retrieve):
        """stream=False returns a JSON response with answer field."""
        response = self.client.post(self.url, {
            "question": "What is photosynthesis?",
            "stream": False,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("answer", data)
        self.assertIn("from_cache", data)

    def test_ask_missing_question_returns_400(self):
        """Missing question field should fail validation."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ask_question_too_short_returns_400(self):
        """Single-char question is too short (min_length=2)."""
        response = self.client.post(self.url, {"question": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ask_invalid_class_returns_400(self):
        """class_no must be between 6–12."""
        response = self.client.post(self.url, {
            "question": "Explain gravity",
            "class_no": 15,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("tutor.views.retrieve_context", return_value=[])
    @patch("tutor.views.stream_response")
    def test_ask_with_class_and_subject(self, mock_stream, mock_retrieve):
        """Question with class_no and subject filters should work."""
        mock_stream.return_value = iter(["Newton's 2nd law…"])

        response = self.client.post(self.url, {
            "question": "Explain Newton's 2nd law",
            "class_no": 9,
            "subject": "science",
            "language": "english",
            "stream": True,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # retrieve_context should have been called with the right args
        mock_retrieve.assert_called_once_with("Explain Newton's 2nd law", 9, "science")

    @patch("tutor.views.cache")
    @patch("tutor.views.retrieve_context")
    def test_asks_returns_cached_answer(self, mock_retrieve, mock_cache):
        """If answer is in cache, it should be returned without calling LLM."""
        mock_cache.get.return_value = "Cached photosynthesis answer"

        response = self.client.post(self.url, {
            "question": "What is photosynthesis?",
            "stream": False,
        }, format="json")

        # retrieve_context must NOT be called when cached
        mock_retrieve.assert_not_called()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DoubtHistoryTest(TestCase):
    """GET /api/doubts/ — recent doubt history."""

    def setUp(self):
        self.client = APIClient()

    def test_doubts_list_returns_200(self):
        response = self.client.get("/api/doubts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)

    def test_doubts_filtered_by_class(self):
        response = self.client.get("/api/doubts/?class_no=10")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_doubts_filtered_by_subject(self):
        response = self.client.get("/api/doubts/?subject=science")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StudentAPITest(TestCase):
    """POST & GET /api/students/"""

    def setUp(self):
        self.client = APIClient()

    def test_create_student(self):
        response = self.client.post("/api/students/", {
            "name": "Ravi Kumar",
            "class_no": 10,
            "subject": "science",
            "language": "hindi",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["name"], "Ravi Kumar")

    def test_list_students(self):
        response = self.client.get("/api/students/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class KnowledgeStatsTest(TestCase):
    """GET /api/knowledge/stats/ — with mocked Pinecone."""

    def setUp(self):
        self.client = APIClient()

    @patch("knowledge.views.Pinecone")
    def test_knowledge_stats_returns_200(self, MockPinecone):
        mock_index = MagicMock()
        mock_index.describe_index_stats.return_value = {"total_vector_count": 1234}
        MockPinecone.return_value.Index.return_value = mock_index

        response = self.client.get("/api/knowledge/stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("total_vectors", data)
        self.assertEqual(data["total_vectors"], 1234)

    @patch("knowledge.views.Pinecone", side_effect=Exception("No API key"))
    def test_knowledge_stats_503_when_pinecone_fails(self, _):
        response = self.client.get("/api/knowledge/stats/")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
