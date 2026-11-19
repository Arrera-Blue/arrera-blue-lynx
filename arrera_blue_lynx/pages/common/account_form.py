from collections.abc import Callable
from pathlib import Path
import re
import unicodedata

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

from arrera_blue_lynx.core.paths import DEV_ASSETS_DIR, SYS_ASSETS_DIR
from arrera_blue_lynx.core.state import UserAccount

USERNAME_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
RESERVED_USERNAMES = {"root", "daemon", "bin", "sys", "nobody", "arrera-setup"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


def _slugify_username(text: str) -> str:
    """Transforme un prénom/nom en identifiant Linux valide (minuscules ASCII)."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    cleaned = re.sub(r"[^a-z0-9_-]+", "", ascii_text)
    cleaned = re.sub(r"^[^a-z_]+", "", cleaned)
    return cleaned[:32]


def list_available_avatars() -> list[Path]:
    """Liste les avatars dispo dans assets/avatars/ puis /usr/share/pixmaps/faces/."""
    dirs = [
        DEV_ASSETS_DIR / "avatars",
        SYS_ASSETS_DIR / "avatars",
        Path("/usr/share/pixmaps/faces"),
    ]
    found: list[Path] = []
    seen_names: set[str] = set()

    for directory in dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
                if path.name not in seen_names:
                    seen_names.add(path.name)
                    found.append(path)
    return found


class AccountForm(Gtk.Box):
    """Formulaire de création de compte réutilisable (Home, Education Adulte & Enfant)."""

    def __init__(self, on_change: Callable[[], None] | None = None) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=48)
        self._on_change = on_change
        self._avatar_path: str | None = None
        self._username_manually_edited = False
        self._updating_username = False

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        # === Colonne gauche : Avatar + bouton Changer ===
        avatar_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        avatar_col.set_valign(Gtk.Align.START)
        avatar_col.set_halign(Gtk.Align.CENTER)
        avatar_col.set_margin_top(4)

        self._avatar = Adw.Avatar(size=128, show_initials=True, text="")
        avatar_col.append(self._avatar)

        self._avatar_popover = self._build_avatar_popover()
        change_btn = Gtk.MenuButton(label="Changer")
        change_btn.set_property("always-show-arrow", False)
        change_btn.set_popover(self._avatar_popover)
        change_btn.add_css_class("suggested-action")
        change_btn.add_css_class("account-avatar-btn")
        change_btn.set_halign(Gtk.Align.CENTER)
        avatar_col.append(change_btn)

        self.append(avatar_col)

        # === Colonne droite : Champs du formulaire ===
        self._fields_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self._fields_col.set_size_request(440, -1)

        # Nom + Prénom côte à côte
        name_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        name_row.set_homogeneous(True)

        self._last_name_entry = Gtk.Entry()
        self._last_name_entry.set_placeholder_text("Nom")
        self._last_name_entry.add_css_class("account-entry")
        self._last_name_entry.connect("changed", self._on_name_changed)
        name_row.append(self._last_name_entry)

        self._first_name_entry = Gtk.Entry()
        self._first_name_entry.set_placeholder_text("Prénom")
        self._first_name_entry.add_css_class("account-entry")
        self._first_name_entry.connect("changed", self._on_name_changed)
        name_row.append(self._first_name_entry)

        self._fields_col.append(name_row)

        # Identifiant du compte
        self._username_entry = Gtk.Entry()
        self._username_entry.set_placeholder_text("Identifiant du compte")
        self._username_entry.add_css_class("account-entry")
        self._username_entry.connect("changed", self._on_username_changed)
        self._fields_col.append(self._username_entry)

        # Slot optionnel au milieu (ex: Catégorie d'âge sur Education Enfant)
        self._middle_slot = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._middle_slot.set_visible(False)
        self._fields_col.append(self._middle_slot)

        # Mot de passe + confirmation
        self._password_entry = Gtk.PasswordEntry()
        self._password_entry.set_property("placeholder-text", "Mot de passe")
        self._password_entry.set_property("show-peek-icon", True)
        self._password_entry.add_css_class("account-entry")
        self._password_entry.set_margin_top(6)
        self._password_entry.connect("changed", self._notify_change)
        self._fields_col.append(self._password_entry)

        self._password_confirm_entry = Gtk.PasswordEntry()
        self._password_confirm_entry.set_property("placeholder-text", "Confirmer le mot de passe")
        self._password_confirm_entry.set_property("show-peek-icon", True)
        self._password_confirm_entry.add_css_class("account-entry")
        self._password_confirm_entry.connect("changed", self._notify_change)
        self._fields_col.append(self._password_confirm_entry)

        # Slot optionnel en bas (ex: case Admin + section Root sur Home)
        self._extra_slot = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._extra_slot.set_visible(False)
        self._fields_col.append(self._extra_slot)

        # Message d'erreur
        self._error_label = Gtk.Label()
        self._error_label.add_css_class("wifi-error-label")
        self._error_label.set_xalign(0.0)
        self._error_label.set_wrap(True)
        self._error_label.set_visible(False)
        self._fields_col.append(self._error_label)

        self.append(self._fields_col)

    def _build_avatar_popover(self) -> Gtk.Popover:
        popover = Gtk.Popover()
        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        container.set_margin_top(12)
        container.set_margin_bottom(12)
        container.set_margin_start(12)
        container.set_margin_end(12)

        title = Gtk.Label(label="Choisir un avatar")
        title.add_css_class("heading")
        container.append(title)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_width(290)
        scrolled.set_min_content_height(220)
        scrolled.set_max_content_height(280)

        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_max_children_per_line(4)
        flow.set_row_spacing(8)
        flow.set_column_spacing(8)
        flow.set_homogeneous(True)

        avatars = list_available_avatars()
        for path in avatars:
            try:
                texture = Gdk.Texture.new_from_filename(str(path))
            except GLib.Error:
                continue

            btn = Gtk.Button()
            btn.add_css_class("flat")
            btn.add_css_class("circular")
            btn.set_tooltip_text(path.stem)

            preview = Adw.Avatar(size=56, show_initials=False)
            preview.set_custom_image(texture)
            btn.set_child(preview)
            btn.connect("clicked", self._on_avatar_chosen, path, texture)
            flow.append(btn)

        if not avatars:
            empty = Gtk.Label(label="Aucune image d'avatar trouvée")
            empty.add_css_class("setup-subtitle")
            flow.append(empty)

        scrolled.set_child(flow)
        container.append(scrolled)

        reset_btn = Gtk.Button(label="Utiliser les initiales par défaut")
        reset_btn.add_css_class("flat")
        reset_btn.connect("clicked", self._on_avatar_reset)
        container.append(reset_btn)

        popover.set_child(container)
        return popover

    def _on_avatar_chosen(self, _btn: Gtk.Button, path: Path, texture: Gdk.Texture) -> None:
        self._avatar_path = str(path)
        self._avatar.set_custom_image(texture)
        self._avatar_popover.popdown()
        self._notify_change()

    def _on_avatar_reset(self, _btn: Gtk.Button) -> None:
        self._avatar_path = None
        self._avatar.set_custom_image(None)
        self._avatar_popover.popdown()
        self._notify_change()

    def _on_name_changed(self, _entry: Gtk.Entry) -> None:
        first = self._first_name_entry.get_text().strip()
        last = self._last_name_entry.get_text().strip()
        full_name = f"{first} {last}".strip()
        self._avatar.set_text(full_name)

        if not self._username_manually_edited:
            suggested = _slugify_username(first or last)
            self._updating_username = True
            self._username_entry.set_text(suggested)
            self._updating_username = False

        self._notify_change()

    def _on_username_changed(self, _entry: Gtk.Entry) -> None:
        if not self._updating_username:
            self._username_manually_edited = bool(self._username_entry.get_text().strip())
        self._notify_change()

    def _notify_change(self, *_args: object) -> None:
        self.clear_error()
        if self._on_change is not None:
            self._on_change()

    def set_middle_widget(self, widget: Gtk.Widget) -> None:
        while (child := self._middle_slot.get_first_child()) is not None:
            self._middle_slot.remove(child)
        self._middle_slot.append(widget)
        self._middle_slot.set_visible(True)

    def append_extra_widget(self, widget: Gtk.Widget) -> None:
        self._extra_slot.append(widget)
        self._extra_slot.set_visible(True)

    def show_error(self, message: str) -> None:
        self._error_label.set_label(message)
        self._error_label.set_visible(True)

    def clear_error(self) -> None:
        self._error_label.set_visible(False)

    def is_empty(self) -> bool:
        """Retourne True si aucun champ texte n'a été rempli."""
        return not any(
            [
                self._last_name_entry.get_text().strip(),
                self._first_name_entry.get_text().strip(),
                self._username_entry.get_text().strip(),
                self._password_entry.get_text(),
                self._password_confirm_entry.get_text(),
            ]
        )

    def validate_and_build(
        self,
        *,
        is_admin: bool,
        profile: str,
        existing_usernames: set[str] | None = None,
    ) -> UserAccount | None:
        """Valide les champs et retourne un UserAccount, ou None en affichant l'erreur."""
        last_name = self._last_name_entry.get_text().strip()
        first_name = self._first_name_entry.get_text().strip()
        username = self._username_entry.get_text().strip()
        password = self._password_entry.get_text()
        confirm = self._password_confirm_entry.get_text()

        if not last_name or not first_name:
            self.show_error("Veuillez renseigner le nom et le prénom.")
            return None

        if not username or not USERNAME_RE.match(username):
            self.show_error(
                "Identifiant invalide : utilisez uniquement des minuscules, chiffres, '-' ou '_' "
                "(sans espaces ni accents)."
            )
            return None

        if username in RESERVED_USERNAMES:
            self.show_error(f"L'identifiant « {username} » est réservé par le système.")
            return None

        if existing_usernames and username in existing_usernames:
            self.show_error(f"L'identifiant « {username} » est déjà utilisé par un autre compte.")
            return None

        if len(password) < 4:
            self.show_error("Le mot de passe doit contenir au moins 4 caractères.")
            return None

        if password != confirm:
            self.show_error("Les deux mots de passe ne correspondent pas.")
            return None

        self.clear_error()
        return UserAccount(
            last_name=last_name,
            first_name=first_name,
            username=username,
            password=password,
            avatar_path=self._avatar_path,
            is_admin=is_admin,
            profile=profile,
        )

    def reset(self) -> None:
        """Réinitialise tous les champs pour saisir un autre compte."""
        self._username_manually_edited = False
        self._updating_username = True
        self._last_name_entry.set_text("")
        self._first_name_entry.set_text("")
        self._username_entry.set_text("")
        self._updating_username = False
        self._password_entry.set_text("")
        self._password_confirm_entry.set_text("")
        self._avatar_path = None
        self._avatar.set_custom_image(None)
        self._avatar.set_text("")
        self.clear_error()
        self._last_name_entry.grab_focus()