#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cbse_tutor.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Activate the venv first:\n"
            "  venv\\Scripts\\activate  (Windows)\n"
            "  source venv/bin/activate  (Mac/Linux)"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
