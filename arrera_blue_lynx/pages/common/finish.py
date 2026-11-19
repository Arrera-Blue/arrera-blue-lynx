from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from arrera_blue_lynx.core.paths import get_asset_path


class FinishPage(Gtk.Overlay):
    """Écran final commun (fond d'écran plage + bouton pilule blanc Commencer →)."""

    def __init__(
        self,
        on_finish: Callable[[], None],
        wallpaper_filename: str = "wallpaper.jpg",
        title_text: str = "Arrera Blue est prêt",
    ) -> None:
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)

        # 1. Fond d'écran plein écran
        wallpaper = Gtk.Picture.new_for_filename(str(get_asset_path(wallpaper_filename)))
        wallpaper.set_content_fit(Gtk.ContentFit.COVER)
        wallpaper.set_can_shrink(True)
        wallpaper.set_hexpand(True)
        wallpaper.set_vexpand(True)
        self.set_child(wallpaper)

        # 2. Contenu par-dessus le fond d'écran
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_hexpand(True)
        content.set_vexpand(True)
        content.set_margin_top(48)
        content.set_margin_bottom(56)
        content.set_margin_start(32)
        content.set_margin_end(32)

        # Titre centré au milieu de l'écran
        title = Gtk.Label(label=title_text)
        title.add_css_class("welcome-title")
        title.set_halign(Gtk.Align.CENTER)
        title.set_valign(Gtk.Align.CENTER)
        title.set_vexpand(True)
        content.append(title)

        # Bouton pilule blanc "Commencer →" en bas
        start_btn = Gtk.Button()
        start_btn.add_css_class("finish-start-btn")
        start_btn.set_halign(Gtk.Align.CENTER)
        start_btn.set_valign(Gtk.Align.END)
        start_btn.connect("clicked", lambda _btn: on_finish())

        btn_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_content.set_halign(Gtk.Align.CENTER)
        btn_content.set_valign(Gtk.Align.CENTER)

        btn_label = Gtk.Label(label="Commencer")
        btn_label.add_css_class("finish-start-label")
        btn_content.append(btn_label)

        arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
        arrow.set_pixel_size(24)
        btn_content.append(arrow)

        start_btn.set_child(btn_content)
        content.append(start_btn)

        self.add_overlay(content)