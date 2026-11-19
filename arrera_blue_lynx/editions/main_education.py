import sys

from arrera_blue_lynx.core.window import LynxApp, LynxWindow
from arrera_blue_lynx.pages.common.language import LanguagePage
from arrera_blue_lynx.pages.common.welcome import WelcomePage
from arrera_blue_lynx.pages.common.wifi import WifiPage
from arrera_blue_lynx.pages.education.adult_account import EducationAdultAccountPage
from arrera_blue_lynx.pages.education.child_account import EducationChildAccountPage
from arrera_blue_lynx.pages.common.install import InstallPage
from arrera_blue_lynx.pages.common.finish import FinishPage

def build_education_pages(window: LynxWindow, force_wifi: bool = False) -> list:
    return [
        WelcomePage(
            logo_filename="logo-education.png",
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
        EducationAdultAccountPage(
            state=window.state,
            on_next=window.next_page,
            on_back=window.previous_page,
        ),
        EducationChildAccountPage(
            state=window.state,
            on_next=window.next_page,
            on_back=window.previous_page,
        ),
        InstallPage(
            state=window.state,
            edition="education",
            logo_filename="logo-education.png",
            on_next=window.next_page,
        ),
        FinishPage(
            on_finish=window.next_page,
        ),
    ]


def main() -> int:
    fullscreen = "--windowed" not in sys.argv
    force_wifi = "--force-wifi" in sys.argv
    app = LynxApp(
        app_id="org.arrera.BlueLynx.Education",
        build_pages=lambda win: build_education_pages(win, force_wifi=force_wifi),
        fullscreen=fullscreen,
    )
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())