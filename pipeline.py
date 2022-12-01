import spacy
from spacy.kb import KnowledgeBase


# instantiate a new transformer pipeline with a Knowledge base
from core.utilities import vec_similarity

nlp = spacy.load("en_core_web_md")
kb = KnowledgeBase(vocab=nlp.vocab, entity_vector_length=nlp.vocab.vectors.shape[1])


