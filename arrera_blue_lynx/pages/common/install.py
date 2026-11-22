from collections.abc import Callable
from dataclasses import dataclass

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

from arrera_blue_lynx.core.installer import run_education_install, run_home_install
from arrera_blue_lynx.core.paths import get_asset_path
from arrera_blue_lynx.core.state import SetupState


@dataclass(frozen=True)
class _SlideData:
    title: str
    body: str
    icon_name: str | None = None
    logo_filename: str | None = None


def _build_slides(edition: str, logo_filename: str) -> list[_SlideData]:
    if edition == "education":
        return [
            _SlideData(
                title="Bienvenue dans Arrera Blue Education",
                body="Un environnement pensé pour apprendre sereinement, à la maison comme en classe.",
                logo_filename=logo_filename,
            ),
            _SlideData(
                title="Des profils adaptés à chaque âge",
                body="Des espaces dédiés pour les enfants et adolescents, encadrés par le compte adulte.",
                icon_name="system-users-symbolic",
            ),
            _SlideData(
                title="Prêt dans quelques instants",
                body="Arrera Blue configure automatiquement vos préférences et vos outils éducatifs.",
                icon_name="emblem-system-symbolic",
            ),
        ]

    return [
        _SlideData(
            title="Bienvenue dans Arrera Blue Home",
            body="Un système rapide, simple et pensé pour le quotidien.",
            logo_filename=logo_filename,
        ),
        _SlideData(
            title="Configuré selon vos choix",
            body="Votre langue, votre noyau et vos logiciels favoris sont en cours de mise en place.",
            icon_name="preferences-system-symbolic",
        ),
        _SlideData(
            title="Prêt dans quelques instants",
            body="Nous finalisons l'installation pour que tout soit prêt dès le premier démarrage.",
            icon_name="emblem-ok-symbolic",
        ),
    ]


class InstallPage(Gtk.Box):
    """Page commune de chargement / installation (graphique + mode démo visuel)."""

    def __init__(
        self,
        state: SetupState,
        edition: str,
        logo_filename: str,
        on_next: Callable[[], None],
        *,
        demo_mode: bool = True,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._state = state
        self._edition = edition
        self._on_next = on_next
        self._demo_mode = demo_mode

        self._slide_timer_id: int | None = None
        self._demo_timer_id: int | None = None
        self._demo_percent: int = 0
        self._slide_widgets: list[Gtk.Widget] = []
        self._current_slide: int = 0

        self.add_css_class("setup-white-page")
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.connect("unrealize", lambda _w: self._stop_timers())

        clamp = Adw.Clamp()
        clamp.set_maximum_size(720)
        clamp.set_tightening_threshold(600)
        clamp.set_hexpand(True)
        clamp.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        content.set_valign(Gtk.Align.CENTER)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(32)
        content.set_margin_end(32)

        # === Grand cadre arrondi central (carrousel de présentation) ===
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.add_css_class("install-showcase-card")
        card.set_size_request(-1, 360)

        self._carousel = Adw.Carousel()
        self._carousel.set_hexpand(True)
        self._carousel.set_vexpand(True)
        self._carousel.set_interactive(True)
        self._carousel.connect("page-changed", self._on_carousel_page_changed)

        for slide_data in _build_slides(edition, logo_filename):
            slide = self._create_slide_widget(slide_data)
            self._slide_widgets.append(slide)
            self._carousel.append(slide)

        card.append(self._carousel)

        dots = Adw.CarouselIndicatorDots()
        dots.set_carousel(self._carousel)
        dots.set_margin_bottom(14)
        card.append(dots)

        content.append(card)

        # === Statut + barre de progression en dessous ===
        progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        progress_box.set_margin_top(8)

        self._status_label = Gtk.Label(label="Préparation de l'installation — 0 %")
        self._status_label.add_css_class("install-status-label")
        self._status_label.set_halign(Gtk.Align.CENTER)
        progress_box.append(self._status_label)

        self._progress_bar = Gtk.ProgressBar()
        self._progress_bar.add_css_class("install-progress")
        self._progress_bar.set_fraction(0.0)
        progress_box.append(self._progress_bar)

        content.append(progress_box)

        clamp.set_child(content)
        self.append(clamp)

    def _create_slide_widget(self, data: _SlideData) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.set_margin_top(28)
        box.set_margin_bottom(12)
        box.set_margin_start(48)
        box.set_margin_end(48)

        if data.logo_filename is not None:
            try:
                texture = Gdk.Texture.new_from_filename(str(get_asset_path(data.logo_filename)))
                img = Gtk.Image.new_from_paintable(texture)
                img.set_pixel_size(116)
                box.append(img)
            except (FileNotFoundError, GLib.Error):
                pass
        elif data.icon_name is not None:
            icon = Gtk.Image.new_from_icon_name(data.icon_name)
            icon.set_pixel_size(84)
            icon.add_css_class("install-slide-icon")
            box.append(icon)

        title = Gtk.Label(label=data.title)
        title.add_css_class("install-slide-title")
        title.set_halign(Gtk.Align.CENTER)
        title.set_wrap(True)
        title.set_justify(Gtk.Justification.CENTER)
        box.append(title)

        body = Gtk.Label(label=data.body)
        body.add_css_class("install-slide-body")
        body.set_halign(Gtk.Align.CENTER)
        body.set_wrap(True)
        body.set_justify(Gtk.Justification.CENTER)
        box.append(body)

        return box

    def _on_carousel_page_changed(self, _carousel: Adw.Carousel, index: int) -> None:
        self._current_slide = index

    def on_enter(self) -> None:
        self._stop_timers()
        self._status_label.remove_css_class("wifi-error-label")
        self._slide_timer_id = GLib.timeout_add_seconds(4, self._advance_slide)
        self.set_progress(0.0, "Préparation de l'installation")

        if self._demo_mode:
            self._demo_percent = 0
            self._demo_timer_id = GLib.timeout_add(90, self._demo_tick)
            return

        if self._edition == "home":
            run_home_install(
                self._state,
                on_progress=self.set_progress,
                on_success=self._on_install_success,
                on_error=self._on_install_error,
            )
        elif self._edition == "education":
            run_education_install(
                self._state,
                on_progress=self.set_progress,
                on_success=self._on_install_success,
                on_error=self._on_install_error,
            )

    def _on_install_success(self) -> None:
        GLib.timeout_add(700, self._finish_once)

    def _on_install_error(self, message: str) -> None:
        self._stop_timers()
        self._status_label.add_css_class("wifi-error-label")
        self._status_label.set_label(f"Erreur : {message}")

    def _advance_slide(self) -> bool:
        if not self._slide_widgets:
            return False
        next_idx = (self._current_slide + 1) % len(self._slide_widgets)
        self._carousel.scroll_to(self._slide_widgets[next_idx], True)
        return True

    def _demo_step_message(self, percent: int) -> str:
        if percent < 20:
            return "Configuration de la langue du système"
        if percent < 45:
            return "Création des comptes utilisateurs"
        if percent < 75:
            if self._edition == "home" and self._state.office_suite:
                return f"Installation des logiciels en cours ({self._state.office_suite})"
            return "Installation des logiciels en cours"
        if percent < 95:
            if self._edition == "home":
                return f"Configuration du noyau ({self._state.kernel})"
            return "Configuration des profils Education"
        return "Finalisation de la configuration"

    def _demo_tick(self) -> bool:
        self._demo_percent += 1
        message = self._demo_step_message(self._demo_percent)
        self.set_progress(self._demo_percent / 100.0, message)

        if self._demo_percent >= 100:
            self._demo_timer_id = None
            GLib.timeout_add(700, self._finish_once)
            return False
        return True

    def _finish_once(self) -> bool:
        self.finish()
        return False

    def set_progress(self, fraction: float, message: str) -> None:
        """Met à jour la barre et le message (utilisable plus tard par la vraie installation)."""
        clamped = max(0.0, min(1.0, fraction))
        percent = round(clamped * 100)
        self._progress_bar.set_fraction(clamped)
        self._status_label.set_label(f"{message} — {percent} %")

    def finish(self) -> None:
        """Arrête les animations et passe à l'écran final."""
        self._stop_timers()
        self._on_next()

    def _stop_timers(self) -> None:
        if self._slide_timer_id is not None:
            GLib.source_remove(self._slide_timer_id)
            self._slide_timer_id = None
        if self._demo_timer_id is not None:
            GLib.source_remove(self._demo_timer_id)
            self._demo_timer_id = None