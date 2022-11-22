import json

from flask import current_app as app
from flask import g
from pymemcache import Client


def get_cache():
    if 'cache' not in g:
        g.cache = Client((app.config['MEMCACHE']['HOST'], 11211))
    return g.cache


def set_in_cache(key, value, lock=None):
    if lock:
        get_cache().cas(key, value, lock)
    else:
        get_cache().set(key, value)


def get_from_cache(key, with_lock=False):
    if with_lock:
        val, lock = get_cache().gets(key)
        return val.decode('utf-8') if val else None, lock
    val = get_cache().get(key)
    return val.decode('utf-8') if val else None

