#!/usr/bin/env python
"""
Verify that the News Rationalizer setup is correct.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("NEWS RATIONALIZER - Setup Verification")
print("=" * 70)

# Test 1: Import analysis modules
print("\n1. Testing analysis module imports...")
try:
    from analysis.collector import ArticleCollector
    from analysis.categorizer import ArticleCategorizer, CATEGORIES
    from analysis.sentiment import SentimentAnalyzer
    from analysis.profiler import AuthorProfiler
    print("   ✓ All analysis modules imported successfully")
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)

# Test 2: Check Django setup
print("\n2. Testing Django setup...")
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    print("   ✓ Django setup successful")
except Exception as e:
    print(f"   ✗ Django setup error: {e}")
    sys.exit(1)

# Test 3: Import Django models
print("\n3. Testing Django models...")
try:
    from dashboard.models import (
        Article, Category, AuthorProfile, AuthorCategoryMetric, AnalysisRun
    )
    print("   ✓ All Django models imported successfully")
except ImportError as e:
    print(f"   ✗ Model import error: {e}")
    sys.exit(1)

# Test 4: Check database connectivity
print("\n4. Testing database connectivity...")
try:
    count = Article.objects.count()
    print(f"   ✓ Database connected ({count} articles in database)")
except Exception as e:
    print(f"   ✗ Database error: {e}")
    sys.exit(1)

# Test 5: Check categories
print("\n5. Checking topic categories...")
print(f"   Found {len(CATEGORIES)} categories:")
for cat_id, cat_info in CATEGORIES.items():
    print(f"     - {cat_info['label']}")

# Test 6: Check static files directory
print("\n6. Checking directory structure...")
required_dirs = ['analysis', 'dashboard', 'config', 'data', 'scripts']
for dir_name in required_dirs:
    if os.path.exists(dir_name):
        print(f"   ✓ {dir_name}/ exists")
    else:
        print(f"   ✗ {dir_name}/ missing")

print("\n" + "=" * 70)
print("✅ SETUP VERIFICATION COMPLETE")
print("=" * 70)
print("\nYour News Rationalizer installation is ready!")
print("\nNext steps:")
print("  1. Run analysis: uv run python scripts/run_analysis.py")
print("  2. Start server: uv run python manage.py runserver")
print("  3. Visit: http://localhost:8000/")
print()
