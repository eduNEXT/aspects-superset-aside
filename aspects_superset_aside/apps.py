"""
aspects_superset_aside Django application initialization.
"""

from django.apps import AppConfig
from edx_django_utils.plugins.constants import PluginSettings


class AspectsSupersetAsideConfig(AppConfig):
    """
    Configuration for the aspects_superset_aside Django application.
    """

    name = 'aspects_superset_aside'
    plugin_app = {
        PluginSettings.CONFIG: {
            'lms.djangoapp': {
                'common': {
                    PluginSettings.RELATIVE_PATH: 'settings.common',
                },
                'devstack': {
                    PluginSettings.RELATIVE_PATH: 'settings.devstack',
                },
                'production': {
                    PluginSettings.RELATIVE_PATH: 'settings.production',
                },
            }
        }
    }
