#!/usr/bin/env python
"""
Run the complete News Rationalizer analysis pipeline.

This script:
1. Collects articles from RSS feeds
2. Categorizes articles by topic
3. Analyzes sentiment/emotional valence
4. Profiles authors
5. Saves results to the database

Usage:
    python scripts/run_analysis.py [--use-ml] [--months 6] [--max-per-source 100]
"""

import os
import sys
import django
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from analysis.collector import collect_news_data
from analysis.categorizer import categorize_articles, CATEGORIES
from analysis.sentiment import analyze_sentiment
from analysis.profiler import profile_authors, profile_publications

from dashboard.models import (
    Article, Category, ArticleCategory, AuthorProfile,
    AuthorCategoryMetric, PublicationProfile, PublicationCategoryMetric,
    AnalysisRun
)


def save_categories_to_db():
    """Ensure all categories exist in the database."""
    print("\n📊 Setting up categories in database...")

    for cat_id, cat_info in CATEGORIES.items():
        category, created = Category.objects.get_or_create(
            category_id=cat_id,
            defaults={
                'label': cat_info['label'],
                'description': cat_info['description']
            }
        )
        if created:
            print(f"  ✓ Created category: {cat_info['label']}")
        else:
            print(f"  - Category exists: {cat_info['label']}")


def save_articles_to_db(articles):
    """Save articles to database."""
    print(f"\n💾 Saving {len(articles)} articles to database...")

    saved_count = 0
    updated_count = 0

    for article_data in articles:
        # Get or create article
        article, created = Article.objects.get_or_create(
            url=article_data['url'],
            defaults={
                'title': article_data.get('title', ''),
                'publication': article_data.get('publication', ''),
                'domain': article_data.get('domain', ''),
                'author': article_data.get('author'),
                'published_date': article_data.get('published_date'),
                'content': article_data.get('content', ''),
                'summary': article_data.get('summary', ''),
            }
        )

        if created:
            saved_count += 1
        else:
            updated_count += 1

        # Update sentiment data
        if 'sentiment' in article_data:
            sentiment = article_data['sentiment']
            article.overall_valence = sentiment.get('overall_valence', 0.0)
            article.title_valence = sentiment.get('title_valence', 0.0)
            article.content_valence = sentiment.get('content_valence', 0.0)
            article.sentiment_confidence = sentiment.get('confidence', 0.0)
            article.sentiment_label = sentiment.get('content_label', '')

        # Update category data
        if 'primary_category' in article_data:
            article.primary_category = article_data['primary_category']
            article.primary_confidence = article_data.get('primary_confidence', 0.0)

        article.save()

        # Save article-category relationships
        if 'categories' in article_data:
            for cat_id, confidence in article_data['categories']:
                try:
                    category = Category.objects.get(category_id=cat_id)
                    ArticleCategory.objects.get_or_create(
                        article=article,
                        category=category,
                        defaults={'confidence': confidence}
                    )
                except Category.DoesNotExist:
                    print(f"  ✗ Category not found: {cat_id}")

    print(f"  ✓ Saved {saved_count} new articles, updated {updated_count} existing")


def save_author_profiles_to_db(profiles):
    """Save author profiles to database."""
    print(f"\n👤 Saving {len(profiles)} author profiles to database...")

    for author_name, profile_data in profiles.items():
        # Get or create author profile
        profile, created = AuthorProfile.objects.get_or_create(
            name=author_name,
            defaults={
                'total_articles': profile_data.get('total_articles', 0),
                'categorized_articles': profile_data.get('categorized_articles', 0),
                'overall_avg_valence': profile_data.get('overall_avg_valence', 0.0),
                'overall_variance': profile_data.get('overall_variance', 0.0),
                'cross_category_variance': profile_data.get('cross_category_variance', 0.0),
                'balance_score': profile_data.get('balance_score', 0.0),
                'balance_rank': profile_data.get('balance_rank', 0),
            }
        )

        if not created:
            # Update existing profile
            profile.total_articles = profile_data.get('total_articles', 0)
            profile.categorized_articles = profile_data.get('categorized_articles', 0)
            profile.overall_avg_valence = profile_data.get('overall_avg_valence', 0.0)
            profile.overall_variance = profile_data.get('overall_variance', 0.0)
            profile.cross_category_variance = profile_data.get('cross_category_variance', 0.0)
            profile.balance_score = profile_data.get('balance_score', 0.0)
            profile.balance_rank = profile_data.get('balance_rank', 0)
            profile.save()

        # Save category metrics
        for cat_id, cat_metrics in profile_data.get('category_metrics', {}).items():
            try:
                category = Category.objects.get(category_id=cat_id)

                # Get most positive/negative articles
                most_positive_article = None
                most_negative_article = None

                if cat_metrics.get('most_positive'):
                    most_positive_article = Article.objects.filter(
                        url=cat_metrics['most_positive'].get('url')
                    ).first()

                if cat_metrics.get('most_negative'):
                    most_negative_article = Article.objects.filter(
                        url=cat_metrics['most_negative'].get('url')
                    ).first()

                # Create or update metric
                metric, created = AuthorCategoryMetric.objects.get_or_create(
                    author=profile,
                    category=category,
                    defaults={
                        'article_count': cat_metrics.get('article_count', 0),
                        'avg_valence': cat_metrics.get('avg_valence', 0.0),
                        'valence_variance': cat_metrics.get('valence_variance', 0.0),
                        'valence_stdev': cat_metrics.get('valence_stdev', 0.0),
                        'rank': cat_metrics.get('rank', 0),
                        'total_in_category': cat_metrics.get('total_in_category', 0),
                        'most_positive_article': most_positive_article,
                        'most_negative_article': most_negative_article,
                    }
                )

                if not created:
                    metric.article_count = cat_metrics.get('article_count', 0)
                    metric.avg_valence = cat_metrics.get('avg_valence', 0.0)
                    metric.valence_variance = cat_metrics.get('valence_variance', 0.0)
                    metric.valence_stdev = cat_metrics.get('valence_stdev', 0.0)
                    metric.rank = cat_metrics.get('rank', 0)
                    metric.total_in_category = cat_metrics.get('total_in_category', 0)
                    metric.most_positive_article = most_positive_article
                    metric.most_negative_article = most_negative_article
                    metric.save()

            except Category.DoesNotExist:
                print(f"  ✗ Category not found: {cat_id}")

    print(f"  ✓ Saved all author profiles")


def save_publication_profiles_to_db(profiles):
    """Save publication profiles to database."""
    print(f"\n📰 Saving {len(profiles)} publication profiles to database...")

    for pub_name, profile_data in profiles.items():
        # Get or create publication profile
        profile, created = PublicationProfile.objects.get_or_create(
            name=pub_name,
            defaults={
                'total_articles': profile_data.get('total_articles', 0),
                'categorized_articles': profile_data.get('categorized_articles', 0),
                'overall_avg_valence': profile_data.get('overall_avg_valence', 0.0),
                'overall_variance': profile_data.get('overall_variance', 0.0),
                'cross_category_variance': profile_data.get('cross_category_variance', 0.0),
                'balance_score': profile_data.get('balance_score', 0.0),
                'balance_rank': profile_data.get('balance_rank', 0),
            }
        )

        if not created:
            # Update existing profile
            profile.total_articles = profile_data.get('total_articles', 0)
            profile.categorized_articles = profile_data.get('categorized_articles', 0)
            profile.overall_avg_valence = profile_data.get('overall_avg_valence', 0.0)
            profile.overall_variance = profile_data.get('overall_variance', 0.0)
            profile.cross_category_variance = profile_data.get('cross_category_variance', 0.0)
            profile.balance_score = profile_data.get('balance_score', 0.0)
            profile.balance_rank = profile_data.get('balance_rank', 0)
            profile.save()

        # Save category metrics
        for cat_id, cat_metrics in profile_data.get('category_metrics', {}).items():
            try:
                category = Category.objects.get(category_id=cat_id)

                # Get most positive/negative articles
                most_positive_article = None
                most_negative_article = None

                if cat_metrics.get('most_positive'):
                    most_positive_article = Article.objects.filter(
                        url=cat_metrics['most_positive'].get('url')
                    ).first()

                if cat_metrics.get('most_negative'):
                    most_negative_article = Article.objects.filter(
                        url=cat_metrics['most_negative'].get('url')
                    ).first()

                # Create or update metric
                metric, created = PublicationCategoryMetric.objects.get_or_create(
                    publication=profile,
                    category=category,
                    defaults={
                        'article_count': cat_metrics.get('article_count', 0),
                        'avg_valence': cat_metrics.get('avg_valence', 0.0),
                        'valence_variance': cat_metrics.get('valence_variance', 0.0),
                        'valence_stdev': cat_metrics.get('valence_stdev', 0.0),
                        'rank': cat_metrics.get('rank', 0),
                        'total_in_category': cat_metrics.get('total_in_category', 0),
                        'most_positive_article': most_positive_article,
                        'most_negative_article': most_negative_article,
                    }
                )

                if not created:
                    metric.article_count = cat_metrics.get('article_count', 0)
                    metric.avg_valence = cat_metrics.get('avg_valence', 0.0)
                    metric.valence_variance = cat_metrics.get('valence_variance', 0.0)
                    metric.valence_stdev = cat_metrics.get('valence_stdev', 0.0)
                    metric.rank = cat_metrics.get('rank', 0)
                    metric.total_in_category = cat_metrics.get('total_in_category', 0)
                    metric.most_positive_article = most_positive_article
                    metric.most_negative_article = most_negative_article
                    metric.save()

            except Category.DoesNotExist:
                print(f"  ✗ Category not found: {cat_id}")

    print(f"  ✓ Saved all publication profiles")


def create_analysis_run_record(articles_collected, articles_categorized, articles_analyzed, authors_profiled, publications_profiled=0):
    """Create a record of this analysis run."""
    # Get date range
    all_articles = Article.objects.all()
    earliest = all_articles.order_by('published_date').first()
    latest = all_articles.order_by('-published_date').first()

    run = AnalysisRun.objects.create(
        articles_collected=articles_collected,
        articles_categorized=articles_categorized,
        articles_analyzed=articles_analyzed,
        authors_profiled=authors_profiled,
        publications_profiled=publications_profiled,
        date_range_start=earliest.published_date if earliest else None,
        date_range_end=latest.published_date if latest else None,
    )

    print(f"\n✓ Analysis run #{run.id} recorded")


def main():
    parser = argparse.ArgumentParser(description='Run News Rationalizer analysis pipeline')
    parser.add_argument(
        '--use-ml',
        action='store_true',
        help='Use ML-based classification (slower but more accurate)'
    )
    parser.add_argument(
        '--months',
        type=int,
        default=12,
        help='Number of months of data to collect (default: 12)'
    )
    parser.add_argument(
        '--max-per-source',
        type=int,
        default=1000,
        help='Maximum articles per source (default: 1000)'
    )
    parser.add_argument(
        '--skip-collection',
        action='store_true',
        help='Skip data collection (use existing data)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("NEWS RATIONALIZER - Analysis Pipeline")
    print("=" * 70)

    # Step 0: Setup categories
    save_categories_to_db()

    # Step 1: Collect articles
    if args.skip_collection:
        print("\n⏭️  Skipping data collection (using existing data)")
        articles = []
    else:
        articles = collect_news_data(
            months_back=args.months,
            max_per_source=args.max_per_source
        )

        if not articles:
            print("\n✗ No articles collected. Exiting.")
            return

    # Step 2: Categorize articles
    if articles:
        articles = categorize_articles(
            articles,
            use_ml=args.use_ml,
            min_confidence=0.10
        )

        # Filter out uncategorized articles
        categorized_articles = [a for a in articles if a.get('categories')]
        print(f"\n✓ {len(categorized_articles)} articles have categories")

        # Step 3: Analyze sentiment
        articles = analyze_sentiment(articles)

        # Step 4: Save articles to database
        save_articles_to_db(articles)

    # Step 5: Load all articles from database for profiling
    print("\n📖 Loading all articles from database for profiling...")
    all_articles = []

    for article in Article.objects.all():
        article_data = {
            'author': article.author,
            'publication': article.publication,
            'title': article.title,
            'url': article.url,
            'published_date': article.published_date,
            'sentiment': {
                'overall_valence': article.overall_valence,
                'title_valence': article.title_valence,
                'content_valence': article.content_valence,
                'confidence': article.sentiment_confidence,
            },
            'categories': [
                (ac.category.category_id, ac.confidence)
                for ac in article.articlecategory_set.all()
            ]
        }
        all_articles.append(article_data)

    print(f"  ✓ Loaded {len(all_articles)} articles")

    # Step 6: Profile authors
    author_profiles = profile_authors(all_articles, min_articles=3, min_total_articles=2)

    # Step 7: Save author profiles to database
    save_author_profiles_to_db(author_profiles)

    # Step 8: Profile publications
    publication_profiles = profile_publications(all_articles, min_articles=3)

    # Step 9: Save publication profiles to database
    save_publication_profiles_to_db(publication_profiles)

    # Step 10: Create analysis run record
    create_analysis_run_record(
        articles_collected=len(articles) if articles else 0,
        articles_categorized=len([a for a in articles if a.get('categories')]) if articles else 0,
        articles_analyzed=len(articles) if articles else 0,
        authors_profiled=len(author_profiles),
        publications_profiled=len(publication_profiles)
    )

    print("\n" + "=" * 70)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 70)
    print(f"\nRun the development server to view results:")
    print("  uv run python manage.py runserver")
    print("\nThen visit: http://localhost:8000/")
    print()


if __name__ == '__main__':
    main()
