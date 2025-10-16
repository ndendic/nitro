from rusty_tags import HtmlString
import uuid



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