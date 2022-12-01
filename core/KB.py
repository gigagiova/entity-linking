from core.embedder import embed_from_wikidata
from core.wikidata import get_alias_referents, get_wikidata_page
from pipeline import kb


def add_wikidata_entity(uid: str):
    entity = get_wikidata_page(uid)

    kb.add_entity(uid, 1, embed_from_wikidata(entity))

    # add page title as alias for the entity
    add_wikidata_alias(entity.data["labels"]["en"]["value"])

    # If the page has no english alias return the function
    if "en" not in entity.data["aliases"]:
        return

    # Loop over all aliases to add them
    for alias in entity.data["aliases"]["en"]:
        add_wikidata_alias(alias["value"])


def add_wikidata_alias(alias: str):
    """
    Given an alias, searches for wikidata entity and adds them
    :param alias: The alias to search for
    :return:
    """

    referents = get_alias_referents(alias)

    # Add all other referents that are not yet there to assign them the alias | TODO: very inefficient, fix it
    for referent in [r["id"] for r in referents]:
        if referent not in kb.get_entity_strings():
            kb.add_entity(referent, 1, embed_from_wikidata(get_wikidata_page(referent)))

    # Add the alias, pointing to all of the found referents with a probability proportional to the referent popularity
    total_views = sum([r["views"] for r in referents])
    kb.add_alias(alias, [r["id"] for r in referents], [r["views"] / total_views for r in referents])
