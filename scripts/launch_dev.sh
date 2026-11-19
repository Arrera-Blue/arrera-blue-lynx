#!/usr/bin/env bash
set -euo pipefail

# Se place toujours à la racine du projet pour que `python3 -m arrera_blue_lynx...` fonctionne
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

CHOICE="${1:-}"
EXTRA_ARGS=("${@:2}")

if [[ -z "${CHOICE}" ]]; then
    echo "=== Arrera Blue Lynx (mode dev fenêtré) ==="
    echo "1) Home      (normal)"
    echo "2) Education (normal)"
    echo "3) Home      + forcer la page Wi-Fi (--force-wifi)"
    echo "4) Education + forcer la page Wi-Fi (--force-wifi)"
    echo ""
    read -rp "Choix [1-4] : " CHOICE
fi

case "${CHOICE}" in
    1|home)
        exec python3 -m arrera_blue_lynx.editions.main_home --windowed "${EXTRA_ARGS[@]}"
        ;;
    2|education)
        exec python3 -m arrera_blue_lynx.editions.main_education --windowed "${EXTRA_ARGS[@]}"
        ;;
    3|home-wifi)
        exec python3 -m arrera_blue_lynx.editions.main_home --windowed --force-wifi "${EXTRA_ARGS[@]}"
        ;;
    4|education-wifi)
        exec python3 -m arrera_blue_lynx.editions.main_education --windowed --force-wifi "${EXTRA_ARGS[@]}"
        ;;
    *)
        echo "Choix invalide : '${CHOICE}'. Utilisez 1 (home), 2 (education), 3 (home-wifi) ou 4 (education-wifi)." >&2
        exit 1
        ;;
esac
