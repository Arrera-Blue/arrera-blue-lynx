from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEV_ASSETS_DIR = PROJECT_ROOT / "assets"
SYS_ASSETS_DIR = Path("/usr/share/arrera-blue-lynx/assets")


def get_asset_path(filename: str) -> Path:
    dev_path = DEV_ASSETS_DIR / filename
    if dev_path.exists():
        return dev_path

    sys_path = SYS_ASSETS_DIR / filename
    if sys_path.exists():
        return sys_path

    raise FileNotFoundError(
        f"Asset introuvable : '{filename}' "
        f"(cherché dans {DEV_ASSETS_DIR} et {SYS_ASSETS_DIR})"
    )