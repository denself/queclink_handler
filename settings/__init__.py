from .parser import Settings
import os
import sys

__all__ = ['settings']


def rel(*x):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), *x))


sys.path.insert(0, rel('..', 'apps'))

settings = Settings()
settings.DB_USER = os.getenv('DB_USER', 'postgres')
settings.DB_PASS = os.getenv('DB_PASS', 'postgres')
settings.DB_HOST = os.getenv('DB_HOST', 'localhost')
settings.DB_NAME = os.getenv('DB_NAME', 'queclink')
settings.DB_URL = "postgresql://{0}:{1}@{2}/{3}".format(settings.DB_USER,
                                                        settings.DB_PASS,
                                                        settings.DB_HOST,
                                                        settings.DB_NAME)
