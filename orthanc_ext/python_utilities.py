from typing import Iterable


def pipeline(*functions):

    class Pipeline:

        def __call__(self, evt, *args):
            arg = evt
            for step in functions:
                arg = step(arg, *args)
            return arg

        def __repr__(self):
            return f'pipeline({functions})'

    return Pipeline()


def ensure_iterable(v):
    return v if isinstance(v, Iterable) else [v]


def hashable(k):
    try:
        return hash(k)
    except TypeError:
        return False


def create_reverse_type_dict(py_type):
    return {v: k for k, v in py_type.__dict__.items() if hashable(v)}
