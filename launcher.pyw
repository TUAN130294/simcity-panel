"""Bộ khởi động cho shortcut ngoài Desktop (chạy bằng pythonw = không hiện cửa sổ đen).

- Panel đã chạy sẵn -> chỉ mở trình duyệt (không chạy 2 lần gây lỗi trùng cổng).
- Chưa chạy -> khởi động panel (app.py tự mở trình duyệt).
- Có lỗi -> ghi ra loi-khoi-dong.txt và báo hộp thoại, vì chạy ẩn nên không thấy lỗi.
"""
import os
import socket
import sys
import traceback
import webbrowser

PORT = 5666
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, "nhat-ky-chay.txt")


def _huong_log_ra_file():
    """Chạy ẩn (pythonw/pyw) thì sys.stdout/stderr = None -> Flask in log là văng lỗi.
    Đẩy hết log ra file để vừa không sập, vừa có cái mà xem khi cần."""
    if sys.stdout is not None and sys.stderr is not None:
        return  # chạy từ cửa sổ lệnh: cứ in ra màn hình như thường
    try:
        f = open(LOG_PATH, "a", encoding="utf-8", buffering=1)
    except OSError:
        f = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = f
    if sys.stderr is None:
        sys.stderr = f


def dang_chay():
    with socket.socket() as s:
        s.settimeout(0.6)
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def bao_loi(text):
    log = os.path.join(BASE_DIR, "loi-khoi-dong.txt")
    try:
        with open(log, "w", encoding="utf-8") as f:
            f.write(text)
    except OSError:
        pass
    try:  # hộp thoại Windows để người dùng biết mà báo lại
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0, f"SimCity Panel không khởi động được.\n\nChi tiết đã ghi vào:\n{log}",
            "SimCity Panel — lỗi", 0x10)
    except Exception:
        pass


def main():
    if dang_chay():
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        return
    os.chdir(BASE_DIR)
    sys.path.insert(0, BASE_DIR)
    import runpy
    runpy.run_path(os.path.join(BASE_DIR, "app.py"), run_name="__main__")


if __name__ == "__main__":
    _huong_log_ra_file()
    try:
        main()
    except Exception:
        bao_loi(traceback.format_exc())
        sys.exit(1)
