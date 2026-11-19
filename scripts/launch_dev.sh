#!/usr/bin/env bash
set -euo pipefail

# Se place toujours à la racine du projet pour que `python3 -m arrera_blue_lynx...` fonctionne
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

CHOICE="${1:-}"

if [[ -z "${CHOICE}" ]]; then
    echo "=== Arrera Blue Lynx (mode dev fenêtré) ==="
    echo "1) Home      (python3 -m arrera_blue_lynx.editions.main_home --windowed)"
    echo "2) Education (python3 -m arrera_blue_lynx.editions.main_education --windowed)"
    echo ""
    read -rp "Choix [1/2] : " CHOICE
fi

case "${CHOICE}" in
    1|home)
        exec python3 -m arrera_blue_lynx.editions.main_home --windowed
        ;;
    2|education)
        exec python3 -m arrera_blue_lynx.editions.main_education --windowed
        ;;
    *)
        echo "Choix invalide : '${CHOICE}'. Utilisez 1 (home) ou 2 (education)." >&2
        exit 1
        ;;
esac
