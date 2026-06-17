"""
Tool for fetching recent crypto news and headlines from NewsAPI.
"""

import logging
from typing import Any, Dict, List

import httpx

from src.config import Config
from src.utils.retry import retry_async

logger = logging.getLogger(__name__)


class NewsProvider:
    """
    Aggregates news headlines from NewsAPI.
    """

    BASE_URL = "https://newsapi.org/v2/everything"

    @retry_async(retries=3, delay=1.0)
    async def get_latest_headlines(self) -> List[Dict[str, Any]]:
        """
        Fetches the most recent news headlines for crypto.
        """
        api_key = Config.NEWS_API_KEY

        if not api_key:
            logger.warning("NEWS_API_KEY not found. Using mock news data.")
            return self._get_mock_headlines()

        try:
            params = {
                "apiKey": api_key,
                "q": "cryptocurrency",
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": "10",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

            articles = data.get("articles", [])
            headlines = []

            for item in articles:
                headlines.append(
                    {
                        "title": item.get("title"),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        # NewsAPI doesn't provide sentiment; defaulting to neutral
                        "sentiment": "neutral",
                        "url": item.get("url"),
                    }
                )

            return headlines if headlines else self._get_mock_headlines()

        except Exception as e:
            logger.error("Failed to fetch news from NewsAPI: %s", e)
            return self._get_mock_headlines()

    def _get_mock_headlines(self) -> List[Dict[str, Any]]:
        """Fallback mock data."""
        return [
            {
                "title": "SEC Approves New Ethereum Staking ETP",
                "source": "MockDaily",
                "sentiment": "bullish",
            },
            {
                "title": "Solana Transaction Volume Hits All-Time High",
                "source": "MockDaily",
                "sentiment": "bullish",
            },
            {
                "title": "Macro Concerns: Fed Signals Potential Rate Hike",
                "source": "MockDaily",
                "sentiment": "bearish",
            },
        ]
