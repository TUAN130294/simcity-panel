"""Đọc/ghi các DANH SÁCH trong file Lua (chat bot, tên bang, bảng giờ...).

Tìm bảng theo 'marker' (vd 'SimCityChat.chatCollection'), lấy span từ '{' tới '}'
khớp (đếm độ sâu ngoặc). Hai loại:
- kind "text" (mặc định): bảng chuỗi "..." — ghi lại nhiều dòng, mỗi dòng 1 câu.
- kind "number": bảng số {0100, 0300, ...} — ghi lại đúng 1 dòng như nguyên bản.
Mọi thứ ngoài 2 ngoặc được giữ nguyên từng byte (kể cả comment sau '}').
"""
import re

_STR = re.compile(r'"((?:[^"\\]|\\.)*)"')
_NUM = re.compile(r'-?\d+')

# Danh mục các danh sách dữ liệu cho phép sửa trên web.
# rel = đường dẫn tương đối trong thư mục simcity; abs = đường dẫn tuyệt đối trên VM.
CATALOG = [
    {"id": "chat_normal", "title": "💬 Câu chat thường của bot",
     "rel": "plugins/pchat.lua", "marker": "SimCityChat.chatCollection",
     "desc": "Các câu bot nói ngẫu nhiên khi đi lại."},
    {"id": "chat_fight", "title": "⚔️ Câu chat khi đánh nhau",
     "rel": "plugins/pchat.lua", "marker": "SimCityChat.chatCollectionFight",
     "desc": "Các câu bot nói khi đang chiến đấu."},
    {"id": "bang_names", "title": "🏳️ Tên bang hội của bot",
     "rel": "class/sim_citizen.lua", "marker": "g_TK_BangNames",
     "desc": "Pool tên bang gắn trước tên bot (nếu bật % tên bang)."},
    {"id": "bang_ranks", "title": "🎖️ Chức vụ trong bang",
     "rel": "class/sim_citizen.lua", "marker": "g_TK_BangRanks",
     "desc": "Bang Chủ / Trưởng lão / Đường Chủ / Đệ Tử..."},
    {"id": "tk_hours", "title": "🕐 Giờ báo danh Tống Kim", "kind": "number",
     "abs": "/home/jxser/server1/script/global/nobitaxd/config/cfg_server.lua",
     "marker": "ThoiGianOpenTK",
     "desc": "Mỗi dòng 1 khung giờ, viết dạng GiờPhút: 0100 = 1 giờ sáng, 1300 = 1 giờ chiều, 2300 = 11 giờ đêm."},
    {"id": "phlt_hours", "title": "🔥 Giờ báo danh Phong Hỏa Liên Thành", "kind": "number",
     "abs": "/home/jxser/server1/script/global/nobitaxd/config/cfg_server.lua",
     "marker": "ThoiGianOpenPHLT",
     "desc": "Mỗi dòng 1 khung giờ dạng GiờPhút (0200 = 2 giờ sáng...). Tránh trùng giờ Tống Kim."},
    {"id": "datau_types", "title": "📜 Loại nhiệm vụ Dã Tẩu được random", "kind": "number",
     "abs": "/home/jxser/server1/script/global/nobitaxd/config/cfg_server.lua",
     "marker": "Loai_NV_Muon_Nhan",
     "desc": "Mỗi dòng 1 con số: 0 = tắt (random thường), 1 = tìm mảnh Sơn Hà Xã Tắc, 2 = tìm/mua vật phẩm, 3 = tìm/xem vật phẩm có thuộc tính, 4 = tìm bản đồ."},
]
BY_ID = {c["id"]: c for c in CATALOG}


def _span(text, marker):
    """Trả về (brace_open_index, brace_close_index) của bảng chứa marker."""
    idx = text.find(marker)
    if idx < 0:
        return None
    open_i = text.find("{", idx)
    if open_i < 0:
        return None
    depth = 0
    i = open_i
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return open_i, i
        i += 1
    return None


def extract(text, marker):
    sp = _span(text, marker)
    if not sp:
        return None
    open_i, close_i = sp
    inner = text[open_i + 1:close_i]
    raw_items = _STR.findall(inner)
    # unescape để hiển thị chuỗi thật (\" -> ", \\ -> \)
    items = [it.replace('\\"', '"').replace("\\\\", "\\") for it in raw_items]
    return {"items": items, "open": open_i, "close": close_i}


def extract_numbers(text, marker):
    """Bảng số 1 dòng {0100, 0300, ...} -> danh sách chuỗi số (giữ nguyên số 0 đầu)."""
    sp = _span(text, marker)
    if not sp:
        return None
    open_i, close_i = sp
    return {"items": _NUM.findall(text[open_i + 1:close_i]), "open": open_i, "close": close_i}


def rebuild_numbers(text, marker, items):
    """Ghi lại bảng số ĐÚNG 1 DÒNG như nguyên bản, giữ nguyên phần ngoài ngoặc."""
    sp = _span(text, marker)
    if not sp:
        return None
    open_i, close_i = sp
    return text[:open_i + 1] + ", ".join(items) + text[close_i:]


def rebuild(text, marker, items):
    sp = _span(text, marker)
    if not sp:
        return None
    open_i, close_i = sp
    # dò indent của dòng chứa '{' để căn ngoặc đóng
    line_start = text.rfind("\n", 0, open_i) + 1
    indent = ""
    for ch in text[line_start:open_i]:
        if ch in " \t":
            indent += ch
        else:
            indent = ""  # có chữ trước -> lấy indent đầu dòng
    lead = text[line_start:open_i]
    base_indent = lead[:len(lead) - len(lead.lstrip(" \t"))]
    body = "\n"
    for it in items:
        esc = it.replace("\\", "\\\\").replace('"', '\\"')
        body += f'{base_indent}\t"{esc}",\n'
    body += base_indent
    return text[:open_i + 1] + body + text[close_i:]
