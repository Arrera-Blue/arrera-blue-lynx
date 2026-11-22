# Arrera Blue Lynx

Interface graphique de premier démarrage (OOBE) pour **Arrera Blue OS** (éditions **Home** et **Education**), développée en Python avec **GTK 4** et **Libadwaita**.

---

## Fonctionnement par édition

### Édition Home (`arrera-blue-lynx-home`)
1. Bienvenue & sélection de la langue système (`localectl set-locale`).
2. Connexion réseau : étape Wi-Fi via `nmcli` (ignorée automatiquement si une connexion Ethernet fonctionnelle est détectée).
3. Création de l'utilisateur principal (administrateur ou non, avatar AccountsService) et mot de passe `root` (optionnel si l'utilisateur est admin, obligatoire sinon).
4. Choix du noyau : **Fedora** (défaut) ou **CachyOS** (ajout du Copr `bieszczaders/kernel-cachyos` via `abpm`, configuration GRUB par défaut et nettoyage différé du noyau Fedora au redémarrage suivant via `arrera-cleanup-fedora-kernel.service`).
5. Choix optionnel de bureautique : **LibreOffice** (DNF), **OnlyOffice** (Flathub) ou aucun.

### Édition Education (`arrera-blue-lynx-education`)
1. Bienvenue, langue et Wi-Fi (identique à Home).
2. Création du compte adulte (administrateur obligatoire).
3. Création optionnelle d'un ou plusieurs comptes enfants/adolescents (profils d'âge, non administrateurs).
4. Activation du Copr `arrera-software/education-suite` si absent et installation des paquets éducatifs via `abpm` (DNF + Flathub ; *Arrera Edu Pilot* non inclus pour le moment).

---

## Intégration dans l'installateur / premier démarrage (OOBE)

### 1. Paquet et binaires fournis
Une fois le RPM `arrera-blue-lynx` installé (via Copr ou en local), deux commandes sont disponibles dans `/usr/bin` :

```bash
arrera-blue-lynx-home
arrera-blue-lynx-education
```

Les ressources graphiques et CSS sont installées dans `/usr/share/arrera-blue-lynx/assets` (utilisé automatiquement si le dossier `assets/` local n'est pas présent).

### 2. Lancement en session kiosque (`cage`)
En environnement de premier démarrage (sans session GNOME complète), lancez l'assistant dans `cage` :

```bash
# Édition Home
cage -- arrera-blue-lynx-home

# Édition Education
cage -- arrera-blue-lynx-education
```

### 3. Options en ligne de commande
Les deux binaires acceptent les options suivantes :

| Option | Effet |
|---|---|
| *(aucune)* | Mode production : plein écran + exécution réelle de l'installation |
| `--windowed` | Lance la fenêtre en `1280x720` (pratique pour les tests en VM) |
| `--force-wifi` | Affiche l'écran Wi-Fi même si Ethernet est actif |
| `--demo` | Simule la barre de progression sans modifier le système |

### 4. Prérequis système et privilèges
- **NetworkManager** doit être actif (`nmcli` utilisé pour détecter Ethernet et connecter le Wi-Fi).
- **Compte de premier démarrage :** l'identifiant `arrera-setup` est déjà réservé dans l'assistant et ne peut pas être choisi par l'utilisateur final.
- **Droits `root` :** lors de l'étape d'installation, si l'application ne tourne pas avec `UID 0`, elle exécute le script généré via `pkexec`. En session kiosque `cage` sans agent Polkit graphique, soit lancez le service OOBE en `root`, soit autorisez l'exécution sans invite pour `arrera-setup` via une règle Polkit.

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

Lancer en mode fenêtré de développement :
```bash
# Mode démo visuel (sans modifier le système)
./scripts/launch_dev.sh 1 --demo   # Home
./scripts/launch_dev.sh 2 --demo   # Education

# Mode réel fenêtré (pour tester dans une VM)
./scripts/launch_dev.sh 1          # Home
./scripts/launch_dev.sh 2          # Education
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
./scripts/build-rpm.sh --copr <utilisateur>/<projet>
```
