from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from arrera_blue_lynx.core.state import CHILD_PROFILES, SetupState, UserAccount
from arrera_blue_lynx.pages.common.account_form import AccountForm


class EducationChildAccountPage(Gtk.Box):
    """Page de création de comptes enfants/ados (optionnelle, multi-comptes) pour Education."""

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

        # Titre + sous-titre + badge compteur d'enfants ajoutés
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        header.set_halign(Gtk.Align.CENTER)

        title = Gtk.Label(label="Création du compte enfant")
        title.add_css_class("setup-title")
        header.append(title)

        subtitle = Gtk.Label(
            label="Optionnel — vous pouvez créer un ou plusieurs comptes enfants, ou continuer directement"
        )
        subtitle.add_css_class("setup-subtitle")
        header.append(subtitle)

        self._added_badge = Gtk.Label()
        self._added_badge.add_css_class("child-added-badge")
        self._added_badge.set_visible(False)
        header.append(self._added_badge)

        outer.append(header)

        # Formulaire centré avec la liste déroulante Catégorie d'âge au milieu
        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        center_box.set_vexpand(True)
        center_box.set_valign(Gtk.Align.CENTER)

        self._form = AccountForm(check_system_users=check_system_users)

        age_labels = ["Catégorie d'âge", *(label for _code, label in CHILD_PROFILES)]
        self._age_dropdown = Gtk.DropDown(model=Gtk.StringList.new(age_labels))
        self._age_dropdown.add_css_class("account-dropdown")
        self._age_dropdown.connect("notify::selected", lambda *_a: self._form.clear_error())
        self._form.set_middle_widget(self._age_dropdown)

        center_box.append(self._form)
        outer.append(center_box)

        # Pied de page : Retour à gauche (optionnel), "Créer un autre compte" + "Continuer" à droite
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        if self._on_back is not None:
            back_btn = Gtk.Button(label="Retour")
            back_btn.add_css_class("account-secondary-btn")
            back_btn.connect("clicked", lambda _btn: self._on_back())
            footer.append(back_btn)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        footer.append(spacer)

        add_another_btn = Gtk.Button(label="Créer un autre compte")
        add_another_btn.add_css_class("suggested-action")
        add_another_btn.add_css_class("account-primary-btn")
        add_another_btn.connect("clicked", lambda _btn: self._add_another())
        footer.append(add_another_btn)

        continue_btn = Gtk.Button(label="Continuer")
        continue_btn.add_css_class("suggested-action")
        continue_btn.add_css_class("account-primary-btn")
        continue_btn.connect("clicked", lambda _btn: self._continue())
        footer.append(continue_btn)

        outer.append(footer)
        self.append(outer)

    def on_enter(self) -> None:
        self._update_added_badge()

    def _validate_current_child(self) -> UserAccount | None:
        selected_idx = self._age_dropdown.get_selected()
        if selected_idx == 0:
            self._form.show_error("Veuillez sélectionner une catégorie d'âge.")
            return None

        profile_code = CHILD_PROFILES[selected_idx - 1][0]
        existing_usernames = {u.username for u in self._state.users}

        return self._form.validate_and_build(
            is_admin=False,
            profile=profile_code,
            existing_usernames=existing_usernames,
        )

    def _update_added_badge(self) -> None:
        children = [u for u in self._state.users if u.profile != "adult"]
        if not children:
            self._added_badge.set_visible(False)
            return

        names = ", ".join(u.first_name for u in children)
        count = len(children)
        label = (
            f"1 compte enfant ajouté : {names}"
            if count == 1
            else f"{count} comptes enfants ajoutés : {names}"
        )
        self._added_badge.set_label(label)
        self._added_badge.set_visible(True)

    def _add_another(self) -> None:
        account = self._validate_current_child()
        if account is None:
            return

        self._state.users.append(account)
        print(
            f"[EducationChildAccountPage] Enfant ajouté : {account.username} "
            f"(profil={account.profile})"
        )
        self._update_added_badge()
        self._form.reset()
        self._age_dropdown.set_selected(0)

    def _continue(self) -> None:
        # Si le formulaire est totalement vide (et aucune catégorie choisie), on continue sans ajouter d'enfant
        if self._form.is_empty() and self._age_dropdown.get_selected() == 0:
            self._on_next()
            return

        account = self._validate_current_child()
        if account is None:
            return

        self._state.users.append(account)
        print(
            f"[EducationChildAccountPage] Enfant ajouté : {account.username} "
            f"(profil={account.profile})"
        )
        self._update_added_badge()
        self._on_next()