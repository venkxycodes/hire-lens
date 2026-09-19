"""WSGI config for the Django application."""

from django.core.wsgi import get_wsgi_application

from host.settings.resolver import configure_default_settings_module

configure_default_settings_module()

application = get_wsgi_application()
