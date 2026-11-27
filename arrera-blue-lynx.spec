Name:           arrera-blue-lynx
Version:        2026.1.0
Release:        3%{?dist}
Summary:        Interface de premier démarrage pour Arrera Blue OS

License:        GPL-3.0-or-later
URL:            https://github.com/Arrera-Blue/arrera-blue-lynx
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros

Requires:       python3
Requires:       NetworkManager
Requires:       abpm
Requires:       polkit
Requires:       shadow-utils
Requires:       systemd
Recommends:     python3-gobject
Recommends:     gtk4
Recommends:     libadwaita
Recommends:     cage

%description
Arrera Blue Lynx est l'assistant de premier démarrage (OOBE) pour
Arrera Blue OS (éditions Home, Education, Enterprise et Server).
Les éditions graphiques utilisent Python avec GTK 4 et Libadwaita ;
l'édition Server fonctionne en console sans dépendance graphique.

%prep
%autosetup

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files arrera_blue_lynx

install -d -m 0755 %{buildroot}%{_datadir}/arrera-blue-lynx/assets
cp -a assets/. %{buildroot}%{_datadir}/arrera-blue-lynx/assets/

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/arrera-blue-lynx-home
%{_bindir}/arrera-blue-lynx-education
%{_bindir}/arrera-blue-lynx-enterprise
%{_bindir}/arrera-blue-lynx-server
%{_datadir}/arrera-blue-lynx

%changelog
* Fri Nov 27 2026 Arrera Software <contact@arrera.org> - 2026.1.0-3
- Ajout des éditions Enterprise et Server (TUI sans dépendance GTK)
- Ajout de la mise à jour système via abpm et finalisation de la bascule complète CachyOS (dracut, grub2-mkconfig, 0-rescue)
- Passage de gtk4, libadwaita, python3-gobject et cage en Recommends pour l'édition Server

* Tue Nov 24 2026 Arrera Software <contact@arrera.org> - 2026.1.0-2
- Différer l'activation du mode plein écran après le premier commit Wayland pour éviter le crash Cage/wlroots (Assertion 'surface->initialized' failed)

* Sun Nov 22 2026 Arrera Software <contact@arrera.org> - 2026.1.0-1
- Premier packaging RPM pour Arrera Blue Lynx (éditions Home et Education)
