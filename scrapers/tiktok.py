"""
TikTok Scraper via Apify
Monitora trend audio e hashtag
Focus su Reel/Video
"""

import requests
import time


class TikTokScraper:
    """Scraper per TikTok usando Apify"""

    def __init__(self, apify_api_key):
        self.api_key = apify_api_key
        self.actor_id = 'GdYC2FRRVehRJJVKw'

    def scrape(self, business_name):
        """
        Scrape TikTok per trend
        """
        if not self.api_key:
            return self._mock_data()

        try:
            hashtags = [f'#{business_name.lower()}', '#sunset', '#aperitivo']
            videos = []

            for tag in hashtags[:2]:
                tag_videos = self._scrape_hashtag(tag)
                videos.extend(tag_videos)

            return self._analyze_videos(videos)

        except Exception as e:
            print(f"TikTok scraping error: {e}")
            return self._mock_data()

    def _scrape_hashtag(self, hashtag):
        """Scrape video per hashtag"""
        url = f"https://api.apify.com/v2/acts/{self.actor_id}/runs"

        payload = {
            'hashtags': [hashtag],
            'resultsPerPage': 30
        }

        try:
            response = requests.post(
                f"{url}?token={self.api_key}",
                json=payload,
                timeout=10
            )

            if response.status_code != 201:
                return []

            run_id = response.json()['data']['id']
            dataset_id = self._wait_for_completion(run_id)

            if dataset_id:
                return self._fetch_dataset(dataset_id)

        except Exception as e:
            print(f"Error scraping {hashtag}: {e}")

        return []

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
        except:
            pass

        return []

    def _analyze_videos(self, videos):
        """
        Analizza video TikTok per trend audio e visual
        """
        audio_trends = []
        visual_trends = []
        hashtags = []

        for video in videos[:30]:
            # Audio trend
            audio = video.get('musicTitle', '')
            if audio:
                audio_trends.append(audio)

            # Visual trend dalla descrizione
            desc = video.get('text', '').lower()
            if 'tramonto' in desc or 'sunset' in desc:
                visual_trends.append('Tramonto')
            if 'cocktail' in desc or 'drink' in desc:
                visual_trends.append('Cocktail making')

            # Hashtag
            tags = video.get('hashtags', [])
            hashtags.extend(tags)

        return {
            'trending_audio': list(set(audio_trends))[:5],
            'visual_trends': list(set(visual_trends))[:5],
            'hashtags': list(set(hashtags))[:10],
            'total_videos': len(videos)
        }

    def _mock_data(self):
        """Dati mock per test"""
        return {
            'trending_audio': ['Summer Vibes Mix', 'Lounge Music'],
            'visual_trends': ['Tramonto', 'Cocktail making'],
            'hashtags': ['#sunset', '#cocktails', '#summervibes'],
            'total_videos': 25
        }
