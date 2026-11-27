import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class WifiNetwork:
    ssid: str
    signal: int
    security: str
    in_use: bool

    @property
    def is_secured(self) -> bool:
        return bool(self.security and self.security != "--")


def _run_nmcli(args: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["LC_ALL"] = "C"
    return subprocess.run(
        ["nmcli", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        check=False,
    )


def _split_nmcli_line(line: str) -> list[str]:
    """Découpe une ligne `nmcli -t -e yes` en respectant les `:` échappés."""
    fields: list[str] = []
    current: list[str] = []
    escaped = False
    for ch in line:
        if escaped:
            current.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(ch)
    fields.append("".join(current))
    return fields


def has_working_ethernet() -> bool:
    """Retourne True si une connexion Ethernet active et fonctionnelle est détectée."""
    try:
        res = _run_nmcli(["-t", "-f", "DEVICE,TYPE,STATE", "device", "status"], timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False

    if res.returncode != 0:
        return False

    connected_eth: list[str] = []
    for line in res.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 3 and parts[1] == "ethernet" and parts[2] == "connected":
            connected_eth.append(parts[0])

    if not connected_eth:
        return False

    # Vérifie que la connectivité générale n'est pas "none"
    try:
        conn = _run_nmcli(["-t", "-f", "CONNECTIVITY", "general"], timeout=5)
        connectivity = conn.stdout.strip().lower()
        if connectivity == "full":
            return True
        if connectivity == "none":
            return False
    except (OSError, subprocess.TimeoutExpired):
        pass

    # Vérifie qu'au moins une interface Ethernet a une adresse IP et une passerelle
    for dev in connected_eth:
        try:
            ip_res = _run_nmcli(["-g", "IP4.ADDRESS", "device", "show", dev], timeout=5)
            gw_res = _run_nmcli(["-g", "IP4.GATEWAY", "device", "show", dev], timeout=5)
            if ip_res.stdout.strip() and gw_res.stdout.strip():
                return True
        except (OSError, subprocess.TimeoutExpired):
            continue

    return False


def list_wifi_networks(rescan: bool = True) -> list[WifiNetwork]:
    """Liste les réseaux Wi-Fi visibles, dédupliqués par SSID et triés par signal."""
    args = [
        "-t",
        "-e",
        "yes",
        "-f",
        "IN-USE,SSID,SIGNAL,SECURITY",
        "device",
        "wifi",
        "list",
        "--rescan",
        "yes" if rescan else "no",
    ]
    try:
        res = _run_nmcli(args, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return []

    if res.returncode != 0:
        return []

    by_ssid: dict[str, WifiNetwork] = {}
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        fields = _split_nmcli_line(line)
        if len(fields) < 4:
            continue

        in_use = fields[0].strip() == "*"
        ssid = fields[1].strip()
        if not ssid:
            continue

        try:
            signal = int(fields[2].strip())
        except ValueError:
            signal = 0

        security = fields[3].strip()
        candidate = WifiNetwork(
            ssid=ssid,
            signal=signal,
            security=security,
            in_use=in_use,
        )

        existing = by_ssid.get(ssid)
        if (
            existing is None
            or (candidate.in_use and not existing.in_use)
            or (candidate.in_use == existing.in_use and candidate.signal > existing.signal)
        ):
            by_ssid[ssid] = candidate

    return sorted(by_ssid.values(), key=lambda net: (not net.in_use, -net.signal, net.ssid.lower()))


def connect_wifi(ssid: str, password: str | None = None) -> tuple[bool, str]:
    """Tente de se connecter à un réseau Wi-Fi via nmcli."""
    args = ["device", "wifi", "connect", ssid]
    if password:
        args.extend(["password", password])

    try:
        res = _run_nmcli(args, timeout=25)
    except subprocess.TimeoutExpired:
        return False, "Délai d'attente dépassé lors de la connexion."
    except OSError as exc:
        return False, f"Erreur système : {exc}"

    if res.returncode == 0:
        return True, ""

    err = (res.stderr or res.stdout).strip()
    if "Secrets were required" in err or "password" in err.lower():
        return False, "Mot de passe incorrect ou refusé par le réseau."
    return False, err or "Impossible de se connecter au réseau Wi-Fi."


def has_wifi_device() -> bool:
    """Retourne True si une interface Wi-Fi est présente sur la machine."""
    try:
        res = _run_nmcli(["-t", "-f", "TYPE", "device", "status"], timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if res.returncode != 0:
        return False
    return any(line.strip() == "wifi" for line in res.stdout.splitlines())


def has_internet_connectivity() -> bool:
    """Retourne True si une connexion réseau active (Ethernet ou Wi-Fi) est disponible."""
    try:
        conn = _run_nmcli(["-t", "-f", "CONNECTIVITY", "general"], timeout=5)
        connectivity = conn.stdout.strip().lower()
        if connectivity == "full":
            return True
        if connectivity == "none":
            return False
    except (OSError, subprocess.TimeoutExpired):
        pass

    try:
        res = _run_nmcli(["-t", "-f", "DEVICE,TYPE,STATE", "device", "status"], timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if res.returncode != 0:
        return False

    for line in res.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 3 and parts[1] in {"ethernet", "wifi"} and parts[2] == "connected":
            dev = parts[0]
            try:
                ip_res = _run_nmcli(["-g", "IP4.ADDRESS", "device", "show", dev], timeout=5)
                gw_res = _run_nmcli(["-g", "IP4.GATEWAY", "device", "show", dev], timeout=5)
                if ip_res.stdout.strip() and gw_res.stdout.strip():
                    return True
            except (OSError, subprocess.TimeoutExpired):
                continue
    return False


def get_local_ip() -> str | None:
    """Retourne la première adresse IPv4 active (hors loopback), ou None."""
    try:
        res = _run_nmcli(["-t", "-f", "DEVICE,TYPE,STATE", "device", "status"], timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if res.returncode != 0:
        return None

    for line in res.stdout.splitlines():
        parts = line.split(":")
        if len(parts) >= 3 and parts[1] in {"ethernet", "wifi"} and parts[2] == "connected":
            try:
                ip_res = _run_nmcli(["-g", "IP4.ADDRESS", "device", "show", parts[0]], timeout=5)
                raw = ip_res.stdout.strip().splitlines()
                if raw:
                    return raw[0].split("/")[0].strip()
            except (OSError, subprocess.TimeoutExpired):
                continue
    return None
