#!/usr/bin/env python
"""
Generate sample data for testing the dashboard without running the full analysis pipeline.
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from dashboard.models import (
    Article, Category, ArticleCategory, AuthorProfile,
    AuthorCategoryMetric, AnalysisRun
)
from analysis.categorizer import CATEGORIES


# Sample authors
AUTHORS = [
    "Sarah Johnson", "Michael Chen", "Emily Rodriguez", "David Kim",
    "Jessica Martinez", "Robert Taylor", "Amanda Wilson", "James Lee",
    "Maria Garcia", "Thomas Anderson", "Jennifer Brown", "Christopher Davis",
    "Patricia Miller", "Daniel Moore", "Lisa Jackson", "Matthew White"
]

# Sample publications
PUBLICATIONS = [
    "BBC News", "Reuters", "The Guardian", "NPR",
    "Al Jazeera", "The Hill", "Axios", "TechCrunch"
]

# Sample headlines by category
HEADLINES = {
    'nuclear_energy': [
        "New nuclear reactor design promises safer, cleaner energy",
        "Critics raise safety concerns over aging nuclear facilities",
        "Small modular reactors gain traction in energy transition",
        "Nuclear waste storage debate intensifies",
        "Fusion breakthrough brings clean energy closer",
        "Opponents call for shutdown of coastal nuclear plant",
        "Government invests billions in next-generation nuclear tech",
        "Environmental groups question nuclear's role in climate fight"
    ],
    'data_centers': [
        "Tech giants expand data center footprint amid AI boom",
        "Local communities oppose new hyperscale facility",
        "Innovative cooling systems reduce data center energy use",
        "Water consumption concerns plague data center expansion",
        "Edge computing transforms data infrastructure landscape",
        "Privacy advocates question data center security practices",
        "Green energy powers new generation of cloud facilities",
        "Job creation promises fail to materialize at new data hub"
    ],
    'healthcare': [
        "New drug shows promise in cancer treatment trials",
        "Healthcare costs continue to rise for American families",
        "Breakthrough in gene therapy offers hope for rare disease",
        "Insurance coverage gaps leave millions vulnerable",
        "AI diagnostics tool achieves human-level accuracy",
        "Rural hospitals face closure amid funding crisis",
        "Vaccine development timeline shortened by new technology",
        "Medical debt crisis deepens across the country"
    ],
    'immigration': [
        "Pathway to citizenship proposed for Dreamers",
        "Border security funding faces Congressional deadlock",
        "Refugee resettlement program expands capacity",
        "Detention conditions draw sharp criticism",
        "Economic benefits of immigration highlighted in new study",
        "Deportation numbers reach highest level in years",
        "Integration programs show success in major cities",
        "Asylum system overwhelmed by application backlog"
    ],
    'technology': [
        "AI startup raises record-breaking funding round",
        "Layoffs sweep through major tech companies",
        "New AI model demonstrates impressive capabilities",
        "Privacy concerns grow over data collection practices",
        "Quantum computing breakthrough announced by researchers",
        "Antitrust investigation targets big tech platforms",
        "Innovation in renewable tech promises cleaner future",
        "Critics warn of AI's potential societal harms"
    ]
}


def create_categories():
    """Create category records."""
    print("\n📊 Creating categories...")
    for cat_id, cat_info in CATEGORIES.items():
        category, created = Category.objects.get_or_create(
            category_id=cat_id,
            defaults={
                'label': cat_info['label'],
                'description': cat_info['description']
            }
        )
        if created:
            print(f"  ✓ Created: {cat_info['label']}")


def generate_sample_articles(num_articles=200):
    """Generate sample articles with realistic data."""
    print(f"\n📰 Generating {num_articles} sample articles...")

    categories = list(Category.objects.all())
    articles_created = 0

    for i in range(num_articles):
        # Random category
        category = random.choice(categories)
        cat_id = category.category_id

        # Random author and publication
        author = random.choice(AUTHORS)
        publication = random.choice(PUBLICATIONS)

        # Random date in last 6 months
        days_ago = random.randint(1, 180)
        pub_date = datetime.now() - timedelta(days=days_ago)

        # Random headline from category
        title = random.choice(HEADLINES[cat_id])

        # Generate valence score (with some author consistency)
        # Some authors tend positive, some negative, some balanced
        author_bias = hash(author) % 100 / 100 - 0.5  # -0.5 to +0.5
        randomness = (random.random() - 0.5) * 0.4  # -0.2 to +0.2
        valence = max(-1.0, min(1.0, author_bias + randomness))

        # Create article
        article, created = Article.objects.get_or_create(
            url=f"https://example.com/article-{i}",
            defaults={
                'title': title,
                'author': author,
                'publication': publication,
                'domain': publication.lower().replace(' ', ''),
                'published_date': pub_date,
                'content': f"Sample content for {title}. " * 50,
                'summary': f"Sample summary for {title}.",
                'overall_valence': round(valence, 4),
                'title_valence': round(valence + random.uniform(-0.1, 0.1), 4),
                'content_valence': round(valence + random.uniform(-0.05, 0.05), 4),
                'sentiment_confidence': random.uniform(0.7, 0.95),
                'sentiment_label': 'positive' if valence > 0.1 else 'negative' if valence < -0.1 else 'neutral',
                'primary_category': cat_id,
                'primary_confidence': random.uniform(0.6, 0.95),
            }
        )

        if created:
            articles_created += 1

            # Create article-category relationship
            ArticleCategory.objects.get_or_create(
                article=article,
                category=category,
                defaults={'confidence': random.uniform(0.6, 0.95)}
            )

            # Sometimes add secondary category
            if random.random() < 0.3:
                secondary_cat = random.choice([c for c in categories if c != category])
                ArticleCategory.objects.get_or_create(
                    article=article,
                    category=secondary_cat,
                    defaults={'confidence': random.uniform(0.2, 0.5)}
                )

    print(f"  ✓ Created {articles_created} articles")


def generate_author_profiles():
    """Generate author profiles from articles."""
    print("\n👤 Generating author profiles...")

    authors = Article.objects.values_list('author', flat=True).distinct()
    profiles_created = 0

    for author_name in authors:
        if not author_name:
            continue

        # Get all articles by this author
        author_articles = Article.objects.filter(author=author_name)

        if author_articles.count() < 3:
            continue

        # Calculate overall metrics
        total_articles = author_articles.count()
        valences = [a.overall_valence for a in author_articles]
        avg_valence = sum(valences) / len(valences)
        variance = sum((v - avg_valence) ** 2 for v in valences) / len(valences)

        # Calculate category-specific metrics
        category_valences = {}
        for category in Category.objects.all():
            cat_articles = author_articles.filter(primary_category=category.category_id)
            if cat_articles.count() >= 3:
                cat_valences = [a.overall_valence for a in cat_articles]
                category_valences[category.category_id] = sum(cat_valences) / len(cat_valences)

        # Calculate cross-category variance
        if len(category_valences) >= 2:
            cat_means = list(category_valences.values())
            cat_mean = sum(cat_means) / len(cat_means)
            cross_var = sum((v - cat_mean) ** 2 for v in cat_means) / len(cat_means)
            balance_score = 1.0 / (1.0 + cross_var * 10)
        else:
            cross_var = 0.0
            balance_score = 0.5

        # Create profile
        profile, created = AuthorProfile.objects.get_or_create(
            name=author_name,
            defaults={
                'total_articles': total_articles,
                'categorized_articles': total_articles,
                'overall_avg_valence': round(avg_valence, 4),
                'overall_variance': round(variance, 4),
                'cross_category_variance': round(cross_var, 4),
                'balance_score': round(balance_score, 4),
            }
        )

        if created:
            profiles_created += 1

            # Create category metrics
            for category in Category.objects.all():
                cat_articles = author_articles.filter(primary_category=category.category_id)

                if cat_articles.count() >= 3:
                    cat_valences = [a.overall_valence for a in cat_articles]
                    cat_avg = sum(cat_valences) / len(cat_valences)
                    cat_var = sum((v - cat_avg) ** 2 for v in cat_valences) / len(cat_valences)

                    AuthorCategoryMetric.objects.create(
                        author=profile,
                        category=category,
                        article_count=cat_articles.count(),
                        avg_valence=round(cat_avg, 4),
                        valence_variance=round(cat_var, 4),
                        valence_stdev=round(cat_var ** 0.5, 4),
                        most_positive_article=cat_articles.order_by('-overall_valence').first(),
                        most_negative_article=cat_articles.order_by('overall_valence').first(),
                    )

    # Calculate rankings
    all_profiles = AuthorProfile.objects.all().order_by('-balance_score')
    for rank, profile in enumerate(all_profiles, 1):
        profile.balance_rank = rank
        profile.save()

    # Calculate category rankings
    for category in Category.objects.all():
        metrics = AuthorCategoryMetric.objects.filter(
            category=category
        ).order_by('avg_valence')

        for rank, metric in enumerate(metrics, 1):
            metric.rank = rank
            metric.total_in_category = metrics.count()
            metric.save()

    print(f"  ✓ Created {profiles_created} author profiles")


def create_analysis_run():
    """Create an analysis run record."""
    print("\n📊 Creating analysis run record...")

    articles = Article.objects.all()
    earliest = articles.order_by('published_date').first()
    latest = articles.order_by('-published_date').first()

    run = AnalysisRun.objects.create(
        articles_collected=articles.count(),
        articles_categorized=articles.count(),
        articles_analyzed=articles.count(),
        authors_profiled=AuthorProfile.objects.count(),
        date_range_start=earliest.published_date if earliest else None,
        date_range_end=latest.published_date if latest else None,
        notes="Sample data generated for testing"
    )

    print(f"  ✓ Analysis run #{run.id} created")


def main():
    print("=" * 70)
    print("NEWS RATIONALIZER - Sample Data Generator")
    print("=" * 70)

    # Clear existing data
    print("\n🗑️  Clearing existing data...")
    Article.objects.all().delete()
    AuthorProfile.objects.all().delete()
    AnalysisRun.objects.all().delete()
    print("  ✓ Cleared")

    # Generate new data
    create_categories()
    generate_sample_articles(num_articles=200)
    generate_author_profiles()
    create_analysis_run()

    print("\n" + "=" * 70)
    print("✅ SAMPLE DATA GENERATION COMPLETE")
    print("=" * 70)
    print(f"\nGenerated:")
    print(f"  - {Article.objects.count()} articles")
    print(f"  - {AuthorProfile.objects.count()} author profiles")
    print(f"  - {Category.objects.count()} categories")
    print("\nStart the server to view results:")
    print("  uv run python manage.py runserver")
    print("\nThen visit: http://localhost:8000/")
    print()


if __name__ == '__main__':
    main()
