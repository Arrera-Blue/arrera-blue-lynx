Name:           arrera-blue-lynx
Version:        2026.1.0
Release:        2%{?dist}
Summary:        Interface de premier démarrage pour Arrera Blue OS

License:        GPL-3.0-or-later
URL:            https://github.com/Arrera-Blue/arrera-blue-lynx
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros

Requires:       python3
Requires:       python3-gobject
Requires:       gtk4
Requires:       libadwaita
Requires:       NetworkManager
Requires:       abpm
Requires:       cage
Requires:       polkit
Requires:       shadow-utils
Requires:       systemd

%description
Arrera Blue Lynx est l'assistant graphique de premier démarrage (OOBE) pour
Arrera Blue OS (éditions Home et Education), développé en Python avec GTK 4
et Libadwaita. Il configure la langue, le Wi-Fi, les comptes utilisateurs,
le noyau et les logiciels via abpm.

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
%{_datadir}/arrera-blue-lynx

%changelog
* Tue Nov 24 2026 Arrera Software <contact@arrera.org> - 2026.1.0-2
- Différer l'activation du mode plein écran après le premier commit Wayland pour éviter le crash Cage/wlroots (Assertion 'surface->initialized' failed)

* Sun Nov 22 2026 Arrera Software <contact@arrera.org> - 2026.1.0-1
- Premier packaging RPM pour Arrera Blue Lynx (éditions Home et Education)
