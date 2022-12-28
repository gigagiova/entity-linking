import re
from typing import Optional

import numpy as np


def vec_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Computes similarity between two vectors
    :param vec1:
    :param vec2:
    :return: similarity measure
    """
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))) ** 2


def format_string(string: Optional[str]):

    if string is None:
        return None

    hex_patterns = re.findall(re.compile("(?:%[0-9a-fA-F]{2})+"), string)
    for pattern in hex_patterns:
        string = string.replace(pattern, bytes.fromhex(pattern.replace("%", "")).decode('utf-8'))
    return string
