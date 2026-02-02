"""
Instagram Scraper via Apify
Monitora trend visivi con focus su Reel/Video
Priorità: Commenti e Condivisioni > Like
"""

import requests
import time


class InstagramScraper:
    """Scraper per Instagram usando Apify"""

    def __init__(self, apify_api_key):
        self.api_key = apify_api_key
        self.actor_id = 'shu8hvrXbJbY3Eb9W'

    def scrape(self, business_name):
        """
        Scrape Instagram per trend visivi
        """
        if not self.api_key:
            return self._mock_data()

        try:
            hashtags = [f'#{business_name.lower()}', '#sunset', '#aperitivo', '#mare']
            posts = []

            for tag in hashtags[:2]:
                tag_posts = self._scrape_hashtag(tag)
                posts.extend(tag_posts)

            return self._analyze_posts(posts)

        except Exception as e:
            print(f"Instagram scraping error: {e}")
            return self._mock_data()

    def _scrape_hashtag(self, hashtag):
        """Scrape posts per hashtag"""
        url = f"https://api.apify.com/v2/acts/{self.actor_id}/runs"

        payload = {
            'hashtags': [hashtag],
            'resultsLimit': 30
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

    def _analyze_posts(self, posts):
        """
        Analizza post con focus su engagement qualitativo
        Peso: Commenti e Condivisioni > Like
        """
        trends = []
        top_hashtags = []
        video_count = 0

        for post in posts[:30]:
            # Priorità Reel/Video
            if post.get('type') in ['Reel', 'Video']:
                video_count += 1

            # Calcola engagement qualitativo
            comments = post.get('commentsCount', 0)
            shares = post.get('sharesCount', 0)
            likes = post.get('likesCount', 0)

            # Formula: (Commenti * 3) + (Condivisioni * 5) + Like
            engagement_score = (comments * 3) + (shares * 5) + likes

            post['quality_score'] = engagement_score

            # Estrai trend
            caption = post.get('caption', '').lower()
            if 'tramonto' in caption or 'sunset' in caption:
                trends.append('Reel tramonto')
            if 'aperitivo' in caption:
                trends.append('Aperitivo vista mare')

            # Hashtag
            hashtags = post.get('hashtags', [])
            top_hashtags.extend(hashtags[:3])

        # Ordina per quality score
        posts.sort(key=lambda x: x.get('quality_score', 0), reverse=True)

        return {
            'trends': list(set(trends))[:5],
            'hashtags': list(set(top_hashtags))[:10],
            'video_percentage': (video_count / len(posts) * 100) if posts else 0,
            'top_posts': posts[:5]
        }

    def _mock_data(self):
        """Dati mock per test"""
        return {
            'trends': ['Reel tramonto', 'Aperitivo vista mare', 'Cocktail signature'],
            'hashtags': ['#sunset', '#aperitivo', '#mare', '#cocktails'],
            'video_percentage': 75,
            'top_posts': []
        }
