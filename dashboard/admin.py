"""
Django admin configuration for News Rationalizer.
"""

from django.contrib import admin
from .models import (
    Article, Category, ArticleCategory, AuthorProfile,
    AuthorCategoryMetric, AnalysisRun
)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'publication', 'published_date', 'overall_valence', 'primary_category']
    list_filter = ['publication', 'primary_category', 'published_date']
    search_fields = ['title', 'author', 'content']
    date_hierarchy = 'published_date'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['label', 'category_id', 'get_article_count']
    search_fields = ['label', 'description']


@admin.register(ArticleCategory)
class ArticleCategoryAdmin(admin.ModelAdmin):
    list_display = ['article', 'category', 'confidence']
    list_filter = ['category']
    search_fields = ['article__title']


@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_articles', 'balance_score', 'balance_rank', 'overall_avg_valence']
    list_filter = ['balance_rank']
    search_fields = ['name']
    ordering = ['-balance_score']


@admin.register(AuthorCategoryMetric)
class AuthorCategoryMetricAdmin(admin.ModelAdmin):
    list_display = ['author', 'category', 'article_count', 'avg_valence', 'rank']
    list_filter = ['category']
    search_fields = ['author__name']


@admin.register(AnalysisRun)
class AnalysisRunAdmin(admin.ModelAdmin):
    list_display = ['run_date', 'articles_collected', 'authors_profiled']
    date_hierarchy = 'run_date'
