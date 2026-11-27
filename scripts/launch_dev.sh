#!/usr/bin/env bash
set -euo pipefail

# Se place toujours à la racine du projet pour que `python3 -m arrera_blue_lynx...` fonctionne
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

CHOICE=""
DEMO_MODE=true
EXTRA_ARGS=()

for arg in "$@"; do
    case "${arg}" in
        --real)
            DEMO_MODE=false
            ;;
        --demo)
            DEMO_MODE=true
            ;;
        *)
            if [[ -z "${CHOICE}" && "${arg}" != -* ]]; then
                CHOICE="${arg}"
            else
                EXTRA_ARGS+=("${arg}")
            fi
            ;;
    esac
done

if [[ "${DEMO_MODE}" == true ]]; then
    EXTRA_ARGS+=("--demo")
fi

if [[ -z "${CHOICE}" ]]; then
    echo "=== Arrera Blue Lynx (mode dev — démo par défaut, --real pour exécuter) ==="
    echo "1) Home       (fenêtré)"
    echo "2) Education  (fenêtré)"
    echo "3) Enterprise (fenêtré)"
    echo "4) Server     (terminal / TUI)"
    echo "5) Home       + forcer la page Wi-Fi (--force-wifi)"
    echo "6) Education  + forcer la page Wi-Fi (--force-wifi)"
    echo "7) Enterprise + forcer la page Wi-Fi (--force-wifi)"
    echo ""
    read -rp "Choix [1-7] : " CHOICE
fi

case "${CHOICE}" in
    1|home)
        exec python3 -m arrera_blue_lynx.editions.main_home --windowed "${EXTRA_ARGS[@]}"
        ;;
    2|education)
        exec python3 -m arrera_blue_lynx.editions.main_education --windowed "${EXTRA_ARGS[@]}"
        ;;
    3|enterprise)
        exec python3 -m arrera_blue_lynx.editions.main_enterprise --windowed "${EXTRA_ARGS[@]}"
        ;;
    4|server)
        exec python3 -m arrera_blue_lynx.editions.main_server "${EXTRA_ARGS[@]}"
        ;;
    5|home-wifi)
        exec python3 -m arrera_blue_lynx.editions.main_home --windowed --force-wifi "${EXTRA_ARGS[@]}"
        ;;
    6|education-wifi)
        exec python3 -m arrera_blue_lynx.editions.main_education --windowed --force-wifi "${EXTRA_ARGS[@]}"
        ;;
    7|enterprise-wifi)
        exec python3 -m arrera_blue_lynx.editions.main_enterprise --windowed --force-wifi "${EXTRA_ARGS[@]}"
        ;;
    *)
        echo "Choix invalide : '${CHOICE}'. Utilisez 1-7 ou home/education/enterprise/server." >&2
        exit 1
        ;;
esac
