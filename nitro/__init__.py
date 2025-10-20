# Re-export everything from rusty-tags core
__version__ = "0.1.0"

# Import framework-specific components
from nitro.utils import show, AttrDict, uniq
from nitro.infrastructure.events.events import *  # noqa: F403
from nitro.infrastructure.events.client import Client
from nitro.infrastructure.html import *  # noqa: F403
from nitro.infrastructure.html.datastar import *  # noqa: F403

__author__ = "Nikola Dendic"
__description__ = "Booster add-on for your favourite web-framework. Built on rusty-tags core."
