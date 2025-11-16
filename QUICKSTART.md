# News Rationalizer - Quick Start Guide

## What Was Built

A complete demonstration web application that analyzes news articles to measure authors' emotional valence patterns and identify balanced vs. biased reporting across topics.

### Core Components

1. **Analysis Pipeline** (`analysis/`)
   - Article collection from 8 RSS feeds
   - Topic categorization (5 categories: Nuclear Energy, Data Centers, Healthcare, Immigration, Technology)
   - Sentiment analysis using RoBERTa model
   - Author profiling with balance metrics

2. **Django Web Application** (`dashboard/`)
   - Landing page with conjugate principle explanation
   - Category views showing author rankings
   - Author profile pages with historical trends
   - Balance rankings comparing authors
   - Tufte-inspired minimalist design

3. **Database** (SQLite)
   - Articles, categories, authors, and metrics
   - Full relational structure with Django ORM

4. **Deployment** (Render/Railway/PythonAnywhere ready)
   - Procfile, render.yaml, and deployment guides
   - Production-ready configuration

## Getting Started (3 Steps)

### 1. Run the Verification Script

```bash
uv run python scripts/verify_setup.py
```

This confirms all dependencies are installed and the project structure is correct.

### 2. Generate Sample Data

```bash
uv run python scripts/generate_sample_data.py
```

This creates 200 sample articles with realistic data for 16 authors across 5 categories.

**OR** Run Real Analysis (takes 5-10 minutes):

```bash
uv run python scripts/run_analysis.py
```

### 3. Start the Server

```bash
uv run python manage.py runserver
```

Visit: **http://localhost:8000/**

## What You'll See

### Landing Page
- Explanation of the "conjugate principle"
- Dataset statistics
- All 5 topic categories
- Sample complementary author pairs

### Category Pages
- Author valence spectrum (most negative to most positive)
- Complementary pairs for balanced reading
- Sample articles from extremes

### Author Profiles
- Valence scores across all categories
- Historical trend
- Balance score and rank
- Most extreme articles

### Rankings Page
- All authors ranked by balance score
- Most balanced vs. most polarized
- Comparative analysis

## Project Structure

```
news_rationalizer/
├── analysis/           # Analysis pipeline
│   ├── collector.py    # RSS feed scraping
│   ├── categorizer.py  # Topic classification
│   ├── sentiment.py    # Valence scoring
│   └── profiler.py     # Author metrics
├── dashboard/          # Django app
│   ├── models.py       # Database models
│   ├── views.py        # Page views
│   ├── templates/      # HTML templates
│   └── admin.py        # Admin interface
├── config/             # Django settings
├── data/               # SQLite database
└── scripts/            # Utility scripts
```

## Running Real Analysis

To collect and analyze real news articles:

```bash
# Full analysis (6 months of data, max 100 articles per source)
uv run python scripts/run_analysis.py

# Customize parameters
uv run python scripts/run_analysis.py --months 3 --max-per-source 50

# Use ML-based categorization (slower but more accurate)
uv run python scripts/run_analysis.py --use-ml

# Re-analyze existing data without fetching new articles
uv run python scripts/run_analysis.py --skip-collection
```

**Note:** Full analysis with ML models may take 10-30 minutes depending on your hardware.

## Admin Interface

Access the Django admin at **http://localhost:8000/admin/**

To create an admin user:

```bash
uv run python manage.py createsuperuser
```

## Deployment

See `DEPLOYMENT.md` for detailed instructions on deploying to:
- **Render** (recommended for free tier)
- **Railway**
- **PythonAnywhere**

Quick deploy to Render:

1. Push to GitHub
2. Connect repository in Render dashboard
3. Deploy (auto-detects `render.yaml`)

## Key Features

### The Conjugate Principle

Just as `(3 + 4i) × (3 - 4i) = 25` eliminates the imaginary component, pairing articles from authors with complementary emotional valences can approach more neutral, comprehensive coverage.

### Balance Score

Calculated as: `1 / (1 + cross_category_variance × 10)`

- High score (near 1.0): Consistent emotional tone across topics
- Low score (near 0): Tone varies significantly between topics

### Valence Score

Range: -1.0 (very negative) to +1.0 (very positive)

- Negative: Critical, pessimistic, unfavorable
- Neutral: Balanced, objective
- Positive: Optimistic, favorable, supportive

## Methodology

1. **Data Collection**: Fetch articles from RSS feeds
2. **Categorization**: Classify by topic (keyword or ML-based)
3. **Sentiment Analysis**: Measure emotional valence using RoBERTa
4. **Author Profiling**: Calculate metrics per author per category
5. **Visualization**: Present in interactive dashboard

## Limitations

- Sentiment ≠ Bias or accuracy
- Model trained on Twitter data
- Keyword categorization can misfire
- Requires 3+ articles per category for meaningful metrics
- Measures tone, not truthfulness or quality

## Next Steps

- Explore the dashboard and sample data
- Run real analysis with `run_analysis.py`
- Check out the methodology page at `/about/`
- Deploy to a hosting platform
- Customize for your specific needs

## Files of Interest

- `README.md` - Comprehensive documentation
- `DEPLOYMENT.md` - Deployment instructions
- `dashboard/templates/` - HTML templates (customizable design)
- `analysis/categorizer.py` - Add/modify topic categories
- `config/settings.py` - Django configuration

## Support

- Run `uv run python scripts/verify_setup.py` to diagnose issues
- Check the README for detailed documentation
- All analysis modules have inline documentation

---

**Built with:** Django, pandas, transformers, PyTorch, feedparser, BeautifulSoup

**License:** [To be determined]

**Demo ready!** The application is fully functional with sample data.
