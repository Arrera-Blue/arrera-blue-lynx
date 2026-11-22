#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
SPEC_FILE="${PROJECT_ROOT}/arrera-blue-lynx.spec"

if [[ ! -f "${SPEC_FILE}" ]]; then
    echo "Erreur : fichier spec introuvable (${SPEC_FILE})." >&2
    exit 1
fi

NAME="$(awk '/^Name:/ {print $2; exit}' "${SPEC_FILE}")"
VERSION="$(awk '/^Version:/ {print $2; exit}' "${SPEC_FILE}")"
TARBALL_NAME="${NAME}-${VERSION}.tar.gz"
RPMBUILD_DIR="${RPMBUILD_DIR:-${HOME}/rpmbuild}"

MODE="all"
COPR_REPO=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --srpm-only)
            MODE="srpm"
            shift
            ;;
        --copr)
            if [[ $# -lt 2 || -z "$2" ]]; then
                echo "Erreur : --copr attend <utilisateur>/<projet>." >&2
                exit 1
            fi
            MODE="copr"
            COPR_REPO="$2"
            shift 2
            ;;
        -h|--help)
            cat <<EOF
Usage : $(basename "$0") [--srpm-only | --copr <utilisateur>/<projet>]

Options :
  (aucune)                     Construit le SRPM et le RPM binaire puis lance rpmlint
  --srpm-only                  Construit uniquement le paquet source (.src.rpm)
  --copr <utilisateur/projet>  Construit le SRPM et lance un build sur Fedora Copr
EOF
            exit 0
            ;;
        *)
            echo "Option inconnue : '$1'" >&2
            exit 1
            ;;
    esac
done

mkdir -p \
    "${RPMBUILD_DIR}/BUILD" \
    "${RPMBUILD_DIR}/BUILDROOT" \
    "${RPMBUILD_DIR}/RPMS" \
    "${RPMBUILD_DIR}/SOURCES" \
    "${RPMBUILD_DIR}/SPECS" \
    "${RPMBUILD_DIR}/SRPMS"

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "${STAGING_DIR}"' EXIT

SRC_PREFIX="${NAME}-${VERSION}"
mkdir -p "${STAGING_DIR}/${SRC_PREFIX}"

cp -a \
    "${PROJECT_ROOT}/arrera_blue_lynx" \
    "${PROJECT_ROOT}/assets" \
    "${PROJECT_ROOT}/pyproject.toml" \
    "${PROJECT_ROOT}/arrera-blue-lynx.spec" \
    "${PROJECT_ROOT}/README.md" \
    "${STAGING_DIR}/${SRC_PREFIX}/"

find "${STAGING_DIR}/${SRC_PREFIX}" \
    \( -name "__pycache__" -o -name "*.py[cod]" -o -name "*.egg-info" \) \
    -exec rm -rf {} +

tar -C "${STAGING_DIR}" -czf "${RPMBUILD_DIR}/SOURCES/${TARBALL_NAME}" "${SRC_PREFIX}"
chmod 644 "${RPMBUILD_DIR}/SOURCES/${TARBALL_NAME}"
cp -f "${SPEC_FILE}" "${RPMBUILD_DIR}/SPECS/${NAME}.spec"

echo "==> Archive source prête : ${RPMBUILD_DIR}/SOURCES/${TARBALL_NAME}"

if [[ "${MODE}" == "srpm" || "${MODE}" == "copr" ]]; then
    rpmbuild --define "_topdir ${RPMBUILD_DIR}" -bs "${RPMBUILD_DIR}/SPECS/${NAME}.spec"
    SRPM_PATH="$(ls -1t "${RPMBUILD_DIR}/SRPMS/${NAME}-${VERSION}-"*.src.rpm | head -n 1)"
    echo "==> SRPM généré : ${SRPM_PATH}"

    if [[ "${MODE}" == "copr" ]]; then
        if ! command -v copr-cli >/dev/null 2>&1; then
            echo "Erreur : 'copr-cli' est introuvable. Installez copr-cli et configurez ~/.config/copr." >&2
            exit 1
        fi
        echo "==> Envoi sur Copr (${COPR_REPO})..."
        copr-cli build "${COPR_REPO}" "${SRPM_PATH}"
    fi
else
    rpmbuild --define "_topdir ${RPMBUILD_DIR}" -ba "${RPMBUILD_DIR}/SPECS/${NAME}.spec"
    SRPM_PATH="$(ls -1t "${RPMBUILD_DIR}/SRPMS/${NAME}-${VERSION}-"*.src.rpm | head -n 1)"
    RPM_PATH="$(ls -1t "${RPMBUILD_DIR}/RPMS/noarch/${NAME}-${VERSION}-"*.noarch.rpm | head -n 1)"
    echo "==> SRPM généré : ${SRPM_PATH}"
    echo "==> RPM généré  : ${RPM_PATH}"

    if command -v rpmlint >/dev/null 2>&1; then
        echo "==> Vérification rpmlint..."
        rpmlint "${SPEC_FILE}" "${SRPM_PATH}" "${RPM_PATH}" || true
    fi
fi
