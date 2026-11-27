from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from arrera_blue_lynx.core.state import SetupState
from arrera_blue_lynx.pages.common.account_form import AccountForm


class EducationAdultAccountPage(Gtk.Box):
    """Page de création du compte adulte (obligatoire, administrateur) pour Education."""

    def __init__(
        self,
        state: SetupState,
        on_next: Callable[[], None],
        on_back: Callable[[], None] | None = None,
        *,
        check_system_users: bool = True,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._state = state
        self._on_next = on_next
        self._on_back = on_back

        self.add_css_class("setup-white-page")
        self.set_hexpand(True)
        self.set_vexpand(True)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        outer.set_hexpand(True)
        outer.set_vexpand(True)
        outer.set_margin_top(36)
        outer.set_margin_bottom(32)
        outer.set_margin_start(48)
        outer.set_margin_end(48)

        # Titre + sous-titre
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        header.set_halign(Gtk.Align.CENTER)

        title = Gtk.Label(label="Création du compte adulte")
        title.add_css_class("setup-title")
        header.append(title)

        subtitle = Gtk.Label(label="Compte parent ou enseignant (administrateur, obligatoire)")
        subtitle.add_css_class("setup-subtitle")
        header.append(subtitle)
        outer.append(header)

        # Formulaire centré
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        center_box.set_vexpand(True)
        center_box.set_valign(Gtk.Align.CENTER)

        self._form = AccountForm(check_system_users=check_system_users)
        center_box.append(self._form)
        outer.append(center_box)

        # Pied de page : bouton Continuer en bas à droite
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        if self._on_back is not None:
            back_btn = Gtk.Button(label="Retour")
            back_btn.add_css_class("account-secondary-btn")
            back_btn.connect("clicked", lambda _btn: self._on_back())
            footer.append(back_btn)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        footer.append(spacer)

        continue_btn = Gtk.Button(label="Continuer")
        continue_btn.add_css_class("suggested-action")
        continue_btn.add_css_class("account-primary-btn")
        continue_btn.connect("clicked", lambda _btn: self._submit())
        footer.append(continue_btn)

        outer.append(footer)
        self.append(outer)

    def _submit(self) -> None:
        # Garde les éventuels enfants déjà ajoutés si l'utilisateur revient en arrière
        other_usernames = {u.username for u in self._state.users if u.profile != "adult"}
        account = self._form.validate_and_build(
            is_admin=True,
            profile="adult",
            existing_usernames=other_usernames,
        )
        if account is None:
            return

        # Remplace le compte adulte s'il existait déjà, en le gardant en premier
        children = [u for u in self._state.users if u.profile != "adult"]
        self._state.users = [account, *children]
        print(f"[EducationAdultAccountPage] Compte adulte prêt : {account.username} (admin=True)")
        self._on_next()