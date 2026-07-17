"""Bật/tắt MÁY ẢO (VMware, qua vmrun trên máy Windows) và GAME SERVER (qua SSH).

Hai tầng khác nhau:
- Máy ảo: panel chạy ngay trên máy có VMware nên gọi thẳng `vmrun` được, kể cả
  khi máy ảo đang tắt (lúc đó SSH không vào được).
- Game server: `jx.sh start|stop` bên trong máy ảo -> bắt buộc máy ảo phải đang bật.

Tắt máy ảo LUÔN ưu tiên tắt sạch bằng `shutdown -h now` qua SSH: máy ảo này ẩn cờ
ảo hoá nên open-vm-tools không chạy, `vmrun stop soft` sẽ không ăn, còn `stop hard`
là rút phích -> hỏng dữ liệu + để lại khoá .lck.
"""
import os
import subprocess
import glob

VMRUN_CANDIDATES = [
    r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe",
    r"C:\Program Files\VMware\VMware Workstation\vmrun.exe",
    r"C:\Program Files (x86)\VMware\VMware VIX\vmrun.exe",
]
# jx.sh mở cửa sổ terminal trong máy ảo nên cần DISPLAY của phiên đồ hoạ.
_JX_ENV = "DISPLAY=:0 XAUTHORITY=/root/.Xauthority"

# jx.sh chạy từng tiến trình bằng `xfce4-terminal --tab`:
#  - đã có cửa sổ terminal -> lệnh gắn thêm tab rồi thoát ngay -> script chạy tiếp.
#  - CHƯA có cửa sổ nào (VM vừa boot) -> nó phải tự mở cửa sổ đầu tiên và NẰM LUÔN ở đó
#    -> jx.sh kẹt vĩnh viễn ngay tiến trình đầu, các tiến trình sau không bao giờ chạy.
# Nên luôn mở sẵn 1 cửa sổ nền (setsid = tách hẳn, không chết theo phiên SSH).
_ENSURE_TERM = (
    "pgrep -x xfce4-terminal >/dev/null 2>&1 || "
    "{ setsid xfce4-terminal --title=SimCityPanel-Host >/dev/null 2>&1 & sleep 5; }"
)


def find_vmrun():
    for p in VMRUN_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


# Tên gợi ý máy ảo game (để chọn đúng khi máy có nhiều máy ảo).
_VMX_HINTS = ("jx", "vltk", "volam", "vo lam", "server", "game", "1click")


def find_vmx_all():
    """Mọi file .vmx tìm được trên các ổ đĩa (dò tới 4 cấp thư mục)."""
    import string
    hits = []
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if not os.path.exists(drive):
            continue
        for depth in range(1, 5):           # <ổ>\*.vmx ... <ổ>\*\*\*\*.vmx
            pat = drive + "\\".join(["*"] * depth) + ".vmx" if depth == 1 \
                  else drive + "\\".join(["*"] * (depth - 1)) + "\\*.vmx"
            try:
                hits.extend(glob.glob(pat))
            except OSError:
                continue
    return hits


def find_vmx():
    """Đoán file .vmx của máy ảo game. Ưu tiên đường dẫn có tên gợi ý game."""
    hits = find_vmx_all()
    if not hits:
        return None
    for h in hits:
        low = h.lower()
        if any(k in low for k in _VMX_HINTS):
            return h
    return hits[0]


def _run(cmd, timeout=90):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")


def vm_running(vmrun, vmx):
    """Máy ảo có trong danh sách đang chạy của VMware không."""
    out = _run([vmrun, "-T", "ws", "list"], timeout=30)
    target = os.path.normcase(os.path.abspath(vmx))
    for line in out.splitlines():
        line = line.strip()
        if line and line.lower().endswith(".vmx"):
            if os.path.normcase(os.path.abspath(line)) == target:
                return True
    return False


def stale_locks(vmx):
    """Khoá .lck còn sót khi không có máy ảo nào chạy -> chặn lần bật sau."""
    folder = os.path.dirname(os.path.abspath(vmx))
    return sorted(glob.glob(os.path.join(folder, "*.lck")))


def clear_stale_locks(vmx):
    """Xoá khoá cũ. CHỈ gọi khi chắc chắn không có máy ảo nào đang chạy."""
    import shutil
    removed = []
    for lck in stale_locks(vmx):
        try:
            shutil.rmtree(lck) if os.path.isdir(lck) else os.remove(lck)
            removed.append(os.path.basename(lck))
        except OSError:
            pass
    return removed


def vm_start(vmrun, vmx, headless=True):
    """Bật máy ảo. Tự dọn khoá cũ nếu chắc chắn không có máy ảo nào chạy."""
    if vm_running(vmrun, vmx):
        return {"ok": True, "already": True, "message": "Máy ảo đang bật sẵn."}
    cleared = []
    if stale_locks(vmx):
        # 'vmrun list' rỗng nghĩa là không tiến trình nào giữ khoá -> khoá là rác
        if "Total running VMs: 0" in _run([vmrun, "-T", "ws", "list"], timeout=30):
            cleared = clear_stale_locks(vmx)
    out = _run([vmrun, "-T", "ws", "start", vmx, "nogui" if headless else "gui"], timeout=180)
    ok = vm_running(vmrun, vmx)
    return {"ok": ok, "cleared_locks": cleared, "output": out.strip()[:400],
            "message": "Đã bật máy ảo, đợi 1-2 phút cho hệ điều hành khởi động."
                       if ok else "Không bật được máy ảo."}


def vm_stop(svc_factory, vmrun, vmx):
    """Tắt máy ảo SẠCH qua SSH (shutdown -h now), rồi đợi VMware nhả máy."""
    import time
    if not vm_running(vmrun, vmx):
        return {"ok": True, "already": True, "message": "Máy ảo đang tắt sẵn."}
    try:
        svc = svc_factory()
        svc.run("nohup sh -c 'sleep 1; shutdown -h now' >/dev/null 2>&1 &", timeout=15)
    except Exception as e:
        return {"ok": False, "error": f"Không gửi được lệnh tắt qua SSH: {e}. "
                                      f"Máy ảo vẫn đang bật — hãy tắt trong cửa sổ VMware."}
    for _ in range(40):  # đợi tối đa ~2 phút
        time.sleep(3)
        if not vm_running(vmrun, vmx):
            return {"ok": True, "message": "Đã tắt máy ảo sạch sẽ."}
    return {"ok": False, "error": "Đã gửi lệnh tắt nhưng sau 2 phút máy ảo vẫn chạy. "
                                  "Kiểm tra trong cửa sổ VMware."}


def game_running(svc):
    # -x: khớp đúng tên tiến trình game (-f dính cả tiến trình vỏ terminal)
    out, _ = svc.run("pgrep -x jx_linux_y >/dev/null && echo UP || echo DOWN", timeout=15)
    return "UP" in out


def game_cmd(svc, action, root="/root/quanlyserver/2.3.1"):
    """Chạy jx.sh start|stop|reload ở chế độ nền (các lệnh này mất vài phút)."""
    if action not in ("start", "stop", "reload"):
        raise ValueError("Lệnh không hợp lệ: " + str(action))
    inner = f"export {_JX_ENV}; {_ENSURE_TERM}; cd {root} && ./jx.sh {action}"
    wrapped = ("nohup bash -c '" + inner.replace("'", "'\\''") +
               f"' >/tmp/simcity-panel-{action}.log 2>&1 & echo STARTED")
    out, err = svc.run(wrapped, timeout=20)
    if "STARTED" not in out:
        raise RuntimeError(err or out or "Không gửi được lệnh")
    return True
