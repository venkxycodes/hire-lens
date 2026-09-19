"""ASGI config for the Django application."""

from django.core.asgi import get_asgi_application

from host.settings.resolver import configure_default_settings_module

configure_default_settings_module()

application = get_asgi_application()
