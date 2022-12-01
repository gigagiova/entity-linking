import numpy as np


def vec_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Computes similarity between two vectors
    :param vec1:
    :param vec2:
    :return: similarity measure
    """
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))) ** 2
