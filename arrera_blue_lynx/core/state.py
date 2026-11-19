from dataclasses import dataclass


@dataclass
class SetupState:
    """État partagé entre toutes les pages de l'assistant."""

    language: str = "fr_FR.UTF-8"