import numpy
import wikipedia
from wikidata.entity import Entity

from pipeline import nlp, kb


def embed_from_wikidata(entity: Entity) -> numpy.ndarray:
    """
    Computes the vector embedding of the english wikipedia page linked with a wikidata entity
    :param entity: wikidata entity
    :return: entity embedding
    """

    # In case a wikipedia page is linked to this entity
    if "enwiki" in entity.data["sitelinks"]:
        # Gets the english wikipedia title from wikidata page and loads the relative wikipedia page
        wiki_title = entity.data["sitelinks"]["enwiki"]["url"].split("/")[-1]
        page = wikipedia.page(title=wiki_title, auto_suggest=False)

        # computes the embedding
        embedded = nlp(page.summary)
        return embedded.vector

    # Else, embed the wikidata description
    if "en" not in entity.data["descriptions"]:
        embedded = nlp(entity.data["descriptions"]["en"]["value"])
        return embedded.vector

    # In case there is no description in english, return an empty vector | TODO: create a more robust approach
    return numpy.zeros(kb.entity_vector_length)



