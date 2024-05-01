import json
import requests
from bs4 import BeautifulSoup

class RemoteSimpleIndex:
    def __init__(self, logger, simple_url, json_url, connect_timeout=5, download_timeout=30, max_retries=3):
        self.remote_simple_url = simple_url
        self.remote_json_url = json_url
        self.connect_timeout = connect_timeout
        self.download_timeout = download_timeout
        self.max_retries = max_retries
        self.logger = logger

    def fetch_content(self, url):
        """Получает контент страницы по URL."""
        self.logger.info(f"Fetching content from {url}")
        for _ in range(self.max_retries):
            try:
                response = requests.get(url, timeout=(self.connect_timeout, self.download_timeout))
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                self.logger.debug(f"Error fetching content: {e}")
        raise requests.exceptions.RequestException(f"Failed to fetch content from {url} after {self.max_retries} retries")

    def fetch_simple_links(self, project_name):
        """Получает SIMPLE LINKS для пакета."""
        # TODO implement MAX_ATTEMPTS
        remote_url = self.remote_simple_url % project_name
        self.logger.debug(f"Fetching SIMPLE LINKS from {remote_url}")
        content = self.fetch_content(remote_url)
        soup = BeautifulSoup(content, 'html.parser')

        links = {}
        for link in soup.find_all('a'):
            link_text = link.string
            link_href = link.get('href')
            links[link_text] = link_href

        return links

    def fetch_pypi_json(self, project_name):
        """Получает JSON для пакета."""
        remote_url = self.remote_json_url % project_name
        # url = f"https://pypi.org/pypi/{project_name}/json"
        self.logger.info(f"Fetching JSON from {remote_url}")
        content = self.fetch_content(remote_url)
        return json.loads(content) if content else None
