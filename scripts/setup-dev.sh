#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Arrera Blue Lynx - Installation de l'environnement de développement et de test
# Cible : Arrera Blue / Fedora (DNF + RPM)
# Stack : Python 3 + GTK4 + Libadwaita + Cage + Meson + outils RPM
# ==============================================================================

if ! command -v dnf >/dev/null 2>&1; then
    echo "Erreur : 'dnf' est introuvable. Ce script est prévu pour Arrera Blue / Fedora." >&2
    exit 1
fi

if [[ "${EUID}" -eq 0 ]]; then
    SUDO=""
else
    SUDO="sudo"
fi

# 1. Runtime Python / GTK4 / Libadwaita / Cage / D-Bus
RUNTIME_PKGS=(
    python3
    python3-gobject
    gobject-introspection
    gtk4
    libadwaita
    cage
    NetworkManager-libnm
    python3-dasbus
    python3-dbus
)

# 2. Build GTK4 / UI / Traductions / Validation desktop
BUILD_PKGS=(
    meson
    ninja-build
    blueprint-compiler
    glib2-devel
    gtk4-devel-tools
    gettext
    desktop-file-utils
    appstream
)

# 3. Qualité & tests Python
DEV_PKGS=(
    python3-pytest
    python3-mypy
    ruff
)

# 4. Packaging RPM
RPM_PKGS=(
    rpm-build
    rpmdevtools
    rpmlint
    pyproject-rpm-macros
    systemd-rpm-macros
)

ALL_PKGS=(
    "${RUNTIME_PKGS[@]}"
    "${BUILD_PKGS[@]}"
    "${DEV_PKGS[@]}"
    "${RPM_PKGS[@]}"
)

echo "==> Installation des dépendances pour Arrera Blue Lynx..."
${SUDO} dnf install -y "${ALL_PKGS[@]}"

# Si le paquet cage est enregistré en base RPM mais que le binaire manque sur le disque
if ! command -v cage >/dev/null 2>&1; then
    echo "==> Binaire 'cage' absent malgré le paquet installé, réinstallation de cage..."
    ${SUDO} dnf reinstall -y cage
fi

# Prépare l'arborescence ~/rpmbuild (idempotent) pour la création du RPM par la suite
if [[ "${EUID}" -ne 0 ]] && command -v rpmdev-setuptree >/dev/null 2>&1; then
    echo "==> Initialisation de l'arborescence ~/rpmbuild..."
    rpmdev-setuptree
fi

echo "==> Vérification de l'environnement installé..."
python3 - <<'EOF'
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

print(f"  - Python     : {sys.version.split()[0]}")
print(f"  - GTK        : {Gtk.get_major_version()}.{Gtk.get_minor_version()}.{Gtk.get_micro_version()}")
print(f"  - Libadwaita : {Adw.get_major_version()}.{Adw.get_minor_version()}.{Adw.get_micro_version()}")
EOF

echo "  - Cage       : $(cage -v 2>&1 || true)"
echo "  - Meson      : $(meson --version)"
echo "  - Blueprint  : $(blueprint-compiler --version)"
echo "  - rpmbuild   : $(rpmbuild --version)"

echo ""
echo "Environnement prêt ! Vous pouvez tester une app GTK dans Cage avec :"
echo "  cage -- python3 <votre_script.py>"
