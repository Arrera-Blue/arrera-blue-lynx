import sys

from arrera_blue_lynx.core.window import LynxApp, LynxWindow
from arrera_blue_lynx.pages.common.language import LanguagePage
from arrera_blue_lynx.pages.common.welcome import WelcomePage


def build_education_pages(window: LynxWindow) -> list:
    return [
        WelcomePage(
            logo_filename="logo-education.png",
            on_next=window.next_page,
        ),
        LanguagePage(
            state=window.state,
            on_next=window.next_page,
        ),
    ]


def main() -> int:
    fullscreen = "--windowed" not in sys.argv
    app = LynxApp(
        app_id="org.arrera.BlueLynx.Education",
        build_pages=build_education_pages,
        fullscreen=fullscreen,
    )
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())