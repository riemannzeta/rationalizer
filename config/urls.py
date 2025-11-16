"""
URL configuration for News Rationalizer project.
"""

from django.contrib import admin
from django.urls import path
from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.landing_page, name='landing'),
    path('category/<str:category_id>/', views.category_view, name='category'),
    path('author/<str:author_name>/', views.author_profile, name='author'),
    path('publication/<str:publication_name>/', views.publication_profile, name='publication'),
    path('publication/<str:publication_name>/category/<str:category_id>/', views.publication_category_breakdown, name='publication_breakdown'),
    path('rankings/', views.balance_rankings, name='rankings'),
    path('about/', views.about, name='about'),
]
