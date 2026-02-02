"""
Base class for Apify scrapers
Reduces code duplication across all scraper implementations
"""

import requests
import time


class BaseApifyScraper:
    """Base scraper with common Apify functionality"""

    def __init__(self, apify_api_key, actor_id):
        self.api_key = apify_api_key
        self.actor_id = actor_id
        self.base_url = 'https://api.apify.com/v2'

    def _run_actor(self, payload, timeout=10):
        """
        Start Apify actor run
        Returns: run_id or None
        """
        url = f"{self.base_url}/acts/{self.actor_id}/runs"

        try:
            response = requests.post(
                f"{url}?token={self.api_key}",
                json=payload,
                timeout=timeout
            )

            if response.status_code == 201:
                return response.json()['data']['id']
            else:
                print(f"Actor run failed: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"Error running actor {self.actor_id}: {e}")
            return None

    def _wait_for_completion(self, run_id, max_wait=60):
        """
        Wait for Apify actor run to complete
        Returns: dataset_id or None
        """
        url = f"{self.base_url}/acts/runs/{run_id}"
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"{url}?token={self.api_key}", timeout=5)
                if response.status_code != 200:
                    return None

                data = response.json()
                status = data['data']['status']

                if status == 'SUCCEEDED':
                    return data['data']['defaultDatasetId']
                elif status in ['FAILED', 'ABORTED', 'TIMED-OUT']:
                    print(f"Actor run {run_id} failed with status: {status}")
                    return None

                time.sleep(3)

            except Exception as e:
                print(f"Error checking run status: {e}")
                return None

        print(f"Actor run {run_id} timed out after {max_wait}s")
        return None

    def _fetch_dataset(self, dataset_id):
        """
        Fetch results from Apify dataset
        Returns: list of items or empty list
        """
        url = f"{self.base_url}/datasets/{dataset_id}/items"

        try:
            response = requests.get(f"{url}?token={self.api_key}", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to fetch dataset: HTTP {response.status_code}")
                return []

        except Exception as e:
            print(f"Error fetching dataset {dataset_id}: {e}")
            return []

    def scrape_with_actor(self, payload):
        """
        Complete scraping workflow: run actor, wait, fetch data
        Returns: scraped data or empty list
        """
        if not self.api_key:
            return None

        run_id = self._run_actor(payload)
        if not run_id:
            return None

        dataset_id = self._wait_for_completion(run_id)
        if not dataset_id:
            return None

        return self._fetch_dataset(dataset_id)
