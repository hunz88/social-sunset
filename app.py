#!/usr/bin/env python3
"""
Sunset Social - Marketing Strategy Monitor
Ottimizzato per Raspberry Pi - Porta 4123
"""

import os
import json
import secrets
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, render_template_string
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# Import scrapers
from scrapers.google_maps import GoogleMapsScraper
from scrapers.instagram import InstagramScraper
from scrapers.tiktok import TikTokScraper
from scrapers.facebook import FacebookScraper

# Import auth and storage
from auth import login_required, check_password, LOGIN_TEMPLATE
from storage import DataStore


# Configure logging
def setup_logging(data_dir):
    """Setup structured logging to file and console"""
    log_dir = os.path.join(data_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f'sunset_social_{datetime.now().strftime("%Y%m%d")}.log')

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler (INFO and above)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Console handler (WARNING and above for production, INFO for dev)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Reduce noise from external libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

    return logging.getLogger('sunset_social')


app = Flask(__name__)

# Generate secure SECRET_KEY if not provided
if not os.environ.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = secrets.token_hex(32)
    # Note: logger not initialized yet at this point, use print
    print("⚠️  WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY in .env for production!")
else:
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Configurazione
CONFIG = {
    'business_name': os.environ.get('BUSINESS_NAME', 'Sunset'),
    'gemini_api_key': os.environ.get('GEMINI_API_KEY', ''),
    'apify_api_key': os.environ.get('APIFY_API_KEY', ''),
    'admin_password': os.environ.get('ADMIN_PASSWORD', 'sunset2024'),
    'port': int(os.environ.get('PORT', 4123)),
    'data_dir': os.path.expanduser('~/SunsetSocial/data'),
    'posts_dir': os.path.expanduser('~/SunsetSocial/post_pronti'),
    'competitors': os.environ.get('COMPETITORS', 'Bar del Porto,Lounge Mediterraneo,Beach Club').split(','),
    'location': os.environ.get('LOCATION', 'zona porto/spiaggia'),
}

# Crea directory se non esistono
os.makedirs(CONFIG['data_dir'], exist_ok=True)
os.makedirs(CONFIG['posts_dir'], exist_ok=True)

# Initialize logging
logger = setup_logging(CONFIG['data_dir'])

# Initialize persistent storage
datastore = DataStore(CONFIG['data_dir'])
pending_ideas = datastore.load_pending()
approved_ideas = datastore.load_approved()
last_run_time = None

logger.info(f"Loaded {len(pending_ideas)} pending ideas and {len(approved_ideas)} approved ideas from storage")


class GeminiStrategy:
    """Integrazione con Gemini AI"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

    def generate_ideas(self, scraped_data):
        if not self.api_key:
            return self._mock_ideas(scraped_data)

        prompt = self._build_prompt(scraped_data)

        try:
            headers = {'Content-Type': 'application/json'}
            payload = {
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {
                    'temperature': 0.9,
                    'maxOutputTokens': 2048,
                }
            }

            response = requests.post(
                f"{self.endpoint}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                return self._parse_ideas(text, scraped_data)
            else:
                return self._mock_ideas(scraped_data)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._mock_ideas(scraped_data)

    def _build_prompt(self, data):
        return f"""
Sei un esperto marketing per "{CONFIG['business_name']}" in {CONFIG['location']}.

DATI RACCOLTI:
- Google Maps: {len(data.get('google_maps', {}).get('our_reviews', []))} recensioni
- Aspetti positivi: {', '.join(data.get('google_maps', {}).get('positive_aspects', []))}
- Trend social: {', '.join(data.get('social', {}).get('visual_trends', []))}
- Eventi locali: {', '.join(data.get('facebook', {}).get('local_events', []))}

Genera 3 idee marketing in formato JSON:
[
  {{
    "titolo": "...",
    "descrizione": "...",
    "testo_post": "...",
    "media_suggeriti": "...",
    "piattaforma": "Instagram/TikTok/Facebook",
    "affidabilita": "Alta/Media/Bassa"
  }}
]
"""

    def _parse_ideas(self, text, scraped_data):
        try:
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end > start:
                ideas = json.loads(text[start:end])
                for idea in ideas:
                    idea['timestamp'] = datetime.now().isoformat()
                    idea['data_source'] = scraped_data
                    idea['status'] = 'pending'
                return ideas[:3]
        except:
            pass
        return self._mock_ideas(scraped_data)

    def _mock_ideas(self, scraped_data):
        return [
            {
                'titolo': '🌅 Golden Hour Special',
                'descrizione': 'Promuovi cocktail al tramonto',
                'testo_post': '🌅 Il tramonto più bello? Con un cocktail da Sunset! #SunsetVibes #GoldenHour',
                'media_suggeriti': 'Reel: Time-lapse tramonto con cocktail',
                'piattaforma': 'Instagram + TikTok',
                'affidabilita': 'Alta',
                'timestamp': datetime.now().isoformat(),
                'data_source': scraped_data,
                'status': 'pending'
            },
            {
                'titolo': '📸 User Generated Content',
                'descrizione': 'Incoraggia clienti a condividere',
                'testo_post': '📸 Tagga @sunset e usa #MySunsetMoment! 🌊',
                'media_suggeriti': 'Carosello foto clienti',
                'piattaforma': 'Instagram',
                'affidabilita': 'Media',
                'timestamp': datetime.now().isoformat(),
                'data_source': scraped_data,
                'status': 'pending'
            },
            {
                'titolo': '🎉 Weekend Event',
                'descrizione': 'Evento weekend',
                'testo_post': '🎉 Live Music & Aperitivo questo weekend! Prenota ora!',
                'media_suggeriti': 'Locandina evento',
                'piattaforma': 'Facebook',
                'affidabilita': 'Media',
                'timestamp': datetime.now().isoformat(),
                'data_source': scraped_data,
                'status': 'pending'
            }
        ]


def run_scrapers():
    """Esegue scrapers e genera idee"""
    global pending_ideas, last_run_time

    logger.info("Running scrapers...")
    last_run_time = datetime.now()

    scraped_data = {
        'timestamp': datetime.now().isoformat(),
        'google_maps': {},
        'social': {},
        'facebook': {}
    }

    try:
        gmaps = GoogleMapsScraper(CONFIG['apify_api_key'])
        scraped_data['google_maps'] = gmaps.scrape(
            CONFIG['business_name'],
            CONFIG['competitors']
        )

        insta = InstagramScraper(CONFIG['apify_api_key'])
        tiktok = TikTokScraper(CONFIG['apify_api_key'])
        
        scraped_data['social'] = {
            'instagram': insta.scrape(CONFIG['business_name']),
            'tiktok': tiktok.scrape(CONFIG['business_name']),
            'visual_trends': ['reels tramonto', 'aperitivo vista mare'],
            'trending_hashtags': ['#sunset', '#aperitivo', '#mare']
        }

        fb = FacebookScraper(CONFIG['apify_api_key'])
        scraped_data['facebook'] = fb.scrape(CONFIG['location'])

        save_scraped_data(scraped_data)

        gemini = GeminiStrategy(CONFIG['gemini_api_key'])
        ideas = gemini.generate_ideas(scraped_data)
        datastore.add_pending(pending_ideas, ideas)

        logger.info(f"Generated {len(ideas)} ideas (Total pending: {len(pending_ideas)})")

    except Exception as e:
        logger.error(f"Error in scrapers: {e}", exc_info=True)


def save_scraped_data(data):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(CONFIG['data_dir'], f'scraped_{timestamp}.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_approved_idea(idea):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{idea['titolo'][:30].replace(' ', '_')}.json"
    filepath = os.path.join(CONFIG['posts_dir'], filename)
    idea['approved_at'] = datetime.now().isoformat()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(idea, f, indent=2, ensure_ascii=False)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if check_password(password, CONFIG['admin_password']):
            session['authenticated'] = True
            session.permanent = True
            next_url = request.form.get('next') or url_for('index')
            return redirect(next_url)
        else:
            return render_template_string(LOGIN_TEMPLATE, error='Password errata', next_url=request.form.get('next', ''))

    next_url = request.args.get('next', '')
    return render_template_string(LOGIN_TEMPLATE, error=None, next_url=next_url)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/')
@login_required
def index():
    return render_template('dashboard.html',
                         pending=pending_ideas,
                         approved=approved_ideas[-10:],
                         config=CONFIG,
                         last_run=last_run_time)


@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html', config=CONFIG)


@app.route('/api/save-config', methods=['POST'])
@login_required
def save_config():
    """Save configuration to .env file"""
    try:
        data = request.get_json()

        # Update .env file
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        env_vars = {}

        # Read existing .env
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()

        # Update with new values (only if not empty)
        if data.get('gemini_api_key'):
            env_vars['GEMINI_API_KEY'] = data['gemini_api_key']
        if data.get('apify_api_key'):
            env_vars['APIFY_API_KEY'] = data['apify_api_key']
        if data.get('admin_password'):
            env_vars['ADMIN_PASSWORD'] = data['admin_password']
        if data.get('business_name'):
            env_vars['BUSINESS_NAME'] = data['business_name']
        if data.get('location'):
            env_vars['LOCATION'] = data['location']
        if data.get('competitors'):
            env_vars['COMPETITORS'] = data['competitors']
        if data.get('port'):
            env_vars['PORT'] = str(data['port'])

        # Add SECRET_KEY if not exists
        if 'SECRET_KEY' not in env_vars:
            env_vars['SECRET_KEY'] = secrets.token_hex(32)

        # Write back to .env
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Sunset Social Configuration\n")
            f.write("# Generated/Updated by Settings Page\n\n")
            f.write("# API Keys\n")
            f.write(f"GEMINI_API_KEY={env_vars.get('GEMINI_API_KEY', '')}\n")
            f.write(f"APIFY_API_KEY={env_vars.get('APIFY_API_KEY', '')}\n\n")
            f.write("# Security\n")
            f.write(f"SECRET_KEY={env_vars.get('SECRET_KEY', '')}\n")
            f.write(f"ADMIN_PASSWORD={env_vars.get('ADMIN_PASSWORD', 'sunset2024')}\n\n")
            f.write("# Configuration\n")
            f.write(f"BUSINESS_NAME={env_vars.get('BUSINESS_NAME', 'Sunset')}\n")
            f.write(f"LOCATION={env_vars.get('LOCATION', 'zona porto/spiaggia')}\n")
            f.write(f"COMPETITORS={env_vars.get('COMPETITORS', 'Bar del Porto,Lounge Mediterraneo,Beach Club')}\n")
            f.write(f"PORT={env_vars.get('PORT', '4123')}\n")

        logger.info("Configuration saved successfully to .env")
        return jsonify({'success': True, 'message': 'Configurazione salvata!'})

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/approve/<int:idea_id>', methods=['POST'])
@login_required
def approve_idea(idea_id):
    global pending_ideas, approved_ideas
    idea = datastore.approve_idea(pending_ideas, approved_ideas, idea_id)
    if idea:
        save_approved_idea(idea)
        return jsonify({'success': True, 'message': 'Idea approvata!'})
    return jsonify({'success': False, 'message': 'Idea non trovata'}), 404


@app.route('/api/reject/<int:idea_id>', methods=['POST'])
@login_required
def reject_idea(idea_id):
    global pending_ideas
    idea = datastore.reject_idea(pending_ideas, idea_id)
    if idea:
        return jsonify({'success': True, 'message': 'Idea scartata'})
    return jsonify({'success': False, 'message': 'Idea non trovata'}), 404


@app.route('/api/run-now', methods=['POST'])
@login_required
def run_now():
    run_scrapers()
    return jsonify({'success': True, 'message': 'Scrapers avviati!'})


@app.route('/api/stats')
@login_required
def stats():
    return jsonify({
        'pending_count': len(pending_ideas),
        'approved_count': len(approved_ideas),
        'last_run': last_run_time.isoformat() if last_run_time else None,
        'config': {
            'business': CONFIG['business_name'],
            'competitors': CONFIG['competitors']
        }
    })


def init_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_scrapers, trigger='cron', hour=9, minute=0)
    scheduler.add_job(func=run_scrapers, trigger='cron', hour=14, minute=0)
    scheduler.start()
    logger.info("Scheduler initialized: scrapers run at 9:00 and 14:00 daily")


if __name__ == '__main__':
    print(f"""
    ╔════════════════════════════════════════╗
    ║      🌅 SUNSET SOCIAL MONITOR 🌅      ║
    ║  Marketing Strategy AI for Raspberry   ║
    ╚════════════════════════════════════════╝

    Port: {CONFIG['port']}
    Dashboard: http://localhost:{CONFIG['port']}
    Logs: {CONFIG['data_dir']}/logs/
    """)

    logger.info(f"Starting Sunset Social Monitor on port {CONFIG['port']}")
    init_scheduler()

    app.run(
        host='0.0.0.0',
        port=CONFIG['port'],
        debug=False,
        threaded=True
    )
