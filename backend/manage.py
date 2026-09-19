#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

from host.settings.resolver import configure_default_settings_module


def main() -> None:
    configure_default_settings_module()

    if "test" in sys.argv:
        os.environ["DJANGO_SETTINGS_MODULE"] = "host.settings.test"

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
