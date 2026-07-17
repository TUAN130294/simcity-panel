"""Local settings store + import of connection info from the game client config.ini.

Settings live in simcity-panel/settings.json (next to app.py). We never hardcode
the VM credentials in source; they are imported from the client's config.ini or
typed by the user in the Settings panel.
"""
import json
import os
import configparser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")

# Không cắm cứng thông tin máy nào ở đây: settings.json (đã .gitignore) giữ
# thông tin riêng của từng người; lần chạy đầu app tự dò (xem detect_service).
DEFAULT_CLIENT_CONFIG = ""

DEFAULTS = {
    "host": "",
    "port": 22,
    "user": "root",
    "password": "",
    "simcity_path": "/home/jxser/server1/script/global/nobitaxd/vdk/simcity",
    "server_root": "/home/jxser/server1",
    "client_dir": "",
    "client_config_ini": "",
    "vmx_path": "",       # file .vmx của máy ảo -> để bật/tắt máy ảo bằng vmrun
    "encoding": "latin-1",
    # jx.sh KHÔNG có lệnh 'restart'; 'reload' cần DISPLAY vì script mở cửa sổ terminal trên VM.
    "reload_cmd": "cd /root/quanlyserver/2.3.1 && DISPLAY=:0 XAUTHORITY=/root/.Xauthority ./jx.sh reload",
}


def load_settings():
    data = dict(DEFAULTS)
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data.update(json.load(f))
        except Exception:
            pass
    return data


def save_settings(patch):
    data = load_settings()
    for key in DEFAULTS:
        if key in patch and patch[key] is not None:
            data[key] = patch[key]
    try:
        data["port"] = int(data.get("port") or 22)
    except (ValueError, TypeError):
        data["port"] = 22
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def import_client_config(ini_path=None):
    """Read [ssh] (and fallbacks) from the client config.ini and merge into settings."""
    ini_path = ini_path or load_settings().get("client_config_ini") or DEFAULT_CLIENT_CONFIG
    if not os.path.exists(ini_path):
        raise FileNotFoundError(ini_path)

    parser = configparser.ConfigParser()
    # config.ini has non-utf8 bytes in [Client]; read tolerant.
    with open(ini_path, "r", encoding="latin-1") as f:
        parser.read_string(f.read())

    patch = {"client_config_ini": ini_path}
    if parser.has_section("ssh"):
        s = parser["ssh"]
        patch["host"] = s.get("host", DEFAULTS["host"])
        patch["port"] = s.get("port", "22")
        patch["user"] = s.get("username", "root")
        patch["password"] = s.get("password", "")
    elif parser.has_section("Server"):
        patch["host"] = parser["Server"].get("UbuntuHost", DEFAULTS["host"])

    return save_settings(patch)
