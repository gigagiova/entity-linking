import json
import sqlite3
import time
from datetime import timedelta, datetime
from sqlite3 import Error
from typing import Optional, List

import numpy
from faiss import index_factory, write_index, Index, read_index
from sentence_transformers import SentenceTransformer
from simstring.database.dict import DictDatabase
from simstring.feature_extractor.character_ngram import CharacterNgramFeatureExtractor

from core.wikidata import batch_descriptions
from variables import sql_queries


class CandidateGenerator:

    def __init__(self, transformer_model: str = 'multi-qa-MiniLM-L6-cos-v1', configuration: str = 'IVF10000_HNSW32,PQ16', path=None, n=100):
        start = time.time()

        # Descriptions to train the index on
        descriptions = batch_descriptions(1, n)

        # Istantiate a transformer model and encodes the sentences to train our index on
        self.model = SentenceTransformer(transformer_model, device="cuda")

        # Decouple descriptions from their uids and encodings from training data, and get dimensionality
        encodings = self.model.encode([d for uid, d in descriptions])
        dimensionality = encodings.shape[1]

        # Creating the index from the index factory
        self.index = index_factory(dimensionality, configuration)

        # Should train it on a number of examples at least equals the number of clusters (10000)
        self.index.train(encodings)

        # Gets the number of indices (0) before adding them to provide a baseline when we will add the mappings to uids
        last_index = self.index.ntotal

        # Adding vectors to the index (since we already embedded them)
        self.index.add(encodings)

        # Save index and mappings to disk, if needed
        self.path = path
        if path is not None:

            # Creates db mapping in disk
            self._create_table(path + "/entities.sqlite3")

            # Saves the FAISS index in the folder, then writes the mappings into the db we just created
            write_index(self.index, path + "/" + configuration + ".index")

            # Save Generator info in a json
            info = {
                "createdAt": str(datetime.now()),
                "transformerModel": transformer_model,
                "index": configuration
            }
            json_object = json.dumps(info, indent=4)
            with open(path + "/info.json", "w") as outfile:
                outfile.write(json_object)
        else:
            self._create_table(":memory:")

        # Writes the entity mapping in the db, in disk or in memory
        self.write_entities([(i + last_index, uid, d) for i, (uid, d) in enumerate(descriptions)])

        end = time.time()

        print(f"Trained: {self.index.is_trained} | Indexed vectors: {self.index.ntotal} | Time: {timedelta(seconds=end - start)}")

    @classmethod
    def load(cls, path):

        with open(path + "/info.json", "r") as openfile:
            json_object = json.load(openfile)

        gen = cls.__new__(cls)
        super(CandidateGenerator, gen).__init__()

        # Loads into the object all necessary attributes
        gen.path = path
        gen.model = SentenceTransformer(json_object["transformerModel"], device="cuda")
        gen.index = read_index(path + "/" + json_object["index"] + ".index")
        gen.conn = sqlite3.connect(path + "/entities.sqlite3")

        return gen

    def __getitem__(self, key) -> Optional[str]:
        """
        Returns the vector relative to the vector indexed at position key in the index object
        :param key: the index of the vector
        :return: The uid of the vector's entity, if found
        """

        cur = self.conn.cursor()
        cur.execute(sql_queries["select_entity_by_id"], (key,))
        res = cur.fetchall()

        # If we found no match, we probably queried an index out of range
        if len(res) == 0:
            return None

        # Since we are querying by the pk we expect only one result, a triplet made by (index, uid, description)
        _, uid, _ = res[0]
        return uid

    def _create_table(self, path: str):
        """
        Creates a database to store faiss indices to uid mapping
        :param path: path of the model folder, pass :memory: to not save
        """
        try:
            self.conn = sqlite3.connect(path)
            c = self.conn.cursor()
            c.execute(sql_queries["create_dictionary_table"])
        except Error as e:
            print(e)

    def write_entities(self, entities: List[tuple]):

        c = self.conn.cursor()
        c.executemany(sql_queries["insert_entities"], entities)

        # Commits changes and returns connection
        self.conn.commit()

    def query(self, query: str, k: int = 16):
        # Encode the query and reshape the vector to match the format required
        query_vector = self.model.encode(query).reshape(1, -1)

        # The search returns D, the pairwise distances, and I, the indices of the nearest neighbors.
        distances, indices = self.index.search(query_vector, k)

        # IDK why they are the first and only element of another list
        indices = indices[0]
        distances = distances[0]

        for i, d in sorted(zip(indices, distances), key=lambda r: r[1]):
            print(f"element https://www.wikidata.org/wiki/{self[int(i)]} has distance {d} ")

