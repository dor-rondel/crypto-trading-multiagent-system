"""
Tests for the News Provider.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tools.news_provider import NewsProvider


@pytest.mark.asyncio
async def test_news_provider_success():
    """
    Test successful data fetch from NewsAPI.
    """
    provider = NewsProvider()

    # Mocking response
    mock_response = {
        "articles": [
            {
                "title": "Bullish News",
                "source": {"name": "TestSource"},
                "url": "http://test.com",
            }
        ]
    }

    with patch("src.config.Config.NEWS_API_KEY", "test_key"):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_res = MagicMock()
            mock_res.json.return_value = mock_response
            mock_res.raise_for_status = lambda: None
            mock_get.return_value = mock_res

            headlines = await provider.get_latest_headlines()

            assert len(headlines) == 1
            assert headlines[0]["title"] == "Bullish News"
            assert headlines[0]["source"] == "TestSource"


@pytest.mark.asyncio
async def test_news_provider_fallback_on_failure():
    """
    Test NewsProvider falling back to mock data on API failure.
    """
    provider = NewsProvider()

    with patch("src.config.Config.NEWS_API_KEY", "test_key"):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_res = MagicMock()
            mock_res.raise_for_status.side_effect = Exception("API Failure")
            mock_get.return_value = mock_res

            headlines = await provider.get_latest_headlines()

            # Should fall back to mock data (length 3)
            assert len(headlines) == 3
            assert headlines[0]["source"] == "MockDaily"
