# Arrera Blue Lynx

Interface de premier démarrage (OOBE) pour **Arrera Blue OS** (éditions **Home**, **Education**, **Enterprise** et **Server**).

---

## Fonctionnement par édition

### Édition Home (`arrera-blue-lynx-home`)
1. Bienvenue & sélection de la langue système (`localectl set-locale`).
2. Connexion réseau : étape Wi-Fi via `nmcli` (ignorée automatiquement si une connexion Ethernet fonctionnelle est détectée).
3. Création de l'utilisateur principal (administrateur ou non, avatar AccountsService) et mot de passe `root` (optionnel si l'utilisateur est admin, obligatoire sinon).
4. Choix du noyau : **Fedora** (défaut) ou **CachyOS** (ajout du Copr `bieszczaders/kernel-cachyos` via `abpm`, génération/vérification `dracut` + `grubby` + `grub2-mkconfig` et suppression différée du noyau Fedora + mise à jour `0-rescue` au redémarrage suivant via `arrera-cleanup-fedora-kernel.service`).
5. Mise à jour système via `abpm update -y --progress` (si Internet est actif) et choix optionnel de bureautique : **LibreOffice** (DNF), **OnlyOffice** (Flathub) ou aucun.

### Édition Education (`arrera-blue-lynx-education`)
1. Bienvenue, langue et Wi-Fi (identique à Home).
2. Création du compte adulte (administrateur obligatoire).
3. Création optionnelle d'un ou plusieurs comptes enfants/adolescents (profils d'âge, non administrateurs).
4. Mise à jour système via `abpm update -y --progress` (si Internet est actif), activation du Copr `arrera-software/education-suite` si absent et installation des paquets éducatifs via `abpm` (DNF + Flathub ; *Arrera Edu Pilot* non inclus pour le moment).

### Édition Enterprise (`arrera-blue-lynx-enterprise`)
1. Bienvenue (`logo-enterprise.png`), langue et Wi-Fi.
2. Création du compte utilisateur/administrateur + mot de passe `root` obligatoire.
3. Mise à jour système via `abpm update -y --progress` (si Internet est actif).

### Édition Server (`arrera-blue-lynx-server`)
1. Interface console / TUI **sans dépendance GTK / Wayland** (exécutable directement sur `/dev/tty1`).
2. Sélection de la langue (`localectl set-locale`) et du clavier console (`localectl set-keymap`, défaut `fr`).
3. Détection Ethernet ; si absent et carte Wi-Fi détectée, scan et connexion via `nmcli`.
4. Saisie du nom d'hôte (défaut `arrera-server`, appliqué via `hostnamectl`, `/etc/hostname` et `/etc/hosts`).
5. Création du compte administrateur (`wheel`) et définition du mot de passe `root`.
6. Si Internet est actif, mise à jour système via `abpm update -y --dnf`, puis affichage du récapitulatif (IP locale, hostname, utilisateur).

---

## Intégration dans l'installateur / premier démarrage (OOBE)

### 1. Paquet et binaires fournis
Une fois le RPM `arrera-blue-lynx` installé (via Copr ou en local), quatre commandes sont disponibles dans `/usr/bin` :

```bash
arrera-blue-lynx-home
arrera-blue-lynx-education
arrera-blue-lynx-enterprise
arrera-blue-lynx-server
```

Les ressources graphiques et CSS sont installées dans `/usr/share/arrera-blue-lynx/assets` (utilisé automatiquement si le dossier `assets/` local n'est pas présent).

### 2. Lancement en session kiosque (`cage`) ou console (`tty1`)
```bash
# Éditions graphiques sous cage
cage -- arrera-blue-lynx-home
cage -- arrera-blue-lynx-education
cage -- arrera-blue-lynx-enterprise

# Édition Server directement en console (sans cage ni GTK)
arrera-blue-lynx-server
```

### 3. Options en ligne de commande
| Option | Effet |
|---|---|
| *(aucune)* | Mode production : exécution réelle (plein écran pour les éditions graphiques) |
| `--windowed` | Lance la fenêtre graphique en `1280x720` (tests en VM) |
| `--force-wifi` | Force la configuration Wi-Fi même si Ethernet est actif |
| `--demo` | Simule l'installation sans modifier le système |

### 4. Prérequis système et privilèges
- **NetworkManager** doit être actif (`nmcli` utilisé pour détecter Ethernet et connecter le Wi-Fi).
- **Compte de premier démarrage :** l'identifiant `arrera-setup` est déjà réservé dans l'assistant et ne peut pas être choisi par l'utilisateur final.
- **Droits `root` :** les éditions graphiques exécutent le script généré directement si `UID 0`, sinon via `pkexec`. Sur **Server**, le script est exécuté directement si `UID 0`, sinon via `sudo`.

### 5. Journaux d'exécution (logs)
Lorsque l'installation réelle s'exécute en `root`, les journaux sont enregistrés avec les droits `600` dans `/root` :
- `/root/arrera-blue-lynx-install.log` : trace complète de l'installation (sans les mots de passe).
- `/root/arrera-blue-lynx-kernel-cleanup.log` : trace du service `arrera-cleanup-fedora-kernel.service` au redémarrage suivant (si le noyau CachyOS a été choisi).

---

## Développement et test local

Installer les dépendances sur Arrera Blue / Fedora :
```bash
./scripts/setup-dev.sh
```

Lancer en développement (mode `--demo` actif par défaut pour ne pas modifier la machine hôte) :
```bash
./scripts/launch_dev.sh 1          # Home (démo)
./scripts/launch_dev.sh 2          # Education (démo)
./scripts/launch_dev.sh 3          # Enterprise (démo)
./scripts/launch_dev.sh 4          # Server (TUI démo)

# Pour tester l'exécution réelle en VM depuis launch_dev.sh :
./scripts/launch_dev.sh 1 --real
```

---

## Packaging RPM et publication Copr

Le dépôt inclut `pyproject.toml`, `arrera-blue-lynx.spec` et `scripts/build-rpm.sh` :

```bash
# Construire le SRPM et le RPM binaire en local (+ vérification rpmlint)
./scripts/build-rpm.sh

# Construire uniquement le paquet source (.src.rpm)
./scripts/build-rpm.sh --srpm-only

# Construire le SRPM et lancer un build sur Fedora Copr
./scripts/build-rpm.sh --copr arrera-software/arrera-blue
```
