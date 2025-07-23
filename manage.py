#!/usr/bin/env -S uv run --script
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "gutenberg.settings.local_settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure you have installed all dependencies from requirements.txt? "
                "Did you forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
