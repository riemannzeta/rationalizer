"""
Django models for storing news analysis results.
"""

from django.db import models
from django.utils import timezone
import json


class Article(models.Model):
    """Represents a news article."""

    title = models.CharField(max_length=500)
    url = models.URLField(max_length=1000, unique=True)
    publication = models.CharField(max_length=200)
    domain = models.CharField(max_length=200)
    author = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    published_date = models.DateTimeField(null=True, blank=True)
    collected_date = models.DateTimeField(default=timezone.now)

    content = models.TextField()
    summary = models.TextField(blank=True)

    # Sentiment analysis results
    overall_valence = models.FloatField(default=0.0, db_index=True)
    title_valence = models.FloatField(default=0.0)
    content_valence = models.FloatField(default=0.0)
    sentiment_confidence = models.FloatField(default=0.0)
    sentiment_label = models.CharField(max_length=50, blank=True)

    # Primary category
    primary_category = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    primary_confidence = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-published_date']
        indexes = [
            models.Index(fields=['author', 'primary_category']),
            models.Index(fields=['overall_valence']),
        ]

    def __str__(self):
        return f"{self.title[:50]}..."

    def get_categories(self):
        """Get all categories for this article."""
        return self.articlecategory_set.all()


class Category(models.Model):
    """Represents a topic category."""

    CATEGORY_CHOICES = [
        # Government & Policy
        ('federal_budget', 'Federal Budget & National Debt'),
        ('immigration', 'Immigration'),
        ('gun_control', 'Gun Control & Second Amendment'),
        ('elections', 'Elections & Campaign Finance'),
        ('judiciary', 'Judiciary & Supreme Court'),
        ('foreign_policy', 'Foreign Policy & International Trade'),
        # Economy & Business
        ('federal_reserve', 'Federal Reserve & Inflation'),
        ('labor_employment', 'Labor & Employment'),
        ('supply_chain', 'Supply Chain Management'),
        ('real_estate', 'Real Estate & Housing'),
        ('small_business', 'Small Business & Entrepreneurship'),
        # Technology & Industry
        ('ai_regulation', 'Artificial Intelligence (AI) Regulation'),
        ('technology', 'Technology Industry'),
        ('data_centers', 'Data Center Development'),
        ('cybersecurity', 'Cybersecurity'),
        ('semiconductor', 'Semiconductor Industry'),
        # Energy & Environment
        ('climate_change', 'Climate Change & Policy'),
        ('energy_transition', 'Energy Transition'),
        ('nuclear_energy', 'Nuclear Energy'),
        ('oil_gas', 'Oil & Gas Industry'),
        ('water_rights', 'Water Rights & Scarcity'),
        # Society & Health
        ('health_insurance', 'Health Insurance & Policy'),
        ('pharmaceuticals', 'Pharmaceuticals & Drug Pricing'),
        ('public_health', 'Public Health'),
        ('education', 'Education (K-12 & Higher Ed)'),
        ('criminal_justice', 'Criminal Justice Reform'),
        ('social_security', 'Social Security & Entitlements'),
        # Infrastructure & Transport
        ('infrastructure', 'National Infrastructure'),
        ('telecommunications', 'Telecommunications'),
        ('aerospace', 'Aerospace & Aviation'),
    ]

    category_id = models.CharField(max_length=100, unique=True, choices=CATEGORY_CHOICES)
    label = models.CharField(max_length=200)
    description = models.TextField()

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.label

    def get_article_count(self):
        """Get number of articles in this category."""
        return self.articlecategory_set.count()


class ArticleCategory(models.Model):
    """Many-to-many relationship between articles and categories with confidence scores."""

    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    confidence = models.FloatField(default=0.0)

    class Meta:
        unique_together = ['article', 'category']
        ordering = ['-confidence']

    def __str__(self):
        return f"{self.article.title[:30]} - {self.category.label} ({self.confidence:.2f})"


class AuthorProfile(models.Model):
    """Represents an author's profile and metrics."""

    name = models.CharField(max_length=200, unique=True, db_index=True)

    # Overall metrics
    total_articles = models.IntegerField(default=0)
    categorized_articles = models.IntegerField(default=0)
    overall_avg_valence = models.FloatField(default=0.0)
    overall_variance = models.FloatField(default=0.0)

    # Balance metrics
    cross_category_variance = models.FloatField(default=0.0)
    balance_score = models.FloatField(default=0.0, db_index=True)
    balance_rank = models.IntegerField(default=0)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-balance_score']

    def __str__(self):
        return self.name

    def get_category_metrics(self):
        """Get all category metrics for this author."""
        return self.authorcategorymetric_set.all()

    def get_categories_covered(self):
        """Get list of categories this author writes about."""
        return [
            metric.category.category_id
            for metric in self.authorcategorymetric_set.filter(
                article_count__gte=3
            )
        ]


class AuthorCategoryMetric(models.Model):
    """Metrics for an author within a specific category."""

    author = models.ForeignKey(AuthorProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    # Category-specific metrics
    article_count = models.IntegerField(default=0)
    avg_valence = models.FloatField(default=0.0, db_index=True)
    valence_variance = models.FloatField(default=0.0)
    valence_stdev = models.FloatField(default=0.0)

    # Rankings
    rank = models.IntegerField(default=0)
    total_in_category = models.IntegerField(default=0)

    # Most extreme articles
    most_positive_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='author_most_positive'
    )
    most_negative_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='author_most_negative'
    )

    class Meta:
        unique_together = ['author', 'category']
        ordering = ['category', 'avg_valence']

    def __str__(self):
        return f"{self.author.name} - {self.category.label}"


class PublicationProfile(models.Model):
    """Represents a publication's profile and metrics."""

    name = models.CharField(max_length=200, unique=True, db_index=True)

    # Overall metrics
    total_articles = models.IntegerField(default=0)
    categorized_articles = models.IntegerField(default=0)
    overall_avg_valence = models.FloatField(default=0.0)
    overall_variance = models.FloatField(default=0.0)

    # Balance metrics
    cross_category_variance = models.FloatField(default=0.0)
    balance_score = models.FloatField(default=0.0, db_index=True)
    balance_rank = models.IntegerField(default=0)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-balance_score']

    def __str__(self):
        return self.name

    def get_category_metrics(self):
        """Get all category metrics for this publication."""
        return self.publicationcategorymetric_set.all()

    def get_categories_covered(self):
        """Get list of categories this publication covers."""
        return [
            metric.category.category_id
            for metric in self.publicationcategorymetric_set.filter(
                article_count__gte=3
            )
        ]


class PublicationCategoryMetric(models.Model):
    """Metrics for a publication within a specific category."""

    publication = models.ForeignKey(PublicationProfile, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    # Category-specific metrics
    article_count = models.IntegerField(default=0)
    avg_valence = models.FloatField(default=0.0, db_index=True)
    valence_variance = models.FloatField(default=0.0)
    valence_stdev = models.FloatField(default=0.0)

    # Rankings
    rank = models.IntegerField(default=0)
    total_in_category = models.IntegerField(default=0)

    # Most extreme articles
    most_positive_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publication_most_positive'
    )
    most_negative_article = models.ForeignKey(
        Article,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publication_most_negative'
    )

    class Meta:
        unique_together = ['publication', 'category']
        ordering = ['category', 'avg_valence']

    def __str__(self):
        return f"{self.publication.name} - {self.category.label}"


class AnalysisRun(models.Model):
    """Tracks when analysis was run and metadata."""

    run_date = models.DateTimeField(default=timezone.now)
    articles_collected = models.IntegerField(default=0)
    articles_categorized = models.IntegerField(default=0)
    articles_analyzed = models.IntegerField(default=0)
    authors_profiled = models.IntegerField(default=0)
    publications_profiled = models.IntegerField(default=0)

    date_range_start = models.DateTimeField(null=True, blank=True)
    date_range_end = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-run_date']

    def __str__(self):
        return f"Analysis run on {self.run_date.strftime('%Y-%m-%d %H:%M')}"
