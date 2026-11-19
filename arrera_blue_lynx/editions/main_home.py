import sys

from arrera_blue_lynx.core.window import LynxApp, LynxWindow
from arrera_blue_lynx.pages.common.welcome import WelcomePage


def build_home_pages(window: LynxWindow) -> list:
    return [
        WelcomePage(
            logo_filename="logo-home.png",
            on_next=window.next_page,
        ),
        # Les prochaines pages Home viendront ici
    ]


def main() -> int:
    fullscreen = "--windowed" not in sys.argv
    app = LynxApp(
        app_id="org.arrera.BlueLynx.Home",
        build_pages=build_home_pages,
        fullscreen=fullscreen,
    )
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())