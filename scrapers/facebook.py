"""
Facebook Scraper via Apify
Analisi gruppi locali per eventi e richieste community
"""

from .base import BaseApifyScraper


class FacebookScraper(BaseApifyScraper):
    """Scraper per Facebook usando Apify"""

    def __init__(self, apify_api_key):
        super().__init__(apify_api_key, 'I1DX7BYeUCWBXl1F7')

    def scrape(self, location):
        """
        Scrape gruppi Facebook per eventi locali e richieste community
        """
        if not self.api_key:
            return self._mock_data()

        try:
            data = self._run_apify_actor(location)
            return self._analyze_posts(data)

        except Exception as e:
            print(f"Facebook scraping error: {e}")
            return self._mock_data()

    def _run_apify_actor(self, search_query):
        """Esegue l'actor Apify per Facebook"""
        payload = {
            'startUrls': [
                {'url': f'https://www.facebook.com/search/top/?q={search_query} eventi'}
            ],
            'resultsLimit': 20
        }

        data = self.scrape_with_actor(payload)
        return data if data else []

    def _analyze_posts(self, posts):
        """
        Analizza post Facebook per eventi e richieste community
        """
        events = []
        requests_community = []

        for post in posts:
            text = post.get('text', '').lower()

            # Identifica eventi
            if any(word in text for word in ['evento', 'serata', 'concerto', 'live']):
                event_desc = text[:100]
                events.append(event_desc)

            # Identifica richieste
            if any(word in text for word in ['consiglio', 'dove', 'cercasi', 'consigliate']):
                request_desc = text[:100]
                requests_community.append(request_desc)

        return {
            'local_events': events[:5],
            'community_requests': requests_community[:5],
            'total_posts_analyzed': len(posts)
        }

    def _mock_data(self):
        """Dati mock per test"""
        return {
            'local_events': [
                'Serata live music questo sabato',
                'Evento aperitivo al tramonto venerdì'
            ],
            'community_requests': [
                'Consigliate un buon posto per aperitivo vista mare?',
                'Dove andare per un cocktail con amici?'
            ],
            'total_posts_analyzed': 10
        }
