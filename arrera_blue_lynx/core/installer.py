import os
import shlex
import subprocess
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from gi.repository import GLib

from arrera_blue_lynx.core.state import SetupState, UserAccount

CACHYOS_COPR = "bieszczaders/kernel-cachyos"

OFFICE_COMMANDS: dict[str, tuple[str, list[str]]] = {
    "libreoffice": (
        "LibreOffice",
        ["abpm", "install", "--dnf", "--progress", "libreoffice"],
    ),
    "onlyoffice": (
        "OnlyOffice",
        ["abpm", "install", "--flatpak", "--progress", "org.onlyoffice.desktopeditors"],
    ),
}

CLEANUP_SCRIPT_PATH = "/usr/local/sbin/arrera-cleanup-fedora-kernel.sh"
CLEANUP_SERVICE_NAME = "arrera-cleanup-fedora-kernel.service"
CLEANUP_SERVICE_PATH = f"/etc/systemd/system/{CLEANUP_SERVICE_NAME}"

_CLEANUP_SCRIPT_CONTENT = f"""#!/usr/bin/env bash
set -euo pipefail

# Ne supprime le noyau Fedora que si le système a bien démarré sur CachyOS
case "$(uname -r)" in
  *cachyos*) ;;
  *) exit 0 ;;
esac

FEDORA_PKGS=()
for pkg in kernel kernel-core kernel-modules kernel-modules-core kernel-modules-extra kernel-devel kernel-devel-matched kernel-uki-virt; do
  if rpm -q "${{pkg}}" >/dev/null 2>&1; then
    FEDORA_PKGS+=("${{pkg}}")
  fi
done

if [ "${{#FEDORA_PKGS[@]}}" -gt 0 ]; then
  abpm remove --dnf -y "${{FEDORA_PKGS[@]}}"
fi

systemctl disable {CLEANUP_SERVICE_NAME} >/dev/null 2>&1 || true
rm -f {CLEANUP_SERVICE_PATH} {CLEANUP_SCRIPT_PATH}
systemctl daemon-reload >/dev/null 2>&1 || true
"""

_CLEANUP_SERVICE_CONTENT = f"""[Unit]
Description=Nettoyage du noyau Fedora après démarrage sur CachyOS
After=local-fs.target

[Service]
Type=oneshot
ExecStart={CLEANUP_SCRIPT_PATH}

[Install]
WantedBy=multi-user.target
"""


def _emit_step(start_pct: int, end_pct: int, msg: str) -> str:
    return f"echo {shlex.quote(f'STEP:{start_pct}:{end_pct}:{msg}')}"


def _build_user_commands(user: UserAccount) -> list[str]:
    full_name = f"{user.first_name} {user.last_name}".strip()
    cmd = ["useradd", "-m", "-c", full_name]
    if user.is_admin:
        cmd.extend(["-G", "wheel"])
    cmd.append(user.username)

    lines = [
        " ".join(shlex.quote(arg) for arg in cmd),
        f"printf '%s:%s\\n' {shlex.quote(user.username)} {shlex.quote(user.password)} | chpasswd",
    ]

    if user.avatar_path:
        q_user = shlex.quote(user.username)
        q_avatar = shlex.quote(user.avatar_path)
        lines.extend(
            [
                f"if [ -f {q_avatar} ]; then",
                "  mkdir -p /var/lib/AccountsService/icons /var/lib/AccountsService/users",
                f"  cp {q_avatar} /var/lib/AccountsService/icons/{q_user}",
                f"  chmod 644 /var/lib/AccountsService/icons/{q_user}",
                f"  printf '[User]\\nIcon=/var/lib/AccountsService/icons/%s\\nSystemAccount=false\\n' {q_user} > /var/lib/AccountsService/users/{q_user}",
                "fi",
            ]
        )
    return lines


def _build_cachyos_commands() -> list[str]:
    """Installe le noyau CachyOS et planifie la suppression du noyau Fedora au reboot suivant."""
    return [
        "",
        _emit_step(25, 35, "Ajout du dépôt CachyOS"),
        f"abpm repo add {shlex.quote(CACHYOS_COPR)}",
        "abpm clean expire-cache",
        _emit_step(35, 65, "Installation du noyau CachyOS"),
        "abpm install --dnf --progress kernel-cachyos kernel-cachyos-devel-matched",
        # Nécessaire avec SELinux en mode enforcing pour le chargement des modules CachyOS
        "if command -v setsebool >/dev/null 2>&1; then setsebool -P domain_kernel_load_modules on || true; fi",
        _emit_step(65, 72, "Configuration du démarrage sur CachyOS"),
        'CACHYOS_VMLINUZ=$(ls -1 /boot/vmlinuz-*cachyos* 2>/dev/null | sort -V | tail -n 1 || true)',
        'if [ -n "${CACHYOS_VMLINUZ}" ] && command -v grubby >/dev/null 2>&1; then',
        '  grubby --set-default="${CACHYOS_VMLINUZ}"',
        "fi",
        "mkdir -p /usr/local/sbin /etc/systemd/system",
        f"cat <<'EOF_CLEANUP_SCRIPT' > {CLEANUP_SCRIPT_PATH}\n{_CLEANUP_SCRIPT_CONTENT.rstrip()}\nEOF_CLEANUP_SCRIPT",
        f"chmod 755 {CLEANUP_SCRIPT_PATH}",
        f"cat <<'EOF_CLEANUP_SERVICE' > {CLEANUP_SERVICE_PATH}\n{_CLEANUP_SERVICE_CONTENT.rstrip()}\nEOF_CLEANUP_SERVICE",
        f"systemctl enable {CLEANUP_SERVICE_NAME}",
    ]


def generate_home_install_script(state: SetupState) -> str:
    """Génère le script bash complet de configuration pour l'édition Home."""
    lines: list[str] = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        _emit_step(5, 10, "Configuration de la langue du système"),
        f"localectl set-locale LANG={shlex.quote(state.language)}",
        "",
        _emit_step(10, 25, "Création des comptes utilisateurs"),
    ]

    for user in state.users:
        lines.extend(_build_user_commands(user))

    if state.root_password:
        lines.append(
            f"printf 'root:%s\\n' {shlex.quote(state.root_password)} | chpasswd"
        )

    if state.kernel == "cachyos":
        lines.extend(_build_cachyos_commands())

    office_entry = OFFICE_COMMANDS.get(state.office_suite or "")
    if office_entry is not None:
        label, office_cmd = office_entry
        lines.extend(
            [
                "",
                _emit_step(72, 98, f"Installation de {label}"),
                " ".join(shlex.quote(arg) for arg in office_cmd),
            ]
        )

    lines.extend(
        [
            "",
            _emit_step(100, 100, "Installation terminée"),
            "",
        ]
    )
    return "\n".join(lines)


def run_home_install(
    state: SetupState,
    on_progress: Callable[[float, str], None],
    on_success: Callable[[], None],
    on_error: Callable[[str], None],
) -> None:
    """Exécute le script généré en arrière-plan et remonte la progression à l'UI GTK."""
    script_content = generate_home_install_script(state)

    def worker() -> None:
        fd, raw_path = tempfile.mkstemp(prefix="arrera-lynx-install-", suffix=".sh")
        script_path = Path(raw_path)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(script_content)
            os.chmod(script_path, 0o700)

            cmd = [str(script_path)] if os.geteuid() == 0 else ["pkexec", str(script_path)]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            step_start = 0
            step_end = 0
            current_msg = "Préparation de l'installation"
            last_error: str | None = None

            assert proc.stdout is not None
            for raw_line in proc.stdout:
                line = raw_line.strip()
                if line.startswith("STEP:"):
                    parts = line.split(":", 3)
                    if len(parts) == 4 and parts[1].isdigit() and parts[2].isdigit():
                        step_start = int(parts[1])
                        step_end = max(step_start, int(parts[2]))
                        current_msg = parts[3]
                        GLib.idle_add(on_progress, step_start / 100.0, current_msg)
                elif line.startswith("PROGRESS:ERROR:"):
                    last_error = line.removeprefix("PROGRESS:ERROR:").strip()
                elif line.startswith("PROGRESS:"):
                    parts = line.split(":", 2)
                    if len(parts) == 3 and parts[1].isdigit():
                        sub_pct = max(0, min(100, int(parts[1])))
                        mapped_pct = step_start + ((step_end - step_start) * sub_pct) / 100.0
                        sub_msg = parts[2] or current_msg
                        GLib.idle_add(on_progress, mapped_pct / 100.0, sub_msg)

            rc = proc.wait()
            if rc == 0:
                GLib.idle_add(on_progress, 1.0, "Installation terminée")
                GLib.idle_add(on_success)
            else:
                GLib.idle_add(on_error, last_error or f"Échec du script (code {rc}).")
        except (OSError, subprocess.SubprocessError) as exc:
            GLib.idle_add(on_error, str(exc))
        finally:
            script_path.unlink(missing_ok=True)

    threading.Thread(target=worker, daemon=True).start()
