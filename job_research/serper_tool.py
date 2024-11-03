import json
import os
import requests


"""
Serper API tool that enables LLMs to perform web searches through Google.
Uses Serper.dev as a cost-effective alternative to the official Google Search API.

The tool:
- Takes natural language queries from LLMs
- Returns structured search results with URLs
- Limits results to control costs and processing time
- Handles API authentication via environment variables
"""


def search_serper(search_query, limit=10):
    """
    Perform a Google search via Serper API and return formatted results.
    
    Args:
        search_query: Search terms/question from LLM
        limit: Maximum number of results to return (default 10)
        
    Returns:
        List of dicts containing:
            - link: Result URL
            - query: Original search query
        Or raw API response if no organic results found
    """
    search_url: str = "https://google.serper.dev/search"
    payload = json.dumps({"q": search_query, "num":limit})
    headers = {
        'X-API-KEY': os.environ['SERPER_API_KEY'],
        'content-type': 'application/json'
    }
    response = requests.request("POST", search_url, headers=headers, data=payload)
    results = response.json()

    if 'organic' in results:
        results = results['organic']
        res_list = []
        for result in results:
            el = {
                'link': result['link'],
                'query': search_query
            }
            res_list.append(el)
        return res_list
    else:
        return results
