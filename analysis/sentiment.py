"""
Sentiment Analysis Module - Analyzes emotional valence of articles.
"""

from typing import List, Dict, Optional
from transformers import pipeline
import re


class SentimentAnalyzer:
    """Analyzes sentiment and emotional valence of articles."""

    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """
        Initialize the sentiment analyzer.

        Args:
            model_name: Hugging Face model to use for sentiment analysis
        """
        self.model_name = model_name
        self.analyzer = None
        self._load_model()

    def _load_model(self):
        """Load the sentiment analysis model."""
        try:
            print(f"Loading sentiment analysis model: {self.model_name}...")
            self.analyzer = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                max_length=512,
                truncation=True
            )
            print("✓ Sentiment model loaded successfully")
        except Exception as e:
            print(f"✗ Could not load sentiment model: {e}")
            self.analyzer = None

    def _normalize_sentiment_score(self, label: str, score: float) -> float:
        """
        Convert sentiment label and score to normalized valence (-1 to +1).

        Args:
            label: Sentiment label (e.g., 'positive', 'negative', 'neutral')
            score: Confidence score (0-1)

        Returns:
            Normalized valence score (-1 to +1)
        """
        label_lower = label.lower()

        if 'positive' in label_lower or label_lower == 'label_2':
            # Positive sentiment: 0 to +1
            return score
        elif 'negative' in label_lower or label_lower == 'label_0':
            # Negative sentiment: 0 to -1
            return -score
        else:
            # Neutral sentiment: close to 0
            return 0.0

    def analyze_text(self, text: str, max_length: int = 2000) -> Dict:
        """
        Analyze sentiment of a text.

        Args:
            text: Text to analyze
            max_length: Maximum text length to process

        Returns:
            Dictionary with sentiment analysis results
        """
        if not self.analyzer or not text:
            return {
                'valence': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'error': 'No analyzer available or empty text'
            }

        # Clean and truncate text
        text = self._clean_text(text[:max_length])

        if len(text) < 10:
            return {
                'valence': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'error': 'Text too short'
            }

        try:
            result = self.analyzer(text)[0]

            valence = self._normalize_sentiment_score(
                result['label'],
                result['score']
            )

            return {
                'valence': round(valence, 4),
                'label': result['label'],
                'confidence': round(result['score'], 4),
                'error': None
            }

        except Exception as e:
            return {
                'valence': 0.0,
                'label': 'neutral',
                'confidence': 0.0,
                'error': str(e)
            }

    def _clean_text(self, text: str) -> str:
        """Clean text for sentiment analysis."""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze sentiment of an article.

        Args:
            article: Article dictionary with 'title' and 'content'

        Returns:
            Article with added sentiment analysis results
        """
        title = article.get('title', '')
        content = article.get('content', '') or article.get('summary', '')

        # Analyze title (often more emotionally charged)
        title_sentiment = self.analyze_text(title, max_length=200)

        # Analyze content
        # For long articles, analyze the beginning (often sets tone)
        content_sentiment = self.analyze_text(content, max_length=2000)

        # Combined score (weighted average: 30% title, 70% content)
        combined_valence = (
            0.3 * title_sentiment['valence'] +
            0.7 * content_sentiment['valence']
        )

        # Add sentiment data to article
        article['sentiment'] = {
            'overall_valence': round(combined_valence, 4),
            'title_valence': title_sentiment['valence'],
            'content_valence': content_sentiment['valence'],
            'title_label': title_sentiment['label'],
            'content_label': content_sentiment['label'],
            'confidence': round(
                (title_sentiment['confidence'] + content_sentiment['confidence']) / 2,
                4
            )
        }

        return article

    def analyze_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Analyze sentiment for a batch of articles.

        Args:
            articles: List of article dictionaries

        Returns:
            Articles with added sentiment analysis
        """
        if not self.analyzer:
            print("✗ No sentiment analyzer available")
            return articles

        print(f"\n💭 Analyzing sentiment for {len(articles)} articles...")

        analyzed = []

        for i, article in enumerate(articles):
            if i % 20 == 0:
                print(f"  Processing {i+1}/{len(articles)}...")

            analyzed_article = self.analyze_article(article)
            analyzed.append(analyzed_article)

        # Print statistics
        valences = [
            a['sentiment']['overall_valence']
            for a in analyzed
            if 'sentiment' in a
        ]

        if valences:
            avg_valence = sum(valences) / len(valences)
            positive = sum(1 for v in valences if v > 0.1)
            negative = sum(1 for v in valences if v < -0.1)
            neutral = len(valences) - positive - negative

            print(f"\n✓ Sentiment analysis complete")
            print(f"  Average valence: {avg_valence:.3f}")
            print(f"  Positive: {positive} | Neutral: {neutral} | Negative: {negative}")

        return analyzed


def analyze_sentiment(
    articles: List[Dict],
    model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
) -> List[Dict]:
    """
    Main function to analyze article sentiment.

    Args:
        articles: List of article dictionaries
        model_name: Hugging Face model to use

    Returns:
        Articles with sentiment analysis added
    """
    analyzer = SentimentAnalyzer(model_name=model_name)
    return analyzer.analyze_batch(articles)
