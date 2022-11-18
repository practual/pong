import json

from flask import current_app as app
from flask import g
from pymemcache import Client


def get_cache():
    if 'cache' not in g:
        g.cache = Client((app.config['MEMCACHE']['HOST'], 11211))
    return g.cache


def set_in_cache(key, value):
    get_cache().set(key, value)


def get_from_cache(key):
    return get_cache().get(key).decode('utf-8')

