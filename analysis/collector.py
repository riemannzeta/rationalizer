"""
Data Collection Module - Fetches articles from RSS feeds and news APIs.
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re


class NewsSource:
    """Represents a news source with its RSS feed."""

    def __init__(self, name: str, feed_url: str, domain: str):
        self.name = name
        self.feed_url = feed_url
        self.domain = domain


# Diverse news sources across the political spectrum and topic areas
NEWS_SOURCES = [
    # General News
    NewsSource("BBC News", "http://feeds.bbci.co.uk/news/rss.xml", "bbc.com"),
    NewsSource("Reuters", "https://www.reutersagency.com/feed/", "reuters.com"),
    NewsSource("The Guardian", "https://www.theguardian.com/world/rss", "theguardian.com"),
    NewsSource("NPR News", "https://feeds.npr.org/1001/rss.xml", "npr.org"),
    NewsSource("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", "aljazeera.com"),
    NewsSource("The Hill", "https://thehill.com/feed/", "thehill.com"),
    NewsSource("Axios", "https://api.axios.com/feed/", "axios.com"),

    # Politics & Policy
    NewsSource("Politico", "https://www.politico.com/rss/politics08.xml", "politico.com"),
    NewsSource("The Washington Post", "https://feeds.washingtonpost.com/rss/politics", "washingtonpost.com"),
    NewsSource("CNN Politics", "http://rss.cnn.com/rss/cnn_allpolitics.rss", "cnn.com"),

    # Business & Economy
    NewsSource("Bloomberg", "https://feeds.bloomberg.com/markets/news.rss", "bloomberg.com"),
    NewsSource("Financial Times", "https://www.ft.com/?format=rss", "ft.com"),
    NewsSource("Wall Street Journal", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "wsj.com"),
    NewsSource("Forbes", "https://www.forbes.com/real-time/feed2/", "forbes.com"),

    # Technology
    NewsSource("TechCrunch", "https://techcrunch.com/feed/", "techcrunch.com"),
    NewsSource("Ars Technica", "http://feeds.arstechnica.com/arstechnica/index", "arstechnica.com"),
    NewsSource("The Verge", "https://www.theverge.com/rss/index.xml", "theverge.com"),
    NewsSource("WIRED", "https://www.wired.com/feed/rss", "wired.com"),

    # Science & Environment
    NewsSource("Scientific American", "http://rss.sciam.com/ScientificAmerican-Global", "scientificamerican.com"),
    NewsSource("Nature News", "http://feeds.nature.com/nature/rss/current", "nature.com"),
    NewsSource("Grist", "https://grist.org/feed/", "grist.org"),

    # Health
    NewsSource("STAT News", "https://www.statnews.com/feed/", "statnews.com"),
    NewsSource("Health Affairs", "https://www.healthaffairs.org/do/10.1377/hp.rss/full/", "healthaffairs.org"),

    # Energy
    NewsSource("E&E News", "https://www.eenews.net/rss/", "eenews.net"),
    NewsSource("Utility Dive", "https://www.utilitydive.com/feeds/news/", "utilitydive.com"),
]


class ArticleCollector:
    """Collects articles from various news sources."""

    def __init__(self, months_back: int = 6):
        """
        Initialize the collector.

        Args:
            months_back: How many months of articles to collect (default: 6)
        """
        self.months_back = months_back
        self.cutoff_date = datetime.now() - timedelta(days=30 * months_back)

    def fetch_rss_feed(self, source: NewsSource, max_articles: int = 100) -> List[Dict]:
        """
        Fetch articles from an RSS feed.

        Args:
            source: The NewsSource to fetch from
            max_articles: Maximum number of articles to fetch

        Returns:
            List of article dictionaries
        """
        articles = []

        try:
            print(f"Fetching from {source.name}...")
            feed = feedparser.parse(source.feed_url)

            for entry in feed.entries[:max_articles]:
                # Parse publication date
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])

                # Skip articles older than our cutoff
                if pub_date and pub_date < self.cutoff_date:
                    continue

                # Extract article data
                article = {
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'publication': source.name,
                    'domain': source.domain,
                    'published_date': pub_date,
                    'summary': entry.get('summary', ''),
                    'author': self._extract_author(entry),
                }

                articles.append(article)

            print(f"  ✓ Fetched {len(articles)} articles from {source.name}")

        except Exception as e:
            print(f"  ✗ Error fetching from {source.name}: {str(e)}")

        return articles

    def _extract_author(self, entry) -> Optional[str]:
        """Extract author name from RSS entry."""
        # Try different author fields
        if hasattr(entry, 'author') and entry.author:
            return self._clean_author_name(entry.author)

        if hasattr(entry, 'authors') and entry.authors:
            return self._clean_author_name(entry.authors[0].get('name', ''))

        # Try to find author in content
        if hasattr(entry, 'content'):
            for content in entry.content:
                author = self._extract_author_from_text(content.get('value', ''))
                if author:
                    return author

        return None

    def _clean_author_name(self, name: str) -> str:
        """Clean and normalize author names."""
        # Remove email addresses
        name = re.sub(r'\s*<[^>]+>', '', name)
        name = re.sub(r'\([^)]*\)', '', name)

        # Remove common prefixes
        name = re.sub(r'^(By|by)\s+', '', name)

        # Clean whitespace
        name = ' '.join(name.split())

        return name.strip()

    def _extract_author_from_text(self, text: str) -> Optional[str]:
        """Try to extract author from article text."""
        # Look for "By Author Name" patterns
        patterns = [
            r'[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'[Aa]uthor:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return self._clean_author_name(match.group(1))

        return None

    def fetch_article_content(self, url: str) -> Optional[str]:
        """
        Fetch the full article content from a URL.

        Args:
            url: The article URL

        Returns:
            Article text content or None
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'header', 'footer']):
                script.decompose()

            # Try to find article content
            article_content = None

            # Look for common article containers
            for selector in ['article', '.article-body', '.story-body', 'main']:
                content = soup.select_one(selector)
                if content:
                    article_content = content
                    break

            if not article_content:
                article_content = soup.body

            if article_content:
                # Extract text from paragraphs
                paragraphs = article_content.find_all('p')
                text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                return text

        except Exception as e:
            print(f"  ✗ Error fetching content from {url}: {str(e)}")

        return None

    def collect_all(self, max_per_source: int = 100, fetch_content: bool = True) -> List[Dict]:
        """
        Collect articles from all configured news sources.

        Args:
            max_per_source: Maximum articles per source
            fetch_content: Whether to fetch full article content (slower)

        Returns:
            List of all collected articles
        """
        all_articles = []

        print(f"\n📰 Collecting articles from {len(NEWS_SOURCES)} sources...")
        print(f"   Cutoff date: {self.cutoff_date.strftime('%Y-%m-%d')}\n")

        for source in NEWS_SOURCES:
            articles = self.fetch_rss_feed(source, max_per_source)

            # Fetch full content if requested
            if fetch_content:
                for i, article in enumerate(articles):
                    if i % 10 == 0:
                        print(f"  Fetching content {i+1}/{len(articles)}...")

                    content = self.fetch_article_content(article['url'])
                    article['content'] = content or article['summary']

                    # Be respectful with rate limiting
                    time.sleep(0.5)
            else:
                # Use summary as content
                for article in articles:
                    article['content'] = article['summary']

            all_articles.extend(articles)
            time.sleep(1)  # Rate limiting between sources

        print(f"\n✓ Collected {len(all_articles)} total articles")

        # Filter out articles without authors
        articles_with_authors = [a for a in all_articles if a.get('author')]
        print(f"✓ {len(articles_with_authors)} articles have identified authors")

        return articles_with_authors


def collect_news_data(months_back: int = 12, max_per_source: int = 1000) -> List[Dict]:
    """
    Main function to collect news data.

    Args:
        months_back: How many months of data to collect (default: 12)
        max_per_source: Maximum articles per source (default: 1000)

    Returns:
        List of article dictionaries
    """
    collector = ArticleCollector(months_back=months_back)
    return collector.collect_all(max_per_source=max_per_source, fetch_content=False)
