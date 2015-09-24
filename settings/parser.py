import importlib
import json
from ConfigParser import SafeConfigParser
import os

class BaseSettings(dict):
    """
    Common logic for settings whether set by a module or by the user.
    """

    def __setitem__(self, name, value):
        super(BaseSettings, self).__setitem__(name.lower(), value)

    def __setattr__(self, name, value):
        self[name.lower()] = value

    def __getattr__(self, name):
        name = name.lower()
        if name in self:
            return self[name]
        raise AttributeError

    def __delattr__(self, name):
        name = name.lower()
        del self[name]


class Settings(BaseSettings):

    def __init__(self, *setting_list, **kw):
        super(Settings, self).__init__(**kw)

        for settings_file in setting_list:
            if settings_file.endswith('.cfg'):
                self.read_cfg(settings_file)
            elif settings_file.endswith('.json'):
                self.read_json(settings_file)
            else:
                self.read_module(settings_file)

    def read_module(self, settings_module=None):
        try:
            mod = importlib.import_module(settings_module)
        except ImportError as e:
            raise ImportError(("Could not import settings '%s'"
                " (Is it on sys.path?): %s") % (settings_module, e))

        for setting in dir(mod):
            setting_value = getattr(mod, setting)
            setattr(self, setting, setting_value)

    def read_cfg(self, cfg_file):
        assert self.PROFILE, 'MOB_PROFILE env var must be enabled'
        cfg_file = cfg_file.format(profile=self.PROFILE)
        parser = SafeConfigParser()
        assert cfg_file in parser.read(cfg_file), \
            'Could not find: {}'.format(cfg_file)
        for name in parser.options('settings'):
            value = parser.get('settings', name)
            if value == 'true':
                value = True
            elif value == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            setattr(self, name, value)

    def read_json(self, json_file):

        json_data = json.loads(open(json_file, 'rb').read())

        assert isinstance(json_data, dict), \
                          'Is not dictionary : {}'.format(json_file)
        self.update(json_data)
