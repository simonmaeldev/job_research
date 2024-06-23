from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from bs4 import BeautifulSoup

import requests
import time


class Scraper:
    """
    Scraper class to extract the content from the links
    """

    def __init__(self, urls, user_agent):
        """
        Initialize the Scraper class.
        Args:
            urls:
        """
        self.urls = urls
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def run(self):
        """
        Extracts the content from the links
        """
        partial_extract = partial(self.extract_data_from_link)
        with ThreadPoolExecutor(max_workers=20) as executor:
            contents = executor.map(partial_extract, self.urls)
        res = [content for content in contents if content["raw_content"] is not None]
        return res

    def extract_data_from_link(self, link):
        """
        Extracts the data from the link
        """
        content = ""
        try:
            content = self.scrape(link)

            if len(content) < 100:
                return {"url": link, "raw_content": None}
            return {"url": link, "raw_content": content}
        except Exception as e:
            return {"url": link, "raw_content": None}
        
    def scrape(self, link):
        """
        This function scrapes content from a webpage by making a GET request, parsing the HTML using
        BeautifulSoup, and extracting script and style elements before returning the cleaned content.
        
        Returns:
          The `scrape` method is returning the cleaned and extracted content from the webpage specified
        by the `self.link` attribute. The method fetches the webpage content, removes script and style
        tags, extracts the text content, and returns the cleaned content as a string. If any exception
        occurs during the process, an error message is printed and an empty string is returned.
        """
        try:
            status_code = 403
            while status_code != 200:
                response = self.session.get(link, timeout=4)
                status_code = response.status_code
                print("sleeping 15s to go over 403")
                time.sleep(15)
            response = self.session.get(link, timeout=4)
            soup = BeautifulSoup(
                response.content, "lxml", from_encoding=response.encoding
            )

            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            raw_content = self.get_content_from_url(soup)
            lines = (line.strip() for line in raw_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = "\n".join(chunk for chunk in chunks if chunk)
            return content

        except Exception as e:
            print("Error! : " + str(e))
            return ""
        
    def get_content_from_url(self, soup):
        """Get the text from the soup

        Args:
            soup (BeautifulSoup): The soup to get the text from

        Returns:
            str: The text from the soup
        """
        text = ""
        tags = ["p", "h1", "h2", "h3", "h4", "h5"]
        for element in soup.find_all(tags):  # Find all the <p> elements
            text += element.text + "\n"
        return text

def scrape_urls(urls):
    """
    Scrapes the urls
    Args:
        urls: List of urls
        cfg: Config (optional)

    Returns:
        text: str

    """
    content = []
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    try:
        content = Scraper(urls, user_agent).run()
    except Exception as e:
        print(f"Error in scrape_urls: {e}")
    return content

content = scrape_urls(["https://ca.indeed.com/viewjob?jk=f3fb6ccd700d0061"])
print(content)
