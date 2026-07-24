"""Chỉnh HÀNG LOẠT giá đi lại (dịch chuyển / xe-trạm / thuyền).

Các file này là MA TRẬN giá (thành đi × thành đến), hàng trăm ô — không thể bắt
người dùng sửa tay. Nên chỉ cho 2 thao tác gọn:
- Đặt TẤT CẢ giá về 1 mức, hoặc
- Nhân tất cả giá lên/xuống theo hệ số.
Ô '-1' (không có tuyến) và dòng/cột tiêu đề luôn giữ nguyên.

Giá GỐC của từng file được ghi lại 1 lần vào baseline (trên VM) để 'nhân' luôn
tính từ gốc và trả về nguyên bản được — cùng cơ chế droprate_service.
"""
import json

from backend import backup_service

_SET = "/home/jxser/server1/settings/"
BASELINE = backup_service.BACKUP_DIR + "/price-baseline.json"

SCOPES = {
    "waypoint": {"title": "Dịch chuyển (Waypoint)", "file": _SET + "waypointprice.txt"},
    "station": {"title": "Xe / Trạm ngựa", "file": _SET + "stationprice.txt"},
    "wharf": {"title": "Thuyền / Bến tàu", "file": _SET + "wharfprice.txt"},
}


def _load_baseline(svc):
    try:
        return json.loads(svc.read_file(BASELINE, "utf-8"))
    except Exception:
        return {}


def _save_baseline(svc, data):
    backup_service._ensure_dir(svc)
    svc.write_file(BASELINE, json.dumps(data, indent=1), "utf-8", make_backup=False)


def _cells(text):
    """Sinh (dòng, cột, giá) cho mọi ô GIÁ (bỏ tiêu đề dòng 0 + cột tên 0 + '-1' + rỗng)."""
    eol = "\r\n" if "\r\n" in text else "\n"
    rows = text.split(eol)
    for i, ln in enumerate(rows):
        if i == 0 or ln.strip() == "":
            continue
        for j, cell in enumerate(ln.split("\t")):
            if j == 0:
                continue
            c = cell.strip()
            if c.lstrip("-").isdigit() and c != "-1":
                yield i, j, int(c)


def _stats(text):
    vals = [v for _, _, v in _cells(text)]
    return {"count": len(vals), "min": min(vals) if vals else 0, "max": max(vals) if vals else 0}


def status(svc):
    out = []
    for sid, meta in SCOPES.items():
        try:
            text = svc.read_file(meta["file"], "latin-1")
            out.append({"id": sid, "title": meta["title"], **_stats(text)})
        except Exception as e:
            out.append({"id": sid, "title": meta["title"], "error": str(e)})
    return out


def _rewrite(text, valfn):
    """Ghi lại: mỗi ô giá (i,j,giá_cũ) -> valfn(i,j,giá_cũ); phần khác giữ nguyên."""
    eol = "\r\n" if "\r\n" in text else "\n"
    rows = text.split(eol)
    by_row = {}
    for i, j, v in _cells(text):
        by_row.setdefault(i, []).append((j, v))
    for i, js in by_row.items():
        cells = rows[i].split("\t")
        for j, v in js:
            cells[j] = str(max(0, int(round(valfn(i, j, v)))))
        rows[i] = "\t".join(cells)
    return eol.join(rows)


def _commit(svc, meta, text, new_text, desc):
    if new_text == text:
        return {"changed": 0, "message": "Giá đã đúng như vậy rồi."}
    backup_service.snapshot(svc, meta["file"], "Chỉnh giá đi lại: " + desc + " (" + meta["title"] + ")")
    svc.write_file(meta["file"], new_text, "latin-1", make_backup=True)
    return {"changed": _stats(new_text)["count"], "message": desc + " — nhớ Restart server."}


def apply_set(svc, scope_id, value):
    """Đặt TẤT CẢ giá của scope về `value`."""
    meta = SCOPES.get(scope_id)
    if not meta:
        raise ValueError("Không rõ nhóm: " + str(scope_id))
    value = int(value)
    text = svc.read_file(meta["file"], "latin-1")
    new_text = _rewrite(text, lambda i, j, old: value)
    return _commit(svc, meta, text, new_text, f"Đặt mọi giá = {value}")


def apply_scale(svc, scope_id, mult):
    """Nhân tất cả giá theo hệ số (tính từ GỐC). mult=1 = trả về nguyên bản."""
    meta = SCOPES.get(scope_id)
    if not meta:
        raise ValueError("Không rõ nhóm: " + str(scope_id))
    mult = float(mult)
    if not (0.0 <= mult <= 1000):
        raise ValueError("Hệ số phải trong 0–1000")
    baseline = _load_baseline(svc)
    text = svc.read_file(meta["file"], "latin-1")
    if scope_id not in baseline:      # lưu giá GỐC từng ô lần đầu
        baseline[scope_id] = {f"{i},{j}": v for i, j, v in _cells(text)}
        _save_baseline(svc, baseline)
    base = baseline[scope_id]
    new_text = _rewrite(text, lambda i, j, old: int(base.get(f"{i},{j}", old)) * mult)
    return _commit(svc, meta, text, new_text, f"Nhân giá x{mult:g}")
