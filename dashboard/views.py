"""
Django views for the News Rationalizer dashboard.
"""

from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Avg, Q
from .models import (
    Article, Category, AuthorProfile, AuthorCategoryMetric, AnalysisRun
)
from analysis.categorizer import CATEGORIES


def landing_page(request):
    """Landing page with summary statistics and concept explanation."""

    # Get latest analysis run
    latest_run = AnalysisRun.objects.first()

    # Get summary statistics
    total_articles = Article.objects.count()
    total_authors = AuthorProfile.objects.count()

    # Get date range
    earliest_article = Article.objects.order_by('published_date').first()
    latest_article = Article.objects.order_by('-published_date').first()

    # Get category distribution
    categories = Category.objects.all()
    category_stats = []

    for category in categories:
        article_count = Article.objects.filter(primary_category=category.category_id).count()
        author_count = AuthorCategoryMetric.objects.filter(
            category=category,
            article_count__gte=3
        ).count()

        category_stats.append({
            'category': category,
            'article_count': article_count,
            'author_count': author_count,
        })

    # Get sample complementary pairs
    sample_pairs = []

    for category in categories:
        # Get most positive and most negative author in this category
        metrics = AuthorCategoryMetric.objects.filter(
            category=category,
            article_count__gte=3
        ).order_by('avg_valence')

        if metrics.count() >= 2:
            most_negative = metrics.first()
            most_positive = metrics.last()

            if most_negative and most_positive:
                sample_pairs.append({
                    'category': category,
                    'negative_author': most_negative,
                    'positive_author': most_positive,
                    'valence_diff': abs(most_positive.avg_valence - most_negative.avg_valence),
                })

    context = {
        'latest_run': latest_run,
        'total_articles': total_articles,
        'total_authors': total_authors,
        'earliest_date': earliest_article.published_date if earliest_article else None,
        'latest_date': latest_article.published_date if latest_article else None,
        'category_stats': category_stats,
        'sample_pairs': sample_pairs[:3],  # Show top 3
    }

    return render(request, 'landing.html', context)


def category_view(request, category_id):
    """View for a specific category showing author rankings and complementary pairs."""

    category = get_object_or_404(Category, category_id=category_id)

    # Get all author metrics for this category
    author_metrics = AuthorCategoryMetric.objects.filter(
        category=category,
        article_count__gte=3
    ).select_related('author').order_by('avg_valence')

    # Get articles in this category
    articles = Article.objects.filter(
        primary_category=category_id
    ).order_by('-published_date')[:50]

    # Calculate complementary pairs
    pairs = []
    metrics_list = list(author_metrics)

    for i, metric1 in enumerate(metrics_list):
        for metric2 in metrics_list[i+1:]:
            # Check if they have opposing valences
            if (metric1.avg_valence * metric2.avg_valence) < 0:
                magnitude_similarity = 1.0 - abs(abs(metric1.avg_valence) - abs(metric2.avg_valence))
                complementarity = magnitude_similarity * (abs(metric1.avg_valence) + abs(metric2.avg_valence)) / 2

                pairs.append({
                    'negative_author': metric1 if metric1.avg_valence < 0 else metric2,
                    'positive_author': metric2 if metric2.avg_valence > 0 else metric1,
                    'complementarity': complementarity,
                })

    # Sort pairs by complementarity
    pairs.sort(key=lambda x: x['complementarity'], reverse=True)

    # Get sample articles from extremes
    positive_articles = articles.filter(overall_valence__gt=0.3).order_by('-overall_valence')[:5]
    negative_articles = articles.filter(overall_valence__lt=-0.3).order_by('overall_valence')[:5]

    context = {
        'category': category,
        'category_info': CATEGORIES.get(category_id, {}),
        'author_metrics': author_metrics,
        'total_authors': author_metrics.count(),
        'complementary_pairs': pairs[:10],
        'positive_articles': positive_articles,
        'negative_articles': negative_articles,
        'total_articles': Article.objects.filter(primary_category=category_id).count(),
    }

    return render(request, 'category.html', context)


def author_profile(request, author_name):
    """View for an individual author's profile."""

    author = get_object_or_404(AuthorProfile, name=author_name)

    # Get category metrics
    category_metrics = AuthorCategoryMetric.objects.filter(
        author=author,
        article_count__gte=3
    ).select_related('category').order_by('-article_count')

    # Get all articles by this author
    articles = Article.objects.filter(author=author_name).order_by('-published_date')

    # Get most extreme articles overall
    most_positive = articles.filter(overall_valence__gt=0).order_by('-overall_valence').first()
    most_negative = articles.filter(overall_valence__lt=0).order_by('overall_valence').first()

    # Calculate historical trend (by month)
    # Group articles by month and calculate average valence
    from django.db.models.functions import TruncMonth
    monthly_trend = articles.annotate(
        month=TruncMonth('published_date')
    ).values('month').annotate(
        avg_valence=Avg('overall_valence'),
        count=Count('id')
    ).order_by('month')

    context = {
        'author': author,
        'category_metrics': category_metrics,
        'articles': articles[:20],  # Show recent 20
        'total_articles': articles.count(),
        'most_positive': most_positive,
        'most_negative': most_negative,
        'monthly_trend': list(monthly_trend),
    }

    return render(request, 'author.html', context)


def balance_rankings(request):
    """View showing authors ranked by balance score."""

    # Get all author profiles
    authors = AuthorProfile.objects.filter(
        categorized_articles__gte=5
    ).order_by('-balance_score')

    # Get most balanced
    most_balanced = authors[:10]

    # Get most polarized (least balanced)
    most_polarized = authors.order_by('balance_score')[:10]

    # Get authors with most coverage
    most_coverage = authors.annotate(
        category_count=Count('authorcategorymetric')
    ).order_by('-category_count')[:10]

    context = {
        'all_authors': authors,
        'most_balanced': most_balanced,
        'most_polarized': most_polarized,
        'most_coverage': most_coverage,
        'total_authors': authors.count(),
    }

    return render(request, 'rankings.html', context)


def about(request):
    """About page explaining the methodology."""

    context = {
        'categories': CATEGORIES,
    }

    return render(request, 'about.html', context)
