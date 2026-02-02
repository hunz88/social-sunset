"""
Facebook Scraper via Apify
Analisi gruppi locali per eventi e richieste community
"""

import requests
import time


class FacebookScraper:
    """Scraper per Facebook usando Apify"""

    def __init__(self, apify_api_key):
        self.api_key = apify_api_key
        self.actor_id = 'I1DX7BYeUCWBXl1F7'

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
        url = f"https://api.apify.com/v2/acts/{self.actor_id}/runs"

        payload = {
            'startUrls': [
                {'url': f'https://www.facebook.com/search/top/?q={search_query} eventi'}
            ],
            'resultsLimit': 20
        }

        try:
            response = requests.post(
                f"{url}?token={self.api_key}",
                json=payload,
                timeout=10
            )

            if response.status_code != 201:
                return {}

            run_id = response.json()['data']['id']
            dataset_id = self._wait_for_completion(run_id)

            if dataset_id:
                return self._fetch_dataset(dataset_id)

        except Exception as e:
            print(f"Apify Facebook error: {e}")

        return {}

    def _wait_for_completion(self, run_id, max_wait=60):
        """Attende completamento run"""
        url = f"https://api.apify.com/v2/acts/runs/{run_id}"
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{url}?token={self.api_key}", timeout=5)
                data = response.json()
                status = data['data']['status']

                if status == 'SUCCEEDED':
                    return data['data']['defaultDatasetId']
                elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                    return None

                time.sleep(3)
            except:
                return None

        return None

    def _fetch_dataset(self, dataset_id):
        """Recupera dataset"""
        url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

        try:
            response = requests.get(f"{url}?token={self.api_key}", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching Facebook dataset: {e}")

        return []

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
