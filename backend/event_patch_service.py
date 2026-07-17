"""Tự vá script máy chủ để panel chỉnh được event — dùng cho server còn CODE GỐC.

Panel chỉ sửa được các hằng số có thật trong file. Bản game gốc hardcode tỉ lệ
rơi/thông số event thẳng trong script, nên máy chủ chưa vá thì các ô event trên
panel không có tác dụng. Module này nhận diện từng file đang ở bản gốc (đúng
byte mẫu) và vá y hệt bản chuẩn: hoist số cứng thành hằng CFG_/EVT_, mở cổng
nhặt Túi nguyên liệu (bỏ bắt buộc nạp thẻ), sửa bug giá shop túi. Mỗi file đều
snapshot trước khi ghi (khôi phục ở tab Backup). Vá xong phải RESTART server.

Trạng thái mỗi file: patched (đã vá) / stock (bản gốc, vá được) / unknown
(script khác bản gốc — không đụng vào, tránh phá server người khác).
"""
import hashlib
import json
import os
import re

from . import backup_service

_SCRIPT = "/home/jxser/server1/script"
_ACT = _SCRIPT + "/activitysys/config"

_CFG_BLOCK = (
    "\n-- ==== EVENT: Tui nguyen lieu & banh event (panel chinh duoc) ====\n"
    "CFG_EventTui_TiLeRoi\t= 5\t-- % roi Tui nguyen lieu moi lan giet quai thuong (0-100)\n"
    'CFG_EventTui_CapQuai\t= "10,20,30,40,50,60,70,80,90"\t-- cac moc cap quai co roi tui\n'
    "CFG_EventTui_CanNapThe\t= 0\t-- 1 = chi nguoi nap the moi nhat duoc tui (goc); 0 = ai cung nhat duoc\n"
    "CFG_EventBanh_ExpNho\t= 200000\t-- exp banh event nho (item 1442)\n"
    "CFG_EventBanh_ExpVua\t= 500000\t-- exp banh event vua (item 1443)\n"
    "CFG_EventBanh_ExpLon\t= 1000000\t-- exp banh event lon (item 1444)\n"
    "CFG_EventBanh_ExpMax\t= 400000000\t-- tran tong exp nhan tu banh event / 1 nhan vat\n"
)

_INC_BONUS = 'Include("\\\\script\\\\global\\\\nobitaxd\\\\config\\\\cfg_activity_bonus.lua")'
_INC_SERVER = 'Include("\\\\script\\\\global\\\\nobitaxd\\\\config\\\\cfg_server.lua")'

_PICK_OLD = "function IsPickable( nItemIndex, nPlayerIndex )\n\tif GetExtPoint(0) <= 0 then"
_PICK_NEW = ("function IsPickable( nItemIndex, nPlayerIndex )\n"
             "\t-- [PANEL] cong tac CFG_EventTui_CanNapThe trong cfg_server.lua (0 = ai cung nhat duoc tui)\n"
             "\tif CFG_EventTui_CanNapThe == 1 and GetExtPoint(0) <= 0 then")


def _evt(act, pairs, header):
    """Job hoist hằng EVT_ cho 1 activity event mùa."""
    return {"path": "%s/%d/config.lua" % (_ACT, act), "marker": "EVT_",
            "desc": "Hoist thông số event %d thành hằng EVT_ (panel chỉnh được)" % act,
            "pairs": pairs,
            "prepend": "-- ==== Hang event (panel chinh duoc) ====\n" + header + "\n"}


PATCHES = [
    {"path": _SCRIPT + "/global/nobitaxd/config/cfg_server.lua", "marker": "CFG_EventTui_TiLeRoi",
     "desc": "Thêm hằng event: tỉ lệ rơi túi, cấp quái, cổng nạp thẻ, exp bánh",
     "pairs": [], "append": _CFG_BLOCK},
    {"path": _ACT + "/36/config.lua", "marker": "CFG_EventTui_TiLeRoi",
     "desc": "Tỉ lệ rơi + mốc cấp quái của Túi nguyên liệu lấy từ cfg_server",
     "pairs": [(_INC_BONUS, _INC_BONUS + "\n" + _INC_SERVER),
               ('{"10,20,30,40,50,60,70,80,90"}', "{CFG_EventTui_CapQuai}"),
               ('{ITEM_SuKien,1,"5"}', "{ITEM_SuKien,1,CFG_EventTui_TiLeRoi}")]},
    {"path": _SCRIPT + "/global/nobitaxd/item/dropitemevent.lua", "marker": "CFG_EventTui_CanNapThe",
     "desc": "Điều kiện nạp thẻ khi nhặt túi → công tắc CFG_EventTui_CanNapThe",
     "pairs": [(_PICK_OLD, _PICK_NEW)]},
    {"path": _SCRIPT + "/item/usecake.lua", "marker": "CFG_EventBanh_ExpMax",
     "desc": "Exp bánh event + trần exp lấy từ hằng cfg_server",
     "pairs": [("if nCurAddExp >= 400000000 then", "if nCurAddExp >= CFG_EventBanh_ExpMax then"),
               ("nExpNum = 200000", "nExpNum = CFG_EventBanh_ExpNho"),
               ("nExpNum = 500000", "nExpNum = CFG_EventBanh_ExpVua"),
               ("nExpNum = 1000000", "nExpNum = CFG_EventBanh_ExpLon")]},
    _evt(2, [('{ITEM_XMAS_%s,1,25} ' % n, '{ITEM_XMAS_%s,1,EVT_TiLeRoi_MapRieng} ' % n)
             for n in ("APPLE", "LANTERN", "CANDY", "BELL", "STAR")] +
            [('{ITEM_XMAS_%s,1,5} ' % n, '{ITEM_XMAS_%s,1,EVT_TiLeRoi_Map322} ' % n)
             for n in ("APPLE", "LANTERN", "CANDY", "BELL", "STAR")],
         "EVT_TiLeRoi_MapRieng = 25\t-- % roi do Noel tai 5 map chi dinh\n"
         "EVT_TiLeRoi_Map322 = 5\t-- % roi ca 5 loai do Noel tai map 322\n"),
    _evt(21, [('{6,1,2496,1,0,0},nExpiredTime=20101011,},1,"5"', '{6,1,2496,1,0,0},nExpiredTime=20101011,},1,EVT_TiLeRoi_BanhHatSen'),
              ('{6,1,2497,1,0,0},nExpiredTime=20101011,},1,"5"', '{6,1,2497,1,0,0},nExpiredTime=20101011,},1,EVT_TiLeRoi_BanhDauXanh'),
              ('{6,1,2498,1,0,0},nExpiredTime=20101011,},1,"1"', '{6,1,2498,1,0,0},nExpiredTime=20101011,},1,EVT_TiLeRoi_BanhKhoaiMon')],
         "EVT_TiLeRoi_BanhHatSen = 5\nEVT_TiLeRoi_BanhDauXanh = 5\nEVT_TiLeRoi_BanhKhoaiMon = 1\n"),
    _evt(22, [('nExpiredTime=20101213,},15,"100"', 'nExpiredTime=20101213,},EVT_SoLuong_DoKhangTuu,"100"')],
         "EVT_SoLuong_DoKhangTuu = 15\n"),
    _evt(25, [('nExpiredTime=20110121,},10,"100"', 'nExpiredTime=20110121,},EVT_SoLuong_PhongLangDo,"100"'),
              ('nExpiredTime=20110121,},15,"100"', 'nExpiredTime=20110121,},EVT_SoLuong_BossTheGioi,"100"')],
         "EVT_SoLuong_PhongLangDo = 10\nEVT_SoLuong_BossTheGioi = 15\n"),
    _evt(30, [('nExpiredTime=20111201,},1,"5"', 'nExpiredTime=20111201,},1,EVT_TiLeRoi_GiayTrang')],
         "EVT_TiLeRoi_GiayTrang = 5\n"),
    _evt(31, [('nExpiredTime=20110630,},1,"8"', 'nExpiredTime=20110630,},1,EVT_TiLeRoi_HopQuaXanh')],
         "EVT_TiLeRoi_HopQuaXanh = 8\n"),
    _evt(37, [('{ITEM_XMAS_CLOTHING,1,"6"}', '{ITEM_XMAS_CLOTHING,1,EVT_TiLeRoi_AoGiangSinh}')],
         "EVT_TiLeRoi_AoGiangSinh = 6\n"),
    _evt(1003, [('nExpiredTime=nItemExpiredTime,},1,"5"', 'nExpiredTime=nItemExpiredTime,},1,EVT_TiLeRoi_HoaHong')],
         "EVT_TiLeRoi_HoaHong = 5\n"),
    _evt(1008, [('{ITEM_HONEY_BOTTLE,1,"7"}', '{ITEM_HONEY_BOTTLE,1,EVT_TiLeRoi_LoMat}')],
         "EVT_TiLeRoi_LoMat = 7\n"),
]

# Bug bản gốc: shop test bán Túi nguyên liệu gói 200/100 vạn nhưng trừ 500 vạn
_SHOP_PATH = _SCRIPT + "/global/nobitaxd/npc/npcthunghiem.lua"
_SHOP_RE = [(200, "2000000"), (100, "1000000")]


def _shop_fix(txt):
    changed = 0
    for count, price in _SHOP_RE:
        pat = re.compile(r"Pay\(5000000\)(\s*\n\s*local tbItem = \{szName=\"[^\"]*\", tbProp=\{6,1,1502,1,0,0\}, nCount=%d\b)" % count)
        txt, n = pat.subn(lambda m, p=price: "Pay(%s)%s" % (p, m.group(1)), txt, count=1)
        changed += n
    return txt, changed


# ---- Vá kiểu THAY NGUYÊN FILE (bot SimCity — nhiều sửa nhỏ rải rác) ----
# backend/patches/manifest.json: [{path, sha_stock, sha_patched, payload}]
# Chỉ thay khi file trên server khớp TỪNG BYTE với bản gốc (sha_stock) — an toàn
# tuyệt đối với server đã tự sửa script riêng (khác gốc thì bỏ qua, báo lại).
_PATCH_DIR = os.path.join(os.path.dirname(__file__), "patches")


def _file_patches():
    try:
        with open(os.path.join(_PATCH_DIR, "manifest.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _sha(txt):
    return hashlib.sha1(txt.encode("latin-1")).hexdigest()


def _replace_state(txt, fp):
    h = _sha(txt)
    if h == fp["sha_patched"]:
        return "patched"
    return "stock" if h == fp["sha_stock"] else "unknown"


def _file_state(txt, p):
    if p["marker"] in txt:
        return "patched"
    if p.get("append") is not None:
        return "stock"
    return "stock" if all(txt.count(old) == 1 for old, _ in p["pairs"]) else "unknown"


def status(svc):
    """Trạng thái vá từng file (cả script event lẫn bot). `ready` = đã vá hết."""
    out = []
    for p in PATCHES:
        try:
            st = _file_state(svc.read_file(p["path"], "latin-1"), p)
        except Exception:
            st = "missing"
        out.append({"path": p["path"], "desc": p["desc"], "state": st})
    for fp in _file_patches():
        try:
            st = _replace_state(svc.read_file(fp["path"], "latin-1"), fp)
        except Exception:
            st = "missing"
        out.append({"path": fp["path"], "desc": "Thông số bot SimCity dùng hằng config (panel chỉnh được)", "state": st})
    return {"files": out, "ready": all(f["state"] == "patched" for f in out)}


def apply(svc):
    """Vá mọi file đang ở bản gốc. File 'unknown' bị bỏ qua và báo lại."""
    done, skipped = [], []
    for p in PATCHES:
        try:
            txt = svc.read_file(p["path"], "latin-1")
        except Exception as e:
            skipped.append({"path": p["path"], "reason": "không đọc được: %s" % e})
            continue
        st = _file_state(txt, p)
        if st == "patched":
            continue
        if st == "unknown":
            skipped.append({"path": p["path"], "reason": "script khác bản gốc — không tự vá để tránh hỏng"})
            continue
        for old, new in p["pairs"]:
            txt = txt.replace(old, new, 1)
        if p.get("prepend"):
            txt = p["prepend"] + txt
        if p.get("append"):
            txt = txt + p["append"]
        backup_service.snapshot(svc, p["path"], "[Kích hoạt chỉnh event] " + p["desc"])
        svc.write_file(p["path"], txt, "latin-1")
        done.append(p["path"])
    # file bot SimCity: thay nguyên file khi đúng bản gốc từng byte
    for fp in _file_patches():
        try:
            txt = svc.read_file(fp["path"], "latin-1")
        except Exception as e:
            skipped.append({"path": fp["path"], "reason": "không đọc được: %s" % e})
            continue
        st = _replace_state(txt, fp)
        if st == "patched":
            continue
        if st == "unknown":
            skipped.append({"path": fp["path"], "reason": "script khác bản gốc — không tự vá để tránh hỏng"})
            continue
        with open(os.path.join(_PATCH_DIR, fp["payload"]), encoding="latin-1", newline="") as f:
            payload = f.read()
        backup_service.snapshot(svc, fp["path"], "[Kích hoạt chỉnh event] Hằng config cho thông số bot")
        svc.write_file(fp["path"], payload, "latin-1")
        done.append(fp["path"])
    # bug giá shop túi (độc lập, có thể đã sửa)
    try:
        txt = svc.read_file(_SHOP_PATH, "latin-1")
        new, n = _shop_fix(txt)
        if n:
            backup_service.snapshot(svc, _SHOP_PATH, "[Kích hoạt chỉnh event] Sửa giá shop Túi nguyên liệu 200/100 vạn")
            svc.write_file(_SHOP_PATH, new, "latin-1")
            done.append(_SHOP_PATH)
    except Exception:
        pass
    return {"patched": done, "skipped": skipped}
