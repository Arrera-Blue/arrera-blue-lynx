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
class KernelOption:
    id: str
    label: str
    tag: str
    logo_stem: str
    description: str
    is_default: bool = False

KERNEL_OPTIONS: list[KernelOption] = [
    KernelOption(
        id="fedora",
        label="Noyau Fedora",
        tag="Recommandé",
        logo_stem="fedora",
        description="Noyau officiel Fedora — équilibré, récent et recommandé par défaut.",
        is_default=True,
    ),
    KernelOption(
        id="lts",
        label="Noyau LTS",
        tag="Long terme",
        logo_stem="lts",
        description="Noyau à support long terme — stabilité maximale et mises à jour conservatrices.",
    ),
    KernelOption(
        id="cachyos",
        label="Noyau CachyOS",
        tag="Performances",
        logo_stem="cachyos",
        description="Noyau optimisé pour les performances et la faible latence (gaming / usage avancé).",
    ),
]


def _find_kernel_logo(stem: str) -> Path | None:
    for ext in (".svg", ".png", ".webp", ".jpg"):
        try:
            return get_asset_path(f"kernels/{stem}{ext}")
        except FileNotFoundError:
            continue
    return None


class _KernelCard(Gtk.Button):
    def __init__(
        self,
        option: KernelOption,
        on_select: Callable[[KernelOption], None],
    ) -> None:
        super().__init__()
        self.option = option
        self.add_css_class("kernel-card")
        self.set_size_request(230, 235)
        self.connect("clicked", lambda _btn: on_select(option))

        overlay = Gtk.Overlay()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(20)
        box.set_margin_bottom(18)
        box.set_margin_start(16)
        box.set_margin_end(16)

        logo_path = _find_kernel_logo(option.logo_stem)
        texture: Gdk.Texture | None = None
        if logo_path is not None:
            try:
                texture = Gdk.Texture.new_from_filename(str(logo_path))
            except GLib.Error as exc:
                print(f"[HomeKernelPage] Impossible de charger '{logo_path}': {exc}")

        if texture is not None:
            logo = Gtk.Image.new_from_paintable(texture)
            logo.set_pixel_size(112)
            logo.set_halign(Gtk.Align.CENTER)
            box.append(logo)
        else:
            fallback = Gtk.Image.new_from_icon_name("computer-symbolic")
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

        # Petite coche blanche en haut à droite lorsque la carte est sélectionnée
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


class HomeKernelPage(Gtk.Box):
    """Page de choix du noyau système pour l'édition Home (Fedora par défaut)."""

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
        self._selected: KernelOption = KERNEL_OPTIONS[0]
        self._cards: dict[str, _KernelCard] = {}

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
        title = Gtk.Label(label="Noyau du système")
        title.add_css_class("setup-title")
        title.set_halign(Gtk.Align.CENTER)
        outer.append(title)

        # Zone centrale : 3 cartes + description du noyau sélectionné
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        center.set_vexpand(True)
        center.set_valign(Gtk.Align.CENTER)
        center.set_halign(Gtk.Align.CENTER)

        cards_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=36)
        cards_row.set_halign(Gtk.Align.CENTER)
        cards_row.set_homogeneous(True)

        for option in KERNEL_OPTIONS:
            card = _KernelCard(option, on_select=self._select_kernel)
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
            next_tooltip="Continuer avec le noyau par défaut",
        )
        outer.append(footer)
        self.append(outer)

        # Sélectionne le noyau déjà présent dans state (Fedora par défaut)
        initial = next(
            (opt for opt in KERNEL_OPTIONS if opt.id == self._state.kernel),
            KERNEL_OPTIONS[0],
        )
        self._select_kernel(initial)

    def _select_kernel(self, option: KernelOption) -> None:
        self._selected = option
        self._state.kernel = option.id

        for opt_id, card in self._cards.items():
            card.set_selected(opt_id == option.id)

        self._description_label.set_label(option.description)

        if option.is_default:
            self._continue_btn.set_tooltip_text("Continuer avec le noyau par défaut")
        else:
            self._continue_btn.set_tooltip_text(f"Continuer avec le {option.label.lower()}")

    def _submit(self) -> None:
        self._state.kernel = self._selected.id
        print(f"[HomeKernelPage] Noyau sélectionné : {self._state.kernel}")
        self._on_next()