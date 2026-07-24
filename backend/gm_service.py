"""GM Tool — 'hòm thư lệnh': panel ghi 1 file lệnh Lua, vòng lặp SimCity trong
game (mainLoop, chạy ~1 giây/lần) đọc → thực thi → xoá, rồi ghi kết quả ra để
panel đọc lại. Không cần restart để chạy từng lệnh (chỉ cần cài móc 1 lần).

Cài móc = nút trên panel (giống bộ nâng cấp): tải gmbox.lua lên + chèn 2 dòng
vào main.lua, đối chiếu chuỗi, tự backup, chạy lại không hỏng. Làm được trên
mọi server gốc.

An toàn: poll ĐỔI TÊN file lệnh trước khi chạy → lệnh lỗi cũng không lặp lại
(không kẹt crash-loop); GMBoxPoll gọi SAU khi mainLoop đã tự đăng ký lại timer
nên tick không chết. Nhân vật phải đang ONLINE (SearchPlayer chỉ thấy người
đang chơi) — đúng nhu cầu chơi solo.
"""
import posixpath
import time

# cwd của game = /home/jxser/server1 -> file lệnh nằm thẳng ở đây
SERVER_ROOT = "/home/jxser/server1"
CMD_FILE = SERVER_ROOT + "/gmbox_cmd.lua"
TMP_FILE = SERVER_ROOT + "/gmbox_cmd.tmp"
RESULT_FILE = SERVER_ROOT + "/gmbox_result.txt"
MAIN_LUA = SERVER_ROOT + "/script/global/nobitaxd/vdk/simcity/main.lua"
GMBOX_LUA = SERVER_ROOT + "/script/global/nobitaxd/vdk/simcity/gmbox.lua"

# Nội dung gmbox.lua — cú pháp Lua 4 (engine JX): openfile/write/closefile/remove/rename.
GMBOX_LUA_SRC = """-- ============================================================
-- GM Box - hom thu lenh (cai boi SimCity Panel, dung sua tay)
-- Panel ghi gmbox_cmd.lua -> mainLoop goi GMBoxPoll() moi tick.
-- ============================================================
GMBOX_CMD = "gmbox_cmd.lua"
GMBOX_RUN = "gmbox_run.lua"
GMBOX_RESULT = "gmbox_result.txt"

function GMBox_Result(msg)
    local h = openfile(GMBOX_RESULT, "w")
    if h then
        write(h, msg)
        closefile(h)
    end
end

function GMBoxPoll()
    -- don rac lan truoc (neu lenh truoc loi giua chung)
    local old = openfile(GMBOX_RUN, "r")
    if old then
        closefile(old)
        remove(GMBOX_RUN)
    end
    -- co lenh moi khong?
    local f = openfile(GMBOX_CMD, "r")
    if not f then
        return
    end
    closefile(f)
    -- CONSUME truoc khi chay: doi ten -> lenh loi cung khong lap lai tick sau
    rename(GMBOX_CMD, GMBOX_RUN)
    dofile(GMBOX_RUN)
    remove(GMBOX_RUN)
end
"""

_INCLUDE_LINE = 'Include("\\\\script\\\\global\\\\nobitaxd\\\\vdk\\\\simcity\\\\gmbox.lua")'
_HEAD_ANCHOR = 'Include("\\\\script\\\\global\\\\nobitaxd\\\\vdk\\\\simcity\\\\head.lua")'
# dòng re-arm timer BÊN TRONG mainLoop (có thụt đầu dòng — phân biệt với dòng cuối file)
_TIMER_ANCHOR = '    AddTimer(REFRESH_RATE, "mainLoop", SimCitizen)'
_POLL_LINE = "    GMBoxPoll()"


def is_installed(svc):
    """Móc GM đã cài chưa (main.lua có gọi GMBoxPoll và gmbox.lua tồn tại)."""
    try:
        main = svc.read_file(MAIN_LUA, "latin-1")
    except Exception:
        return False
    if "GMBoxPoll" not in main:
        return False
    try:
        svc.read_file(GMBOX_LUA, "latin-1")
        return True
    except Exception:
        return False


def install_hook(svc):
    """Cài móc GM: tải gmbox.lua + chèn Include & GMBoxPoll vào main.lua.
    Idempotent — chạy lại khi đã cài thì không đổi gì."""
    from backend import backup_service
    # 1. gmbox.lua (ghi mới hoặc cập nhật nội dung mới nhất)
    svc.write_file(GMBOX_LUA, GMBOX_LUA_SRC, "latin-1", make_backup=False)
    # 2. main.lua
    main = svc.read_file(MAIN_LUA, "latin-1")
    changed = []
    if _INCLUDE_LINE not in main:
        if _HEAD_ANCHOR not in main:
            raise RuntimeError("Không tìm thấy dòng Include head.lua trong main.lua — server lạ?")
        main = main.replace(_HEAD_ANCHOR, _HEAD_ANCHOR + "\n" + _INCLUDE_LINE, 1)
        changed.append("Include gmbox.lua")
    if "GMBoxPoll()" not in main:
        if main.count(_TIMER_ANCHOR) < 1:
            raise RuntimeError("Không tìm thấy dòng AddTimer trong mainLoop — server lạ?")
        main = main.replace(_TIMER_ANCHOR, _TIMER_ANCHOR + "\n" + _POLL_LINE, 1)
        changed.append("gọi GMBoxPoll trong mainLoop")
    if changed:
        backup_service.snapshot(svc, MAIN_LUA, "Cài móc GM Tool (hòm thư lệnh) vào mainLoop")
        svc.write_file(MAIN_LUA, main, "latin-1", make_backup=True)
    return {"changed": changed, "already": not changed}


def send_command(svc, lua_body, wait=8.0):
    """Gửi 1 lệnh Lua vào hòm thư, chờ game trả kết quả (tối đa `wait` giây).

    Lệnh phải tự gọi GMBox_Result("...") để báo về. Trả (ok, message).
    """
    # xoá kết quả cũ để không đọc nhầm
    try:
        svc.run("rm -f " + RESULT_FILE, timeout=10)
    except Exception:
        pass
    # ghi file tạm rồi đổi tên (atomic) -> game không đọc phải file ghi dở
    svc.write_file(TMP_FILE, lua_body, "latin-1", make_backup=False)
    svc.run("mv -f " + TMP_FILE + " " + CMD_FILE, timeout=10)
    # chờ kết quả
    deadline = time.time() + wait
    while time.time() < deadline:
        try:
            res = svc.read_file(RESULT_FILE, "latin-1")
            if res.strip():
                svc.run("rm -f " + RESULT_FILE, timeout=10)
                ok = not res.strip().upper().startswith(("OFFLINE", "LOI", "TUI DAY"))
                return ok, res.strip()
        except Exception:
            pass
        time.sleep(0.8)
    # hết giờ mà chưa có kết quả: có thể móc chưa chạy (chưa reload) hoặc game bận
    return False, ("Chưa nhận được phản hồi sau %ds. "
                   "Nếu vừa cài móc GM lần đầu, cần Restart server 1 lần để móc hoạt động." % int(wait))


def _q(s):
    """Bọc chuỗi vào nháy kép Lua an toàn (thoát \\ và ")."""
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _wrap_player(name, body_lua, ok_msg):
    """Sinh lệnh Lua: tìm người chơi online theo tên, đổi ngữ cảnh, chạy body."""
    return (
        "do\n"
        "  local idx = SearchPlayer(" + _q(name) + ")\n"
        "  if idx and idx > 0 then\n"
        "    local old = PlayerIndex\n"
        "    PlayerIndex = idx\n"
        "    " + body_lua + "\n"
        "    PlayerIndex = old\n"
        "    GMBox_Result(" + _q(ok_msg) + ")\n"
        "  else\n"
        "    GMBox_Result(" + _q("OFFLINE: khong thay '" + name + "' dang online") + ")\n"
        "  end\n"
        "end\n"
    )


# ---------- các hành động GM (sinh thân lệnh Lua) ----------
def cmd_money(name, kind, amount):
    """kind: 'nganluong' (Earn, đơn vị vạn), 'tiendong' (id 417), 'knb' (id 343)."""
    amount = int(amount)
    if kind == "nganluong":
        body = "Earn(" + str(amount) + ")"
        ok = "Da phat " + str(amount) + " van ngan luong"
    elif kind in ("tiendong", "knb"):
        item_id = 417 if kind == "tiendong" else 343
        ten = "Tien Dong" if kind == "tiendong" else "Kim Nguyen Bao"
        body = ("if CalcFreeItemCellCount() < 1 then GMBox_Result(" + _q("TUI DAY") + "); "
                "PlayerIndex = old; return end\n"
                "    AddStackItem(" + str(amount) + ",4," + str(item_id) + ",1,1,0,0,0)")
        ok = "Da phat " + str(amount) + " " + ten
    else:
        raise ValueError("Loại tiền không hợp lệ")
    return _wrap_player(name, body, ok)


def cmd_level(name, level):
    """Nâng nhân vật LÊN cấp `level` (chỉ tăng, không hạ)."""
    level = int(level)
    body = ("local cur = GetLevel()\n"
            "    if cur < " + str(level) + " then ST_LevelUp(" + str(level) + " - cur) end")
    return _wrap_player(name, body, "Da nang len cap " + str(level))


def cmd_repute(name, amount):
    body = "AddRepute(" + str(int(amount)) + ")"
    return _wrap_player(name, body, "Da them " + str(int(amount)) + " diem danh vong")


def cmd_item(name, genre, detail, particular, level=1, need_cells=1):
    """Phát 1 vật phẩm/ngựa. genre/detail/particular theo bảng game."""
    g, d, p, lv = int(genre), int(detail), int(particular), int(level)
    body = ("if CalcFreeItemCellCount() < " + str(int(need_cells)) + " then GMBox_Result(" + _q("TUI DAY") + "); "
            "PlayerIndex = old; return end\n"
            "    local ii = AddItem(" + f"{g},{d},{p},{lv},0,0" + ")\n"
            "    if ii and ii > 0 then SetItemBindState(ii, -1) end")
    return _wrap_player(name, body, "Da phat vat pham")


# Danh mục ngựa (từ bảng TAB_THUCUOI trong npcthunghiem.lua) — genre 0, detail 10.
HORSES = [
    {"name": "Ô Vân Đạp Tuyết", "g": 0, "d": 10, "p": 5, "lv": 6},
    {"name": "Xích Thố", "g": 0, "d": 10, "p": 5, "lv": 7},
    {"name": "Tuyệt Ảnh", "g": 0, "d": 10, "p": 5, "lv": 8},
    {"name": "Đích Lô", "g": 0, "d": 10, "p": 5, "lv": 9},
    {"name": "Chiếu Dạ Ngọc Sư Tử", "g": 0, "d": 10, "p": 5, "lv": 10},
    {"name": "Phi Vân", "g": 0, "d": 10, "p": 8, "lv": 10},
    {"name": "Bôn Tiêu", "g": 0, "d": 10, "p": 6, "lv": 10},
    {"name": "Phiên Vũ", "g": 0, "d": 10, "p": 7, "lv": 10},
]


def cmd_horse(name, idx):
    """Phát ngựa thứ `idx` trong HORSES cho nhân vật. Ngựa chiếm ô 2x3."""
    h = HORSES[int(idx)]
    body = ("if CalcFreeItemCellCount() < 6 then GMBox_Result(" + _q("TUI DAY") + "); "
            "PlayerIndex = old; return end\n"
            "    local ii = AddItem(" + f"{h['g']},{h['d']},{h['p']},{h['lv']},0,0" + ")\n"
            "    if ii and ii > 0 then SetItemBindState(ii, -1) end")
    return _wrap_player(name, body, "Da phat ngua " + h["name"])


def cmd_goldset(name, ids):
    """Phát 1 bộ trang bị Hoàng Kim (danh sách gold-item id) bằng AddGoldItem(0,id)."""
    ids = [int(i) for i in ids]
    lines = "\n    ".join("AddGoldItem(0, %d)" % i for i in ids)
    body = ("if CalcFreeItemCellCount() < %d then GMBox_Result(" % (len(ids) * 6) + _q("TUI DAY (can it nhat "
            + str(len(ids)) + " o rong)") + "); PlayerIndex = old; return end\n    " + lines)
    return _wrap_player(name, body, "Da phat bo trang bi (" + str(len(ids)) + " mon)")


def cmd_purple(name, genre, detail, particular):
    """Phát đồ tím: loop 5 series ngũ hành (AddQualityItem quality=2 level=10)."""
    g, d, p = int(genre), int(detail), int(particular)
    body = ("if CalcFreeItemCellCount() < 5 then GMBox_Result(" + _q("TUI DAY") + "); PlayerIndex = old; return end\n"
            "    for i = 0, 4 do AddQualityItem(2, %d, %d, %d, 10, i, 0, -1, -1, -1, -1, -1, -1) end" % (g, d, p))
    return _wrap_player(name, body, "Da phat do tim (5 mon ngu hanh)")


def cmd_skill(name, base_ids, adv_ids):
    """Học skill 1 phái: base cấp 1 (nếu chưa có), adv đặt cấp 20 (trừ support skill)."""
    base = "\n    ".join("if HaveMagic(%d) == -1 then AddMagic(%d) end" % (i, i) for i in base_ids)
    adv_lines = []
    from backend import gm_catalog
    for i in adv_ids:
        if i in gm_catalog._SKILL_SUPPORT:
            adv_lines.append("if HaveMagic(%d) == -1 then AddMagic(%d) end" % (i, i))
        else:
            adv_lines.append("AddMagic(%d, 20)" % i)
    body = base + "\n    " + "\n    ".join(adv_lines)
    return _wrap_player(name, body, "Da hoc skill phai (chac chan dung phai moi len duoc)")


def cmd_boss(name, npc_id, series, level):
    """Triệu boss tại chỗ nhân vật đang đứng (cần map cho phép chiến đấu)."""
    npc_id, series, level = int(npc_id), int(series), int(level)
    body = (
        "if GetFightState() == 0 then GMBox_Result(" + _q("KHONG THE: dang o map cam danh (phi chien). "
        "Di toi map co the danh nhau roi thu lai.") + "); PlayerIndex = old; return end\n"
        "    local nw, nx, ny = GetWorldPos()\n"
        "    local bi = AddNpcEx(%d, %d, %d, SubWorldID2Idx(nw), nx*32, ny*32, 1, " % (npc_id, level, series) + _q("Boss") + ", 1)\n"
        "    if bi and bi > 0 then\n"
        "      SetNpcDeathScript(bi, \"\\\\script\\\\missions\\\\boss\\\\bossdeath.lua\")\n"
        "      SetNpcParam(bi, 1, %d)\n" % npc_id +
        "      SetNpcTimer(bi, 120*60*18)\n"
        "    end")
    return _wrap_player(name, body, "Da trieu boss tai cho ban dung")


def cmd_ping(name):
    """Lệnh vô hại để test kênh: chỉ nhắn 1 câu cho nhân vật."""
    body = 'Msg2Player("GM Tool: ket noi thanh cong!")'
    return _wrap_player(name, body, "OK: da nhan tin cho " + name)
