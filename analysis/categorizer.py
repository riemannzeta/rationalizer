"""
Article Categorization Module - Classifies articles into topic categories.
"""

from typing import List, Dict, Tuple
from transformers import pipeline
import re


# Topic categories and their associated keywords
CATEGORIES = {
    'nuclear_energy': {
        'label': 'Nuclear Energy',
        'keywords': [
            'nuclear', 'reactor', 'fission', 'uranium', 'plutonium',
            'nuclear power', 'nuclear plant', 'radioactive', 'chernobyl',
            'fukushima', 'three mile island', 'atomic energy', 'SMR',
            'small modular reactor', 'thorium', 'nuclear waste'
        ],
        'description': 'Nuclear energy, power plants, and atomic technology'
    },
    'data_centers': {
        'label': 'Data Centers',
        'keywords': [
            'data center', 'data centre', 'server farm', 'cloud infrastructure',
            'colocation', 'hyperscale', 'edge computing', 'CDN',
            'data storage', 'server rack', 'cooling', 'power usage effectiveness',
            'PUE', 'AWS', 'Azure', 'Google Cloud', 'datacenter'
        ],
        'description': 'Data centers, cloud infrastructure, and server facilities'
    },
    'healthcare': {
        'label': 'Healthcare',
        'keywords': [
            'healthcare', 'health care', 'medical', 'hospital', 'doctor',
            'nurse', 'patient', 'medicare', 'medicaid', 'insurance',
            'pharmaceutical', 'drug price', 'vaccine', 'treatment',
            'diagnosis', 'clinical', 'epidemic', 'pandemic', 'public health'
        ],
        'description': 'Healthcare systems, medical treatment, and public health'
    },
    'immigration': {
        'label': 'Immigration',
        'keywords': [
            'immigration', 'immigrant', 'migrant', 'refugee', 'asylum',
            'border', 'visa', 'green card', 'citizenship', 'deportation',
            'ICE', 'border patrol', 'DACA', 'undocumented', 'illegal immigration',
            'refugee crisis', 'migration', 'border security'
        ],
        'description': 'Immigration policy, border issues, and refugee matters'
    },
    'technology': {
        'label': 'Technology Industry',
        'keywords': [
            'tech industry', 'silicon valley', 'startup', 'big tech',
            'artificial intelligence', 'AI', 'machine learning', 'software',
            'algorithm', 'cryptocurrency', 'blockchain', 'metaverse',
            'social media', 'platform', 'app', 'digital', 'innovation',
            'venture capital', 'IPO', 'tech company'
        ],
        'description': 'Technology industry, AI, and digital innovation'
    }
}


class ArticleCategorizer:
    """Categorizes articles into predefined topic categories."""

    def __init__(self, use_ml: bool = False):
        """
        Initialize the categorizer.

        Args:
            use_ml: Whether to use ML-based classification (slower but more accurate)
        """
        self.use_ml = use_ml
        self.classifier = None

        if use_ml:
            try:
                print("Loading zero-shot classification model...")
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
                print("✓ Model loaded successfully")
            except Exception as e:
                print(f"✗ Could not load ML model: {e}")
                print("  Falling back to keyword-based classification")
                self.use_ml = False

    def categorize_by_keywords(self, text: str, title: str = "") -> Dict[str, float]:
        """
        Categorize article using keyword matching.

        Args:
            text: Article content
            title: Article title (weighted more heavily)

        Returns:
            Dictionary mapping category IDs to confidence scores (0-1)
        """
        # Combine title (weighted 3x) and text
        combined_text = (title.lower() + " ") * 3 + text.lower()

        scores = {}

        for category_id, category_info in CATEGORIES.items():
            # Count keyword matches
            matches = 0
            total_keywords = len(category_info['keywords'])

            for keyword in category_info['keywords']:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, combined_text):
                    matches += 1

            # Calculate confidence score
            # Use a sigmoid-like function to scale the score
            raw_score = matches / total_keywords if total_keywords > 0 else 0

            # Boost score if multiple keywords found
            if matches >= 3:
                raw_score = min(1.0, raw_score * 1.5)
            elif matches >= 2:
                raw_score = min(1.0, raw_score * 1.2)

            scores[category_id] = round(raw_score, 3)

        return scores

    def categorize_by_ml(self, text: str, title: str = "") -> Dict[str, float]:
        """
        Categorize article using zero-shot classification.

        Args:
            text: Article content
            title: Article title

        Returns:
            Dictionary mapping category IDs to confidence scores (0-1)
        """
        if not self.classifier:
            return self.categorize_by_keywords(text, title)

        # Use title + first 500 chars of content for classification
        sample_text = f"{title}. {text[:500]}"

        # Get category labels and descriptions
        candidate_labels = [info['description'] for info in CATEGORIES.values()]

        try:
            result = self.classifier(
                sample_text,
                candidate_labels,
                multi_label=True
            )

            # Map results back to category IDs
            scores = {}
            category_ids = list(CATEGORIES.keys())

            for label, score in zip(result['labels'], result['scores']):
                # Find matching category
                for cat_id in category_ids:
                    if CATEGORIES[cat_id]['description'] == label:
                        scores[cat_id] = round(score, 3)
                        break

            return scores

        except Exception as e:
            print(f"✗ ML classification failed: {e}")
            return self.categorize_by_keywords(text, title)

    def categorize_article(
        self,
        article: Dict,
        min_confidence: float = 0.15
    ) -> List[Tuple[str, float]]:
        """
        Categorize a single article.

        Args:
            article: Article dictionary with 'title' and 'content'
            min_confidence: Minimum confidence threshold for category assignment

        Returns:
            List of (category_id, confidence) tuples
        """
        text = article.get('content', '') or article.get('summary', '')
        title = article.get('title', '')

        if not text and not title:
            return []

        # Get scores
        if self.use_ml:
            scores = self.categorize_by_ml(text, title)
        else:
            scores = self.categorize_by_keywords(text, title)

        # Filter by confidence threshold and sort
        categories = [
            (cat_id, score)
            for cat_id, score in scores.items()
            if score >= min_confidence
        ]

        categories.sort(key=lambda x: x[1], reverse=True)

        return categories

    def categorize_batch(
        self,
        articles: List[Dict],
        min_confidence: float = 0.15
    ) -> List[Dict]:
        """
        Categorize a batch of articles.

        Args:
            articles: List of article dictionaries
            min_confidence: Minimum confidence threshold

        Returns:
            Articles with added 'categories' field
        """
        print(f"\n📊 Categorizing {len(articles)} articles...")

        categorized = []

        for i, article in enumerate(articles):
            if i % 50 == 0:
                print(f"  Processing {i+1}/{len(articles)}...")

            categories = self.categorize_article(article, min_confidence)

            # Add categories to article
            article['categories'] = categories

            # Add primary category
            if categories:
                article['primary_category'] = categories[0][0]
                article['primary_confidence'] = categories[0][1]
            else:
                article['primary_category'] = None
                article['primary_confidence'] = 0.0

            categorized.append(article)

        # Print statistics
        categorized_count = sum(1 for a in categorized if a['categories'])
        print(f"\n✓ Categorized {categorized_count}/{len(articles)} articles")

        # Category distribution
        category_counts = {}
        for article in categorized:
            for cat_id, _ in article.get('categories', []):
                category_counts[cat_id] = category_counts.get(cat_id, 0) + 1

        print("\nCategory distribution:")
        for cat_id, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {CATEGORIES[cat_id]['label']}: {count}")

        return categorized


def categorize_articles(
    articles: List[Dict],
    use_ml: bool = False,
    min_confidence: float = 0.15
) -> List[Dict]:
    """
    Main function to categorize articles.

    Args:
        articles: List of article dictionaries
        use_ml: Whether to use ML-based classification
        min_confidence: Minimum confidence threshold

    Returns:
        Articles with categories added
    """
    categorizer = ArticleCategorizer(use_ml=use_ml)
    return categorizer.categorize_batch(articles, min_confidence)
