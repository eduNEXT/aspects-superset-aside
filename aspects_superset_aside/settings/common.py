"""Default settings load from environment"""


def plugin_settings(settings):
    """
    Get summary hook aside settings from calling application
    """
    env_tokens = getattr(settings, 'ENV_TOKENS', {})
    settings.DUMMY_SETTINGS = env_tokens.get('DUMMY_SETTING', '')
