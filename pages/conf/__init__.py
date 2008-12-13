from django.conf import settings
from pages.conf import pages_settings

class CombinedSettingsHolder(object):
    """
    Convenience object for access to custom pages application settings,
    which enforces default settings when the global settings module does not
    contain the appropriate settings.
    """
    def __init__(self, global_settings, default_settings):
        self.global_settings = global_settings
        self.default_settings = default_settings

    def __getattr__(self, name):
        if hasattr(self.global_settings, name):
            return getattr(self.global_settings, name)
        return getattr(self.default_settings, name)

settings = CombinedSettingsHolder(settings, pages_settings)
