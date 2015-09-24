from .parser import Settings
import os
import sys


__all__ = ['settings']


def rel(*x):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *x))

sys.path.insert(0, rel('..', 'apps'))

settings = Settings()