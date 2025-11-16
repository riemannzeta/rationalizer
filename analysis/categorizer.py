"""
Article Categorization Module - Classifies articles into topic categories.
"""

from typing import List, Dict, Tuple
from transformers import pipeline
import re


# Topic categories and their associated keywords
CATEGORIES = {
    # Government & Policy
    'federal_budget': {
        'label': 'Federal Budget & National Debt',
        'keywords': [
            'federal budget', 'national debt', 'deficit', 'fiscal policy',
            'spending', 'budget deficit', 'debt ceiling', 'appropriations',
            'fiscal cliff', 'sequestration', 'budget resolution', 'CBO',
            'congressional budget office', 'debt-to-GDP', 'budget surplus'
        ],
        'description': 'Federal budget, national debt, spending, deficits, and fiscal policy'
    },
    'immigration': {
        'label': 'Immigration',
        'keywords': [
            'immigration', 'immigrant', 'migrant', 'refugee', 'asylum',
            'border', 'visa', 'green card', 'citizenship', 'deportation',
            'ICE', 'border patrol', 'DACA', 'undocumented', 'illegal immigration',
            'refugee crisis', 'migration', 'border security', 'immigration reform',
            'H1B', 'work visa', 'sanctuary city'
        ],
        'description': 'Immigration, border security, asylum policies, and visa reform'
    },
    'gun_control': {
        'label': 'Gun Control & Second Amendment',
        'keywords': [
            'gun control', 'second amendment', 'firearms', 'gun violence',
            'background check', 'assault weapon', 'NRA', 'gun rights',
            'gun legislation', 'concealed carry', 'open carry', 'red flag law',
            'mass shooting', 'gun safety', 'gun reform', 'ATF',
            'gun permit', 'stand your ground'
        ],
        'description': 'Gun control legislation, Second Amendment rights, court cases, and public debate'
    },
    'elections': {
        'label': 'Elections & Campaign Finance',
        'keywords': [
            'election', 'campaign', 'polling', 'voter', 'ballot',
            'campaign finance', 'PAC', 'super PAC', 'election integrity',
            'voter fraud', 'gerrymandering', 'electoral college', 'primary',
            'caucus', 'midterm', 'presidential election', 'voting rights',
            'FEC', 'campaign contribution', 'dark money'
        ],
        'description': 'Elections, polling, election integrity, campaign finance, and funding'
    },
    'judiciary': {
        'label': 'Judiciary & Supreme Court',
        'keywords': [
            'supreme court', 'SCOTUS', 'judicial', 'justice', 'court ruling',
            'federal judge', 'circuit court', 'appellate court', 'judicial nominee',
            'confirmation', 'judicial philosophy', 'originalism', 'constitutional',
            'court decision', 'dissent', 'majority opinion', 'judicial review',
            'federal judiciary', 'bench', 'judicial appointment'
        ],
        'description': 'Judiciary, Supreme Court rulings, nominations, and judicial philosophy'
    },
    'foreign_policy': {
        'label': 'Foreign Policy & International Trade',
        'keywords': [
            'foreign policy', 'diplomacy', 'international trade', 'tariff',
            'trade agreement', 'USMCA', 'trade war', 'sanctions', 'embargo',
            'trade deficit', 'export', 'import', 'WTO', 'bilateral',
            'multilateral', 'trade deal', 'diplomatic relations', 'treaty',
            'foreign aid', 'state department'
        ],
        'description': 'Foreign policy, tariffs, trade agreements, and diplomatic relations'
    },

    # Economy & Business
    'federal_reserve': {
        'label': 'Federal Reserve & Inflation',
        'keywords': [
            'federal reserve', 'Fed', 'interest rate', 'inflation', 'deflation',
            'monetary policy', 'FOMC', 'Jerome Powell', 'rate hike', 'rate cut',
            'quantitative easing', 'CPI', 'consumer price index', 'core inflation',
            'PCE', 'cost of living', 'price stability', 'central bank'
        ],
        'description': 'Federal Reserve, interest rate policy, inflation, and cost-of-living changes'
    },
    'labor_employment': {
        'label': 'Labor & Employment',
        'keywords': [
            'employment', 'unemployment', 'jobs report', 'labor market',
            'wage', 'salary', 'union', 'unionization', 'collective bargaining',
            'strike', 'labor shortage', 'gig economy', 'minimum wage',
            'unemployment rate', 'job growth', 'hiring', 'layoffs',
            'labor force participation', 'worker rights'
        ],
        'description': 'Jobs reports, employment, unionization, and wage growth'
    },
    'supply_chain': {
        'label': 'Supply Chain Management',
        'keywords': [
            'supply chain', 'logistics', 'shipping', 'port', 'freight',
            'container ship', 'warehouse', 'inventory', 'manufacturing',
            'production', 'shortage', 'backlog', 'bottleneck', 'distribution',
            'just-in-time', 'nearshoring', 'reshoring', 'supplier'
        ],
        'description': 'Supply chain logistics, port activity, and manufacturing resilience'
    },
    'real_estate': {
        'label': 'Real Estate & Housing',
        'keywords': [
            'real estate', 'housing', 'home price', 'mortgage', 'housing market',
            'affordable housing', 'rent', 'rental market', 'homeownership',
            'housing affordability', 'property value', 'foreclosure',
            'housing shortage', 'residential', 'commercial real estate',
            'mortgage rate', 'home sales', 'housing crisis'
        ],
        'description': 'Real estate market trends, housing affordability, and interest rates'
    },
    'small_business': {
        'label': 'Small Business & Entrepreneurship',
        'keywords': [
            'small business', 'startup', 'entrepreneur', 'SMB', 'SME',
            'business loan', 'SBA', 'small business administration',
            'venture capital', 'angel investor', 'seed funding',
            'business regulation', 'small business owner', 'main street',
            'local business', 'franchise', 'business formation'
        ],
        'description': 'Small businesses, startups, lending, and regulatory challenges'
    },

    # Technology & Industry
    'ai_regulation': {
        'label': 'Artificial Intelligence (AI) Regulation',
        'keywords': [
            'AI regulation', 'artificial intelligence policy', 'AI ethics',
            'AI safety', 'algorithmic bias', 'AI governance', 'AI oversight',
            'machine learning regulation', 'AI accountability', 'AI transparency',
            'AI standards', 'responsible AI', 'AI risk', 'AI framework',
            'generative AI', 'large language model', 'LLM'
        ],
        'description': 'AI regulation, policy, ethics, and safety'
    },
    'technology': {
        'label': 'Technology Industry',
        'keywords': [
            'tech industry', 'silicon valley', 'big tech', 'tech company',
            'software', 'platform', 'app', 'digital', 'innovation',
            'tech layoffs', 'antitrust', 'tech monopoly', 'tech earnings',
            'social media', 'content moderation', 'section 230',
            'tech regulation', 'tech sector', 'IPO'
        ],
        'description': 'Technology industry, layoffs, innovations, and antitrust'
    },
    'data_centers': {
        'label': 'Data Center Development',
        'keywords': [
            'data center', 'data centre', 'server farm', 'cloud infrastructure',
            'colocation', 'hyperscale', 'edge computing', 'datacenter',
            'data storage', 'server rack', 'cooling', 'power usage effectiveness',
            'PUE', 'AWS', 'Azure', 'Google Cloud', 'data center energy',
            'data center location', 'data center infrastructure'
        ],
        'description': 'Data center development, energy use, location, and infrastructure'
    },
    'cybersecurity': {
        'label': 'Cybersecurity',
        'keywords': [
            'cybersecurity', 'cyber attack', 'data breach', 'hacking',
            'ransomware', 'malware', 'phishing', 'cyber threat',
            'encryption', 'data privacy', 'CISA', 'national security cyber',
            'critical infrastructure', 'cyber defense', 'vulnerability',
            'zero-day', 'security patch', 'cyber espionage'
        ],
        'description': 'Cybersecurity, national security threats, data breaches, and privacy'
    },
    'semiconductor': {
        'label': 'Semiconductor Industry',
        'keywords': [
            'semiconductor', 'chip', 'microchip', 'silicon', 'fab',
            'fabrication', 'TSMC', 'Intel', 'chip shortage', 'CHIPS Act',
            'chip manufacturing', 'foundry', 'wafer', 'chipmaker',
            'semiconductor subsidy', 'chip R&D', 'advanced packaging',
            'chip design', 'EUV lithography'
        ],
        'description': 'Semiconductor industry, domestic manufacturing, subsidies, and R&D'
    },

    # Energy & Environment
    'climate_change': {
        'label': 'Climate Change & Policy',
        'keywords': [
            'climate change', 'global warming', 'greenhouse gas', 'emissions',
            'carbon emissions', 'net zero', 'climate policy', 'Paris agreement',
            'climate accord', 'decarbonization', 'carbon neutral',
            'climate action', 'climate summit', 'IPCC', 'carbon footprint',
            'climate target', 'emissions reduction', 'climate crisis'
        ],
        'description': 'Climate change, emissions reduction, and international agreements'
    },
    'energy_transition': {
        'label': 'Energy Transition',
        'keywords': [
            'renewable energy', 'solar', 'wind', 'solar power', 'wind power',
            'clean energy', 'green energy', 'energy transition', 'solar panel',
            'wind turbine', 'offshore wind', 'solar farm', 'wind farm',
            'grid modernization', 'smart grid', 'energy storage', 'battery storage',
            'transmission lines', 'grid infrastructure'
        ],
        'description': 'Energy transition, renewable sources (solar, wind), and grid modernization'
    },
    'nuclear_energy': {
        'label': 'Nuclear Energy',
        'keywords': [
            'nuclear', 'nuclear power', 'nuclear plant', 'reactor',
            'nuclear energy', 'SMR', 'small modular reactor', 'advanced reactor',
            'uranium', 'nuclear fuel', 'nuclear waste', 'radioactive',
            'atomic energy', 'fission', 'nuclear facility', 'nuclear construction',
            'nuclear license', 'NRC'
        ],
        'description': 'Nuclear energy, new plant development, and SMRs (Small Modular Reactors)'
    },
    'oil_gas': {
        'label': 'Oil & Gas Industry',
        'keywords': [
            'oil', 'gas', 'petroleum', 'crude oil', 'natural gas', 'LNG',
            'oil price', 'gas price', 'OPEC', 'drilling', 'fracking',
            'shale', 'pipeline', 'refinery', 'oil production', 'energy independence',
            'strategic petroleum reserve', 'SPR', 'fossil fuel'
        ],
        'description': 'Oil and gas industry, production levels, pricing, and energy independence'
    },
    'water_rights': {
        'label': 'Water Rights & Scarcity',
        'keywords': [
            'water rights', 'water scarcity', 'drought', 'water shortage',
            'Colorado River', 'water allocation', 'water conservation',
            'groundwater', 'aquifer', 'water reservoir', 'Lake Mead',
            'desalination', 'water policy', 'water supply', 'irrigation',
            'water management', 'water crisis', 'western water'
        ],
        'description': 'Water rights and scarcity, particularly in the Western U.S.'
    },

    # Society & Health
    'health_insurance': {
        'label': 'Health Insurance & Policy',
        'keywords': [
            'health insurance', 'ACA', 'Affordable Care Act', 'Obamacare',
            'Medicare', 'Medicaid', 'healthcare policy', 'insurance coverage',
            'health plan', 'premium', 'deductible', 'copay', 'insurance cost',
            'uninsured', 'Medicare for All', 'public option', 'insurance marketplace'
        ],
        'description': 'Health insurance, Affordable Care Act (ACA), Medicare, and costs'
    },
    'pharmaceuticals': {
        'label': 'Pharmaceuticals & Drug Pricing',
        'keywords': [
            'pharmaceutical', 'drug price', 'prescription', 'medication',
            'pharmacy', 'drug cost', 'FDA', 'drug approval', 'clinical trial',
            'pharma', 'generic drug', 'brand name drug', 'drug manufacturer',
            'insulin', 'drug negotiation', 'pharma R&D', 'biopharmaceutical'
        ],
        'description': 'Pharmaceuticals, prescription costs, FDA approvals, and R&D'
    },
    'public_health': {
        'label': 'Public Health',
        'keywords': [
            'public health', 'CDC', 'epidemic', 'pandemic', 'disease',
            'vaccination', 'vaccine', 'immunization', 'outbreak',
            'health crisis', 'infectious disease', 'virus', 'prevention',
            'substance abuse', 'opioid', 'addiction', 'mental health',
            'health emergency', 'WHO'
        ],
        'description': 'Public health, CDC guidance, pandemic preparedness, and substance abuse'
    },
    'education': {
        'label': 'Education (K-12 & Higher Ed)',
        'keywords': [
            'education', 'school', 'K-12', 'elementary', 'high school',
            'college', 'university', 'higher education', 'student loan',
            'curriculum', 'education policy', 'school funding', 'teacher',
            'education reform', 'charter school', 'school choice',
            'standardized test', 'literacy', 'tuition', 'student debt'
        ],
        'description': 'Education, funding, curriculum debates, and student loans'
    },
    'criminal_justice': {
        'label': 'Criminal Justice Reform',
        'keywords': [
            'criminal justice', 'policing', 'police reform', 'prison',
            'incarceration', 'sentencing', 'parole', 'probation',
            'criminal justice reform', 'law enforcement', 'police brutality',
            'mass incarceration', 'bail reform', 'prison reform',
            'recidivism', 'rehabilitation', 'sentencing reform'
        ],
        'description': 'Criminal justice reform, policing, sentencing, and prison systems'
    },
    'social_security': {
        'label': 'Social Security & Entitlements',
        'keywords': [
            'social security', 'SSA', 'retirement', 'pension', 'entitlement',
            'disability', 'SSDI', 'SSI', 'social security trust fund',
            'retirement age', 'social security benefits', 'COLA',
            'cost of living adjustment', 'social security solvency',
            'entitlement reform', 'Medicare trust fund'
        ],
        'description': 'Social Security, entitlements, long-term solvency, and policy debates'
    },

    # Infrastructure & Transport
    'infrastructure': {
        'label': 'National Infrastructure',
        'keywords': [
            'infrastructure', 'roads', 'bridges', 'highway', 'public works',
            'infrastructure bill', 'infrastructure spending', 'construction',
            'transportation infrastructure', 'water infrastructure',
            'sewer', 'infrastructure investment', 'crumbling infrastructure',
            'infrastructure repair', 'federal infrastructure', 'IIJA'
        ],
        'description': 'National infrastructure, roads, bridges, and public works spending'
    },
    'telecommunications': {
        'label': 'Telecommunications',
        'keywords': [
            'telecommunications', '5G', 'broadband', 'internet access',
            'rural broadband', 'fiber optic', 'wireless', 'cellular',
            'net neutrality', 'FCC', 'spectrum', 'telecom', 'connectivity',
            'digital divide', 'internet service provider', 'ISP', 'bandwidth'
        ],
        'description': 'Telecommunications, 5G rollout, rural broadband, and net neutrality'
    },
    'aerospace': {
        'label': 'Aerospace & Aviation',
        'keywords': [
            'aerospace', 'aviation', 'FAA', 'airline', 'aircraft',
            'aviation safety', 'air travel', 'airport', 'Boeing', 'Airbus',
            'space exploration', 'NASA', 'SpaceX', 'satellite', 'rocket',
            'commercial space', 'space industry', 'aviation regulation',
            'flight', 'space mission'
        ],
        'description': 'Aerospace, aviation, FAA regulation, airline industry, and space exploration'
    }
}


class ArticleCategorizer:
    """Categorizes articles into predefined topic categories."""

    def __init__(self, use_ml: bool = False):
        """
        Initialize the categorizer.

        Args:
            use_ml: Whether to use ML-based classification (slower but more accurate)
        """
        self.use_ml = use_ml
        self.classifier = None

        if use_ml:
            try:
                print("Loading zero-shot classification model...")
                self.classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
                print("✓ Model loaded successfully")
            except Exception as e:
                print(f"✗ Could not load ML model: {e}")
                print("  Falling back to keyword-based classification")
                self.use_ml = False

    def categorize_by_keywords(self, text: str, title: str = "") -> Dict[str, float]:
        """
        Categorize article using keyword matching.

        Args:
            text: Article content
            title: Article title (weighted more heavily)

        Returns:
            Dictionary mapping category IDs to confidence scores (0-1)
        """
        # Combine title (weighted 3x) and text
        combined_text = (title.lower() + " ") * 3 + text.lower()

        scores = {}

        for category_id, category_info in CATEGORIES.items():
            # Count keyword matches
            matches = 0
            total_keywords = len(category_info['keywords'])

            for keyword in category_info['keywords']:
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, combined_text):
                    matches += 1

            # Calculate confidence score
            # Use a sigmoid-like function to scale the score
            raw_score = matches / total_keywords if total_keywords > 0 else 0

            # Boost score if multiple keywords found
            if matches >= 3:
                raw_score = min(1.0, raw_score * 1.5)
            elif matches >= 2:
                raw_score = min(1.0, raw_score * 1.2)

            scores[category_id] = round(raw_score, 3)

        return scores

    def categorize_by_ml(self, text: str, title: str = "") -> Dict[str, float]:
        """
        Categorize article using zero-shot classification.

        Args:
            text: Article content
            title: Article title

        Returns:
            Dictionary mapping category IDs to confidence scores (0-1)
        """
        if not self.classifier:
            return self.categorize_by_keywords(text, title)

        # Use title + first 500 chars of content for classification
        sample_text = f"{title}. {text[:500]}"

        # Get category labels and descriptions
        candidate_labels = [info['description'] for info in CATEGORIES.values()]

        try:
            result = self.classifier(
                sample_text,
                candidate_labels,
                multi_label=True
            )

            # Map results back to category IDs
            scores = {}
            category_ids = list(CATEGORIES.keys())

            for label, score in zip(result['labels'], result['scores']):
                # Find matching category
                for cat_id in category_ids:
                    if CATEGORIES[cat_id]['description'] == label:
                        scores[cat_id] = round(score, 3)
                        break

            return scores

        except Exception as e:
            print(f"✗ ML classification failed: {e}")
            return self.categorize_by_keywords(text, title)

    def categorize_article(
        self,
        article: Dict,
        min_confidence: float = 0.15
    ) -> List[Tuple[str, float]]:
        """
        Categorize a single article.

        Args:
            article: Article dictionary with 'title' and 'content'
            min_confidence: Minimum confidence threshold for category assignment

        Returns:
            List of (category_id, confidence) tuples
        """
        text = article.get('content', '') or article.get('summary', '')
        title = article.get('title', '')

        if not text and not title:
            return []

        # Get scores
        if self.use_ml:
            scores = self.categorize_by_ml(text, title)
        else:
            scores = self.categorize_by_keywords(text, title)

        # Filter by confidence threshold and sort
        categories = [
            (cat_id, score)
            for cat_id, score in scores.items()
            if score >= min_confidence
        ]

        categories.sort(key=lambda x: x[1], reverse=True)

        return categories

    def categorize_batch(
        self,
        articles: List[Dict],
        min_confidence: float = 0.15
    ) -> List[Dict]:
        """
        Categorize a batch of articles.

        Args:
            articles: List of article dictionaries
            min_confidence: Minimum confidence threshold

        Returns:
            Articles with added 'categories' field
        """
        print(f"\n📊 Categorizing {len(articles)} articles...")

        categorized = []

        for i, article in enumerate(articles):
            if i % 50 == 0:
                print(f"  Processing {i+1}/{len(articles)}...")

            categories = self.categorize_article(article, min_confidence)

            # Add categories to article
            article['categories'] = categories

            # Add primary category
            if categories:
                article['primary_category'] = categories[0][0]
                article['primary_confidence'] = categories[0][1]
            else:
                article['primary_category'] = None
                article['primary_confidence'] = 0.0

            categorized.append(article)

        # Print statistics
        categorized_count = sum(1 for a in categorized if a['categories'])
        print(f"\n✓ Categorized {categorized_count}/{len(articles)} articles")

        # Category distribution
        category_counts = {}
        for article in categorized:
            for cat_id, _ in article.get('categories', []):
                category_counts[cat_id] = category_counts.get(cat_id, 0) + 1

        print("\nCategory distribution:")
        for cat_id, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {CATEGORIES[cat_id]['label']}: {count}")

        return categorized


def categorize_articles(
    articles: List[Dict],
    use_ml: bool = False,
    min_confidence: float = 0.15
) -> List[Dict]:
    """
    Main function to categorize articles.

    Args:
        articles: List of article dictionaries
        use_ml: Whether to use ML-based classification
        min_confidence: Minimum confidence threshold

    Returns:
        Articles with categories added
    """
    categorizer = ArticleCategorizer(use_ml=use_ml)
    return categorizer.categorize_batch(articles, min_confidence)
