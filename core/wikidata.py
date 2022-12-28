import json
import re
from statistics import mean
from typing import List, Optional
from urllib.error import HTTPError

import requests
from wikidata.entity import Entity
from wikidata.client import Client
from pywikibot.data import api
from pywikibot.scripts.generate_user_files import pywikibot
from wikipedia import wikipedia, DisambiguationError, PageError, WikipediaException

from core.utilities import format_string

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


def get_wikidata_page(uid: str) -> Optional[Entity]:
    try:
        return client.get(uid, load=True)
    except HTTPError:
        return None


def get_wikidata_description(uid: str) -> str:
    if "en" not in get_wikidata_page(uid).data["descriptions"]:
        return ""

    return get_wikidata_page(uid).data["descriptions"]["en"]["value"]


def description_from_uid(uid: str) -> Optional[str]:
    """
    Finds the description of the english wikipedia page linked with a wikidata entity, if not found uses wikidata
    :param uid: wikidata uid
    :return: entity embedding
    """

    entity = get_wikidata_page(uid)

    if entity is None:
        return None

    # In case a wikipedia page is linked to this entity
    if "enwiki" in entity.data["sitelinks"]:
        # Gets the english wikipedia title from wikidata and loads the relative wikipedia page to return the summary
        wiki_title = format_string(re.search("(?<=wiki/).*$", entity.data["sitelinks"]["enwiki"]["url"]).group(0))
        print(f"{uid}: {wiki_title}")

        # Avoid disambiguation pages, since they are not articles and other possible errors
        try:
            page = wikipedia.page(title=wiki_title, auto_suggest=False)
        except (DisambiguationError, PageError, WikipediaException) as e:
            return None

        return format_string(page.summary)

    # Else, returns the wikidata description
    if "en" in entity.data["descriptions"]:
        return format_string(entity.data["descriptions"]["en"]["value"])

    # In case there is no description in english, return an empty vector
    return None


def batch_descriptions(start: int, stop: int) -> List[tuple]:
    return [(f"Q{i}", d) for i in range(start, stop) if (d := description_from_uid(f"Q{i}")) is not None]

