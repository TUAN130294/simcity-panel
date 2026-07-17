"""Tự dò server game trong mạng — để người dùng mới không phải gõ IP.

Hai cách, chạy lần lượt:
1. Đọc `config.ini` của client VLTK (mục [ssh] có sẵn host/user/password) —
   tìm ở các ổ đĩa/thư mục thường gặp.
2. Quét mạng LAN: tìm máy mở cổng SSH, thử đăng nhập rồi kiểm tra có thư mục
   game (`/home/jxser`) hay không.

Chỉ ĐỌC, không đổi gì trên máy người dùng.
"""
import configparser
import os
import socket
import string
from concurrent.futures import ThreadPoolExecutor

# Thư mục con hay gặp của client VLTK (dò nông cho nhanh).
_CLIENT_HINTS = ("vltk", "jx", "volam", "võ lâm", "client", "game", "server", "phunghoangson")
_MAX_DEPTH = 3
GAME_MARKER = "/home/jxser"


# ---------- cách 1: đọc config.ini của client ----------
def _read_ini(path):
    """Trả về dict thông tin ssh nếu file config.ini có mục [ssh] hợp lệ."""
    try:
        parser = configparser.ConfigParser()
        with open(path, "r", encoding="latin-1") as f:
            parser.read_string(f.read())
    except Exception:
        return None
    if not parser.has_section("ssh"):
        return None
    s = parser["ssh"]
    host = (s.get("host") or "").strip()
    if not host:
        return None
    return {
        "host": host,
        "port": (s.get("port") or "22").strip(),
        "user": (s.get("username") or "root").strip(),
        "password": s.get("password") or "",
        "client_config_ini": path,
        "client_dir": os.path.dirname(path),
        "source": "config.ini của client",
    }


def _walk_for_ini(root, depth=0):
    """Duyệt nông tìm config.ini, chỉ vào thư mục có tên gợi ý game."""
    if depth > _MAX_DEPTH:
        return None
    try:
        entries = list(os.scandir(root))
    except (PermissionError, OSError):
        return None
    for e in entries:
        try:
            if e.is_file() and e.name.lower() == "config.ini":
                found = _read_ini(e.path)
                if found:
                    return found
        except OSError:
            continue
    for e in entries:
        try:
            if not e.is_dir():
                continue
        except OSError:
            continue
        name = e.name.lower()
        if depth == 0 or any(h in name for h in _CLIENT_HINTS):
            found = _walk_for_ini(e.path, depth + 1)
            if found:
                return found
    return None


def find_client_config():
    """Dò config.ini của client trên các ổ đĩa. Trả về dict hoặc None."""
    roots = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            roots.append(drive)
    for extra in (os.path.expanduser("~/Desktop"), os.path.expanduser("~/Downloads")):
        if os.path.isdir(extra):
            roots.append(extra)
    for root in roots:
        found = _walk_for_ini(root)
        if found:
            return found
    return None


# ---------- cách 2: quét mạng LAN ----------
def _local_subnets():
    """Các dải /24 của máy này (vd 192.168.1.0/24)."""
    nets = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith("127."):
                continue
            prefix = ip.rsplit(".", 1)[0]
            if prefix not in nets:
                nets.append(prefix)
    except Exception:
        pass
    return nets


def _ssh_open(ip, port=22, timeout=0.35):
    with socket.socket() as s:
        s.settimeout(timeout)
        return ip if s.connect_ex((ip, port)) == 0 else None


def scan_lan(port=22):
    """Trả về danh sách IP trong LAN đang mở cổng SSH."""
    hosts = []
    for prefix in _local_subnets():
        targets = [f"{prefix}.{i}" for i in range(1, 255)]
        with ThreadPoolExecutor(max_workers=120) as pool:
            for res in pool.map(lambda ip: _ssh_open(ip, port), targets):
                if res:
                    hosts.append(res)
    return hosts


def verify_game_host(ip, port, user, password):
    """Đăng nhập thử và kiểm tra có thư mục game không. True = đúng server game."""
    from backend.ssh_service import SSHService  # import trễ: tránh vòng lặp import
    try:
        svc = SSHService(ip, port, user, password)
        out, _ = svc.run(f"test -d {GAME_MARKER} && echo YES || echo NO", timeout=10)
        return "YES" in out
    except Exception:
        return False


def autodetect(user="root", password="", port=22):
    """Dò server game. Trả về {found, ...thông tin} — KHÔNG tự lưu settings."""
    # 1. config.ini của client là nguồn tin cậy nhất (có sẵn cả mật khẩu)
    found = find_client_config()
    if found:
        ok = verify_game_host(found["host"], int(found["port"] or 22),
                              found["user"], found["password"])
        found["verified"] = ok
        found["found"] = True
        return found

    # 2. không có client -> quét LAN, cần user/password người dùng nhập
    if not password:
        return {"found": False,
                "error": "Không tìm thấy config.ini của client. Hãy nhập mật khẩu VM rồi bấm dò lại "
                         "(app sẽ quét mạng nội bộ tìm máy chủ game)."}
    for ip in scan_lan(port):
        if verify_game_host(ip, port, user, password):
            return {"found": True, "verified": True, "host": ip, "port": str(port),
                    "user": user, "password": password, "source": "quét mạng nội bộ"}
    return {"found": False,
            "error": "Quét hết mạng nội bộ nhưng không thấy máy chủ game nào. "
                     "Kiểm tra máy ảo đã bật chưa, hoặc nhập tay IP trong ô VM Host."}
