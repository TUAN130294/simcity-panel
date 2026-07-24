"""Chỉnh rơi đồ CHI TIẾT theo TỪNG file (từng loại quái / từng boss).

Khác droprate_service (nhân cả nhóm), đây cho chọn 1 file cụ thể rồi chỉnh
các núm ở [Main] của nó:
- RandRange = "vòng quay xổ số": NHỎ hơn = rơi NHIỀU hơn. Hiển thị dạng hệ số
  so với gốc cho dễ (x2 = rơi gấp đôi = RandRange gốc/2).
- MoneyRate / MoneyScale = tiền quái rơi.
- MagicRate = tỉ lệ ra đồ có thuộc tính (phẩm chất).

Không đụng tới từng món [N] (cần biết mã vật phẩm — quá sâu cho người dùng).
Baseline RandRange gốc lưu trên VM để hệ số luôn tính từ gốc.
"""
import json
import re

from backend import ini_config_parser as iniparse
from backend import backup_service

_DROP = "/home/jxser/server1/settings/droprate/"
_ITEM = "/home/jxser/server1/settings/item/"
BASELINE = backup_service.BACKUP_DIR + "/droprate-detail-baseline.json"

# Danh mục file có nhãn tiếng Việt. File không liệt kê vẫn dò được qua scan().
FILES = [
    {"id": "chung", "file": _ITEM + "npcdroprate.ini", "title": "Quái thường (chung)"},
    {"id": "army", "file": _ITEM + "armydroprate.ini", "title": "Quái quan binh"},
] + [
    {"id": f"lv{n}", "file": _DROP + f"npcdroprate{n}.ini", "title": f"Quái cấp {n}"}
    for n in (10, 20, 30, 40, 50, 60, 70, 80, 90, 110, 119)
] + [
    {"id": "datu", "file": _DROP + "datushashiwei.ini", "title": "Dã Tẩu Sát Thủ Vệ"},
    {"id": "boatthief", "file": _DROP + "npcdroprate_boatthief.ini", "title": "Thủy tặc (cướp thuyền)"},
    {"id": "fenglin_bac", "file": _DROP + "npcdroprate_fenglindubei.ini", "title": "Phong Lăng Độ (Bắc)"},
    {"id": "fenglin_nam", "file": _DROP + "npcdroprate_fenglindunan.ini", "title": "Phong Lăng Độ (Nam)"},
    {"id": "mobei", "file": _DROP + "npcdroprate_mobeicaoyuan.ini", "title": "Mạc Bắc Thảo Nguyên"},
]
BY_ID = {f["id"]: f for f in FILES}

_MAIN_KEYS = ["RandRange", "MoneyRate", "MoneyScale", "MagicRate"]


def _load_baseline(svc):
    try:
        return json.loads(svc.read_file(BASELINE, "utf-8"))
    except Exception:
        return {}


def _save_baseline(svc, data):
    backup_service._ensure_dir(svc)
    svc.write_file(BASELINE, json.dumps(data, indent=1), "utf-8", make_backup=False)


def _read_main(text):
    """Đọc các khoá [Main] + tổng RandRate (để không kẹp RandRange quá nhỏ)."""
    vals, total = {}, 0
    for e in iniparse.parse_all(text):
        if e["section"] == "Main" and e["name"] in _MAIN_KEYS:
            vals[e["name"]] = {"value": e["value"], "line": e["line"], "type": e["type"]}
        elif e["name"] == "RandRate" and e["type"] == "int":
            total += int(e["value"])
    return vals, total


def get_one(svc, file_id):
    meta = BY_ID.get(file_id)
    if not meta:
        raise ValueError("Không rõ file: " + str(file_id))
    text = svc.read_file(meta["file"], "latin-1")
    vals, total = _read_main(text)
    baseline = _load_baseline(svc)
    base_rr = baseline.get(meta["file"])
    cur_rr = int(vals.get("RandRange", {}).get("value", 0) or 0)
    if base_rr is None:
        base_rr = cur_rr
    mult = round(base_rr / cur_rr, 2) if cur_rr > 0 else 1.0
    return {
        "id": file_id, "title": meta["title"],
        "rand_mult": mult,                                  # độ hiếm dạng hệ số so với gốc
        "money_rate": int(vals.get("MoneyRate", {}).get("value", 0) or 0),
        "money_scale": int(vals.get("MoneyScale", {}).get("value", 0) or 0),
        "magic_rate": int(vals.get("MagicRate", {}).get("value", 0) or 0),
        "total_randrate": total,
    }


def list_all(svc):
    return [{"id": f["id"], "title": f["title"]} for f in FILES]


def patch_one(svc, file_id, rand_mult=None, money_rate=None, money_scale=None, magic_rate=None):
    """Chỉnh núm [Main] của 1 file. rand_mult tính từ RandRange GỐC."""
    meta = BY_ID.get(file_id)
    if not meta:
        raise ValueError("Không rõ file: " + str(file_id))
    text = svc.read_file(meta["file"], "latin-1")
    vals, total = _read_main(text)
    line_map = {}

    if rand_mult is not None:
        mult = float(rand_mult)
        if not (0.01 <= mult <= 100):
            raise ValueError("Hệ số rơi phải trong 0.01–100")
        baseline = _load_baseline(svc)
        if meta["file"] not in baseline:
            baseline[meta["file"]] = int(vals["RandRange"]["value"])
            _save_baseline(svc, baseline)
        orig = baseline[meta["file"]]
        new_rr = max(total or 1, int(round(orig / mult)))   # không nhỏ hơn tổng lát trúng
        line_map[vals["RandRange"]["line"]] = str(new_rr)

    for key, val in (("MoneyRate", money_rate), ("MoneyScale", money_scale), ("MagicRate", magic_rate)):
        if val is not None and key in vals:
            v = int(val)
            if v < 0:
                raise ValueError(key + " không được âm")
            line_map[vals[key]["line"]] = str(v)

    if not line_map:
        return {"changed": 0, "message": "Không có gì thay đổi."}
    new_text, applied = iniparse.apply_patch_by_line(text, line_map)
    if not applied:
        return {"changed": 0, "message": "Không ghi được (dòng lệch?)."}
    backup_service.snapshot(svc, meta["file"], "Chỉnh rơi đồ chi tiết: " + meta["title"])
    svc.write_file(meta["file"], new_text, "latin-1", make_backup=True)
    return {"changed": len(applied), "message": "Đã lưu — nhớ Restart server."}
