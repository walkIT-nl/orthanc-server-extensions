from typing import Iterable


def ensure_iterable(v):
    return v if isinstance(v, Iterable) else [v]
