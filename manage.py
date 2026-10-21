#!/usr/bin/env python
import os
import sys


def main() -> None:
    """Point d'entrée des commandes Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "locahome.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Assure-toi qu'il est installé "
            "et disponible dans ton environnement (virtualenv, etc.)."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()



