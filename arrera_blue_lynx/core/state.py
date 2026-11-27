import grp
import pwd
import re
import unicodedata
from dataclasses import dataclass, field

USERNAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
HOSTNAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
RESERVED_USERNAMES = {"root", "daemon", "bin", "sys", "nobody", "arrera-setup"}

CHILD_PROFILES: list[tuple[str, str]] = [
    ("child_3_6", "Enfant (3 - 6 ans)"),
    ("child_6_7", "Enfant (6 - 7 ans)"),
    ("child_8_10", "Enfant (8 - 10 ans)"),
    ("teen_11_18", "Ado (11 - 18 ans)"),
]


def slugify_username(text: str) -> str:
    """Transforme un prénom/nom en identifiant Linux valide (minuscules ASCII)."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    cleaned = re.sub(r"[^a-z0-9_-]+", "", ascii_text)
    cleaned = re.sub(r"^[^a-z_]+", "", cleaned)
    return cleaned[:32]


def validate_username(
    username: str,
    existing_usernames: set[str] | None = None,
    *,
    check_system: bool = False,
) -> str | None:
    """Valide un identifiant Linux. Retourne un message d'erreur ou None si valide."""
    if not username or not USERNAME_RE.match(username):
        return (
            "Identifiant invalide : utilisez uniquement des minuscules, chiffres, '-' ou '_' "
            "(sans espaces ni accents)."
        )
    if username in RESERVED_USERNAMES:
        return f"L'identifiant « {username} » est réservé par le système."
    if existing_usernames and username in existing_usernames:
        return f"L'identifiant « {username} » est déjà utilisé par un autre compte."
    if check_system:
        try:
            pwd.getpwnam(username)
        except KeyError:
            pass
        else:
            return f"L'identifiant « {username} » existe déjà sur le système."
        try:
            grp.getgrnam(username)
        except KeyError:
            pass
        else:
            return f"Le groupe « {username} » existe déjà sur le système, choisissez un autre identifiant."
    return None


def validate_password(password: str, confirm: str, label: str = "Le mot de passe") -> str | None:
    """Valide un mot de passe et sa confirmation. Retourne un message d'erreur ou None."""
    if len(password) < 4:
        return f"{label} doit contenir au moins 4 caractères."
    if password != confirm:
        return "Les deux mots de passe ne correspondent pas."
    return None


def validate_hostname(hostname: str) -> str | None:
    """Valide un nom d'hôte Linux (RFC 1123). Retourne un message d'erreur ou None."""
    if not hostname or not HOSTNAME_RE.match(hostname):
        return (
            "Nom d'hôte invalide : utilisez uniquement des minuscules, chiffres ou '-' "
            "(1 à 63 caractères, sans '-' au début ou à la fin)."
        )
    return None


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
    keymap: str = "fr"
    hostname: str = "arrera-server"
    network_mode: str = "none"  # "ethernet", "wifi" ou "none"
    wifi_ssid: str | None = None
    users: list[UserAccount] = field(default_factory=list)
    root_password: str | None = None
    kernel: str = "fedora"  # "fedora" ou "cachyos"
    office_suite: str | None = None  # "onlyoffice", "libreoffice" ou None
