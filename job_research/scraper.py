import csv
import logging
import random
import time
from typing import Iterator
import sqlite3
from urllib.parse import urlparse, urlencode
from dotenv import load_dotenv
import os

import requests
from fake_useragent import UserAgent


class Scraper:
    def __init__(self, api_key, max_retries=3, initial_delay=2, backoff_factor=2, handled_status_codes=None):
        self.conn = sqlite3.connect('webdomains.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS webdomains
                          (domain TEXT PRIMARY KEY, level INTEGER)''')
        self.ua = UserAgent()
        self.proxies = []
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.handled_status_codes = handled_status_codes or [403, 404, 429, 500]
        self.api_key = api_key
        logging.basicConfig(filename='scraper.log', level=logging.INFO,
                            format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    def __del__(self):
        self.conn.close()

    def insert_or_update(self, domain, level):
        try:
            self.c.execute("INSERT INTO webdomains VALUES (?, ?)", (domain, level))
        except sqlite3.IntegrityError:
            self.c.execute("UPDATE webdomains SET level = ? WHERE domain = ?", (level, domain))
        self.conn.commit()

    def get_level(self, domain):
        self.c.execute("SELECT level FROM webdomains WHERE domain = ?", (domain,))
        result = self.c.fetchone()
        return result[0] if result else None

    def get_domain_name(self, url):
        domain = urlparse(url).netloc
        domain_parts = domain.split('.')
        domain = '.'.join(domain_parts[-2:]) if len(domain_parts) > 2 else domain
        return domain

    def get_random_proxy(self) -> dict:
        return {'http': random.choice(self.proxies)} if self.proxies else {}

    def get_scrapeops_url(self, url, level=0):
        payload = {'api_key': self.api_key, 'url': url}
        if level > 0:
            payload['bypass'] = f"cloudflare_level_{level}"
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        return proxy_url

    def process_request(self, url: str, headers: dict = None, proxies: dict = None):
        response = requests.get(url, headers=headers, proxies=proxies)
        status = response.status_code
        if status in self.handled_status_codes:
            return (status, [])
        else:
            logging.info(f"Successfully scraped URL: {url}")
            return (status, response.content)

    def retry_with_scrapeops(self, url: str) -> Iterator[dict]:
        domain = self.get_domain_name(url)
        lvl = self.get_level(domain) or 0
        if lvl > 3:
            return []
        proxy_url = self.get_scrapeops_url(url, lvl)
        status, data = self.process_request(proxy_url)
        if status == 500:
            self.insert_or_update(domain, lvl + 1)
            return self.retry_with_scrapeops(url)
        logging.info(f"Successfully scraped URL: {url} with level {lvl}")
        print(f"Successfully scraped URL: {url} with level {lvl}")
        return [] if status in self.handled_status_codes else data

    def retry_with_backoff(self, url: str, retry_count: int = 0, delay: int = None) -> Iterator[dict]:
        delay = delay or self.initial_delay
        if retry_count >= self.max_retries:
            logging.error(f"Maximum retries reached for URL: {url}. Retrying using ScrapeOps.")
            print(f"Maximum retries reached for URL: {url}. Retrying using ScrapeOps.")
            return self.retry_with_scrapeops(url)

        try:
            headers = {'User-Agent': self.ua.random}
            proxy = self.get_random_proxy()
            status, data = self.process_request(url, headers=headers, proxies=proxy)
            if status in self.handled_status_codes:
                logging.warning(f"Error {status} occurred for URL: {url}, retrying...")
                print(f"Error {status} occurred for URL: {url}, retrying in {delay}s ...")
                time.sleep(delay)
                return self.retry_with_backoff(url, retry_count + 1, delay * self.backoff_factor)
            return data
        except Exception as e:
            logging.error(f"An error occurred for URL: {url}, Error: {e}")
            print(f"An error occurred for URL: {url}, Error: {e}")
            time.sleep(delay)
            return self.retry_with_backoff(url, retry_count + 1, delay * self.backoff_factor)

    def save_to_csv(self, data: Iterator[dict], filename: str) -> None:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)


if __name__ == '__main__':
    load_dotenv()
    api_key = os.getenv('SCRAPEOPS_API_KEY')
    scraper = Scraper(api_key)
    url = 'https://ca.indeed.com/q-artificial-intelligence-l-montr%C3%A9al,-qc-jobs.html'
    data = scraper.retry_with_backoff(url)
    scraper.save_to_csv(data, 'job_listings.csv')
