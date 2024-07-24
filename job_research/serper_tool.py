import json
import os
import requests


def search_serper(search_query, limit=10):
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
