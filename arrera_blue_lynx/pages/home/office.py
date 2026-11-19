from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

from arrera_blue_lynx.core.paths import get_asset_path
from arrera_blue_lynx.core.state import SetupState
from arrera_blue_lynx.pages.common.nav import create_nav_bar


@dataclass(frozen=True)
class OfficeOption:
    id: str
    label: str
    tag: str
    logo_stem: str
    description: str


OFFICE_OPTIONS: list[OfficeOption] = [
    OfficeOption(
        id="onlyoffice",
        label="OnlyOffice",
        tag="Compatible MS Office",
        logo_stem="onlyoffice",
        description="OnlyOffice — interface moderne et excellente compatibilité avec les fichiers Microsoft Office.",
    ),
    OfficeOption(
        id="libreoffice",
        label="LibreOffice",
        tag="Libre et complet",
        logo_stem="libreoffice",
        description="LibreOffice — suite bureautique libre, complète et utilisable hors-ligne.",
    ),
]


def _find_office_logo(stem: str) -> Path | None:
    for ext in (".svg", ".png", ".webp", ".jpg"):
        try:
            return get_asset_path(f"office/{stem}{ext}")
        except FileNotFoundError:
            continue
    return None


class _OfficeCard(Gtk.Button):
    def __init__(
        self,
        option: OfficeOption,
        on_toggle: Callable[[OfficeOption], None],
    ) -> None:
        super().__init__()
        self.option = option
        self.add_css_class("kernel-card")
        self.set_size_request(240, 235)
        self.connect("clicked", lambda _btn: on_toggle(option))

        overlay = Gtk.Overlay()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(20)
        box.set_margin_bottom(18)
        box.set_margin_start(16)
        box.set_margin_end(16)

        logo_path = _find_office_logo(option.logo_stem)
        texture: Gdk.Texture | None = None
        if logo_path is not None:
            try:
                texture = Gdk.Texture.new_from_filename(str(logo_path))
            except GLib.Error as exc:
                print(f"[HomeOfficePage] Impossible de charger '{logo_path}': {exc}")

        if texture is not None:
            logo = Gtk.Image.new_from_paintable(texture)
            logo.set_pixel_size(112)
            logo.set_halign(Gtk.Align.CENTER)
            box.append(logo)
        else:
            fallback = Gtk.Image.new_from_icon_name("x-office-document-symbolic")
            fallback.set_pixel_size(96)
            fallback.add_css_class("kernel-card-fallback")
            box.append(fallback)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label(label=option.label)
        label.add_css_class("kernel-card-label")
        text_box.append(label)

        tag = Gtk.Label(label=option.tag)
        tag.add_css_class("kernel-card-tag")
        text_box.append(tag)

        box.append(text_box)
        overlay.set_child(box)

        self._check_badge = Gtk.Image.new_from_icon_name("object-select-symbolic")
        self._check_badge.set_pixel_size(18)
        self._check_badge.add_css_class("kernel-card-check")
        self._check_badge.set_halign(Gtk.Align.END)
        self._check_badge.set_valign(Gtk.Align.START)
        self._check_badge.set_margin_top(12)
        self._check_badge.set_margin_end(12)
        self._check_badge.set_visible(False)
        overlay.add_overlay(self._check_badge)

        self.set_child(overlay)

    def set_selected(self, selected: bool) -> None:
        self._check_badge.set_visible(selected)
        if selected:
            self.add_css_class("kernel-card-selected")
        else:
            self.remove_css_class("kernel-card-selected")


class HomeOfficePage(Gtk.Box):
    """Page de choix du logiciel de bureautique pour l'édition Home (optionnel)."""

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
        self._selected: OfficeOption | None = None
        self._cards: dict[str, _OfficeCard] = {}

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
        title = Gtk.Label(label="Logiciel de bureautique")
        title.add_css_class("setup-title")
        title.set_halign(Gtk.Align.CENTER)
        outer.append(title)

        # Zone centrale : 2 cartes + description
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        center.set_vexpand(True)
        center.set_valign(Gtk.Align.CENTER)
        center.set_halign(Gtk.Align.CENTER)

        cards_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=48)
        cards_row.set_halign(Gtk.Align.CENTER)
        cards_row.set_homogeneous(True)

        for option in OFFICE_OPTIONS:
            card = _OfficeCard(option, on_toggle=self._toggle_office)
            self._cards[option.id] = card
            cards_row.append(card)

        center.append(cards_row)

        self._description_label = Gtk.Label()
        self._description_label.add_css_class("setup-subtitle")
        self._description_label.set_halign(Gtk.Align.CENTER)
        self._description_label.set_wrap(True)
        center.append(self._description_label)

        outer.append(center)

        # Pied de page : boutons circulaires ← / →
        footer, self._continue_btn = create_nav_bar(
            on_next=self._submit,
            on_back=self._on_back,
            next_tooltip="Continuer sans logiciel de bureautique",
        )
        outer.append(footer)
        self.append(outer)

        # Restaure un éventuel choix déjà présent dans state (None par défaut)
        initial = next(
            (opt for opt in OFFICE_OPTIONS if opt.id == self._state.office_suite),
            None,
        )
        self._apply_selection(initial)

    def _toggle_office(self, option: OfficeOption) -> None:
        # Recliquer sur la carte déjà sélectionnée la désélectionne
        if self._selected is not None and self._selected.id == option.id:
            self._apply_selection(None)
        else:
            self._apply_selection(option)

    def _apply_selection(self, option: OfficeOption | None) -> None:
        self._selected = option
        self._state.office_suite = option.id if option is not None else None

        for opt_id, card in self._cards.items():
            card.set_selected(option is not None and opt_id == option.id)

        if option is None:
            self._description_label.set_label(
                "Aucun logiciel de bureautique sélectionné — cliquez sur une carte ou continuez sans."
            )
            self._continue_btn.set_tooltip_text("Continuer sans logiciel de bureautique")
        else:
            self._description_label.set_label(option.description)
            self._continue_btn.set_tooltip_text(f"Continuer avec {option.label}")

    def _submit(self) -> None:
        self._state.office_suite = self._selected.id if self._selected is not None else None
        print(f"[HomeOfficePage] Logiciel de bureautique : {self._state.office_suite}")
        self._on_next()