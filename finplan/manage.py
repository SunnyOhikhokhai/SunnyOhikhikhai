#!/usr/bin/env python
"""Django's command-line utility for FINPLAN administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Is your virtual environment activated? "
            "Run: .venv\\Scripts\\Activate.ps1 (PowerShell) and then "
            "pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
