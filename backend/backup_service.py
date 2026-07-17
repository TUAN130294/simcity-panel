"""Lịch sử backup có mô tả + khôi phục (restore) file trên VM.

Mỗi lần panel ghi đè một file game, chụp lại bản HIỆN TẠI vào thư mục
backup trên VM kèm mô tả "sửa gì, lúc nào" trong manifest.jsonl.
Người dùng xem danh sách ở tab Backup và bấm Khôi phục khi game lỗi.

Khôi phục cũng tự chụp lại trạng thái trước đó — nên không bao giờ mất dữ liệu.
"""
import json
import posixpath
import time

BACKUP_DIR = "/home/jxser/simcity-panel-backups"
MANIFEST = BACKUP_DIR + "/manifest.jsonl"
KEEP_MAX = 300  # giữ tối đa bấy nhiêu bản gần nhất trong danh sách


def _ensure_dir(svc):
    svc.run("mkdir -p " + BACKUP_DIR, timeout=10)


def snapshot(svc, path, desc):
    """Chụp bản hiện tại của `path` trước khi ghi đè. Trả về id (None nếu file chưa tồn tại)."""
    try:
        content = svc.read_file(path, "latin-1")  # latin-1 giữ nguyên từng byte
    except Exception:
        return None  # file mới, chưa có gì để backup
    _ensure_dir(svc)
    fid = time.strftime("%Y%m%d-%H%M%S") + "-" + posixpath.basename(path)
    existing, _ = svc.run("ls " + BACKUP_DIR, timeout=10)
    names = set(existing.split())
    base, n = fid, 1
    while fid in names:  # tránh trùng khi lưu nhiều lần cùng 1 giây
        n += 1
        fid = base + "." + str(n)
    svc.write_file(BACKUP_DIR + "/" + fid, content, "latin-1", make_backup=False)
    entry = {"id": fid, "ts": time.strftime("%Y-%m-%d %H:%M:%S"), "path": path, "desc": desc}
    try:
        manifest = svc.read_file(MANIFEST, "utf-8")
    except Exception:
        manifest = ""
    svc.write_file(MANIFEST, manifest + json.dumps(entry, ensure_ascii=False) + "\n",
                   "utf-8", make_backup=False)
    return fid


def list_backups(svc):
    """Danh sách backup, MỚI NHẤT trước."""
    try:
        manifest = svc.read_file(MANIFEST, "utf-8")
    except Exception:
        return []
    entries = []
    for line in manifest.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass  # dòng hỏng thì bỏ qua, không chết cả danh sách
    return entries[::-1][:KEEP_MAX]


def restore(svc, fid):
    """Khôi phục file về bản backup `fid`. Tự chụp trạng thái hiện tại trước."""
    entry = next((e for e in list_backups(svc) if e["id"] == fid), None)
    if not entry:
        raise ValueError("Không tìm thấy bản backup: " + str(fid))
    snapshot(svc, entry["path"], "Tự chụp trước khi khôi phục về bản " + entry["ts"])
    content = svc.read_file(BACKUP_DIR + "/" + fid, "latin-1")
    svc.write_file(entry["path"], content, "latin-1", make_backup=False)
    return entry
