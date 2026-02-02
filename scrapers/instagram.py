"""
Instagram Scraper via Apify
Monitora trend visivi con focus su Reel/Video
Priorità: Commenti e Condivisioni > Like
"""

from .base import BaseApifyScraper


class InstagramScraper(BaseApifyScraper):
    """Scraper per Instagram usando Apify"""

    def __init__(self, apify_api_key):
        super().__init__(apify_api_key, 'shu8hvrXbJbY3Eb9W')

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
        payload = {
            'hashtags': [hashtag],
            'resultsLimit': 30
        }

        data = self.scrape_with_actor(payload)
        return data if data else []

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
