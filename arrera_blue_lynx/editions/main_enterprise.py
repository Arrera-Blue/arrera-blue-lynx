import sys

from arrera_blue_lynx.core.window import LynxApp, LynxWindow
from arrera_blue_lynx.pages.common.finish import FinishPage
from arrera_blue_lynx.pages.common.install import InstallPage
from arrera_blue_lynx.pages.common.language import LanguagePage
from arrera_blue_lynx.pages.common.welcome import WelcomePage
from arrera_blue_lynx.pages.common.wifi import WifiPage
from arrera_blue_lynx.pages.home.user_account import HomeUserAccountPage


def build_enterprise_pages(
    window: LynxWindow,
    force_wifi: bool = False,
    demo_mode: bool = False,
) -> list:
    return [
        WelcomePage(
            logo_filename="logo-enterprise.png",
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
        HomeUserAccountPage(
            state=window.state,
            on_next=window.next_page,
            on_back=window.previous_page,
            require_root=True,
            check_system_users=not demo_mode,
        ),
        InstallPage(
            state=window.state,
            edition="enterprise",
            logo_filename="logo-enterprise.png",
            on_next=window.next_page,
            demo_mode=demo_mode,
        ),
        FinishPage(
            on_finish=window.next_page,
        ),
    ]


def main() -> int:
    fullscreen = "--windowed" not in sys.argv
    force_wifi = "--force-wifi" in sys.argv
    demo_mode = "--demo" in sys.argv
    app = LynxApp(
        app_id="org.arrera.BlueLynx.Enterprise",
        build_pages=lambda win: build_enterprise_pages(
            win,
            force_wifi=force_wifi,
            demo_mode=demo_mode,
        ),
        fullscreen=fullscreen,
    )
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())
