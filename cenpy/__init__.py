__version__ = '1.0.0post2'
__author__ = 'Levi John Wolf levi.john.wolf@gmail.com'

from . import explorer
from .remote import APIConnection as _APIConnection
from .tools import _load_sitekey, set_sitekey
from .products import *

SITEKEY = _load_sitekey()

#__all__ = ['explorer', 'base']
