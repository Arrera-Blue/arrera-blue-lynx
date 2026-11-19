from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


def create_nav_bar(
    on_next: Callable[[], None],
    on_back: Callable[[], None] | None = None,
    *,
    next_tooltip: str = "Continuer",
    extra_widget: Gtk.Widget | None = None,
) -> tuple[Gtk.Box, Gtk.Button]:
    """Crée la barre de navigation circulaire cohérente (← / [optionnel] / →)."""
    nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
    nav_box.set_halign(Gtk.Align.CENTER)
    nav_box.set_margin_top(8)

    if on_back is not None:
        back_btn = Gtk.Button()
        back_btn.add_css_class("circular")
        back_btn.add_css_class("setup-nav-back-btn")
        back_btn.set_tooltip_text("Retour")
        back_btn.connect("clicked", lambda _btn: on_back())

        back_icon = Gtk.Image.new_from_icon_name("go-previous-symbolic")
        back_icon.set_pixel_size(20)
        back_btn.set_child(back_icon)
        nav_box.append(back_btn)

    if extra_widget is not None:
        nav_box.append(extra_widget)

    next_btn = Gtk.Button()
    next_btn.add_css_class("circular")
    next_btn.add_css_class("suggested-action")
    next_btn.add_css_class("setup-nav-next-btn")
    next_btn.set_tooltip_text(next_tooltip)
    next_btn.connect("clicked", lambda _btn: on_next())

    next_icon = Gtk.Image.new_from_icon_name("go-next-symbolic")
    next_icon.set_pixel_size(22)
    next_btn.set_child(next_icon)
    nav_box.append(next_btn)

    return nav_box, next_btn
