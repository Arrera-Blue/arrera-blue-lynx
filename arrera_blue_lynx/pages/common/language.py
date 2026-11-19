from collections.abc import Callable
from dataclasses import dataclass

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from arrera_blue_lynx.core.state import SetupState


@dataclass(frozen=True)
class LanguageOption:
    locale: str
    native_name: str
    title: str
    subtitle: str


LANGUAGES: list[LanguageOption] = [
    LanguageOption("fr_FR.UTF-8", "Français", "Langue", "Choisissez la langue du système"),
    LanguageOption("en_US.UTF-8", "English", "Language", "Choose your system language"),
    LanguageOption("de_DE.UTF-8", "Deutsch", "Sprache", "Wählen Sie die Systemsprache"),
    LanguageOption("es_ES.UTF-8", "Español", "Idioma", "Seleccione el idioma del sistema"),
    LanguageOption("it_IT.UTF-8", "Italiano", "Lingua", "Scegli la lingua del sistema"),
    LanguageOption("pt_PT.UTF-8", "Português", "Idioma", "Escolha o idioma do sistema"),
    LanguageOption("pt_BR.UTF-8", "Português (Brasil)", "Idioma", "Escolha o idioma do sistema"),
    LanguageOption("nl_NL.UTF-8", "Nederlands", "Taal", "Kies de systeemtaal"),
    LanguageOption("pl_PL.UTF-8", "Polski", "Język", "Wybierz język systemu"),
    LanguageOption("sv_SE.UTF-8", "Svenska", "Språk", "Välj systemspråk"),
    LanguageOption("nb_NO.UTF-8", "Norsk bokmål", "Språk", "Velg systemspråk"),
    LanguageOption("da_DK.UTF-8", "Dansk", "Sprog", "Vælg systemsprog"),
    LanguageOption("fi_FI.UTF-8", "Suomi", "Kieli", "Valitse järjestelmän kieli"),
    LanguageOption("ru_RU.UTF-8", "Русский", "Язык", "Выберите язык системы"),
    LanguageOption("tr_TR.UTF-8", "Türkçe", "Dil", "Sistem dilini seçin"),
    LanguageOption("ja_JP.UTF-8", "日本語", "言語", "システム言語を選択してください"),
    LanguageOption("ko_KR.UTF-8", "한국어", "언어", "시스템 언어를 선택하세요"),
    LanguageOption("zh_CN.UTF-8", "简体中文", "语言", "选择系统语言"),
    LanguageOption("zh_TW.UTF-8", "繁體中文", "語言", "選擇系統語言"),
]


class _LanguageRow(Gtk.ListBoxRow):
    def __init__(self, option: LanguageOption) -> None:
        super().__init__()
        self.option = option
        self.add_css_class("language-row")

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(18)
        box.set_margin_end(18)

        label = Gtk.Label(label=option.native_name)
        label.set_xalign(0.0)
        label.set_hexpand(True)
        label.add_css_class("language-row-label")
        box.append(label)

        self.check_icon = Gtk.Image.new_from_icon_name("object-select-symbolic")
        self.check_icon.set_pixel_size(16)
        self.check_icon.add_css_class("language-check-icon")
        self.check_icon.set_visible(False)
        box.append(self.check_icon)

        self.set_child(box)


class LanguagePage(Gtk.Box):
    """Page commune de choix de la langue système (fond blanc, style GTK4 épuré)."""

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
        self._selected: LanguageOption = LANGUAGES[0]
        self._rows: list[_LanguageRow] = []

        self.add_css_class("setup-white-page")
        self.set_hexpand(True)
        self.set_vexpand(True)

        # Conteneur centré avec largeur maîtrisée (typique Libadwaita)
        clamp = Adw.Clamp()
        clamp.set_maximum_size(460)
        clamp.set_tightening_threshold(400)
        clamp.set_hexpand(True)
        clamp.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content.set_valign(Gtk.Align.CENTER)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(24)
        content.set_margin_end(24)

        # En-tête : icône + titre + sous-titre
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        header.set_halign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name("preferences-desktop-locale-symbolic")
        icon.set_pixel_size(44)
        icon.add_css_class("setup-header-icon")
        header.append(icon)

        self._title_label = Gtk.Label(label=self._selected.title)
        self._title_label.add_css_class("setup-title")
        header.append(self._title_label)

        self._subtitle_label = Gtk.Label(label=self._selected.subtitle)
        self._subtitle_label.add_css_class("setup-subtitle")
        header.append(self._subtitle_label)

        content.append(header)

        # Liste scrollable des langues
        scrolled = Gtk.ScrolledWindow()
        scrolled.add_css_class("language-scroll")
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(340)
        scrolled.set_max_content_height(380)
        scrolled.set_propagate_natural_height(False)

        self._listbox = Gtk.ListBox()
        self._listbox.add_css_class("language-list")
        self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._listbox.set_activate_on_single_click(False)
        self._listbox.connect("row-selected", self._on_row_selected)
        self._listbox.connect("row-activated", self._on_row_activated)

        default_row: _LanguageRow | None = None
        for option in LANGUAGES:
            row = _LanguageRow(option)
            self._rows.append(row)
            self._listbox.append(row)
            if option.locale == self._state.language:
                default_row = row

        scrolled.set_child(self._listbox)
        content.append(scrolled)

        # Barre de navigation en bas (Retour discret + Flèche Suivant)
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        nav_box.set_halign(Gtk.Align.CENTER)
        nav_box.set_margin_top(8)

        if self._on_back is not None:
            back_btn = Gtk.Button()
            back_btn.add_css_class("circular")
            back_btn.add_css_class("setup-nav-back-btn")
            back_btn.set_tooltip_text("Retour")
            back_btn.connect("clicked", lambda _btn: self._on_back())

            back_icon = Gtk.Image.new_from_icon_name("go-previous-symbolic")
            back_icon.set_pixel_size(20)
            back_btn.set_child(back_icon)
            nav_box.append(back_btn)

        next_btn = Gtk.Button()
        next_btn.add_css_class("circular")
        next_btn.add_css_class("suggested-action")
        next_btn.add_css_class("setup-nav-next-btn")
        next_btn.set_tooltip_text("Continuer")
        next_btn.connect("clicked", lambda _btn: self._confirm_and_next())

        next_icon = Gtk.Image.new_from_icon_name("go-next-symbolic")
        next_icon.set_pixel_size(22)
        next_btn.set_child(next_icon)
        nav_box.append(next_btn)

        content.append(nav_box)

        clamp.set_child(content)
        self.append(clamp)

        # Pré-sélectionne la langue courante de l'état
        self._listbox.select_row(default_row or self._rows[0])

    def _on_row_selected(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if not isinstance(row, _LanguageRow):
            return

        self._selected = row.option
        self._state.language = row.option.locale
        self._title_label.set_label(row.option.title)
        self._subtitle_label.set_label(row.option.subtitle)

        for item in self._rows:
            item.check_icon.set_visible(item is row)

    def _on_row_activated(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if isinstance(row, _LanguageRow):
            self._confirm_and_next()

    def _confirm_and_next(self) -> None:
        self._state.language = self._selected.locale
        print(f"[LanguagePage] Langue sélectionnée : {self._state.language}")
        self._on_next()