from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

from arrera_blue_lynx.core.paths import get_asset_path
from arrera_blue_lynx.core.state import SetupState


def load_css() -> None:
    provider = Gtk.CssProvider()
    provider.load_from_path(str(get_asset_path("style.css")))
    display = Gdk.Display.get_default()
    if display is not None:
        Gtk.StyleContext.add_provider_for_display(
            display,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


class LynxApp(Adw.Application):
    """Application principale partagée par les éditions Home et Education."""

    def __init__(
        self,
        app_id: str,
        build_pages: Callable[["LynxWindow"], list[Gtk.Widget]],
        fullscreen: bool = True,
    ) -> None:
        super().__init__(application_id=app_id)
        self._build_pages = build_pages
        self._fullscreen = fullscreen

    def do_activate(self) -> None:
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        load_css()
        win = LynxWindow(self, self._build_pages, fullscreen=self._fullscreen)
        win.present()


class LynxWindow(Adw.ApplicationWindow):
    def __init__(
        self,
        app: Adw.Application,
        build_pages: Callable[["LynxWindow"], list[Gtk.Widget]],
        fullscreen: bool = True,
    ) -> None:
        super().__init__(application=app, title="Arrera Blue Lynx")
        self.set_default_size(1280, 720)
        self.state = SetupState()

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._stack.set_transition_duration(250)
        self.set_content(self._stack)

        self._pages = build_pages(self)
        self._current_index = 0

        for idx, page in enumerate(self._pages):
            self._stack.add_named(page, f"page-{idx}")

        if self._pages:
            self._show_page(0)

        if fullscreen:
            # Différer l'appel fullscreen après le commit Wayland initial pour éviter
            # le crash Cage / wlroots : Assertion `surface->initialized' failed.
            self.connect("map", lambda _w: GLib.timeout_add(150, self._deferred_fullscreen))

    def _deferred_fullscreen(self) -> bool:
        if self.get_mapped():
            self.fullscreen()
        return False

    def _should_skip(self, page: Gtk.Widget) -> bool:
        skip_fn = getattr(page, "should_skip", None)
        return bool(skip_fn()) if callable(skip_fn) else False

    def _show_page(self, index: int) -> None:
        self._current_index = index
        self._stack.set_visible_child_name(f"page-{index}")
        on_enter = getattr(self._pages[index], "on_enter", None)
        if callable(on_enter):
            on_enter()

    def next_page(self) -> None:
        idx = self._current_index + 1
        while idx < len(self._pages) and self._should_skip(self._pages[idx]):
            idx += 1

        if idx < len(self._pages):
            self._show_page(idx)
        else:
            print(f"Fin des pages — état collecté : {self.state}")
            self.close()

    def previous_page(self) -> None:
        idx = self._current_index - 1
        while idx >= 0 and self._should_skip(self._pages[idx]):
            idx -= 1

        if idx >= 0:
            self._show_page(idx)