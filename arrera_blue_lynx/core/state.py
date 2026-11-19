from dataclasses import dataclass, field


CHILD_PROFILES: list[tuple[str, str]] = [
    ("child_3_6", "Enfant (3 - 6 ans)"),
    ("child_6_7", "Enfant (6 - 7 ans)"),
    ("child_8_10", "Enfant (8 - 10 ans)"),
    ("teen_11_18", "Ado (11 - 18 ans)"),
]


@dataclass
class UserAccount:
    """Représente un compte utilisateur à créer sur le système."""

    last_name: str
    first_name: str
    username: str
    password: str
    avatar_path: str | None = None
    is_admin: bool = False
    profile: str = "standard"  # "standard", "adult", "child_3_6", "child_6_7", "child_8_10", "teen_11_18"


@dataclass
class SetupState:
    """État partagé entre toutes les pages de l'assistant."""

    language: str = "fr_FR.UTF-8"
    network_mode: str = "none"  # "ethernet" ou "wifi"
    wifi_ssid: str | None = None
    users: list[UserAccount] = field(default_factory=list)
    root_password: str | None = None
    kernel: str = "fedora"  # "fedora", "lts" ou "cachyos"
    office_suite: str | None = None  # "onlyoffice", "libreoffice" ou None