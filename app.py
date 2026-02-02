#!/usr/bin/env python3
"""
Sunset Social - Marketing Strategy Monitor
Ottimizzato per Raspberry Pi - Porta 4123
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# Import scrapers
from scrapers.google_maps import GoogleMapsScraper
from scrapers.instagram import InstagramScraper
from scrapers.tiktok import TikTokScraper
from scrapers.facebook import FacebookScraper

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sunset-social-2024')

# Configurazione
CONFIG = {
    'business_name': os.environ.get('BUSINESS_NAME', 'Sunset'),
    'gemini_api_key': os.environ.get('GEMINI_API_KEY', ''),
    'apify_api_key': os.environ.get('APIFY_API_KEY', ''),
    'port': int(os.environ.get('PORT', 4123)),
    'data_dir': os.path.expanduser('~/SunsetSocial/data'),
    'posts_dir': os.path.expanduser('~/SunsetSocial/post_pronti'),
    'competitors': ['Bar del Porto', 'Lounge Mediterraneo', 'Beach Club'],
    'location': os.environ.get('LOCATION', 'zona porto/spiaggia'),
}

# Crea directory se non esistono
os.makedirs(CONFIG['data_dir'], exist_ok=True)
os.makedirs(CONFIG['posts_dir'], exist_ok=True)

# Storage in-memory
pending_ideas = []
approved_ideas = []
last_run_time = None


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
            print(f"Gemini error: {e}")
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
    
    print(f"[{datetime.now()}] Running scrapers...")
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
        pending_ideas.extend(ideas)

        print(f"[{datetime.now()}] Generated {len(ideas)} ideas")

    except Exception as e:
        print(f"Error in scrapers: {e}")


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


@app.route('/')
def index():
    return render_template('dashboard.html',
                         pending=pending_ideas,
                         approved=approved_ideas[-10:],
                         config=CONFIG,
                         last_run=last_run_time)


@app.route('/api/approve/<int:idea_id>', methods=['POST'])
def approve_idea(idea_id):
    global pending_ideas, approved_ideas
    if 0 <= idea_id < len(pending_ideas):
        idea = pending_ideas.pop(idea_id)
        idea['status'] = 'approved'
        approved_ideas.append(idea)
        save_approved_idea(idea)
        return jsonify({'success': True, 'message': 'Idea approvata!'})
    return jsonify({'success': False, 'message': 'Idea non trovata'}), 404


@app.route('/api/reject/<int:idea_id>', methods=['POST'])
def reject_idea(idea_id):
    global pending_ideas
    if 0 <= idea_id < len(pending_ideas):
        pending_ideas.pop(idea_id)
        return jsonify({'success': True, 'message': 'Idea scartata'})
    return jsonify({'success': False, 'message': 'Idea non trovata'}), 404


@app.route('/api/run-now', methods=['POST'])
def run_now():
    run_scrapers()
    return jsonify({'success': True, 'message': 'Scrapers avviati!'})


@app.route('/api/stats')
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
    print("Scheduler initialized: 9:00 and 14:00 daily")


if __name__ == '__main__':
    print(f"""
    ╔════════════════════════════════════════╗
    ║      🌅 SUNSET SOCIAL MONITOR 🌅      ║
    ║  Marketing Strategy AI for Raspberry   ║
    ╚════════════════════════════════════════╝

    Port: {CONFIG['port']}
    Dashboard: http://localhost:{CONFIG['port']}
    """)

    init_scheduler()

    app.run(
        host='0.0.0.0',
        port=CONFIG['port'],
        debug=False,
        threaded=True
    )
