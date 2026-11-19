from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gtk

from arrera_blue_lynx.core.paths import get_asset_path


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

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._stack.set_transition_duration(250)
        self.set_content(self._stack)

        self._pages = build_pages(self)
        self._current_index = 0

        for idx, page in enumerate(self._pages):
            self._stack.add_named(page, f"page-{idx}")

        if self._pages:
            self._stack.set_visible_child_name("page-0")

        if fullscreen:
            self.fullscreen()

    def next_page(self) -> None:
        if self._current_index + 1 < len(self._pages):
            self._current_index += 1
            self._stack.set_visible_child_name(f"page-{self._current_index}")
        else:
            print("Fin des pages (temporaire : fermeture de l'app)")
            self.close()

    def previous_page(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._stack.set_visible_child_name(f"page-{self._current_index}")