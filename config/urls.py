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
    path('rankings/', views.balance_rankings, name='rankings'),
    path('about/', views.about, name='about'),
]
