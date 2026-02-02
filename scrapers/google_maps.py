"""
Google Maps Scraper via Apify
Estrae recensioni del Sunset e competitor per sentiment analysis
"""

import requests
import time


class GoogleMapsScraper:
    """Scraper per Google Maps usando Apify"""

    def __init__(self, apify_api_key):
        self.api_key = apify_api_key
        self.actor_id = 'nwua9Gu5YrADL7ZDj'

    def scrape(self, business_name, competitors):
        """
        Scrape recensioni del business e competitor
        """
        if not self.api_key:
            return self._mock_data()

        try:
            our_data = self._scrape_place(business_name)
            competitor_data = []
            
            for comp in competitors[:2]:
                comp_data = self._scrape_place(comp)
                if comp_data:
                    competitor_data.append(comp_data)

            return self._analyze_reviews(our_data, competitor_data)

        except Exception as e:
            print(f"Google Maps scraping error: {e}")
            return self._mock_data()

    def _scrape_place(self, place_name):
        """Scrape singolo locale"""
        url = f"https://api.apify.com/v2/acts/{self.actor_id}/runs"

        payload = {
            'searchStringsArray': [place_name],
            'maxReviews': 50,
            'language': 'it'
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
            print(f"Error scraping {place_name}: {e}")

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
                elif status in ['FAILED', 'ABORTED']:
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
            print(f"Error fetching dataset: {e}")

        return []

    def _analyze_reviews(self, our_reviews, competitor_reviews):
        """
        Analisi sentiment delle recensioni
        """
        positive_aspects = []
        improvements = []
        competitor_insights = []

        # Analizza nostre recensioni
        for review in our_reviews[:30]:
            text = review.get('text', '').lower()
            stars = review.get('stars', 0)

            if stars >= 4:
                if 'tramonto' in text or 'vista' in text:
                    positive_aspects.append('Vista tramonto')
                if 'cocktail' in text or 'drink' in text:
                    positive_aspects.append('Cocktail')
            else:
                if 'servizio' in text or 'attesa' in text:
                    improvements.append('Velocizzare servizio')

        # Analizza competitor
        for comp_data in competitor_reviews:
            for review in comp_data[:20]:
                text = review.get('text', '').lower()
                if 'manca' in text or 'vorrei' in text:
                    competitor_insights.append(text[:100])

        return {
            'our_reviews': our_reviews[:10],
            'positive_aspects': list(set(positive_aspects))[:5],
            'improvements': list(set(improvements))[:3],
            'competitor_insights': competitor_insights[:3]
        }

    def _mock_data(self):
        """Dati mock per test"""
        return {
            'our_reviews': [
                {'text': 'Vista tramonto spettacolare, cocktail ottimi!', 'stars': 5},
                {'text': 'Location bellissima sul mare', 'stars': 4}
            ],
            'positive_aspects': ['Vista tramonto', 'Cocktail', 'Location mare'],
            'improvements': ['Servizio più veloce'],
            'competitor_insights': ['Mancano eventi live', 'Vorrei più opzioni vegetariane']
        }
