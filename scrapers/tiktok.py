"""
TikTok Scraper via Apify
Monitora trend audio e hashtag
Focus su Reel/Video
"""

from .base import BaseApifyScraper


class TikTokScraper(BaseApifyScraper):
    """Scraper per TikTok usando Apify"""

    def __init__(self, apify_api_key):
        super().__init__(apify_api_key, 'GdYC2FRRVehRJJVKw')

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
        payload = {
            'hashtags': [hashtag],
            'resultsPerPage': 30
        }

        data = self.scrape_with_actor(payload)
        return data if data else []

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
