from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from arrera_blue_lynx.core.paths import get_asset_path


class WelcomePage(Gtk.Overlay):
    """Écran de bienvenue partagé entre Home (bleu) et Education (vert)."""

    def __init__(
        self,
        logo_filename: str,
        on_next: Callable[[], None],
        wallpaper_filename: str = "wallpaper.jpg",
        title_text: str = "Bienvenue sur Arrera Blue OS",
    ) -> None:
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)

        # 1. Fond d'écran plein écran (recadré proprement sans déformation)
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

        # Titre en haut
        title = Gtk.Label(label=title_text)
        title.add_css_class("welcome-title")
        title.set_halign(Gtk.Align.CENTER)
        title.set_valign(Gtk.Align.START)
        content.append(title)

        # Logo au centre
        logo = Gtk.Picture.new_for_filename(str(get_asset_path(logo_filename)))
        logo.set_content_fit(Gtk.ContentFit.CONTAIN)
        logo.set_can_shrink(True)
        logo.set_size_request(240, 240)
        logo.set_halign(Gtk.Align.CENTER)
        logo.set_valign(Gtk.Align.CENTER)
        logo.set_vexpand(True)
        content.append(logo)

        # Bouton circulaire blanc avec flèche en bas
        next_btn = Gtk.Button()
        next_btn.add_css_class("welcome-next-btn")
        next_btn.set_halign(Gtk.Align.CENTER)
        next_btn.set_valign(Gtk.Align.END)
        next_btn.set_tooltip_text("Commencer")
        next_btn.connect("clicked", lambda _btn: on_next())

        arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
        arrow.set_pixel_size(28)
        next_btn.set_child(arrow)
        content.append(next_btn)

        self.add_overlay(content)