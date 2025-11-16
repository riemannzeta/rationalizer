# News Rationalizer

**Measuring Emotional Valence in News Coverage**

A demonstration web application that analyzes news articles to measure authors' emotional valence patterns and identify balanced vs. biased reporting across topics.

## Core Concept: The Conjugate Principle

Just as multiplying a complex number by its conjugate yields a real number:

```
(3 + 4i) × (3 - 4i) = 25
```

We can **rationalize news coverage** by blending stories from authors with complementary emotional valences—pairing positive-leaning and negative-leaning perspectives on the same topic to approach more neutral, comprehensive coverage.

## Features

- **Article Collection**: Automatically scrapes articles from 8+ diverse news sources via RSS feeds
- **Topic Categorization**: Classifies articles into 5 key categories (Nuclear Energy, Data Centers, Healthcare, Immigration, Technology)
- **Sentiment Analysis**: Measures emotional valence using pre-trained RoBERTa model
- **Author Profiling**: Calculates balance scores and ranks authors by consistency across topics
- **Interactive Dashboard**: Tufte-inspired visualizations showing emotional spectrum and complementary pairs

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd rationalizer

# Install dependencies with uv
uv sync

# Run database migrations
uv run python manage.py migrate

# Create admin user (optional)
uv run python manage.py createsuperuser
```

### Running the Analysis

```bash
# Collect and analyze articles (takes 5-10 minutes)
uv run python scripts/run_analysis.py

# With options
uv run python scripts/run_analysis.py --months 3 --max-per-source 50

# Use ML-based categorization (slower but more accurate)
uv run python scripts/run_analysis.py --use-ml
```

### Running the Dashboard

```bash
# Start development server
uv run python manage.py runserver

# Visit http://localhost:8000/
```

## Project Structure

```
news_rationalizer/
├── analysis/              # Analysis pipeline modules
│   ├── collector.py       # Article fetching from RSS feeds
│   ├── categorizer.py     # Topic classification
│   ├── sentiment.py       # Emotional valence scoring
│   └── profiler.py        # Author analysis & balance metrics
├── dashboard/             # Django web application
│   ├── models.py          # Database models
│   ├── views.py           # Dashboard views
│   ├── templates/         # HTML templates (Tufte-inspired)
│   └── admin.py           # Django admin configuration
├── config/                # Django settings
│   ├── settings.py        # Project settings
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI configuration
├── data/                  # Database and data files
│   └── analysis_results.db
├── scripts/               # Utility scripts
│   └── run_analysis.py    # Main analysis pipeline script
└── manage.py              # Django management script
```

## How It Works

### 1. Data Collection

Articles are collected from diverse news sources:
- BBC News, Reuters, The Guardian, NPR
- Al Jazeera, The Hill, Axios, TechCrunch

The collector extracts:
- Title, author, publication date
- Full article content (or summary)
- Source publication and domain

### 2. Topic Categorization

Each article is classified into one or more categories:

- **Nuclear Energy**: Nuclear power, reactors, atomic technology
- **Data Centers**: Cloud infrastructure, server farms, edge computing
- **Healthcare**: Medical systems, treatment, public health
- **Immigration**: Border policy, refugee matters, asylum
- **Technology Industry**: AI, software, startups, big tech

Methods:
- **Keyword-based** (fast): Pattern matching with curated keyword lists
- **ML-based** (accurate): Zero-shot classification using BART-large-MNLI

### 3. Sentiment Analysis

Emotional valence is measured using `cardiffnlp/twitter-roberta-base-sentiment-latest`:

- **Title valence**: Sentiment of headline (-1 to +1)
- **Content valence**: Sentiment of article body (-1 to +1)
- **Overall valence**: Weighted combination (30% title, 70% content)

Negative values indicate critical/pessimistic tone; positive values indicate optimistic/favorable tone.

### 4. Author Profiling

For each author with 3+ articles per category:

- **Average valence per category**: Mean emotional tone in each topic
- **Valence variance**: Consistency within each category
- **Cross-category variance**: How much tone varies between topics
- **Balance score**: `1 / (1 + cross_category_variance × 10)`

Authors are ranked by:
- **Balance**: Highest balance scores (most consistent across topics)
- **Polarity**: Emotional spectrum within each category

### 5. Complementary Pairing

The system identifies author pairs with opposing valences in the same category:

- **Complementarity score**: Measures how well two authors "cancel out"
- Higher when valences are opposite and similar in magnitude
- Ideal for "rationalized" reading—consume both perspectives

## Dashboard Views

### Landing Page
- Summary statistics and date range
- Overview of all topic categories
- Sample complementary author pairs
- Explanation of the conjugate principle

### Category Views
- Author ranking by emotional valence
- Top complementary pairs for balanced reading
- Sample articles from positive and negative extremes

### Author Profiles
- Valence scores across all categories
- Historical trend over time
- Most positive and negative articles
- Balance score and rank

### Balance Rankings
- All authors ranked by consistency across topics
- Most balanced vs. most polarized
- Comparative analysis

## Methodology & Limitations

### Known Limitations

**Model Bias**: The sentiment model was trained on Twitter data, which may not generalize perfectly to formal news writing.

**Sample Size**: Authors need multiple articles per category for meaningful metrics. Results with <3 articles should be viewed skeptically.

**Topic Misclassification**: Keyword-based categorization can incorrectly classify articles that merely mention a topic in passing.

**Sentiment ≠ Bias**: Negative valence doesn't mean "wrong" or "biased." Critical coverage can be accurate; positive coverage can be misleading.

**Missing Context**: This measures tone, not truthfulness, depth, sourcing quality, or argumentation strength.

### Falsifiability

To test if the system is working:

1. Click through to individual articles and verify sentiment classifications make sense
2. Check sample sizes—ignore authors with <3 articles in a category
3. Look for high variance scores (low confidence in classification)
4. Compare keyword vs. ML categorization methods
5. Manually review complementary pairs—do they actually cover the same events?

### What This Is NOT

- ❌ A truth detector or fact-checker
- ❌ A measure of journalistic quality
- ❌ A political bias detector
- ❌ A replacement for critical thinking

### What This IS

- ✅ An experimental heuristic for exploring emotional framing
- ✅ A tool to surface opposing perspectives on topics
- ✅ A demonstration of sentiment analysis applied to news
- ✅ A starting point for thinking about media consumption patterns

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions on deploying to:
- Render (recommended)
- Railway
- PythonAnywhere

Quick deploy to Render:

```bash
# Push to GitHub
git init
git add .
git commit -m "Initial commit"
git push -u origin main

# Deploy via Render dashboard (auto-detects render.yaml)
```

## Development

### Running Tests

```bash
uv run python manage.py test
```

### Database Migrations

```bash
# Create migrations after model changes
uv run python manage.py makemigrations

# Apply migrations
uv run python manage.py migrate
```

### Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to:
- Browse all articles, authors, and categories
- Manually verify sentiment classifications
- Edit analysis run records

### Re-running Analysis

```bash
# Re-analyze existing data without fetching new articles
uv run python scripts/run_analysis.py --skip-collection

# Fetch fresh data
uv run python scripts/run_analysis.py --months 1
```

## Dependencies

Core libraries:
- **Django 5.2+**: Web framework
- **pandas**: Data processing
- **transformers**: Hugging Face ML models
- **torch**: PyTorch for model inference
- **feedparser**: RSS feed parsing
- **beautifulsoup4**: HTML parsing
- **gunicorn**: Production server
- **whitenoise**: Static file serving

## Contributing

This is a demonstration project. Potential improvements:

1. **Better categorization**: Fine-tune a classifier on news article data
2. **Entity-level sentiment**: Analyze sentiment toward specific entities/topics within articles
3. **Temporal analysis**: Track how author sentiment changes over time or in response to events
4. **Source diversity**: Add more news sources, especially international and niche publications
5. **User feedback**: Allow users to flag incorrect classifications
6. **Alternative metrics**: Explore other measures of balance beyond variance

## License

MIT

## Acknowledgments

- Sentiment model: [cardiffnlp/twitter-roberta-base-sentiment-latest](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest)
- Zero-shot classification: [facebook/bart-large-mnli](https://huggingface.co/facebook/bart-large-mnli)
- News sources: BBC, Reuters, The Guardian, NPR, Al Jazeera, The Hill, Axios, TechCrunch

## Citation

If you use this project in academic work, please cite:

```bibtex
@software{news_rationalizer,
  title = {News Rationalizer: Emotional Valence Analysis in Journalism},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/news-rationalizer}
}
```

## Contact

For questions, issues, or feedback, please open an issue on GitHub.

---

**Disclaimer**: This is an experimental tool for educational and research purposes. Results should be interpreted with caution and skepticism. Always verify sentiment classifications and consider multiple sources when evaluating news coverage.
