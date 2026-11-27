import getpass
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

from arrera_blue_lynx.core.network import (
    connect_wifi,
    get_local_ip,
    has_internet_connectivity,
    has_wifi_device,
    has_working_ethernet,
    list_wifi_networks,
)
from arrera_blue_lynx.core.state import (
    SetupState,
    UserAccount,
    slugify_username,
    validate_hostname,
    validate_password,
    validate_username,
)

SERVER_LOCALES: list[tuple[str, str]] = [
    ("fr_FR.UTF-8", "Français (fr_FR.UTF-8)"),
    ("en_US.UTF-8", "English (en_US.UTF-8)"),
    ("de_DE.UTF-8", "Deutsch (de_DE.UTF-8)"),
    ("es_ES.UTF-8", "Español (es_ES.UTF-8)"),
    ("it_IT.UTF-8", "Italiano (it_IT.UTF-8)"),
]

SERVER_KEYMAPS: list[tuple[str, str]] = [
    ("fr", "Français (AZERTY - fr)"),
    ("us", "English US (QWERTY - us)"),
    ("be-latin1", "Belge (AZERTY - be-latin1)"),
    ("fr_CH", "Suisse romand (QWERTZ - fr_CH)"),
    ("de", "Allemand (QWERTZ - de)"),
    ("es", "Espagnol (QWERTY - es)"),
]

INSTALL_LOG_PATH = "/root/arrera-blue-lynx-install.log"


def _print_banner(title: str) -> None:
    line = "=" * 60
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")


def _prompt(text: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{text}{suffix} : ").strip()
        if value:
            return value
        if default is not None:
            return default


def _prompt_password(prompt_text: str, confirm_text: str, label: str) -> str:
    while True:
        pwd = getpass.getpass(f"{prompt_text} : ")
        confirm = getpass.getpass(f"{confirm_text} : ")
        err = validate_password(pwd, confirm, label=label)
        if err is None:
            return pwd
        print(f"  [!] {err}")


def _select_locale_and_keymap(state: SetupState, *, demo_mode: bool) -> None:
    _print_banner("1. Langue & Clavier console")
    print("Langues disponibles :")
    for idx, (_code, label) in enumerate(SERVER_LOCALES, start=1):
        print(f"  {idx}) {label}")

    while True:
        raw = _prompt("Choix de la langue (numéro ou code locale)", default="1")
        if raw.isdigit() and 1 <= int(raw) <= len(SERVER_LOCALES):
            state.language = SERVER_LOCALES[int(raw) - 1][0]
            break
        if "." in raw or "_" in raw:
            state.language = raw
            break
        print("  [!] Choix invalide.")

    print("\nDispositions clavier console :")
    for idx, (_code, label) in enumerate(SERVER_KEYMAPS, start=1):
        print(f"  {idx}) {label}")

    while True:
        raw = _prompt("Choix du clavier (numéro ou keymap)", default="1")
        if raw.isdigit() and 1 <= int(raw) <= len(SERVER_KEYMAPS):
            state.keymap = SERVER_KEYMAPS[int(raw) - 1][0]
            break
        if raw and " " not in raw:
            state.keymap = raw
            break
        print("  [!] Choix invalide.")

    if not demo_mode and os.geteuid() == 0:
        subprocess.run(["localectl", "set-keymap", state.keymap], check=False)

    print(f"-> Langue : {state.language} | Clavier : {state.keymap}")


def _configure_network(state: SetupState, *, force_wifi: bool, demo_mode: bool) -> None:
    _print_banner("2. Configuration réseau")
    if not force_wifi and has_working_ethernet():
        state.network_mode = "ethernet"
        state.wifi_ssid = None
        print("Connexion Ethernet active détectée.")
        return

    if not force_wifi and not has_wifi_device():
        state.network_mode = "none"
        state.wifi_ssid = None
        print("Aucune connexion Ethernet active et aucune carte Wi-Fi détectée (mode hors-ligne).")
        return

    while True:
        print("Recherche des réseaux Wi-Fi...")
        networks = list_wifi_networks(rescan=True)
        if not networks:
            print("Aucun réseau Wi-Fi trouvé.")
            choice = _prompt("Taper 'r' pour rescanner ou 's' pour continuer sans réseau", default="s")
            if choice.lower() == "r":
                continue
            state.network_mode = "none"
            state.wifi_ssid = None
            return

        for idx, net in enumerate(networks, start=1):
            sec = "Sécurisé" if net.is_secured else "Ouvert"
            active = " [Connecté]" if net.in_use else ""
            print(f"  {idx}) {net.ssid} ({net.signal} %, {sec}){active}")

        raw = _prompt("Numéro du réseau ('r' = actualiser, 's' = ignorer)", default="1" if networks[0].in_use else "s")
        lower = raw.lower()
        if lower == "r":
            continue
        if lower == "s":
            state.network_mode = "none"
            state.wifi_ssid = None
            return
        if not raw.isdigit() or not (1 <= int(raw) <= len(networks)):
            print("  [!] Numéro invalide.")
            continue

        selected = networks[int(raw) - 1]
        if selected.in_use:
            state.network_mode = "wifi"
            state.wifi_ssid = selected.ssid
            print(f"-> Réseau sélectionné : {selected.ssid}")
            return

        password: str | None = None
        if selected.is_secured:
            password = getpass.getpass(f"Mot de passe pour « {selected.ssid} » : ")

        if demo_mode:
            state.network_mode = "wifi"
            state.wifi_ssid = selected.ssid
            print(f"-> [Démo] Connexion simulée à {selected.ssid}")
            return

        print(f"Connexion à « {selected.ssid} »...")
        ok, err = connect_wifi(selected.ssid, password)
        if ok:
            state.network_mode = "wifi"
            state.wifi_ssid = selected.ssid
            print(f"-> Connecté à « {selected.ssid} »")
            return
        print(f"  [!] Échec : {err}")


def _configure_hostname(state: SetupState) -> None:
    _print_banner("3. Nom d'hôte (Hostname)")
    while True:
        hostname = _prompt("Nom d'hôte du serveur", default=state.hostname).lower()
        err = validate_hostname(hostname)
        if err is None:
            state.hostname = hostname
            print(f"-> Nom d'hôte : {state.hostname}")
            return
        print(f"  [!] {err}")


def _configure_accounts(state: SetupState, *, demo_mode: bool = False) -> None:
    _print_banner("4. Comptes Administrateur & Root")
    last_name = _prompt("Nom de l'administrateur")
    first_name = _prompt("Prénom de l'administrateur")
    suggested = slugify_username(first_name or last_name) or "admin"

    while True:
        username = _prompt("Identifiant du compte administrateur", default=suggested)
        err = validate_username(username, check_system=not demo_mode)
        if err is None:
            break
        print(f"  [!] {err}")

    user_pwd = _prompt_password(
        "Mot de passe du compte administrateur",
        "Confirmer le mot de passe",
        label="Le mot de passe",
    )
    root_pwd = _prompt_password(
        "Mot de passe du compte super administrateur (Root)",
        "Confirmer le mot de passe Root",
        label="Le mot de passe Root",
    )

    state.users = [
        UserAccount(
            last_name=last_name,
            first_name=first_name,
            username=username,
            password=user_pwd,
            is_admin=True,
            profile="standard",
        )
    ]
    state.root_password = root_pwd
    print(f"-> Compte administrateur prêt : {username} (wheel) + root")


def generate_server_install_script(
    state: SetupState,
    *,
    has_internet: bool,
    log_to_root: bool = True,
) -> str:
    """Génère le script bash de configuration pour Arrera Blue Server."""
    usernames = ", ".join(u.username for u in state.users) or "aucun"
    lines: list[str] = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        'trap \'case "$0" in /tmp/arrera-lynx-*.sh) rm -f -- "$0" ;; esac\' EXIT',
        "",
    ]

    if log_to_root:
        lines.extend(
            [
                'if [ -d /root ] && [ "$(id -u)" -eq 0 ]; then',
                f"  touch {INSTALL_LOG_PATH}",
                f"  chmod 600 {INSTALL_LOG_PATH}",
                f"  exec > >(tee -a {INSTALL_LOG_PATH}) 2>&1",
                "fi",
            ]
        )

    q_host = shlex.quote(state.hostname)
    hosts_sed = shlex.quote(f"s/^127\\.0\\.1\\.1[[:space:]].*/127.0.1.1   {state.hostname}/")
    lines.extend(
        [
            'trap \'echo "[ERREUR] Commande échouée à la ligne ${LINENO} (code $?)"\' ERR',
            'echo "=== [$(date -Iseconds)] Début installation (server) ==="',
            f"echo {shlex.quote(f'Config: lang={state.language} | keymap={state.keymap} | hostname={state.hostname} | users=[{usernames}]')}",
            "",
            f"localectl set-locale LANG={shlex.quote(state.language)}",
            f"localectl set-keymap {shlex.quote(state.keymap)}",
            "",
            f"hostnamectl set-hostname {q_host}",
            f"printf '%s\\n' {q_host} > /etc/hostname",
            "if [ ! -f /etc/hosts ]; then",
            "  printf '127.0.0.1   localhost localhost.localdomain\\n::1         localhost localhost.localdomain\\n' > /etc/hosts",
            "fi",
            "if grep -qE '^127\\.0\\.1\\.1[[:space:]]' /etc/hosts; then",
            f"  sed -i -E {hosts_sed} /etc/hosts",
            "else",
            f"  printf '127.0.1.1   %s\\n' {q_host} >> /etc/hosts",
            "fi",
        ]
    )

    for user in state.users:
        full_name = f"{user.first_name} {user.last_name}".strip()
        cmd = ["useradd", "-m", "-c", full_name]
        if user.is_admin:
            cmd.extend(["-G", "wheel"])
        cmd.append(user.username)
        lines.extend(
            [
                " ".join(shlex.quote(arg) for arg in cmd),
                f"printf '%s:%s\\n' {shlex.quote(user.username)} {shlex.quote(user.password)} | chpasswd",
            ]
        )

    if state.root_password:
        lines.append(
            f"printf 'root:%s\\n' {shlex.quote(state.root_password)} | chpasswd"
        )

    if has_internet:
        lines.extend(
            [
                "",
                "abpm clean expire-cache || true",
                "abpm update -y --dnf || true",
            ]
        )

    lines.extend(
        [
            "",
            'echo "=== [$(date -Iseconds)] Fin installation (server) ==="',
            "",
        ]
    )
    return "\n".join(lines)


def _apply_server_config(state: SetupState, *, demo_mode: bool) -> int:
    _print_banner("5. Application de la configuration & mise à jour abpm")
    internet_ok = (state.network_mode != "none") if demo_mode else has_internet_connectivity()
    script_content = generate_server_install_script(state, has_internet=internet_ok)

    if demo_mode:
        print("[Mode démo] Script généré (non exécuté) :")
        for line in script_content.splitlines():
            if "chpasswd" in line:
                print("  <commande chpasswd masquée>")
            else:
                print(f"  {line}")
        return 0

    fd, raw_path = tempfile.mkstemp(prefix="arrera-lynx-server-", suffix=".sh")
    script_path = Path(raw_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(script_content)
        os.chmod(script_path, 0o700)

        cmd = [str(script_path)] if os.geteuid() == 0 else ["sudo", str(script_path)]
        res = subprocess.run(cmd, check=False)
        return res.returncode
    finally:
        script_path.unlink(missing_ok=True)


def _print_summary(state: SetupState) -> None:
    _print_banner("6. Résumé de la configuration Arrera Blue Server")
    admin_user = state.users[0].username if state.users else "aucun"
    local_ip = get_local_ip() or "Non disponible"
    print(f"  Nom d'hôte      : {state.hostname}")
    print(f"  Adresse IP      : {local_ip}")
    print(f"  Administrateur  : {admin_user}")
    print(f"  Langue / Clavier: {state.language} / {state.keymap}")
    print("=" * 60)


def main() -> int:
    force_wifi = "--force-wifi" in sys.argv
    demo_mode = "--demo" in sys.argv
    state = SetupState()

    _print_banner("Bienvenue sur Arrera Blue Server (Configuration initiale)")

    try:
        _select_locale_and_keymap(state, demo_mode=demo_mode)
        _configure_network(state, force_wifi=force_wifi, demo_mode=demo_mode)
        _configure_hostname(state)
        _configure_accounts(state, demo_mode=demo_mode)
    except (EOFError, KeyboardInterrupt):
        print("\nConfiguration interrompue.")
        return 130

    rc = _apply_server_config(state, demo_mode=demo_mode)
    if rc != 0:
        print(f"\n[ERREUR] Échec de la configuration (code {rc}). Consultez {INSTALL_LOG_PATH}.")
        return rc

    _print_summary(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
