from rusty_tags import HtmlString
import uuid
from fnmatch import fnmatch


def uniq(length: int = 6):
    return str(uuid.uuid4().hex[:length])

def show(html: HtmlString):
    try:
        from IPython.display import HTML # type: ignore
        return HTML(html.render())
    except ImportError:
        raise ImportError("IPython is not installed. Please install IPython to use this function.")

class AttrDict(dict):
    "`dict` subclass that also provides access to keys as attrs"
    def __getattr__(self,k): return self[k] if k in self else None
    def __setattr__(self, k, v): (self.__setitem__,super().__setattr__)[k[0]=='_'](k,v)
    def __dir__(self): return super().__dir__() + list(self.keys()) # type: ignore
    def copy(self): return AttrDict(**self)

def match(query: str, item: str) -> bool:
    reverse = query.startswith("!")
    query = query[1:] if reverse else query
    return fnmatch(item, query) if not reverse else not fnmatch(item, query)

def filter_dict(query: str, dct: dict) -> dict:
    filtered = {}
    for k,v in dct.items():
        if match(query, k):
            filtered[k]=v
    return filtered
