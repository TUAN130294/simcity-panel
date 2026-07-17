"""Event theo mùa (hệ activitysys 2010–2012) — bật/tắt + chỉnh thông số từng event.

Mỗi event bật/tắt bằng cặp ngày `pActivity.nStartDate/nEndDate` trong head.lua:
  BẬT  = start 2026 (quá khứ) → end 2037 (xa tương lai)  ⇒ luôn hoạt động
  TẮT  = start/end đều 2037 (chưa tới)                    ⇒ ngủ đông
Khi BẬT còn tự vá mọi hạn-sử-dụng vật phẩm hardcode năm 2000–2019 trong thư mục
event (không vá thì item rơi ra là hết hạn ngay). Thông số (tỉ lệ rơi, số lượng,
khung giờ quà) là hằng EVT_*/pActivity.* đã hoist sẵn — sửa theo dòng qua lua parser.
Mọi lần ghi đều snapshot vào tab Backup. Đổi xong phải RESTART server.
"""
import re
import time

from . import backup_service
from .lua_config_parser import parse_all, apply_patch_by_line

ROOT = "/home/jxser/server1/script/activitysys/config"
ON_START, ON_END = "202601010000", "203701010000"
OFF_START, OFF_END = "203712010000", "203712020000"

# Hạn dùng/ngày cũ 2000–2019 (8 hoặc 12 số) → đôn về 2026/2037 giữ nguyên độ dài
_OLD_DATE = re.compile(r"\b(n(?:Item)?ExpiredTime|nStartDate|nEndDate)(\s*=\s*)(20[01]\d{5}(?:\d{4})?)\b")


def _knob(var, file, label, desc, unit="%", vmin=0, vmax=100, step=1):
    return {"key": var.replace(".", "_"), "var": var, "file": file, "label": label,
            "desc": desc, "unit": unit, "min": vmin, "max": vmax, "step": step}


EVENTS = [
    {"key": "giangsinh2011", "acts": [2, 37], "name": "🎄 Giáng Sinh 2011",
     "desc": "Ông già Noel + tuần lộc xuất hiện trong thành, hộp quà rơi khắp map theo khung giờ, "
             "quái rơi 5 loại đồ Noel (Táo, Lồng đèn, Kẹo, Chuông, Sao) và Áo Giáng Sinh (cần tổng cấp 150).",
     "knobs": [
         _knob("EVT_TiLeRoi_MapRieng", "2/config.lua", "Tỉ lệ rơi đồ Noel — 5 map chỉ định",
               "Mỗi map trong 5 map sự kiện rơi 1 loại đồ Noel riêng với xác suất này."),
         _knob("EVT_TiLeRoi_Map322", "2/config.lua", "Tỉ lệ rơi đồ Noel — map 322",
               "Map 322 rơi cả 5 loại đồ Noel, mỗi loại xác suất này."),
         _knob("EVT_TiLeRoi_AoGiangSinh", "37/config.lua", "Tỉ lệ rơi Áo Giáng Sinh",
               "Xác suất rơi Áo Giáng Sinh khi giết quái (người chơi tổng cấp ≥ 150)."),
         _knob("pActivity.nRefreshGiftStartTime", "2/extend.lua", "Giờ bắt đầu rơi hộp quà",
               "Viết dạng GiờPhút: 1900 = 19:00. Trong khung giờ này hộp quà xuất hiện khắp map, 30 giây một đợt.",
               unit="GiờPhút", vmin=0, vmax=2359, step=100),
         _knob("pActivity.nRefreshGiftEndTime", "2/extend.lua", "Giờ ngừng rơi hộp quà",
               "Viết dạng GiờPhút: 2300 = 23:00. Phải sau giờ bắt đầu.", unit="GiờPhút", vmin=0, vmax=2359, step=100),
         _knob("pActivity.nRefreshCount", "2/extend.lua", "Số hộp quà mỗi đợt",
               "Mỗi đợt làm mới rơi bấy nhiêu hộp quà trên map sự kiện.", unit="hộp", vmax=500, step=10),
     ]},
    {"key": "trungthu2010", "acts": [21], "name": "🥮 Trung Thu 2010",
     "desc": "Giết quái rơi bánh Trung Thu (người chơi cấp ≥ 50): quái bãi 90 rơi Bánh Hạt Sen + Bánh Đậu Xanh, "
             "bãi 10–80 rơi Bánh Khoai Môn.",
     "knobs": [
         _knob("EVT_TiLeRoi_BanhHatSen", "21/config.lua", "Tỉ lệ rơi Bánh Hạt Sen", "Quái bãi cấp 90."),
         _knob("EVT_TiLeRoi_BanhDauXanh", "21/config.lua", "Tỉ lệ rơi Bánh Đậu Xanh", "Quái bãi cấp 90."),
         _knob("EVT_TiLeRoi_BanhKhoaiMon", "21/config.lua", "Tỉ lệ rơi Bánh Khoai Môn", "Quái bãi cấp 10–80."),
     ]},
    {"key": "nhagiao2010", "acts": [22], "name": "📖 Nhà giáo 20/11/2010",
     "desc": "Đánh Phong Lăng Độ rơi Đỗ Khang Tửu (100% mỗi lần, số lượng chỉnh được) + chuỗi nhiệm vụ tri ân.",
     "knobs": [
         _knob("EVT_SoLuong_DoKhangTuu", "22/config.lua", "Số Đỗ Khang Tửu mỗi lần",
               "Số bình rơi ra mỗi lần thắng Phong Lăng Độ.", unit="bình", vmax=200),
     ]},
    {"key": "nguyendan2011", "acts": [25], "name": "🎇 Nguyên Đán 2011 (Tết dương)",
     "desc": "Rơi Chùy Bạc Nguyên Đản: thắng Phong Lăng Độ và hạ Boss Thế Giới (100% mỗi lần, số lượng chỉnh được).",
     "knobs": [
         _knob("EVT_SoLuong_PhongLangDo", "25/config.lua", "Số Chùy Bạc — Phong Lăng Độ",
               "Số Chùy Bạc rơi mỗi lần thắng Phong Lăng Độ.", unit="cái", vmax=200),
         _knob("EVT_SoLuong_BossTheGioi", "25/config.lua", "Số Chùy Bạc — Boss Thế Giới",
               "Số Chùy Bạc rơi mỗi lần hạ Boss Thế Giới.", unit="cái", vmax=200),
     ]},
    {"key": "nhagiao2011", "acts": [30], "name": "📝 Nhà giáo 20/11/2011",
     "desc": "Giết quái rơi Giấy Trắng để đổi quà tri ân thầy cô (cần tổng cấp ≥ 150).",
     "knobs": [_knob("EVT_TiLeRoi_GiayTrang", "30/config.lua", "Tỉ lệ rơi Giấy Trắng", "Xác suất mỗi lần giết quái.")]},
    {"key": "sinhnhat2011", "acts": [31], "name": "🎂 Sinh nhật VLTK 2011",
     "desc": "Giết quái rơi Hộp Quà Màu Xanh mừng sinh nhật Võ Lâm Truyền Kỳ (cần tổng cấp ≥ 150).",
     "knobs": [_knob("EVT_TiLeRoi_HopQuaXanh", "31/config.lua", "Tỉ lệ rơi Hộp Quà Màu Xanh", "Xác suất mỗi lần giết quái.")]},
    {"key": "phienbanmoi2011", "acts": [1003], "name": "🆕 Mừng phiên bản mới 2011",
     "desc": "Giết quái rơi Hoa Hồng Đỏ đổi thưởng (cần tổng cấp ≥ 150).",
     "knobs": [_knob("EVT_TiLeRoi_HoaHong", "1003/config.lua", "Tỉ lệ rơi Hoa Hồng Đỏ", "Xác suất mỗi lần giết quái.")]},
    {"key": "tinhnhan2012", "acts": [1008], "name": "💘 Tình nhân 2012",
     "desc": "Giết quái rơi Lọ Mật — nguyên liệu sự kiện Valentine (cần tổng cấp ≥ 150).",
     "knobs": [_knob("EVT_TiLeRoi_LoMat", "1008/config.lua", "Tỉ lệ rơi Lọ Mật", "Xác suất mỗi lần giết quái.")]},
]


def _head(act):
    return "%s/%d/head.lua" % (ROOT, act)


def _now():
    return int(time.strftime("%Y%m%d%H%M"))


def _dates(svc, act):
    """(start, end) hiện tại trong head.lua của activity."""
    vals = {c["key"]: c["value"] for c in parse_all(svc.read_file(_head(act), "latin-1"))}
    return (int(vals.get("pActivity.nStartDate", 0) or 0), int(vals.get("pActivity.nEndDate", 0) or 0))


def status(svc):
    """Danh sách event + trạng thái + giá trị thông số (đọc file thật trên VM)."""
    out = []
    for ev in EVENTS:
        start, end = _dates(svc, ev["acts"][0])
        item = {"key": ev["key"], "name": ev["name"], "desc": ev["desc"],
                "active": start <= _now() < end if (start and end) else (start == 0),
                "knobs": []}
        cache = {}
        for k in ev["knobs"]:
            path = "%s/%s" % (ROOT, k["file"])
            if path not in cache:
                cache[path] = {c["key"]: c["value"] for c in parse_all(svc.read_file(path, "latin-1"))}
            item["knobs"].append({**{x: k[x] for x in ("key", "label", "desc", "unit", "min", "max", "step")},
                                  "value": cache[path].get(k["var"])})
        out.append(item)
    return out


def _find(key):
    ev = next((e for e in EVENTS if e["key"] == key), None)
    if not ev:
        raise ValueError("Không có event: " + str(key))
    return ev


def _set_dates(svc, act, start, end):
    path = _head(act)
    txt = svc.read_file(path, "latin-1")
    changes = {c["line"]: {"pActivity.nStartDate": start, "pActivity.nEndDate": end}[c["key"]]
               for c in parse_all(txt) if c["key"] in ("pActivity.nStartDate", "pActivity.nEndDate")}
    if len(changes) < 2:
        raise ValueError("head.lua của activity %d thiếu dòng ngày" % act)
    new, _ = apply_patch_by_line(txt, changes)
    backup_service.snapshot(svc, path, "Đổi ngày event (bật/tắt) activity %d" % act)
    svc.write_file(path, new, "latin-1")


def _fix_expiry(svc, act):
    """Đôn mọi hạn dùng/ngày cũ 2000–2019 trong thư mục event về 2026/2037 (giữ độ dài)."""
    folder = "%s/%d" % (ROOT, act)
    names, _ = svc.run("ls %s" % folder, timeout=15)
    for name in names.split():
        if not name.endswith(".lua"):
            continue
        path = "%s/%s" % (folder, name)
        txt = svc.read_file(path, "latin-1")

        def rep(m):
            base = "2026" if m.group(1) == "nStartDate" else "2037"
            return m.group(1) + m.group(2) + (base + "0101" + ("0000" if len(m.group(3)) == 12 else ""))
        new = _OLD_DATE.sub(rep, txt)
        if new != txt:
            backup_service.snapshot(svc, path, "Vá hạn dùng item event cũ (act %d) → còn hạn" % act)
            svc.write_file(path, new, "latin-1")


def toggle(svc, key, enable):
    """Bật/tắt event. Trả về trạng thái mới."""
    ev = _find(key)
    for act in ev["acts"]:
        if enable:
            _fix_expiry(svc, act)  # gồm cả head.lua nhưng ghi đè ngay dưới cho chắc
            _set_dates(svc, act, ON_START, ON_END)
        else:
            _set_dates(svc, act, OFF_START, OFF_END)
    return {"key": key, "active": bool(enable)}


def set_knob(svc, key, knob_key, value):
    """Đổi 1 thông số của event (sửa đúng dòng, snapshot trước)."""
    ev = _find(key)
    k = next((x for x in ev["knobs"] if x["key"] == knob_key), None)
    if not k:
        raise ValueError("Không có thông số: " + str(knob_key))
    try:
        val = int(float(value))
    except (TypeError, ValueError):
        raise ValueError("Giá trị phải là số")
    path = "%s/%s" % (ROOT, k["file"])
    txt = svc.read_file(path, "latin-1")
    line = next((c["line"] for c in parse_all(txt) if c["key"] == k["var"]), None)
    if line is None:
        raise ValueError("Không tìm thấy hằng %s trong %s" % (k["var"], k["file"]))
    new, applied = apply_patch_by_line(txt, {line: val})
    if not applied:
        raise ValueError("Không sửa được dòng %d" % line)
    backup_service.snapshot(svc, path, "Event %s: %s = %s" % (ev["name"], k["label"], val))
    svc.write_file(path, new, "latin-1")
    return {"key": key, "knob": knob_key, "value": val}
