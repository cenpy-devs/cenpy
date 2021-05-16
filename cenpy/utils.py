import requests


class RestApiBase:
    def __init__(self, session=None):
        self._session = session if session else requests.session()

    def _get(self, url, params={}):
        return self._session.get(url, params=params)


# https://stevenloria.com/lazy-properties/
def lazy_property(fn):
    """Decorator that makes a property lazy-evaluated."""
    attr_name = "_lazy_" + fn.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    return _lazy_property


def chunks(values, chunk_size):
    chunk_size = chunk_size if len(values) > chunk_size else len(values)
    for c in range(0, len(values), chunk_size):
        yield values[c : c + chunk_size]
