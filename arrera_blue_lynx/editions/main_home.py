import sys

from arrera_blue_lynx.core.window import LynxApp, LynxWindow
from arrera_blue_lynx.pages.common.language import LanguagePage
from arrera_blue_lynx.pages.common.welcome import WelcomePage
from arrera_blue_lynx.pages.common.wifi import WifiPage


def build_home_pages(window: LynxWindow, force_wifi: bool = False) -> list:
    return [
        WelcomePage(
            logo_filename="logo-home.png",
            on_next=window.next_page,
        ),
        LanguagePage(
            state=window.state,
            on_next=window.next_page,
        ),
        WifiPage(
            state=window.state,
            on_next=window.next_page,
            on_back=window.previous_page,
            force_show=force_wifi,
        ),
    ]


def main() -> int:
    fullscreen = "--windowed" not in sys.argv
    force_wifi = "--force-wifi" in sys.argv
    app = LynxApp(
        app_id="org.arrera.BlueLynx.Home",
        build_pages=lambda win: build_home_pages(win, force_wifi=force_wifi),
        fullscreen=fullscreen,
    )
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())