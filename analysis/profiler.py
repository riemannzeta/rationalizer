"""
Author Profiling Module - Calculates author-level metrics and balance scores.
"""

from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import statistics
import math


class AuthorProfiler:
    """Profiles authors based on their article sentiment patterns."""

    def __init__(self, min_articles_per_category: int = 3):
        """
        Initialize the profiler.

        Args:
            min_articles_per_category: Minimum articles required for category metrics
        """
        self.min_articles = min_articles_per_category

    def build_author_profiles(self, articles: List[Dict], min_total_articles: int = 2) -> Dict[str, Dict]:
        """
        Build profiles for all authors.

        Args:
            articles: List of analyzed articles
            min_total_articles: Minimum total articles required to include author (default: 2)

        Returns:
            Dictionary mapping author names to their profiles
        """
        print(f"\n👤 Building author profiles...")

        # Group articles by author
        author_articles = defaultdict(list)

        for article in articles:
            author = article.get('author')
            if author and 'sentiment' in article and article.get('categories'):
                author_articles[author].append(article)

        print(f"  Found {len(author_articles)} authors with analyzable content")

        # Filter authors with insufficient articles
        author_articles = {
            author: arts for author, arts in author_articles.items()
            if len(arts) >= min_total_articles
        }

        print(f"  After filtering (min {min_total_articles} articles): {len(author_articles)} authors")

        # Build profile for each author
        profiles = {}

        for author, author_arts in author_articles.items():
            profile = self._build_author_profile(author, author_arts)
            profiles[author] = profile

        # Calculate rankings within categories
        profiles = self._calculate_category_rankings(profiles)

        # Calculate overall balance rankings
        profiles = self._calculate_balance_rankings(profiles)

        print(f"✓ Built profiles for {len(profiles)} authors\n")

        return profiles

    def _build_author_profile(self, author: str, articles: List[Dict]) -> Dict:
        """Build profile for a single author."""

        # Group articles by category
        category_articles = defaultdict(list)

        for article in articles:
            for cat_id, confidence in article.get('categories', []):
                category_articles[cat_id].append({
                    'valence': article['sentiment']['overall_valence'],
                    'confidence': confidence,
                    'title': article['title'],
                    'url': article['url'],
                    'date': article.get('published_date')
                })

        # Calculate category-level metrics
        category_metrics = {}

        for cat_id, cat_articles in category_articles.items():
            if len(cat_articles) >= self.min_articles:
                valences = [a['valence'] for a in cat_articles]

                category_metrics[cat_id] = {
                    'article_count': len(cat_articles),
                    'avg_valence': round(statistics.mean(valences), 4),
                    'valence_variance': round(statistics.variance(valences) if len(valences) > 1 else 0, 4),
                    'valence_stdev': round(statistics.stdev(valences) if len(valences) > 1 else 0, 4),
                    'most_positive': max(cat_articles, key=lambda x: x['valence']),
                    'most_negative': min(cat_articles, key=lambda x: x['valence']),
                }

        # Calculate overall metrics
        all_valences = [
            a['sentiment']['overall_valence']
            for a in articles
        ]

        # Calculate cross-category balance score
        # Lower variance across categories = more balanced
        if len(category_metrics) >= 2:
            category_means = [m['avg_valence'] for m in category_metrics.values()]
            cross_category_variance = statistics.variance(category_means)
            balance_score = 1.0 / (1.0 + cross_category_variance * 10)  # Normalize to 0-1
        else:
            cross_category_variance = 0.0
            balance_score = 0.5  # Neutral if insufficient data

        profile = {
            'name': author,
            'total_articles': len(articles),
            'categorized_articles': sum(len(articles) for articles in category_articles.values()),
            'categories_covered': list(category_metrics.keys()),
            'category_metrics': category_metrics,
            'overall_avg_valence': round(statistics.mean(all_valences), 4),
            'overall_variance': round(statistics.variance(all_valences) if len(all_valences) > 1 else 0, 4),
            'cross_category_variance': round(cross_category_variance, 4),
            'balance_score': round(balance_score, 4),
        }

        return profile

    def _calculate_category_rankings(self, profiles: Dict[str, Dict]) -> Dict[str, Dict]:
        """Calculate author rankings within each category."""

        # Group authors by category
        category_authors = defaultdict(list)

        for author, profile in profiles.items():
            for cat_id in profile['category_metrics'].keys():
                category_authors[cat_id].append({
                    'author': author,
                    'avg_valence': profile['category_metrics'][cat_id]['avg_valence']
                })

        # Rank authors within each category
        for cat_id, authors in category_authors.items():
            # Sort by valence (most negative to most positive)
            sorted_authors = sorted(authors, key=lambda x: x['avg_valence'])

            # Assign ranks
            for rank, author_data in enumerate(sorted_authors, 1):
                author = author_data['author']
                profiles[author]['category_metrics'][cat_id]['rank'] = rank
                profiles[author]['category_metrics'][cat_id]['total_in_category'] = len(sorted_authors)

        return profiles

    def _calculate_balance_rankings(self, profiles: Dict[str, Dict]) -> Dict[str, Dict]:
        """Calculate overall balance rankings."""

        # Sort authors by balance score (most balanced first)
        sorted_profiles = sorted(
            profiles.items(),
            key=lambda x: x[1]['balance_score'],
            reverse=True
        )

        # Assign balance ranks
        for rank, (author, profile) in enumerate(sorted_profiles, 1):
            profiles[author]['balance_rank'] = rank
            profiles[author]['total_authors'] = len(profiles)

        return profiles

    def find_complementary_pairs(
        self,
        profiles: Dict[str, Dict],
        category: str,
        max_pairs: int = 10
    ) -> List[Tuple[Dict, Dict, float]]:
        """
        Find authors with complementary (opposing) valences in a category.

        Args:
            profiles: Author profiles
            category: Category ID to find pairs for
            max_pairs: Maximum number of pairs to return

        Returns:
            List of (author1_profile, author2_profile, complementarity_score) tuples
        """
        # Get authors who write in this category
        category_authors = [
            (author, profile)
            for author, profile in profiles.items()
            if category in profile['category_metrics']
        ]

        if len(category_authors) < 2:
            return []

        # Find pairs with opposing valences
        pairs = []

        for i, (author1, profile1) in enumerate(category_authors):
            valence1 = profile1['category_metrics'][category]['avg_valence']

            for author2, profile2 in category_authors[i+1:]:
                valence2 = profile2['category_metrics'][category]['avg_valence']

                # Calculate complementarity score
                # Higher when valences are opposite and similar in magnitude
                if (valence1 * valence2) < 0:  # Opposite signs
                    magnitude_similarity = 1.0 - abs(abs(valence1) - abs(valence2))
                    complementarity = magnitude_similarity * (abs(valence1) + abs(valence2)) / 2

                    pairs.append((profile1, profile2, round(complementarity, 4)))

        # Sort by complementarity score
        pairs.sort(key=lambda x: x[2], reverse=True)

        return pairs[:max_pairs]

    def get_top_balanced_authors(
        self,
        profiles: Dict[str, Dict],
        n: int = 10
    ) -> List[Dict]:
        """
        Get the most balanced authors.

        Args:
            profiles: Author profiles
            n: Number of authors to return

        Returns:
            List of author profiles, sorted by balance score
        """
        sorted_authors = sorted(
            profiles.values(),
            key=lambda x: x['balance_score'],
            reverse=True
        )

        return sorted_authors[:n]

    def get_top_polarized_authors(
        self,
        profiles: Dict[str, Dict],
        n: int = 10
    ) -> List[Dict]:
        """
        Get the most polarized (least balanced) authors.

        Args:
            profiles: Author profiles
            n: Number of authors to return

        Returns:
            List of author profiles, sorted by balance score (ascending)
        """
        sorted_authors = sorted(
            profiles.values(),
            key=lambda x: x['balance_score']
        )

        return sorted_authors[:n]

    def get_category_spectrum(
        self,
        profiles: Dict[str, Dict],
        category: str
    ) -> List[Dict]:
        """
        Get authors ranked by valence in a category (negative to positive).

        Args:
            profiles: Author profiles
            category: Category ID

        Returns:
            List of author profiles with category metrics
        """
        category_authors = [
            {
                'author': profile['name'],
                'avg_valence': profile['category_metrics'][category]['avg_valence'],
                'article_count': profile['category_metrics'][category]['article_count'],
                'variance': profile['category_metrics'][category]['valence_variance'],
            }
            for profile in profiles.values()
            if category in profile['category_metrics']
        ]

        # Sort by valence
        category_authors.sort(key=lambda x: x['avg_valence'])

        return category_authors


class PublicationProfiler:
    """Profiles publications based on their article sentiment patterns."""

    def __init__(self, min_articles_per_category: int = 3):
        """
        Initialize the profiler.

        Args:
            min_articles_per_category: Minimum articles required for category metrics
        """
        self.min_articles = min_articles_per_category

    def build_publication_profiles(self, articles: List[Dict]) -> Dict[str, Dict]:
        """
        Build profiles for all publications.

        Args:
            articles: List of analyzed articles

        Returns:
            Dictionary mapping publication names to their profiles
        """
        print(f"\n📰 Building publication profiles...")

        # Group articles by publication
        pub_articles = defaultdict(list)

        for article in articles:
            publication = article.get('publication')
            if publication and 'sentiment' in article and article.get('categories'):
                pub_articles[publication].append(article)

        print(f"  Found {len(pub_articles)} publications with analyzable content")

        # Build profile for each publication
        profiles = {}

        for publication, pub_arts in pub_articles.items():
            profile = self._build_publication_profile(publication, pub_arts)
            profiles[publication] = profile

        # Calculate rankings within categories
        profiles = self._calculate_category_rankings(profiles)

        # Calculate overall balance rankings
        profiles = self._calculate_balance_rankings(profiles)

        print(f"✓ Built profiles for {len(profiles)} publications\n")

        return profiles

    def _build_publication_profile(self, publication: str, articles: List[Dict]) -> Dict:
        """Build profile for a single publication."""

        # Group articles by category
        category_articles = defaultdict(list)

        for article in articles:
            for cat_id, confidence in article.get('categories', []):
                category_articles[cat_id].append({
                    'valence': article['sentiment']['overall_valence'],
                    'confidence': confidence,
                    'title': article['title'],
                    'url': article['url'],
                    'author': article.get('author'),
                    'date': article.get('published_date')
                })

        # Calculate category-level metrics
        category_metrics = {}

        for cat_id, cat_articles in category_articles.items():
            if len(cat_articles) >= self.min_articles:
                valences = [a['valence'] for a in cat_articles]

                category_metrics[cat_id] = {
                    'article_count': len(cat_articles),
                    'avg_valence': round(statistics.mean(valences), 4),
                    'valence_variance': round(statistics.variance(valences) if len(valences) > 1 else 0, 4),
                    'valence_stdev': round(statistics.stdev(valences) if len(valences) > 1 else 0, 4),
                    'most_positive': max(cat_articles, key=lambda x: x['valence']),
                    'most_negative': min(cat_articles, key=lambda x: x['valence']),
                    'articles': sorted(cat_articles, key=lambda x: x.get('date') or '', reverse=True),
                }

        # Calculate overall metrics
        all_valences = [
            a['sentiment']['overall_valence']
            for a in articles
        ]

        # Calculate cross-category balance score
        if len(category_metrics) >= 2:
            category_means = [m['avg_valence'] for m in category_metrics.values()]
            cross_category_variance = statistics.variance(category_means)
            balance_score = 1.0 / (1.0 + cross_category_variance * 10)
        else:
            cross_category_variance = 0.0
            balance_score = 0.5

        profile = {
            'name': publication,
            'total_articles': len(articles),
            'categorized_articles': sum(len(articles) for articles in category_articles.values()),
            'categories_covered': list(category_metrics.keys()),
            'category_metrics': category_metrics,
            'overall_avg_valence': round(statistics.mean(all_valences), 4),
            'overall_variance': round(statistics.variance(all_valences) if len(all_valences) > 1 else 0, 4),
            'cross_category_variance': round(cross_category_variance, 4),
            'balance_score': round(balance_score, 4),
        }

        return profile

    def _calculate_category_rankings(self, profiles: Dict[str, Dict]) -> Dict[str, Dict]:
        """Calculate publication rankings within each category."""

        # Group publications by category
        category_pubs = defaultdict(list)

        for pub, profile in profiles.items():
            for cat_id in profile['category_metrics'].keys():
                category_pubs[cat_id].append({
                    'publication': pub,
                    'avg_valence': profile['category_metrics'][cat_id]['avg_valence']
                })

        # Rank publications within each category
        for cat_id, pubs in category_pubs.items():
            # Sort by valence (most negative to most positive)
            sorted_pubs = sorted(pubs, key=lambda x: x['avg_valence'])

            # Assign ranks
            for rank, pub_data in enumerate(sorted_pubs, 1):
                pub = pub_data['publication']
                profiles[pub]['category_metrics'][cat_id]['rank'] = rank
                profiles[pub]['category_metrics'][cat_id]['total_in_category'] = len(sorted_pubs)

        return profiles

    def _calculate_balance_rankings(self, profiles: Dict[str, Dict]) -> Dict[str, Dict]:
        """Calculate overall balance rankings."""

        # Sort publications by balance score
        sorted_profiles = sorted(
            profiles.items(),
            key=lambda x: x[1]['balance_score'],
            reverse=True
        )

        # Assign balance ranks
        for rank, (pub, profile) in enumerate(sorted_profiles, 1):
            profiles[pub]['balance_rank'] = rank
            profiles[pub]['total_publications'] = len(profiles)

        return profiles

    def get_category_author_breakdown(
        self,
        profiles: Dict[str, Dict],
        publication: str,
        category: str
    ) -> List[Dict]:
        """
        Get author-level breakdown for a publication within a category.
        Used for drill-down functionality.

        Args:
            profiles: Publication profiles
            publication: Publication name
            category: Category ID

        Returns:
            List of articles grouped by author with their valences
        """
        if publication not in profiles:
            return []

        profile = profiles[publication]
        if category not in profile['category_metrics']:
            return []

        articles = profile['category_metrics'][category].get('articles', [])

        # Group by author
        author_data = defaultdict(list)
        for article in articles:
            author = article.get('author', 'Unknown')
            author_data[author].append(article)

        # Calculate per-author metrics
        breakdown = []
        for author, auth_articles in author_data.items():
            valences = [a['valence'] for a in auth_articles]
            breakdown.append({
                'author': author,
                'article_count': len(auth_articles),
                'avg_valence': round(statistics.mean(valences), 4),
                'articles': sorted(auth_articles, key=lambda x: x.get('date') or '', reverse=True),
            })

        # Sort by average valence
        breakdown.sort(key=lambda x: x['avg_valence'])

        return breakdown


def profile_authors(articles: List[Dict], min_articles: int = 3, min_total_articles: int = 2) -> Dict[str, Dict]:
    """
    Main function to profile authors.

    Args:
        articles: List of analyzed articles
        min_articles: Minimum articles required per category
        min_total_articles: Minimum total articles to include author

    Returns:
        Dictionary of author profiles
    """
    profiler = AuthorProfiler(min_articles_per_category=min_articles)
    return profiler.build_author_profiles(articles, min_total_articles=min_total_articles)


def profile_publications(articles: List[Dict], min_articles: int = 3) -> Dict[str, Dict]:
    """
    Main function to profile publications.

    Args:
        articles: List of analyzed articles
        min_articles: Minimum articles required per category

    Returns:
        Dictionary of publication profiles
    """
    profiler = PublicationProfiler(min_articles_per_category=min_articles)
    return profiler.build_publication_profiles(articles)
