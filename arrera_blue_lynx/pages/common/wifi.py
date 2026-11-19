from collections.abc import Callable
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from arrera_blue_lynx.core.network import (
    WifiNetwork,
    connect_wifi,
    has_working_ethernet,
    list_wifi_networks,
)
from arrera_blue_lynx.core.state import SetupState


def _signal_icon_name(signal: int) -> str:
    if signal >= 75:
        return "network-wireless-signal-excellent-symbolic"
    if signal >= 50:
        return "network-wireless-signal-good-symbolic"
    if signal >= 25:
        return "network-wireless-signal-ok-symbolic"
    return "network-wireless-signal-weak-symbolic"


class _WifiRow(Gtk.ListBoxRow):
    def __init__(self, network: WifiNetwork) -> None:
        super().__init__()
        self.network = network
        self.add_css_class("language-row")

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)

        signal_icon = Gtk.Image.new_from_icon_name(_signal_icon_name(network.signal))
        signal_icon.set_pixel_size(18)
        box.append(signal_icon)

        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name_box.set_hexpand(True)

        ssid_label = Gtk.Label(label=network.ssid)
        ssid_label.set_xalign(0.0)
        ssid_label.add_css_class("language-row-label")
        name_box.append(ssid_label)

        if network.in_use:
            connected_label = Gtk.Label(label="Connecté")
            connected_label.set_xalign(0.0)
            connected_label.add_css_class("wifi-connected-badge")
            name_box.append(connected_label)

        box.append(name_box)

        if network.is_secured:
            lock_icon = Gtk.Image.new_from_icon_name("network-wireless-encrypted-symbolic")
            lock_icon.set_pixel_size(15)
            lock_icon.add_css_class("wifi-lock-icon")
            box.append(lock_icon)

        if network.in_use:
            check_icon = Gtk.Image.new_from_icon_name("object-select-symbolic")
            check_icon.set_pixel_size(16)
            check_icon.add_css_class("language-check-icon")
            box.append(check_icon)

        self.set_child(box)


class WifiPage(Gtk.Box):
    """Page commune de connexion Wi-Fi (sautée automatiquement si Ethernet fonctionne)."""

    def __init__(
        self,
        state: SetupState,
        on_next: Callable[[], None],
        on_back: Callable[[], None] | None = None,
        force_show: bool = False,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._state = state
        self._on_next = on_next
        self._on_back = on_back
        self._force_show = force_show
        self._busy = False
        self._connected_ssid: str | None = None

        self.add_css_class("setup-white-page")
        self.set_hexpand(True)
        self.set_vexpand(True)

        clamp = Adw.Clamp()
        clamp.set_maximum_size(480)
        clamp.set_tightening_threshold(400)
        clamp.set_hexpand(True)
        clamp.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_valign(Gtk.Align.CENTER)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(24)
        content.set_margin_end(24)

        # En-tête
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        header.set_halign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name("network-wireless-signal-excellent-symbolic")
        icon.set_pixel_size(44)
        icon.add_css_class("setup-header-icon")
        header.append(icon)

        title = Gtk.Label(label="Connexion Wi-Fi")
        title.add_css_class("setup-title")
        header.append(title)

        self._subtitle_label = Gtk.Label(
            label="Choisissez un réseau Wi-Fi pour vous connecter à Internet"
        )
        self._subtitle_label.add_css_class("setup-subtitle")
        header.append(self._subtitle_label)

        content.append(header)

        # Barre de statut + bouton Actualiser
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self._spinner = Gtk.Spinner()
        toolbar.append(self._spinner)

        self._status_label = Gtk.Label(label="Réseaux disponibles")
        self._status_label.set_xalign(0.0)
        self._status_label.set_hexpand(True)
        self._status_label.add_css_class("wifi-status-label")
        toolbar.append(self._status_label)

        self._refresh_btn = Gtk.Button()
        self._refresh_btn.add_css_class("flat")
        self._refresh_btn.add_css_class("circular")
        self._refresh_btn.set_tooltip_text("Actualiser les réseaux")
        self._refresh_btn.set_child(Gtk.Image.new_from_icon_name("view-refresh-symbolic"))
        self._refresh_btn.connect("clicked", lambda _btn: self.refresh_networks(rescan=True))
        toolbar.append(self._refresh_btn)

        content.append(toolbar)

        # Liste scrollable des réseaux Wi-Fi
        scrolled = Gtk.ScrolledWindow()
        scrolled.add_css_class("language-scroll")
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)
        scrolled.set_max_content_height(340)
        scrolled.set_propagate_natural_height(False)

        self._listbox = Gtk.ListBox()
        self._listbox.add_css_class("language-list")
        self._listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self._listbox.connect("row-activated", self._on_row_activated)

        self._empty_label = Gtk.Label(label="Recherche de réseaux Wi-Fi…")
        self._empty_label.add_css_class("setup-subtitle")
        self._empty_label.set_margin_top(48)
        self._empty_label.set_margin_bottom(48)
        self._listbox.set_placeholder(self._empty_label)

        scrolled.set_child(self._listbox)
        content.append(scrolled)

        # Message d'erreur (masqué par défaut)
        self._error_label = Gtk.Label()
        self._error_label.add_css_class("wifi-error-label")
        self._error_label.set_wrap(True)
        self._error_label.set_halign(Gtk.Align.CENTER)
        self._error_label.set_visible(False)
        content.append(self._error_label)

        # Navigation en bas : Retour (optionnel) + Suivant + Ignorer
        footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        footer.set_halign(Gtk.Align.CENTER)
        footer.set_margin_top(4)

        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        nav_box.set_halign(Gtk.Align.CENTER)

        if self._on_back is not None:
            back_btn = Gtk.Button()
            back_btn.add_css_class("circular")
            back_btn.add_css_class("setup-nav-back-btn")
            back_btn.set_tooltip_text("Retour")
            back_btn.connect("clicked", lambda _btn: self._on_back())

            back_icon = Gtk.Image.new_from_icon_name("go-previous-symbolic")
            back_icon.set_pixel_size(20)
            back_btn.set_child(back_icon)
            nav_box.append(back_btn)

        self._next_btn = Gtk.Button()
        self._next_btn.add_css_class("circular")
        self._next_btn.add_css_class("suggested-action")
        self._next_btn.add_css_class("setup-nav-next-btn")
        self._next_btn.set_tooltip_text("Continuer")
        self._next_btn.set_sensitive(False)
        self._next_btn.connect("clicked", lambda _btn: self._confirm_and_next())

        next_icon = Gtk.Image.new_from_icon_name("go-next-symbolic")
        next_icon.set_pixel_size(22)
        self._next_btn.set_child(next_icon)
        nav_box.append(self._next_btn)

        footer.append(nav_box)

        content.append(footer)

        clamp.set_child(content)
        self.append(clamp)

    def should_skip(self) -> bool:
        """Saute cette page si une connexion Ethernet fonctionnelle est déjà active."""
        if self._force_show:
            return False
        if has_working_ethernet():
            self._state.network_mode = "ethernet"
            self._state.wifi_ssid = None
            print("[WifiPage] Ethernet fonctionnel détecté -> étape Wi-Fi ignorée")
            return True
        return False

    def on_enter(self) -> None:
        """Lance un scan Wi-Fi dès que la page devient visible."""
        self.refresh_networks(rescan=True)

    def _set_busy(self, busy: bool, status_text: str) -> None:
        self._busy = busy
        self._refresh_btn.set_sensitive(not busy)
        self._listbox.set_sensitive(not busy)
        self._status_label.set_label(status_text)
        if busy:
            self._spinner.start()
        else:
            self._spinner.stop()

    def refresh_networks(self, rescan: bool = True) -> None:
        if self._busy:
            return
        self._error_label.set_visible(False)
        self._set_busy(True, "Recherche de réseaux Wi-Fi…")

        def worker() -> None:
            networks = list_wifi_networks(rescan=rescan)
            GLib.idle_add(self._populate_networks, networks)

        threading.Thread(target=worker, daemon=True).start()

    def _populate_networks(self, networks: list[WifiNetwork]) -> bool:
        while (child := self._listbox.get_first_child()) is not None:
            self._listbox.remove(child)

        self._connected_ssid = None
        for net in networks:
            self._listbox.append(_WifiRow(net))
            if net.in_use:
                self._connected_ssid = net.ssid

        if not networks:
            self._empty_label.set_label("Aucun réseau Wi-Fi détecté")

        if self._connected_ssid:
            self._state.network_mode = "wifi"
            self._state.wifi_ssid = self._connected_ssid
            self._subtitle_label.set_label(f"Connecté à « {self._connected_ssid} »")
            self._next_btn.set_sensitive(True)
        else:
            self._subtitle_label.set_label(
                "Choisissez un réseau Wi-Fi pour vous connecter à Internet"
            )
            self._next_btn.set_sensitive(False)

        self._set_busy(False, "Réseaux disponibles")
        return False

    def _on_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if self._busy or not isinstance(row, _WifiRow):
            return

        net = row.network
        if net.in_use:
            self._confirm_and_next()
            return

        if net.is_secured:
            self._ask_password(net)
        else:
            self._start_connect(net.ssid, None)

    def _ask_password(self, network: WifiNetwork) -> None:
        dialog = Adw.AlertDialog(
            heading=f"Connexion à « {network.ssid} »",
            body="Entrez le mot de passe du réseau Wi-Fi.",
        )

        entry = Gtk.PasswordEntry()
        entry.set_property("placeholder-text", "Mot de passe")
        entry.set_property("show-peek-icon", True)
        entry.set_property("activates-default", True)
        dialog.set_extra_child(entry)

        dialog.add_response("cancel", "Annuler")
        dialog.add_response("connect", "Se connecter")
        dialog.set_response_appearance("connect", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("connect")
        dialog.set_close_response("cancel")

        def on_response(_dlg: Adw.AlertDialog, response: str) -> None:
            if response == "connect":
                password = entry.get_text()
                if password:
                    self._start_connect(network.ssid, password)

        dialog.connect("response", on_response)
        dialog.present(self.get_root())
        entry.grab_focus()

    def _start_connect(self, ssid: str, password: str | None) -> None:
        self._error_label.set_visible(False)
        self._set_busy(True, f"Connexion à « {ssid} »…")

        def worker() -> None:
            ok, err = connect_wifi(ssid, password)
            GLib.idle_add(self._on_connect_finished, ssid, ok, err)

        threading.Thread(target=worker, daemon=True).start()

    def _on_connect_finished(self, ssid: str, ok: bool, err: str) -> bool:
        self._set_busy(False, "Réseaux disponibles")
        if ok:
            self._connected_ssid = ssid
            self._state.network_mode = "wifi"
            self._state.wifi_ssid = ssid
            self._next_btn.set_sensitive(True)
            self.refresh_networks(rescan=False)
        else:
            self._error_label.set_label(err)
            self._error_label.set_visible(True)
        return False

    def _confirm_and_next(self) -> None:
        print(f"[WifiPage] Réseau validé : {self._state.network_mode} ({self._state.wifi_ssid})")
        self._on_next()