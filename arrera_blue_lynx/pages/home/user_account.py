from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from arrera_blue_lynx.core.state import SetupState
from arrera_blue_lynx.pages.common.account_form import AccountForm


class HomeUserAccountPage(Gtk.Box):
    """Page de création de l'utilisateur pour l'édition Home (+ Root)."""

    def __init__(
        self,
        state: SetupState,
        on_next: Callable[[], None],
        on_back: Callable[[], None] | None = None,
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

        # Titre en haut
        title = Gtk.Label(label="Création de l'utilisateur")
        title.add_css_class("setup-title")
        title.set_halign(Gtk.Align.CENTER)
        outer.append(title)

        # Zone centrale (scrollable si petit écran)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        self._form = AccountForm()

        # Case Administrateur (cochée par défaut, toujours modifiable)
        self._admin_check = Gtk.CheckButton(label="Faire de ce compte un compte administrateur")
        self._admin_check.set_active(True)
        self._admin_check.set_margin_top(4)
        self._admin_check.connect("toggled", self._on_admin_toggled)
        self._form.append_extra_widget(self._admin_check)

        # Section Root (optionnelle si admin coché, obligatoire sinon)
        self._root_label = Gtk.Label(label="Compte super administrateur (Root) — optionnel")
        self._root_label.set_xalign(0.0)
        self._root_label.add_css_class("account-section-label")
        self._form.append_extra_widget(self._root_label)

        self._root_password_entry = Gtk.PasswordEntry()
        self._root_password_entry.set_property("placeholder-text", "Mot de passe Root")
        self._root_password_entry.set_property("show-peek-icon", True)
        self._root_password_entry.add_css_class("account-entry")
        self._root_password_entry.connect("changed", lambda _e: self._form.clear_error())
        self._form.append_extra_widget(self._root_password_entry)

        self._root_confirm_entry = Gtk.PasswordEntry()
        self._root_confirm_entry.set_property("placeholder-text", "Confirmer le mot de passe Root")
        self._root_confirm_entry.set_property("show-peek-icon", True)
        self._root_confirm_entry.add_css_class("account-entry")
        self._root_confirm_entry.connect("changed", lambda _e: self._form.clear_error())
        self._form.append_extra_widget(self._root_confirm_entry)

        scrolled.set_child(self._form)
        outer.append(scrolled)

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

    def _on_admin_toggled(self, check: Gtk.CheckButton) -> None:
        self._form.clear_error()
        if check.get_active():
            self._root_label.set_label("Compte super administrateur (Root) — optionnel")
        else:
            self._root_label.set_label("Compte super administrateur (Root) — obligatoire")

    def _submit(self) -> None:
        is_admin = self._admin_check.get_active()
        account = self._form.validate_and_build(is_admin=is_admin, profile="standard")
        if account is None:
            return

        root_pwd = self._root_password_entry.get_text()
        root_confirm = self._root_confirm_entry.get_text()

        # Root obligatoire si l'utilisateur n'est pas admin ; optionnel sinon mais validé si rempli
        if not is_admin and not root_pwd:
            self._form.show_error(
                "Le mot de passe du compte Root est obligatoire si l'utilisateur n'est pas administrateur."
            )
            return

        if root_pwd or root_confirm:
            if len(root_pwd) < 4:
                self._form.show_error("Le mot de passe Root doit contenir au moins 4 caractères.")
                return
            if root_pwd != root_confirm:
                self._form.show_error("Les deux mots de passe Root ne correspondent pas.")
                return
            self._state.root_password = root_pwd
        else:
            self._state.root_password = None

        self._state.users = [account]
        print(
            f"[HomeUserAccountPage] Utilisateur prêt : {account.username} "
            f"(admin={account.is_admin}, root={'oui' if self._state.root_password else 'non'})"
        )
        self._on_next()