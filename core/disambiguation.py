import re

from spacy.kb import get_candidates, Candidate
from core.KB import add_wikidata_alias
from core.utilities import vec_similarity

from pipeline import nlp, kb


def disambiguate(context: str, mention: str) -> Candidate:
    context_doc = nlp(context)
    add_wikidata_alias(mention)

    # Searches for the position of the mention in the context
    res = re.search(mention, context_doc.text, re.IGNORECASE)

    # Raise exception in case the mention is not in the context
    if not res:
        raise KeyError("Mention was not found in the context")

    # This simple loop finds the token at the start and at the end of the mention
    current_index, start_index, end_index = 0, 0, 0
    for t in context_doc:

        current_token_end = current_index + len(t.text)

        if current_index <= res.start() <= current_token_end:
            start_index = t.i

        if current_index <= res.end() <= current_token_end:
            end_index = t.i + 1
            break

        current_index = current_token_end + 1

    print(context_doc[start_index:end_index])

    # Calculates the candidates and returns the one with the greatest vector similarity with the context
    candidates = get_candidates(kb, context_doc[start_index:end_index])
    print(candidates)
    return max(candidates, key=lambda c: vec_similarity(context_doc.vector, c.entity_vector))
