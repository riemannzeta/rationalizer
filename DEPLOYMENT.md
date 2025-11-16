# Deployment Guide

News Rationalizer can be deployed to various free-tier hosting platforms. Here are instructions for the most common options:

## Option 1: Render (Recommended)

Render offers free tier hosting with automatic deployments from Git.

### Steps:

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo-url>
   git push -u origin main
   ```

2. **Create Render account:**
   - Go to https://render.com and sign up
   - Connect your GitHub account

3. **Create new Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will detect the `render.yaml` file

4. **Configure environment:**
   - Render will auto-generate a `SECRET_KEY`
   - Set `ALLOWED_HOSTS` to your Render domain (e.g., `your-app.onrender.com`)

5. **Deploy:**
   - Click "Create Web Service"
   - Wait for build to complete (first build takes ~10-15 minutes due to ML dependencies)

6. **Run initial analysis:**
   - After deployment, access the Render shell
   - Run: `uv run python scripts/run_analysis.py`

### Notes:
- Free tier spins down after 15 minutes of inactivity
- Database is SQLite (persists between deployments but not between service recreations)
- For production, upgrade to paid tier with PostgreSQL

## Option 2: Railway

Railway also offers free tier with $5/month credit.

### Steps:

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and initialize:**
   ```bash
   railway login
   railway init
   ```

3. **Deploy:**
   ```bash
   railway up
   ```

4. **Set environment variables:**
   ```bash
   railway variables set SECRET_KEY=<random-secret-key>
   railway variables set DEBUG=False
   railway variables set ALLOWED_HOSTS=<your-railway-domain>
   ```

5. **Run migrations:**
   ```bash
   railway run python manage.py migrate
   railway run python manage.py collectstatic --noinput
   ```

6. **Run analysis:**
   ```bash
   railway run python scripts/run_analysis.py
   ```

## Option 3: PythonAnywhere

PythonAnywhere offers free tier specifically for Python apps.

### Steps:

1. **Create account:**
   - Sign up at https://www.pythonanywhere.com

2. **Upload code:**
   - Use Git clone or upload via web interface

3. **Create virtual environment:**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.11 rationalizer
   pip install uv
   uv sync
   ```

4. **Configure web app:**
   - Web tab → Add a new web app
   - Manual configuration → Python 3.11
   - Set source code directory
   - Set WSGI configuration file to point to `config/wsgi.py`

5. **Run initial setup:**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   python scripts/run_analysis.py
   ```

## Environment Variables

Required environment variables for production:

```bash
SECRET_KEY=<random-50-char-string>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## Running Analysis Updates

To update the data with fresh articles:

```bash
# On Render/Railway (via shell)
uv run python scripts/run_analysis.py

# With specific options
uv run python scripts/run_analysis.py --months 3 --max-per-source 50

# Skip collection, just re-analyze existing data
uv run python scripts/run_analysis.py --skip-collection
```

## Monitoring & Maintenance

- **Database size:** SQLite file grows with more articles. Monitor `data/analysis_results.db`
- **Memory usage:** ML models require ~2-3GB RAM during analysis
- **Build time:** First deployment takes 10-15 minutes due to PyTorch/transformers
- **Update frequency:** Run analysis weekly/monthly to keep data fresh

## Troubleshooting

### Build fails with "Out of memory"
- Reduce `--max-per-source` during analysis
- Consider using keyword-based categorization instead of ML (`--use-ml` flag)

### Static files not loading
```bash
python manage.py collectstatic --noinput
```

### Database locked errors
- Ensure only one analysis process runs at a time
- SQLite doesn't handle concurrent writes well

### Slow page loads
- First request after spin-down takes time to load ML models
- Consider caching or switching to PostgreSQL for production
