"""Buff/nerf tỉ lệ rơi đồ TOÀN SERVER bằng 1 hệ số nhân.

Cơ chế game: mỗi file droprate .ini có [Main] RandRange = độ rộng "vòng quay
xổ số" mỗi lần giết quái; các mục [N] RandRate = lát trúng thưởng.
=> Xác suất rơi ≈ tổng(RandRate)/RandRange. GIẢM RandRange = rơi NHIỀU hơn.

Hệ số x2 = RandRange gốc / 2 (kẹp không nhỏ hơn tổng RandRate để không vỡ).
RandRange GỐC của từng file được ghi lại 1 lần vào baseline.json trên VM —
nhờ đó áp x2 rồi áp x3 vẫn tính từ gốc, và trả về x1 là về đúng nguyên bản.
"""
import json
import posixpath

from backend import ini_config_parser as iniparse
from backend import backup_service

BASELINE = backup_service.BACKUP_DIR + "/droprate-baseline.json"

_SV = "/home/jxser/server1/settings"
SCOPES = {
    "thuong": {
        "title": "Quái thường (train, theo cấp)",
        "find": f"ls {_SV}/item/npcdroprate.ini {_SV}/item/armydroprate.ini {_SV}/droprate/npcdroprate*.ini 2>/dev/null",
    },
    "boss": {
        "title": "Boss & NPC hoàng kim",
        "find": f"find {_SV}/droprate/boss {_SV}/droprate/goldennpc -name '*.ini' 2>/dev/null",
    },
}


def _load_baseline(svc):
    try:
        return json.loads(svc.read_file(BASELINE, "utf-8"))
    except Exception:
        return {}


def _save_baseline(svc, data):
    backup_service._ensure_dir(svc)
    svc.write_file(BASELINE, json.dumps(data, indent=1), "utf-8", make_backup=False)


def _read_main(text):
    """Trả (randrange_entry, tong_randrate) từ 1 file droprate đã đọc."""
    rr, total = None, 0
    for e in iniparse.parse_all(text):
        if e["key"] == "Main.RandRange":
            rr = e
        elif e["name"] == "RandRate" and e["type"] == "int":
            total += int(e["value"])
    return rr, total


def _scope_files(svc, scope_id):
    out, _ = svc.run(SCOPES[scope_id]["find"], timeout=20)
    return [ln.strip() for ln in out.splitlines() if ln.strip().endswith(".ini")]


def status(svc):
    """Hiện trạng từng scope: số file + hệ số nhân hiện tại (so với gốc)."""
    baseline = _load_baseline(svc)
    changed = False
    result = []
    for sid, meta in SCOPES.items():
        files = _scope_files(svc, sid)
        mults = []
        for path in files:
            try:
                text = svc.read_file(path, "latin-1")
            except Exception:
                continue
            rr, _total = _read_main(text)
            if not rr:
                continue
            cur = int(rr["value"])
            if path not in baseline:  # lần đầu thấy file -> giá trị hiện tại là gốc
                baseline[path] = cur
                changed = True
            if cur > 0:
                mults.append(baseline[path] / cur)
        avg = round(sum(mults) / len(mults), 2) if mults else 1.0
        result.append({"id": sid, "title": meta["title"], "files": len(files), "mult": avg})
    if changed:
        _save_baseline(svc, baseline)
    return result


def apply(svc, scope_id, mult):
    """Đặt hệ số rơi đồ cho scope (tính từ GỐC). mult=1 là trả về nguyên bản."""
    if scope_id not in SCOPES:
        raise ValueError("Không rõ phạm vi: " + str(scope_id))
    mult = float(mult)
    if not (0.1 <= mult <= 50):
        raise ValueError("Hệ số phải trong khoảng 0.1 – 50")
    baseline = _load_baseline(svc)
    done, skipped = [], []
    for path in _scope_files(svc, scope_id):
        try:
            text = svc.read_file(path, "latin-1")
            rr, total = _read_main(text)
            if not rr:
                skipped.append(posixpath.basename(path))
                continue
            if path not in baseline:
                baseline[path] = int(rr["value"])
            orig = baseline[path]
            new = max(total or 1, int(round(orig / mult)))  # kẹp: không nhỏ hơn tổng lát trúng
            if str(new) == rr["value"]:
                continue  # không đổi thì khỏi ghi
            backup_service.snapshot(svc, path, f"Đặt hệ số rơi đồ x{mult:g} ({SCOPES[scope_id]['title']})")
            new_text, applied = iniparse.apply_patch_by_line(text, {rr["line"]: str(new)})
            if applied:
                svc.write_file(path, new_text, "latin-1", make_backup=True)
                done.append(posixpath.basename(path))
        except Exception:
            skipped.append(posixpath.basename(path))
    _save_baseline(svc, baseline)
    return {"changed": done, "skipped": skipped}
