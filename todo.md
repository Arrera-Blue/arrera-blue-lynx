# TODO — `arrera-blue-lynx` : OOBE sur les 4 Éditions (Home, Education, Enterprise, Server), Mise à jour Système via `abpm` & Bascule complète sur le Noyau CachyOS

Ce document détaille l'ensemble des modifications à apporter dans `arrera-blue-lynx` pour couvrir toutes les éditions d'Arrera Blue OS 2026, centraliser la mise à jour initiale du système via **`abpm`**, et garantir le remplacement complet du noyau Fedora par le noyau CachyOS.

---

## 1. Ajout de l'Édition Graphique Enterprise (`arrera-blue-lynx-enterprise`)

### [ ] A. Point d'entrée et ressource graphique (`pyproject.toml`, `assets/`)
- **Fichier** : [pyproject.toml](file:///Users/baptistep/Documents/arrera-blue/arrera-blue-lynx/pyproject.toml)
  - Ajouter l'exécutable :
    ```toml
    arrera-blue-lynx-enterprise = "arrera_blue_lynx.editions.main_enterprise:main"
    ```
- **Asset** : Copier le logo Enterprise (`arrera-logo.png` de `arrera-installer/branding/arrera-enterprise/`) vers `assets/logo-enterprise.png`.

### [ ] B. Pipeline de pages Enterprise (`arrera_blue_lynx/editions/main_enterprise.py`)
- Créer `arrera_blue_lynx/editions/main_enterprise.py` (`app_id="org.arrera.BlueLynx.Enterprise"`) avec l'enchaînement suivant :
  1. `WelcomePage(logo_filename="logo-enterprise.png")`
  2. `LanguagePage` (configuration `localectl set-locale`)
  3. `WifiPage` (ignorée automatiquement si une connexion Ethernet active est détectée)
  4. `HomeUserAccountPage` (création du compte utilisateur/administrateur + mot de passe `root`)
     *(Structure modulaire prête pour intercaler ultérieurement une étape d'intégration LDAP / Active Directory).*
  5. `HomeOfficePage` (choix optionnel : **OnlyOffice**, **LibreOffice**, ou aucun — **sans** la page de sélection du noyau CachyOS)
  6. `InstallPage(edition="enterprise", logo_filename="logo-enterprise.png")`
  7. `FinishPage`

---

## 2. Ajout de l'Édition Console / TUI Server (`arrera-blue-lynx-server`)

### [ ] A. Point d'entrée sans dépendance graphique (`pyproject.toml`, `arrera_blue_lynx/editions/main_server.py`)
- **Fichier** : [pyproject.toml](file:///Users/baptistep/Documents/arrera-blue/arrera-blue-lynx/pyproject.toml)
  - Ajouter l'exécutable :
    ```toml
    arrera-blue-lynx-server = "arrera_blue_lynx.editions.main_server:main"
    ```
- **Fichier** : Créer `arrera_blue_lynx/editions/main_server.py` :
  - **Zéro import `gi` / `Gtk` / `Adw`** afin de s'exécuter directement sur `/dev/tty1` sans compositeur Wayland (`cage`) ni bibliothèques graphiques.
  - Flux interactif en terminal clair et structuré :
    1. **Langue & Clavier** : sélection de la locale système (`localectl set-locale`) et du keymap console (`localectl set-keymap`, défaut : `fr`).
    2. **Réseau** : détection automatique d'Ethernet ; si non connecté et carte Wi-Fi présente, scan et connexion via `nmcli`.
    3. **Nom d'hôte (Hostname)** : saisie du nom d'hôte (défaut : `arrera-server`) et application via `hostnamectl set-hostname` + `/etc/hostname` + `/etc/hosts`.
    4. **Comptes Administrateur & Root** : création du compte administrateur (`useradd -m -G wheel`) avec validation d'identifiant et définition du mot de passe `root`.
    5. **Mise à jour du système via `abpm`** : si Internet est disponible, exécution de :
       ```bash
       abpm clean expire-cache
       abpm update -y --dnf
       ```
    6. **Finalisation** : affichage du récapitulatif (adresse IP locale, hostname, compte créé) et sortie avec code `0` pour que `arrera-oobe.sh` désactive le service OOBE et démarre `getty@tty1.service`.

---

## 3. Mise à jour Système via `abpm` et Remplacement Complet du Noyau Fedora par CachyOS

### [ ] A. Intégration de `abpm update -y --progress` dans l'étape d'installation (`arrera_blue_lynx/core/installer.py`, `arrera_blue_lynx/pages/common/install.py`)
- **Fichier** : [arrera_blue_lynx/core/installer.py](file:///Users/baptistep/Documents/arrera-blue/arrera-blue-lynx/arrera_blue_lynx/core/installer.py)
- **Actions** :
  1. Sur les éditions **Home**, **Education** et **Enterprise**, ajouter une étape de mise à jour globale du système et des applications (exécutée automatiquement si une connexion Internet est active) :
     ```bash
     abpm clean expire-cache
     abpm update -y --progress || true
     ```
  2. Ajouter `generate_enterprise_install_script()` et `run_enterprise_install()` (et brancher `self._edition == "enterprise"` dans [arrera_blue_lynx/pages/common/install.py](file:///Users/baptistep/Documents/arrera-blue/arrera-blue-lynx/arrera_blue_lynx/pages/common/install.py#L202-L216)).

### [ ] B. Installation du noyau CachyOS et suppression du noyau Fedora au redémarrage (`arrera_blue_lynx/core/installer.py`)
- **Fichier** : [arrera_blue_lynx/core/installer.py](file:///Users/baptistep/Documents/arrera-blue/arrera-blue-lynx/arrera_blue_lynx/core/installer.py) (fonction `_build_cachyos_commands()` et `_CLEANUP_SCRIPT_CONTENT`)
- **Déroulement en 2 temps (installation pendant l'OOBE, suppression du noyau Fedora au redémarrage suivant)** :
  1. **Pendant l'OOBE (premier démarrage)** :
     - Ajout du Copr `bieszczaders/kernel-cachyos` et installation de `kernel-cachyos kernel-cachyos-devel-matched` via `abpm install --dnf --progress`.
     - Vérification que `/boot/vmlinuz-${CACHYOS_KVER}` et `/boot/initramfs-${CACHYOS_KVER}.img` existent bien dans `/boot` (sinon copie depuis `/usr/lib/modules/${CACHYOS_KVER}/vmlinuz` et génération via `dracut -f --hostonly --no-hostonly-cmdline --add plymouth --kver "${CACHYOS_KVER}"`).
     - Activation de CachyOS comme noyau par défaut pour le prochain redémarrage :
       - `grubby --set-default="/boot/vmlinuz-${CACHYOS_KVER}"` (pour UEFI / BLS et `grubenv`).
       - `grub2-mkconfig -o /boot/grub2/grub.cfg` (indispensable en BIOS Legacy où `GRUB_ENABLE_BLSCFG=false` utilise des blocs `menuentry` statiques).
     - Activation du service systemd `arrera-cleanup-fedora-kernel.service` pour le redémarrage suivant (et redémarrage automatique déclenché par `arrera-oobe.sh` à la fin de l'assistant).
  2. **Au redémarrage suivant sur CachyOS (`arrera-cleanup-fedora-kernel.service`)** :
     - Le script `/usr/local/sbin/arrera-cleanup-fedora-kernel.sh` vérifie que le noyau actif est bien CachyOS (`uname -r == *cachyos*`).
     - Désinstalle alors les paquets du noyau Fedora via `abpm` (qui fonctionne hors-ligne dès `local-fs.target` et déverrouille `protected_packages` sur `kernel-core`) :
       ```bash
       FEDORA_PKGS=()
       for pkg in kernel kernel-core kernel-modules kernel-modules-core kernel-modules-extra kernel-devel kernel-devel-matched kernel-uki-virt; do
         if rpm -q "${pkg}" >/dev/null 2>&1; then
           FEDORA_PKGS+=("${pkg}")
         fi
       done
       if [ "${#FEDORA_PKGS[@]}" -gt 0 ]; then
         abpm remove --dnf -y "${FEDORA_PKGS[@]}"
       fi
       ```
     - Met à jour l'image `0-rescue` dans `/boot` avec une copie du noyau et de l'initramfs CachyOS, régénère `/boot/grub2/grub.cfg`, puis autodétruit le service `arrera-cleanup-fedora-kernel.service`.

---

## 4. Packaging RPM (`arrera-blue-lynx.spec`)

### [ ] A. Mise à jour des dépendances et des binaires installés
- **Fichier** : [arrera-blue-lynx.spec](file:///Users/baptistep/Documents/arrera-blue/arrera-blue-lynx/arrera-blue-lynx.spec)
- **Actions** :
  1. Ajouter dans `%files` :
     ```spec
     %{_bindir}/arrera-blue-lynx-enterprise
     %{_bindir}/arrera-blue-lynx-server
     ```
  2. Déplacer `gtk4`, `libadwaita`, `python3-gobject`, `cage` de `Requires:` vers `Recommends:` afin que l'installation sur **Arrera Server** n'impose pas la pile graphique si elle n'est pas souhaitée (les saveurs Desktop installent déjà GTK4, Libadwaita et Cage).
  3. Incrémenter `Release` à `3%{?dist}` (`2026.1.0-3`) et publier sur le Copr `arrera-software/arrera-blue`.
