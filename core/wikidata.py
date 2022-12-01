import json
from statistics import mean
from typing import List

import requests
from wikidata.entity import Entity
from wikidata.client import Client
from pywikibot.data import api
from pywikibot.scripts.generate_user_files import pywikibot

# Initialize wikidata apis

site = pywikibot.Site("wikidata", "wikidata")
client = Client()


def get_avg_views(uid: str) -> float:
    """
    Returns average daily views of a wikidata article
    :param uid: uid of the article
    :return: average daily views
    """
    item = pywikibot.Page(site, uid)

    req = api.Request(site=site, parameters={'action': 'query',
                                             'titles': item.title(),
                                             'prop': 'pageviews'})

    res = req.submit()['query']['pages'][str(item.pageid)]['pageviews']
    page_views = [v for v in res.values() if isinstance(v, int)]

    if len(page_views) == 0:
        return 1

    return max(mean(page_views), 1)


def get_alias_referents(alias: str) -> List[dict]:

    # Searches for an alias on wikidata
    r = requests.get(f'https://www.wikidata.org/w/api.php?action=wbsearchentities&search={alias}&language=en&format=json')
    results = r.json()["search"]

    # Update each search result with its daily average view count
    for result in results:
        result["views"] = get_avg_views(result["id"])

    return results


def get_wikidata_page(uid: str) -> Entity:
    return client.get(uid, load=True)


def get_wikidata_description(uid: str) -> str:
    if "en" not in get_wikidata_page(uid).data["descriptions"]:
        return ""

    return get_wikidata_page(uid).data["descriptions"]["en"]["value"]
