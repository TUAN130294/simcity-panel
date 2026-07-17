"""Kiểm tra & tự cập nhật bản mới từ GitHub.

So sánh `version.txt` của bản đang chạy với bản trên nhánh main. Có bản mới →
giao diện hiện popup; người dùng đồng ý → tải ZIP main về, chép đè thư mục app
(giữ nguyên settings.json chứa IP/mật khẩu VM) rồi tự khởi động lại panel.
Mạng lỗi/offline → coi như không có bản mới, không làm phiền.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from threading import Timer

REPO = "TUAN130294/simcity-panel"
BRANCH = "main"
RAW_VERSION_URL = "https://raw.githubusercontent.com/%s/%s/version.txt" % (REPO, BRANCH)
ZIP_URL = "https://github.com/%s/archive/refs/heads/%s.zip" % (REPO, BRANCH)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/.. = thư mục app

_cache = {"t": 0.0, "remote": None}


def local_version():
    try:
        with open(os.path.join(APP_DIR, "version.txt"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "0.0.0"  # bản cài trước khi có version.txt


def _ver_tuple(v):
    try:
        return tuple(int(x) for x in v.strip().split("."))
    except ValueError:
        return (0,)


def remote_version(ttl=3600):
    """Bản mới nhất trên GitHub (cache 1 giờ để không gọi mạng mỗi lần tải trang)."""
    now = time.time()
    if _cache["remote"] and now - _cache["t"] < ttl:
        return _cache["remote"]
    req = urllib.request.Request(RAW_VERSION_URL, headers={"User-Agent": "simcity-panel"})
    with urllib.request.urlopen(req, timeout=5) as r:
        v = r.read().decode("utf-8").strip()
    _cache.update(t=now, remote=v)
    return v


def check():
    cur = local_version()
    try:
        latest = remote_version()
    except Exception:
        return {"current": cur, "latest": None, "update_available": False}
    return {"current": cur, "latest": latest,
            "update_available": _ver_tuple(latest) > _ver_tuple(cur)}


def apply_update():
    """Tải bản mới, chép đè (giữ settings.json), hẹn tự khởi động lại sau 1.5s."""
    tmp = tempfile.mkdtemp(prefix="simcity-panel-up-")
    try:
        zpath = os.path.join(tmp, "src.zip")
        req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "simcity-panel"})
        with urllib.request.urlopen(req, timeout=90) as r, open(zpath, "wb") as f:
            shutil.copyfileobj(r, f)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(tmp)
        src = next(os.path.join(tmp, d) for d in os.listdir(tmp)
                   if os.path.isdir(os.path.join(tmp, d)))
        for root, _dirs, files in os.walk(src):
            rel = os.path.relpath(root, src)
            for name in files:
                if rel == "." and name == "settings.json":
                    continue  # không đụng cài đặt kết nối của người dùng
                dst_dir = APP_DIR if rel == "." else os.path.join(APP_DIR, rel)
                os.makedirs(dst_dir, exist_ok=True)
                shutil.copy2(os.path.join(root, name), os.path.join(dst_dir, name))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    Timer(1.5, _restart).start()  # để kịp trả response cho trình duyệt trước
    return {"updated_to": local_version()}


def _restart():
    """Thoát tiến trình hiện tại, nhờ cmd chờ ~2s (nhả cổng 5666) rồi mở lại launcher."""
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pyw):
        exe = pyw
    launcher = os.path.join(APP_DIR, "launcher.pyw")
    cmd = 'ping -n 3 127.0.0.1 >nul & start "" "%s" "%s"' % (exe, launcher)
    DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP = 0x00000008, 0x00000200
    subprocess.Popen(["cmd", "/c", cmd], cwd=APP_DIR,
                     creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
    os._exit(0)
